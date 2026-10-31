from typing import Optional
from django.db.models import QuerySet
from .models import AlertRecord, AlertStatus, AlertEvidence, AlertConfirmationToken

def get_alert_by_id(alert_id) -> Optional[AlertRecord]:
    return AlertRecord.objects.filter(id=alert_id).select_related(
        'qr_badge', 'user', 'claimed_by', 'closed_by'
    ).first()

def list_alerts_for_user(user) -> QuerySet[AlertRecord]:
    return AlertRecord.objects.filter(user=user).select_related(
        'qr_badge', 'claimed_by', 'closed_by'
    )

def list_active_alerts() -> QuerySet[AlertRecord]:
    """
    Returns alerts that are actively in progress (CONFIRMED or ACTIVE).
    """
    return AlertRecord.objects.filter(
        status__in=[AlertStatus.CONFIRMED, AlertStatus.ACTIVE]
    ).select_related('qr_badge', 'user', 'claimed_by', 'closed_by')

def list_operator_alert_queue() -> QuerySet[AlertRecord]:
    """
    Queue of alerts requiring operator attention, ordered by priority / creation time.
    """
    return AlertRecord.objects.filter(
        status__in=[AlertStatus.CONFIRMED, AlertStatus.ACTIVE]
    ).order_by('created_at').select_related('qr_badge', 'user', 'claimed_by')

def get_alert_evidence(alert: AlertRecord) -> QuerySet[AlertEvidence]:
    return AlertEvidence.objects.filter(alert=alert).order_by('-uploaded_at')
