import uuid
from apps.audit.services import log_audit_event
from .models import IncidentRecord, IncidentStatus, IncidentType

def create_incident(
    incident_type: str = IncidentType.ROAD_ACCIDENT,
    reporter=None,
    alert=None,
    latitude=None,
    longitude=None,
    location_address: str = '',
    description: str = ''
) -> IncidentRecord:
    # Generate human readable incident number e.g. INC-2026-928472
    incident_number = f"INC-{uuid.uuid4().hex[:8].upper()}"
    incident = IncidentRecord.objects.create(
        incident_number=incident_number,
        incident_type=incident_type,
        status=IncidentStatus.REPORTED,
        reporter=reporter,
        alert=alert,
        latitude=latitude,
        longitude=longitude,
        location_address=location_address,
        description=description
    )
    log_audit_event(
        action='INCIDENT_REPORTED',
        actor=reporter,
        target_model='IncidentRecord',
        target_id=str(incident.id),
        payload={'incident_number': incident.incident_number, 'type': incident.incident_type}
    )
    return incident

def update_incident_status(incident: IncidentRecord, new_status: str, actor=None) -> IncidentRecord:
    old_status = incident.status
    incident.status = new_status
    incident.save(update_fields=['status', 'updated_at'])
    log_audit_event(
        action='INCIDENT_STATUS_CHANGED',
        actor=actor,
        target_model='IncidentRecord',
        target_id=str(incident.id),
        payload={'old_status': old_status, 'new_status': new_status, 'incident_number': incident.incident_number}
    )
    return incident
