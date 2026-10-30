from django.db.models import QuerySet
from .models import AuditEvent

def list_audit_events() -> QuerySet[AuditEvent]:
    return AuditEvent.objects.select_related('actor').all()

def get_audit_events_for_actor(actor_id) -> QuerySet[AuditEvent]:
    return AuditEvent.objects.filter(actor_id=actor_id).select_related('actor')

def get_audit_events_by_action(action: str) -> QuerySet[AuditEvent]:
    return AuditEvent.objects.filter(action=action).select_related('actor')
