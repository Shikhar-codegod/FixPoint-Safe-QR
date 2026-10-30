import logging
from typing import Optional, Dict, Any
from .models import AuditEvent

logger = logging.getLogger('apps.audit')

# Sensitive keys to sanitize from audit log payloads
SENSITIVE_KEYS = {
    'password', 'token', 'access', 'refresh', 'secret', 'authorization',
    'phone', 'phone_number', 'email', 'number', 'destination', 'recipient_destination'
}

def sanitize_payload(payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not payload or not isinstance(payload, dict):
        return {}
    sanitized = {}
    for k, v in payload.items():
        if any(sens in k.lower() for sens in SENSITIVE_KEYS):
            sanitized[k] = '[REDACTED]'
        elif isinstance(v, dict):
            sanitized[k] = sanitize_payload(v)
        else:
            sanitized[k] = v
    return sanitized

def log_audit_event(
    action: str,
    actor=None,
    ip_address: Optional[str] = None,
    user_agent: str = '',
    target_model: str = '',
    target_id: str = '',
    payload: Optional[Dict[str, Any]] = None
) -> AuditEvent:
    """
    Persists an immutable audit log record and emits a safe application log.
    """
    clean_payload = sanitize_payload(payload)
    event = AuditEvent.objects.create(
        actor=actor,
        action=action,
        ip_address=ip_address,
        user_agent=user_agent[:512] if user_agent else '',
        target_model=target_model,
        target_id=str(target_id) if target_id else '',
        payload=clean_payload
    )
    actor_identifier = actor.email if actor and hasattr(actor, 'email') else 'ANONYMOUS'
    logger.info(f"AUDIT_EVENT: action={action} actor={actor_identifier} ip={ip_address} target={target_model}:{target_id}")
    return event
