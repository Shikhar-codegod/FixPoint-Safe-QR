import hmac
import hashlib
import logging
import secrets
from datetime import timedelta
from typing import Optional, Dict, Any, Tuple, List
from django.db import transaction
from django.utils import timezone
from django.conf import settings

from apps.audit.services import log_audit_event
from apps.contacts.utils import mask_phone_number
from .models import (
    NotificationRecord,
    NotificationChannel,
    NotificationStatus,
    ContactNotificationChain,
    ChainStatus,
    ChainStep,
    DeliveryAttempt,
    AttemptStatus,
)
from .providers.factory import get_provider

logger = logging.getLogger('apps.notifications')

def queue_notification(
    recipient_destination: str,
    body: str,
    channel: str = NotificationChannel.SMS,
    title: str = '',
    recipient=None
) -> NotificationRecord:
    """
    Foundational notification dispatcher with destination masking.
    """
    masked_dest = mask_phone_number(recipient_destination) if recipient_destination else ''
    record = NotificationRecord.objects.create(
        recipient=recipient,
        recipient_destination=masked_dest,
        channel=channel,
        title=title,
        body=body,
        status=NotificationStatus.QUEUED
    )
    from .tasks import dispatch_notification_task
    try:
        dispatch_notification_task.delay(str(record.id))
    except Exception as exc:
        logger.warning(f"Could not enqueue dispatch_notification_task: {exc}")
    return record


def start_contact_chains_for_alert(alert) -> Dict[str, Any]:
    """
    Initializes independent notification chains for all GRANTED emergency contacts of the alert owner.
    Supports wave escalation: Wave-2 contacts start 3 minutes later if Wave-1 contacts exist.
    """
    if not alert or not alert.user:
        return {'status': 'no_user', 'chains_created': 0}

    granted_contacts = list(alert.user.emergency_contacts.filter(consent_status='GRANTED'))
    if not granted_contacts:
        log_audit_event(
            action='NO_ELIGIBLE_CONTACTS',
            actor=alert.user,
            target_model='AlertRecord',
            target_id=str(alert.id),
            payload={'reason': 'No emergency contacts with GRANTED consent found.'}
        )
        return {'status': 'no_eligible_contacts', 'chains_created': 0}

    chains = []
    now = timezone.now()
    has_wave_1 = any(c.wave == 1 for c in granted_contacts)

    with transaction.atomic():
        for contact in granted_contacts:
            raw_ack_token = secrets.token_urlsafe(32)
            ack_hash = hashlib.sha256(raw_ack_token.encode('utf-8')).hexdigest()

            # Wave-2 starts 3 minutes later only if Wave-1 contacts exist
            if contact.wave == 2 and has_wave_1:
                initial_next_action = now + timedelta(minutes=3)
            else:
                initial_next_action = now

            chain, created = ContactNotificationChain.objects.get_or_create(
                alert=alert,
                contact=contact,
                defaults={
                    'status': ChainStatus.ACTIVE,
                    'current_step': ChainStep.WHATSAPP,
                    'next_action_at': initial_next_action,
                    'ack_token_hash': ack_hash,
                }
            )
            # Store temporary raw token on object in memory for demo/test access if newly created
            if created:
                chain.raw_ack_token_for_demo = raw_ack_token
            chains.append(chain)

    return {'status': 'success', 'chains_created': len(chains), 'chains': chains}


