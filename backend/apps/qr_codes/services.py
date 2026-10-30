import uuid
from apps.audit.services import log_audit_event
from .models import QRCodeBadge, QRCodeStatus

def create_qr_badge(user, vehicle_registration: str = '', vehicle_model: str = '') -> QRCodeBadge:
    # Generate unique alphanumeric identifier token for the physical sticker/badge
    code_identifier = f"FP-{uuid.uuid4().hex[:10].upper()}"
    badge = QRCodeBadge.objects.create(
        user=user,
        code_identifier=code_identifier,
        vehicle_registration=vehicle_registration.upper(),
        vehicle_model=vehicle_model,
        status=QRCodeStatus.ACTIVE
    )
    log_audit_event(
        action='QR_BADGE_CREATED',
        actor=user,
        target_model='QRCodeBadge',
        target_id=str(badge.id),
        payload={'code_identifier': badge.code_identifier, 'vehicle': badge.vehicle_registration}
    )
    return badge

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
