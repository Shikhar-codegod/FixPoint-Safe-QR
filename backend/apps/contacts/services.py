import secrets
import hashlib
from datetime import timedelta
from typing import Optional, Tuple, Dict, Any
from django.db import transaction
from django.utils import timezone
from apps.audit.services import log_audit_event
from .models import EmergencyContact, ConsentStatus
from .utils import normalize_phone_number, compute_phone_hash

def create_emergency_contact(
    user,
    name: str,
    relationship: str,
    phone_number: str,
    email: str = '',
    priority_order: int = 1,
    is_primary: bool = False,
    preferred_language: str = 'en',
    notify_whatsapp: bool = True,
    notify_sms: bool = True,
    notify_call: bool = True,
    wave: int = 1
) -> EmergencyContact:
    normalized_phone = normalize_phone_number(phone_number)
    phone_hash = compute_phone_hash(normalized_phone)

    with transaction.atomic():
        if is_primary:
            EmergencyContact.objects.filter(user=user, is_primary=True).update(is_primary=False)
        
        contact = EmergencyContact.objects.create(
            user=user,
            name=name,
            relationship=relationship,
            phone_number=normalized_phone,
            phone_hash=phone_hash,
            email=email,
            priority_order=priority_order,
            is_primary=is_primary,
            preferred_language=preferred_language,
            notify_whatsapp=notify_whatsapp,
            notify_sms=notify_sms,
            notify_call=notify_call,
            wave=wave,
            consent_status=ConsentStatus.PENDING
        )
        log_audit_event(
            action='EMERGENCY_CONTACT_CREATED',
            actor=user,
            target_model='EmergencyContact',
            target_id=str(contact.id),
            payload={'name': name, 'relationship': relationship, 'priority_order': priority_order}
        )
    return contact

def update_emergency_contact(
    contact: EmergencyContact,
    user,
    validated_data: Dict[str, Any]
) -> EmergencyContact:
    with transaction.atomic():
        if validated_data.get('is_primary', False):
            EmergencyContact.objects.filter(user=user, is_primary=True).exclude(id=contact.id).update(is_primary=False)

        if 'phone_number' in validated_data:
            normalized_phone = normalize_phone_number(validated_data['phone_number'])
            contact.phone_number = normalized_phone
            contact.phone_hash = compute_phone_hash(normalized_phone)

        for field in [
            'name', 'relationship', 'email', 'priority_order', 'is_primary',
            'preferred_language', 'notify_whatsapp', 'notify_sms', 'notify_call', 'wave'
        ]:
            if field in validated_data:
                setattr(contact, field, validated_data[field])

        contact.save()
        log_audit_event(
            action='EMERGENCY_CONTACT_UPDATED',
            actor=user,
            target_model='EmergencyContact',
            target_id=str(contact.id),
            payload={'name': contact.name, 'relationship': contact.relationship}
        )
    return contact

def delete_emergency_contact(contact: EmergencyContact, user) -> None:
    contact_id = str(contact.id)
    with transaction.atomic():
        # Cancel any active notification chains linked to this contact
        try:
            from apps.notifications.models import ContactNotificationChain, ChainStatus, DeliveryAttempt, AttemptStatus
            chains = ContactNotificationChain.objects.filter(contact=contact, status=ChainStatus.ACTIVE)
            for chain in chains:
                chain.status = ChainStatus.CANCELLED
                chain.save(update_fields=['status', 'updated_at'])
                DeliveryAttempt.objects.filter(chain=chain, status=AttemptStatus.PENDING).update(status=AttemptStatus.CANCELLED)
        except Exception:
            pass

        contact.delete()
        log_audit_event(
            action='EMERGENCY_CONTACT_DELETED',
            actor=user,
            target_model='EmergencyContact',
            target_id=contact_id
        )