def process_chain(chain_id: str, now=None) -> Optional[ContactNotificationChain]:
    """
    Advances a single ContactNotificationChain inside a row-locked transaction.
    Orchestrates WhatsApp -> SMS -> Automated Call with deterministic failure escalation.
    """
    now = now or timezone.now()

    with transaction.atomic():
        try:
            chain = ContactNotificationChain.objects.select_for_update().select_related(
                'contact', 'alert', 'alert__user'
            ).get(id=chain_id)
        except ContactNotificationChain.DoesNotExist:
            logger.error(f"Notification chain {chain_id} does not exist.")
            return None

        # RE-CHECK: Chain must still be ACTIVE
        if chain.status != ChainStatus.ACTIVE:
            logger.info(f"Chain {chain_id} is in status {chain.status}; stopping processing.")
            return chain

        # RE-CHECK: Contact consent must still be GRANTED
        if chain.contact.consent_status != 'GRANTED':
            logger.info(f"Contact for chain {chain_id} consent is {chain.contact.consent_status}; cancelling chain.")
            chain.status = ChainStatus.CANCELLED
            chain.save(update_fields=['status', 'updated_at'])
            DeliveryAttempt.objects.filter(chain=chain, status=AttemptStatus.PENDING).update(status=AttemptStatus.CANCELLED)
            return chain

        # RE-CHECK: Alert must not be RESOLVED or CANCELLED
        if chain.alert.status in ['RESOLVED', 'CANCELLED']:
            logger.info(f"Alert {chain.alert_id} is {chain.alert.status}; cancelling notification chain.")
            chain.status = ChainStatus.CANCELLED
            chain.save(update_fields=['status', 'updated_at'])
            DeliveryAttempt.objects.filter(chain=chain, status=AttemptStatus.PENDING).update(status=AttemptStatus.CANCELLED)
            return chain

        # RE-CHECK: Wave 2 contacts cancel if any wave-1 contact has acknowledged
        if chain.contact.wave == 2:
            wave1_ack = ContactNotificationChain.objects.filter(
                alert=chain.alert,
                contact__wave=1,
                status=ChainStatus.ACKNOWLEDGED
            ).exists()
            if wave1_ack:
                logger.info(f"Wave-1 contact acknowledged alert {chain.alert_id}; cancelling wave-2 chain {chain_id}.")
                chain.status = ChainStatus.CANCELLED
                chain.save(update_fields=['status', 'updated_at'])
                return chain

        real_phone = chain.contact.phone_number
        masked_phone = mask_phone_number(real_phone)

        # ----------------- STEP 1: WHATSAPP -----------------
        if chain.current_step == ChainStep.WHATSAPP:
            if chain.next_action_at and now < chain.next_action_at:
                logger.info(f"Chain {chain_id} WHATSAPP step is scheduled for {chain.next_action_at}; waiting.")
                return chain

            if not chain.contact.notify_whatsapp:
                logger.info(f"Contact {chain.contact_id} disabled WhatsApp; moving to SMS.")
                chain.current_step = ChainStep.SMS
                chain.next_action_at = now
                chain.save(update_fields=['current_step', 'next_action_at', 'updated_at'])
                return chain
            else:
                attempt_no = 1
                idempotency_key = f"{chain.id}:WHATSAPP:{attempt_no}"
                attempt, created = DeliveryAttempt.objects.get_or_create(
                    idempotency_key=idempotency_key,
                    defaults={
                        'chain': chain,
                        'channel': 'WHATSAPP',
                        'attempt_no': attempt_no,
                        'status': AttemptStatus.PENDING,
                        'provider_name': 'MOCK',
                        'is_simulated': True,
                        'masked_destination': masked_phone,
                    }
                )
                if not created and attempt.status != AttemptStatus.PENDING:
                    return chain  # Step already processed

                provider = get_provider('WHATSAPP')
                msg_body = f"[SIMULATED] FixPoint SOS Alert: {chain.alert.user.first_name or 'A contact'} needs urgent assistance!"
                result = provider.send('WHATSAPP', real_phone, msg_body, idempotency_key)

                if result.status == 'ACCEPTED':
                    attempt.status = AttemptStatus.ACCEPTED
                    attempt.accepted_at = now
                    attempt.provider_message_id = result.provider_message_id
                    attempt.save(update_fields=['status', 'accepted_at', 'provider_message_id', 'updated_at'])

                    # Advance to SMS waiting for timeout
                    wait_sec = getattr(settings, 'NOTIFICATION_WHATSAPP_WAIT_SECONDS', 60)
                    chain.current_step = ChainStep.SMS
                    chain.next_action_at = now + timedelta(seconds=wait_sec)
                    chain.save(update_fields=['current_step', 'next_action_at', 'updated_at'])
                    return chain
                else:
                    # Provider failed: escalate immediately to SMS
                    attempt.status = AttemptStatus.FAILED
                    attempt.error_code = result.error_code
                    attempt.error_message = result.error_message
                    attempt.save(update_fields=['status', 'error_code', 'error_message', 'updated_at'])

                    chain.current_step = ChainStep.SMS
                    chain.next_action_at = now
                    chain.save(update_fields=['current_step', 'next_action_at', 'updated_at'])
                    return chain

        # ----------------- STEP 2: SMS -----------------
        if chain.current_step == ChainStep.SMS:
            if chain.next_action_at and now < chain.next_action_at:
                logger.info(f"Chain {chain_id} SMS step is scheduled for {chain.next_action_at}; waiting.")
                return chain

            if not chain.contact.notify_sms:
                logger.info(f"Contact {chain.contact_id} disabled SMS; moving to CALL.")
                chain.current_step = ChainStep.CALL
                chain.next_action_at = now
                chain.save(update_fields=['current_step', 'next_action_at', 'updated_at'])
                return chain
            else:
                attempt_no = 1
                idempotency_key = f"{chain.id}:SMS:{attempt_no}"
                attempt, created = DeliveryAttempt.objects.get_or_create(
                    idempotency_key=idempotency_key,
                    defaults={
                        'chain': chain,
                        'channel': 'SMS',
                        'attempt_no': attempt_no,
                        'status': AttemptStatus.PENDING,
                        'provider_name': 'MOCK',
                        'is_simulated': True,
                        'masked_destination': masked_phone,
                    }
                )
                if not created and attempt.status != AttemptStatus.PENDING:
                    return chain

                provider = get_provider('SMS')
                msg_body = f"[SIMULATED] FixPoint SOS Alert: {chain.alert.user.first_name or 'A contact'} needs urgent assistance!"
                result = provider.send('SMS', real_phone, msg_body, idempotency_key)

                if result.status == 'ACCEPTED':
                    attempt.status = AttemptStatus.ACCEPTED
                    attempt.accepted_at = now
                    attempt.provider_message_id = result.provider_message_id
                    attempt.save(update_fields=['status', 'accepted_at', 'provider_message_id', 'updated_at'])

                    # Advance to CALL waiting for timeout
                    delay_sec = getattr(settings, 'NOTIFICATION_SMS_TO_CALL_DELAY_SECONDS', 30)
                    chain.current_step = ChainStep.CALL
                    chain.next_action_at = now + timedelta(seconds=delay_sec)
                    chain.save(update_fields=['current_step', 'next_action_at', 'updated_at'])
                    return chain
                else:
                    # SMS failed: escalate immediately to CALL
                    attempt.status = AttemptStatus.FAILED
                    attempt.error_code = result.error_code
                    attempt.error_message = result.error_message
                    attempt.save(update_fields=['status', 'error_code', 'error_message', 'updated_at'])

                    chain.current_step = ChainStep.CALL
                    chain.next_action_at = now
                    chain.save(update_fields=['current_step', 'next_action_at', 'updated_at'])
                    return chain

        # ----------------- STEP 3: CALL -----------------
        if chain.current_step == ChainStep.CALL:
            if chain.next_action_at and now < chain.next_action_at:
                return chain

            if not chain.contact.notify_call:
                logger.info(f"Contact {chain.contact_id} disabled CALL; chain exhausted.")
                chain.status = ChainStatus.EXHAUSTED
                chain.current_step = ChainStep.DONE
                chain.save(update_fields=['status', 'current_step', 'updated_at'])
                return chain

            attempt_no = chain.call_attempts + 1
            idempotency_key = f"{chain.id}:CALL:{attempt_no}"
            attempt, created = DeliveryAttempt.objects.get_or_create(
                idempotency_key=idempotency_key,
                defaults={
                    'chain': chain,
                    'channel': 'VOICE_CALL',
                    'attempt_no': attempt_no,
                    'status': AttemptStatus.PENDING,
                    'provider_name': 'MOCK',
                    'is_simulated': True,
                    'masked_destination': masked_phone,
                }
            )
            if not created and attempt.status != AttemptStatus.PENDING:
                return chain

            provider = get_provider('VOICE_CALL')
            msg_body = f"[SIMULATED] Automated voice emergency alert for {chain.contact.name}"
            result = provider.send('VOICE_CALL', real_phone, msg_body, idempotency_key)

            if result.status == 'ACCEPTED':
                attempt.status = AttemptStatus.ACCEPTED
                attempt.accepted_at = now
                attempt.provider_message_id = result.provider_message_id
                attempt.save(update_fields=['status', 'accepted_at', 'provider_message_id', 'updated_at'])

                chain.call_attempts += 1
                chain.save(update_fields=['call_attempts', 'updated_at'])
                return chain
            else:
                attempt.status = AttemptStatus.FAILED
                attempt.error_code = result.error_code
                attempt.error_message = result.error_message
                attempt.save(update_fields=['status', 'error_code', 'error_message', 'updated_at'])

                chain.call_attempts += 1
                retry_limit = getattr(settings, 'NOTIFICATION_CALL_RETRY_LIMIT', 1)

                if chain.call_attempts <= retry_limit:
                    # Retry once
                    chain.next_action_at = now + timedelta(seconds=5)
                    chain.save(update_fields=['call_attempts', 'next_action_at', 'updated_at'])
                    return chain
                else:
                    chain.status = ChainStatus.EXHAUSTED
                    chain.current_step = ChainStep.DONE
                    chain.save(update_fields=['status', 'current_step', 'call_attempts', 'updated_at'])
                    log_audit_event(
                        action='CONTACT_CHAIN_EXHAUSTED',
                        actor=None,
                        target_model='ContactNotificationChain',
                        target_id=str(chain.id),
                        payload={'alert_id': str(chain.alert_id), 'reason': 'Contact unreachable on all channels.'}
                    )
                    return chain

        return chain


