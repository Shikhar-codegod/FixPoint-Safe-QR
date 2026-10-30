from typing import Optional
from django.db.models import QuerySet, Case, When, Value, IntegerField, Q
from .models import IncidentRecord, IncidentPriority

def list_scoped_incidents(user) -> QuerySet[IncidentRecord]:
    """
    Returns incidents scoped by user role:
    - Operators, Supervisors, Admins: see all incidents.
    - Regular users: see incidents reported by themselves OR reported against their own QR badges.
    """
    qs = IncidentRecord.objects.select_related('reporter', 'qr_badge').prefetch_related('photos').all()

    if user.role in ['OPERATOR', 'SUPERVISOR', 'ADMIN'] or user.is_staff:
        return qs

    return qs.filter(
        Q(reporter=user) | Q(qr_badge__user=user)
    ).distinct()

def get_operator_queue(status: Optional[str] = None, category: Optional[str] = None) -> QuerySet[IncidentRecord]:
    """
    Operator incident dispatch queue, ordered by severity/priority descending, then age (oldest first).
    """
    priority_order = Case(
        When(priority=IncidentPriority.CRITICAL, then=Value(1)),
        When(priority=IncidentPriority.HIGH, then=Value(2)),
        When(priority=IncidentPriority.MEDIUM, then=Value(3)),
        When(priority=IncidentPriority.LOW, then=Value(4)),
        default=Value(5),
        output_field=IntegerField()
    )

    qs = IncidentRecord.objects.select_related('reporter', 'qr_badge').prefetch_related('photos').annotate(
        priority_rank=priority_order
    ).all()

    if status:
        qs = qs.filter(status=status)
    if category:
        qs = qs.filter(incident_type=category)

    return qs.order_by('priority_rank', 'created_at')

def get_incident_by_number(incident_number: str) -> Optional[IncidentRecord]:
    return IncidentRecord.objects.filter(
        incident_number=incident_number
    ).select_related('reporter', 'qr_badge', 'qr_badge__user').prefetch_related('photos').first()
