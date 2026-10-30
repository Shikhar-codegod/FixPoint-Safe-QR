import logging
from typing import Optional
from django.db import transaction
from apps.audit.services import log_audit_event
from .models import CustomUser, UserRole

logger = logging.getLogger('apps.accounts')

def register_user(
    email: str,
    password: str,
    first_name: str = '',
    last_name: str = '',
    phone_number: str = '',
    role: str = UserRole.CUSTOMER,
    ip_address: Optional[str] = None,
    user_agent: str = ''
) -> CustomUser:
    """
    Registers a new user and records audit trail.
    """
    with transaction.atomic():
        user = CustomUser.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            role=role
        )
        log_audit_event(
            action='USER_REGISTERED',
            actor=user,
            ip_address=ip_address,
            user_agent=user_agent,
            target_model='CustomUser',
            target_id=str(user.id),
            payload={'email': user.email, 'role': user.role}
        )
    return user

def set_responder_verification(
    user_id: str,
    is_verified: bool,
    verified_by: CustomUser,
    notes: str = '',
    ip_address: Optional[str] = None
) -> CustomUser:
    """
    Explicit responder credential verification workflow.
    Supervisors or Administrators approve or revoke responder status.
    """
    with transaction.atomic():
        user = CustomUser.objects.select_for_update().get(id=user_id)
        user.is_verified_responder = is_verified
        user.save(update_fields=['is_verified_responder', 'updated_at'])

        log_audit_event(
            action='RESPONDER_VERIFICATION_UPDATED',
            actor=verified_by,
            ip_address=ip_address,
            target_model='CustomUser',
            target_id=str(user.id),
            payload={'is_verified': is_verified, 'notes': notes, 'target_email': user.email}
        )
        logger.info(f"Responder verification updated: user={user.email} verified={is_verified} by={verified_by.email}")
    return user