def process_due_chains(now=None) -> int:
    """
    Sweeper routine: recovers stale pending attempts and processes all due active notification chains.
    Crash-safe and runnable without Redis.
    """
    now = now or timezone.now()
    stale_sec = getattr(settings, 'NOTIFICATION_PENDING_STALE_SECONDS', 20)
    stale_cutoff = now - timedelta(seconds=stale_sec)

    # 1. Recover stale PENDING attempts
    stale_attempts = DeliveryAttempt.objects.filter(
        status=AttemptStatus.PENDING,
        requested_at__lt=stale_cutoff
    ).select_related('chain')

    for att in stale_attempts:
        if att.channel in ['WHATSAPP', 'SMS']:
            # Resent at most once: mark failed and let chain retry or progress
            att.status = AttemptStatus.FAILED
            att.error_code = 'STALE_PENDING_TIMEOUT'
            att.error_message = f"Delivery attempt timed out after {stale_sec}s pending."
            att.save(update_fields=['status', 'error_code', 'error_message', 'updated_at'])
            # Escalate chain to next step
            if att.chain.status == ChainStatus.ACTIVE:
                att.chain.next_action_at = now
                att.chain.save(update_fields=['next_action_at', 'updated_at'])
        elif att.channel in ['VOICE_CALL', 'CALL']:
            # Calls are NEVER automatically repeated
            att.status = AttemptStatus.FAILED
            att.error_code = 'CALL_STALE_MANUAL_FOLLOWUP'
            att.error_message = "Call attempt stale; marked for manual follow-up."
            att.save(update_fields=['status', 'error_code', 'error_message', 'updated_at'])
            if att.chain.status == ChainStatus.ACTIVE:
                att.chain.status = ChainStatus.EXHAUSTED
                att.chain.current_step = ChainStep.DONE
                att.chain.save(update_fields=['status', 'current_step', 'updated_at'])

    # 2. Process all ACTIVE chains where next_action_at <= now
    due_chains = ContactNotificationChain.objects.filter(
        status=ChainStatus.ACTIVE,
        next_action_at__lte=now
    ).values_list('id', flat=True)

    processed_count = 0
    for chain_id in due_chains:
        process_chain(str(chain_id), now=now)
        processed_count += 1

    return processed_count


