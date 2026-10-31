from typing import Optional
from django.db import models
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


def list_incidents_for_user(user, status: Optional[str] = None) -> QuerySet[IncidentRecord]:
    """
    Returns incidents filtered according to user role and authorization:
    - Operators, supervisors, and admins can view all incidents.
    - Verified responders can view incidents assigned to them or reported by them.
    - Customers, public users, and unverified responders can only view incidents they reported.
    """
    from apps.responders.models import ResponderDispatch

    qs = IncidentRecord.objects.select_related('reporter')

    if (
        user.role in ['OPERATOR', 'SUPERVISOR', 'ADMIN']
        or getattr(user, 'is_staff', False)
        or getattr(user, 'is_superuser', False)
    ):
        pass
    elif (
        user.role in ['POLICE_RESPONDER', 'MEDICAL_RESPONDER']
        and getattr(user, 'is_verified_responder', False)
    ):
        assigned_incident_ids = ResponderDispatch.objects.filter(
            responder=user
        ).values_list('incident_id', flat=True)
        qs = qs.filter(
            models.Q(id__in=assigned_incident_ids) | models.Q(reporter=user)
        )
    else:
        qs = qs.filter(reporter=user)

    if status:
        qs = qs.filter(status=status)
    return qs


def get_incident_by_number(incident_number: str) -> Optional[IncidentRecord]:
    return IncidentRecord.objects.filter(
        incident_number=incident_number
    ).select_related('reporter', 'qr_badge', 'qr_badge__user').prefetch_related('photos').first()
