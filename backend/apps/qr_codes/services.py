import uuid
import secrets
import hashlib
from apps.audit.services import log_audit_event
from .models import QRCodeBadge, QRCodeStatus

def hash_qr_token(token: str) -> str:
    """
    Computes SHA-256 digest of a raw QR token string.
    """
    return hashlib.sha256(token.encode('utf-8')).hexdigest()

def create_qr_badge(user, vehicle_registration: str = '', vehicle_model: str = '') -> QRCodeBadge:
    # Generate unique alphanumeric reference identifier
    code_identifier = f"FP-{uuid.uuid4().hex[:10].upper()}"
    # Cryptographically secure random token (24 bytes base64url = 192 bits of entropy >= 128 bits required)
    raw_token = secrets.token_urlsafe(24)
    token_hash = hash_qr_token(raw_token)

    badge = QRCodeBadge.objects.create(
        user=user,
        code_identifier=code_identifier,
        token_hash=token_hash,
        generation=1,
        vehicle_registration=vehicle_registration.upper(),
        vehicle_model=vehicle_model,
        status=QRCodeStatus.ACTIVE
    )
    badge.raw_token = raw_token

    log_audit_event(
        action='QR_BADGE_CREATED',
        actor=user,
        target_model='QRCodeBadge',
        target_id=str(badge.id),
        payload={'code_identifier': badge.code_identifier, 'vehicle': badge.vehicle_registration}
    )
    return badge

def rotate_qr_badge(badge: QRCodeBadge, actor=None) -> tuple[QRCodeBadge, str]:
    """
    Rotates the secret token for a badge, invalidating previous QR codes while preserving history.
    """
    raw_token = secrets.token_urlsafe(24)
    badge.token_hash = hash_qr_token(raw_token)
    badge.generation = badge.generation + 1
    badge.save(update_fields=['token_hash', 'generation', 'updated_at'])
    badge.raw_token = raw_token

    log_audit_event(
        action='QR_BADGE_ROTATED',
        actor=actor,
        target_model='QRCodeBadge',
        target_id=str(badge.id),
        payload={'code_identifier': badge.code_identifier, 'generation': badge.generation}
    )
    return badge, raw_token

def update_badge_status(badge: QRCodeBadge, new_status: str, actor=None) -> QRCodeBadge:
    badge.status = new_status
    badge.save(update_fields=['status', 'updated_at'])
    log_audit_event(
        action='QR_BADGE_STATUS_UPDATED',
        actor=actor,
        target_model='QRCodeBadge',
        target_id=str(badge.id),
        payload={'status': new_status, 'code_identifier': badge.code_identifier}
    )
    return badge