def get_ack_summary(token: str) -> Optional[Dict[str, Any]]:
    """
    Public lookup for ACK page: displays alert summary and confirmation button.
    DOES NOT change state (link scanners must not acknowledge).
    """
    token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
    chain = ContactNotificationChain.objects.select_related(
        'contact', 'alert', 'alert__user'
    ).filter(ack_token_hash=token_hash).first()

    if not chain:
        return None

    return {
        'alert_id': str(chain.alert.id),
        'severity': chain.alert.severity,
        'user_first_name': chain.alert.user.first_name if chain.alert.user else 'A user',
        'contact_name': chain.contact.name,
        'status': chain.status,
        'created_at': chain.alert.created_at,
        'is_already_acknowledged': chain.status == ChainStatus.ACKNOWLEDGED
    }


def acknowledge_chain_by_token(token: str, channel: str = 'WEB') -> Tuple[bool, str, Optional[ContactNotificationChain]]:
    """
    Single contact + single alert acknowledgement. Idempotent.
    Stops remaining pending/scheduled steps for this contact only.
    """
    token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()

    with transaction.atomic():
        chain = ContactNotificationChain.objects.select_for_update().select_related(
            'contact', 'alert'
        ).filter(ack_token_hash=token_hash).first()

        if not chain:
            return False, "Invalid or unrecognized acknowledgement token.", None

        if chain.alert.status in ['RESOLVED', 'CANCELLED']:
            return False, "Emergency alert is already closed.", chain

        if chain.status == ChainStatus.ACKNOWLEDGED:
            return True, "Alert was already acknowledged.", chain

        chain.status = ChainStatus.ACKNOWLEDGED
        chain.acknowledged_at = timezone.now()
        chain.ack_channel = channel
        chain.current_step = ChainStep.DONE
        chain.save(update_fields=['status', 'acknowledged_at', 'ack_channel', 'current_step', 'updated_at'])

        # Cancel remaining pending attempts
        DeliveryAttempt.objects.filter(
            chain=chain,
            status=AttemptStatus.PENDING
        ).update(status=AttemptStatus.CANCELLED)

        # If this chain was Wave-1, immediately cancel any active Wave-2 chains for this alert
        if chain.contact.wave == 1:
            wave2_chains = ContactNotificationChain.objects.filter(
                alert=chain.alert,
                contact__wave=2,
                status=ChainStatus.ACTIVE
            )
            for w2 in wave2_chains:
                w2.status = ChainStatus.CANCELLED
                w2.save(update_fields=['status', 'updated_at'])
                DeliveryAttempt.objects.filter(chain=w2, status=AttemptStatus.PENDING).update(status=AttemptStatus.CANCELLED)

        log_audit_event(
            action='ALERT_ACKNOWLEDGED_BY_CONTACT',
            actor=None,
            target_model='ContactNotificationChain',
            target_id=str(chain.id),
            payload={'ack_channel': channel, 'alert_id': str(chain.alert_id)}
        )
        return True, "Emergency alert acknowledged successfully.", chain


