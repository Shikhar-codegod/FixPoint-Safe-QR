from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from apps.audit.services import log_audit_event
from apps.incidents.models import IncidentRecord
from .models import ResponderDispatch, DispatchStatus

# Permitted dispatch status transitions.
# COMPLETED and CANCELLED are terminal — no further transitions allowed.
PERMITTED_DISPATCH_TRANSITIONS = {
    DispatchStatus.ASSIGNED: {DispatchStatus.EN_ROUTE, DispatchStatus.ON_SCENE, DispatchStatus.CANCELLED},
    DispatchStatus.EN_ROUTE: {DispatchStatus.ON_SCENE, DispatchStatus.CANCELLED},
    DispatchStatus.ON_SCENE: {DispatchStatus.COMPLETED, DispatchStatus.CANCELLED},
    DispatchStatus.COMPLETED: set(),   # Terminal
    DispatchStatus.CANCELLED: set(),   # Terminal
}

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
    new_status: str = None,
    notes: str = None,
    actor=None
) -> ResponderDispatch:
    with transaction.atomic():
        locked_dispatch = ResponderDispatch.objects.select_for_update().get(id=dispatch.id)
        update_fields = ['updated_at']
        if new_status and new_status != locked_dispatch.status:
            allowed = PERMITTED_DISPATCH_TRANSITIONS.get(locked_dispatch.status, set())
            if new_status not in allowed:
                raise ValidationError(
                    f"Invalid dispatch status transition from '{locked_dispatch.status}' to '{new_status}'."
                )
            locked_dispatch.status = new_status
            if new_status == DispatchStatus.ON_SCENE and not locked_dispatch.arrived_at:
                locked_dispatch.arrived_at = timezone.now()
                update_fields.append('arrived_at')
            elif new_status == DispatchStatus.COMPLETED and not locked_dispatch.completed_at:
                locked_dispatch.completed_at = timezone.now()
                update_fields.append('completed_at')
            update_fields.append('status')

        if notes is not None:
            locked_dispatch.notes = notes
            update_fields.append('notes')

        locked_dispatch.save(update_fields=update_fields)
        log_audit_event(
            action='DISPATCH_STATUS_UPDATED',
            actor=actor,
            target_model='ResponderDispatch',
            target_id=str(locked_dispatch.id),
            payload={'status': locked_dispatch.status, 'notes': locked_dispatch.notes}
        )
    return locked_dispatch

