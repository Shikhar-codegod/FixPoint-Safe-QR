from apps.audit.services import log_audit_event
from .models import AlertRecord, AlertStatus, AlertSeverity

def create_alert_record(
    user=None,
    qr_badge=None,
    severity: str = AlertSeverity.CRITICAL,
    latitude=None,
    longitude=None,
    location_address: str = '',
    notes: str = ''
) -> AlertRecord:
    alert = AlertRecord.objects.create(
        user=user,
        qr_badge=qr_badge,
        status=AlertStatus.TRIGGERED,
        severity=severity,
        latitude=latitude,
        longitude=longitude,
        location_address=location_address,
        notes=notes
    )
    log_audit_event(
        action='ALERT_RECORD_CREATED',
        actor=user,
        target_model='AlertRecord',
        target_id=str(alert.id),
        payload={'status': alert.status, 'severity': alert.severity}
    )
    return alert