def process_mock_webhook(payload: dict, signature: str) -> Tuple[bool, str]:
    """
    Simulates inbound webhook callback (e.g. WhatsApp quick-reply button '1' or IVR 'press 1').
    Validates HMAC signature and processes acknowledgement idempotently.
    """
    secret = getattr(settings, 'SECRET_KEY', 'default-key').encode('utf-8')
    token = payload.get('token', '')
    channel = payload.get('channel', 'WHATSAPP')
    
    # Compute expected signature: sha256 HMAC of token + channel
    msg = f"{token}:{channel}".encode('utf-8')
    expected_sig = hmac.new(secret, msg, hashlib.sha256).hexdigest()

    if not signature or not hmac.compare_digest(signature, expected_sig):
        return False, "Invalid webhook HMAC signature."

    success, msg, chain = acknowledge_chain_by_token(token, channel=channel)
    return success, msg


def get_alert_timeline(alert, actor) -> List[Dict[str, Any]]:
    """
    Returns sanitized notification timeline for an alert.
    Never exposes raw phone numbers or secret tokens.
    """
    chains = alert.notification_chains.select_related('contact').prefetch_related('delivery_attempts').all()
    timeline = []
    for chain in chains:
        attempts = []
        for att in chain.delivery_attempts.all():
            attempts.append({
                'attempt_no': att.attempt_no,
                'channel': att.channel,
                'status': att.status,
                'provider_name': att.provider_name,
                'is_simulated': att.is_simulated,
                'masked_destination': att.masked_destination,
                'error_code': att.error_code,
                'error_message': att.error_message,
                'requested_at': att.requested_at,
                'accepted_at': att.accepted_at,
                'delivered_at': att.delivered_at,
            })

        timeline.append({
            'chain_id': str(chain.id),
            'contact_id': str(chain.contact.id),
            'contact_name': chain.contact.name,
            'relationship': chain.contact.relationship,
            'status': chain.status,
            'current_step': chain.current_step,
            'call_attempts': chain.call_attempts,
            'acknowledged_at': chain.acknowledged_at,
            'ack_channel': chain.ack_channel,
            'attempts': attempts,
        })
    return timeline