def request_contact_consent(contact: EmergencyContact, user) -> Tuple[EmergencyContact, str]:
    """
    Generates a 32-byte URL-safe token, stores ONLY its SHA-256 hash with 7-day expiry,
    and returns the contact and plaintext token.
    """
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()
    expires_at = timezone.now() + timedelta(days=7)

    with transaction.atomic():
        contact.consent_token_hash = token_hash
        contact.consent_token_expires_at = expires_at
        contact.consent_status = ConsentStatus.PENDING
        contact.save(update_fields=['consent_token_hash', 'consent_token_expires_at', 'consent_status', 'updated_at'])

        log_audit_event(
            action='CONTACT_CONSENT_REQUESTED',
            actor=user,
            target_model='EmergencyContact',
            target_id=str(contact.id),
            payload={'consent_status': contact.consent_status}
        )
    return contact, raw_token

def get_consent_request_info(token: str) -> Optional[Dict[str, Any]]:
    """
    Public lookup for consent page: returns only requester first name. No state change.
    """
    token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
    now = timezone.now()
    contact = EmergencyContact.objects.select_related('user').filter(
        consent_token_hash=token_hash,
        consent_token_expires_at__gt=now
    ).first()

    if not contact:
        return None

    return {
        'requester_first_name': contact.user.first_name or "A FixPoint user",
        'contact_name': contact.name,
        'preferred_language': contact.preferred_language
    }

def process_consent_decision(token: str, decision: str) -> Tuple[bool, str, Optional[EmergencyContact]]:
    """
    Processes single-use consent decision (accept/decline). Idempotent.
    """
    token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
    now = timezone.now()

    with transaction.atomic():
        contact = EmergencyContact.objects.filter(
            consent_token_hash=token_hash,
            consent_token_expires_at__gt=now
        ).first()

        if not contact:
            # Check if this token was already processed recently (idempotency check)
            return False, "Invalid or expired consent token.", None

        if decision == 'accept':
            contact.consent_status = ConsentStatus.GRANTED
            contact.consent_given_at = now
            contact.consent_token_hash = ''
            contact.save(update_fields=['consent_status', 'consent_given_at', 'consent_token_hash', 'updated_at'])
            log_audit_event(
                action='CONTACT_CONSENT_GRANTED',
                actor=None,
                target_model='EmergencyContact',
                target_id=str(contact.id),
                payload={'consent_status': contact.consent_status}
            )
            return True, "Emergency contact consent granted successfully.", contact
        elif decision == 'decline':
            contact.consent_status = ConsentStatus.DECLINED
            contact.consent_token_hash = ''
            contact.save(update_fields=['consent_status', 'consent_token_hash', 'updated_at'])
            log_audit_event(
                action='CONTACT_CONSENT_DECLINED',
                actor=None,
                target_model='EmergencyContact',
                target_id=str(contact.id),
                payload={'consent_status': contact.consent_status}
            )
            return True, "Emergency contact request declined.", contact
        else:
            return False, "Invalid decision.", None

def withdraw_contact_consent(contact: EmergencyContact, user) -> EmergencyContact:
    """
    Withdraws contact consent immediately and cancels active notification chains.
    """
    with transaction.atomic():
        contact.consent_status = ConsentStatus.WITHDRAWN
        contact.consent_withdrawn_at = timezone.now()
        contact.consent_token_hash = ''
        contact.save(update_fields=['consent_status', 'consent_withdrawn_at', 'consent_token_hash', 'updated_at'])

        # Cancel any active notification chains for this contact
        try:
            from apps.notifications.models import ContactNotificationChain, ChainStatus, DeliveryAttempt, AttemptStatus
            chains = ContactNotificationChain.objects.filter(contact=contact, status=ChainStatus.ACTIVE)
            for chain in chains:
                chain.status = ChainStatus.CANCELLED
                chain.save(update_fields=['status', 'updated_at'])
                DeliveryAttempt.objects.filter(chain=chain, status=AttemptStatus.PENDING).update(status=AttemptStatus.CANCELLED)
        except Exception:
            pass

        log_audit_event(
            action='CONTACT_CONSENT_WITHDRAWN',
            actor=user,
            target_model='EmergencyContact',
            target_id=str(contact.id),
            payload={'consent_status': contact.consent_status}
        )
    return contact
