from django.utils import timezone
from django.db import transaction
from apps.audit.services import log_audit_event
from apps.incidents.models import IncidentRecord
from .models import ResponderDispatch, DispatchStatus

def assign_responder_to_incident(
    responder,
    incident: IncidentRecord,
    assigning_operator=None
) -> ResponderDispatch:
    with transaction.atomic():
        dispatch, created = ResponderDispatch.objects.get_or_create(
            responder=responder,
            incident=incident,
            defaults={'status': DispatchStatus.ASSIGNED}
        )
        if not created:
            dispatch.status = DispatchStatus.ASSIGNED
            dispatch.save(update_fields=['status', 'updated_at'])

        log_audit_event(
            action='RESPONDER_DISPATCHED',
            actor=assigning_operator,
            target_model='ResponderDispatch',
            target_id=str(dispatch.id),
            payload={
                'responder': getattr(responder, 'email', str(responder)),
                'incident': incident.incident_number
            }
        )
    return dispatch

def update_dispatch_status(
    dispatch: ResponderDispatch,
    new_status: str,
    actor=None
) -> ResponderDispatch:
    with transaction.atomic():
        dispatch.status = new_status
        if new_status == DispatchStatus.ON_SCENE and not dispatch.arrived_at:
            dispatch.arrived_at = timezone.now()
        elif new_status == DispatchStatus.COMPLETED and not dispatch.completed_at:
            dispatch.completed_at = timezone.now()
        dispatch.save()
        log_audit_event(
            action='DISPATCH_STATUS_UPDATED',
            actor=actor,
            target_model='ResponderDispatch',
            target_id=str(dispatch.id),
            payload={'status': new_status}
        )
    return dispatch
