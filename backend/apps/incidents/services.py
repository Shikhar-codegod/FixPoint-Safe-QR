import io
import uuid
from typing import Optional, Dict, Any
from django.db import transaction
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from PIL import Image
from apps.audit.services import log_audit_event
from .models import (
    IncidentRecord,
    IncidentStatus,
    IncidentType,
    IncidentPriority,
    LocationPrecision,
    IncidentPhoto,
)

# Permitted lifecycle status transitions
PERMITTED_TRANSITIONS = {
    IncidentStatus.REPORTED: {
        IncidentStatus.DISPATCHED,
        IncidentStatus.IN_PROGRESS,
        IncidentStatus.CLOSED,
    },
    IncidentStatus.DISPATCHED: {
        IncidentStatus.IN_PROGRESS,
        IncidentStatus.RESOLVED,
        IncidentStatus.CLOSED,
    },
    IncidentStatus.IN_PROGRESS: {
        IncidentStatus.RESOLVED,
        IncidentStatus.CLOSED,
    },
    IncidentStatus.RESOLVED: {
        IncidentStatus.CLOSED,
        IncidentStatus.IN_PROGRESS,  # Re-opened
    },
    IncidentStatus.CLOSED: set(),  # Terminal state
}


def create_incident(
    incident_type: str = IncidentType.ACCIDENT,
    reporter=None,
    alert=None,
    qr_badge=None,
    priority: str = IncidentPriority.LOW,
    location_precision: str = LocationPrecision.NONE,
    reporter_contact_shared: bool = False,
    latitude=None,
    longitude=None,
    location_address: str = '',
    description: str = ''
) -> IncidentRecord:
    incident_number = f"INC-{uuid.uuid4().hex[:8].upper()}"

    with transaction.atomic():
        incident = IncidentRecord.objects.create(
            incident_number=incident_number,
            incident_type=incident_type,
            status=IncidentStatus.REPORTED,
            priority=priority,
            location_precision=location_precision,
            reporter_contact_shared=reporter_contact_shared,
            reporter=reporter,
            alert=alert,
            qr_badge=qr_badge,
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
            payload={
                'incident_number': incident.incident_number,
                'type': incident.incident_type,
                'priority': incident.priority,
            }
        )
    return incident


def update_incident(
    incident: IncidentRecord,
    new_status: Optional[str] = None,
    description: Optional[str] = None,
    actor=None
) -> IncidentRecord:
    """
    Updates an incident record with pessimistic row locking and status transition validation.
    """
    with transaction.atomic():
        locked_incident = IncidentRecord.objects.select_for_update().get(id=incident.id)
        update_fields = ['updated_at']

        if new_status and new_status != locked_incident.status:
            allowed = PERMITTED_TRANSITIONS.get(locked_incident.status, set())
            if new_status not in allowed:
                raise ValidationError(
                    f"Invalid status transition from '{locked_incident.status}' to '{new_status}'."
                )

            old_status = locked_incident.status
            locked_incident.status = new_status
            update_fields.append('status')

            log_audit_event(
                action='INCIDENT_STATUS_CHANGED',
                actor=actor,
                target_model='IncidentRecord',
                target_id=str(locked_incident.id),
                payload={
                    'old_status': old_status,
                    'new_status': new_status,
                    'incident_number': locked_incident.incident_number
                }
            )

        if description is not None and description != locked_incident.description:
            locked_incident.description = description
            update_fields.append('description')

            log_audit_event(
                action='INCIDENT_DESCRIPTION_CHANGED',
                actor=actor,
                target_model='IncidentRecord',
                target_id=str(locked_incident.id),
                payload={
                    'incident_number': locked_incident.incident_number,
                    'description_changed': True,
                    # Description content is intentionally omitted — may contain PII
                }
            )

        if len(update_fields) > 1:
            locked_incident.save(update_fields=update_fields)

        return locked_incident


def update_incident_status(incident: IncidentRecord, new_status: str, actor=None) -> IncidentRecord:
    """
    Thin wrapper for backward compatibility — delegates to update_incident().
    """
    return update_incident(incident=incident, new_status=new_status, actor=actor)


def add_incident_photo(incident: IncidentRecord, uploaded_file, actor=None) -> IncidentPhoto:
    """
    Validates photo with Pillow, strips all EXIF/GPS metadata, enforces max 3 photos and 5MB limit,
    and saves securely under private storage.
    """
    if incident.photos.count() >= 3:
        raise ValueError("Maximum 3 photos permitted per incident.")

    max_size = 5 * 1024 * 1024  # 5MB
    if uploaded_file.size > max_size:
        raise ValueError("Photo file size exceeds maximum limit of 5 MB.")

    # Validate image format via Pillow
    try:
        uploaded_file.seek(0)
        img = Image.open(uploaded_file)
        img_format = img.format.upper() if img.format else ''
        if img_format not in ['JPEG', 'JPG', 'PNG', 'WEBP']:
            raise ValueError(f"Unsupported image format: {img_format}. Allowed formats: JPEG, PNG, WEBP.")
    except Exception as exc:
        if isinstance(exc, ValueError):
            raise exc
        raise ValueError(f"Uploaded file is not a valid image: {exc}")

    # Re-encode image to strip EXIF and GPS metadata
    uploaded_file.seek(0)
    image = Image.open(uploaded_file)

    # Normalize RGB for JPEG save
    save_format = 'JPEG'
    content_type = 'image/jpeg'
    file_ext = 'jpg'
    if img_format == 'PNG':
        save_format = 'PNG'
        content_type = 'image/png'
        file_ext = 'png'
    elif img_format == 'WEBP':
        save_format = 'WEBP'
        content_type = 'image/webp'
        file_ext = 'webp'
    else:
        if image.mode in ('RGBA', 'P', 'LA'):
            image = image.convert('RGB')

    output_stream = io.BytesIO()
    # Saving without exif parameter strips all EXIF / GPS tags completely
    image.save(output_stream, format=save_format, quality=85)
    output_stream.seek(0)
    cleaned_data = output_stream.getvalue()

    random_filename = f"{uuid.uuid4().hex}.{file_ext}"

    with transaction.atomic():
        photo = IncidentPhoto(
            incident=incident,
            file_size=len(cleaned_data),
            content_type=content_type,
        )
        photo.photo_file.save(random_filename, ContentFile(cleaned_data), save=True)

        log_audit_event(
            action='INCIDENT_PHOTO_UPLOADED',
            actor=actor,
            target_model='IncidentPhoto',
            target_id=str(photo.id),
            payload={
                'incident_number': incident.incident_number,
                'file_size': photo.file_size,
            }
        )
    return photo


def upgrade_incident_to_alert(incident: IncidentRecord, actor=None):
    """
    Upgrades an incident to an emergency alert DRAFT.
    Links the created alert to the incident and logs an audit event.
    The resulting alert requires explicit confirmation before any emergency workflow starts.
    """
    from apps.alerts.services import create_alert_record
    from apps.alerts.models import AlertSeverity

    if incident.alert:
        raise ValueError(f"Incident {incident.incident_number} is already linked to Alert {incident.alert.id}")

    # Determine alert user: QR badge owner takes priority, then incident reporter
    alert_user = None
    if incident.qr_badge and incident.qr_badge.user:
        alert_user = incident.qr_badge.user
    elif incident.reporter:
        alert_user = incident.reporter

    notes = f"Upgraded from Incident {incident.incident_number}: {incident.description}".strip()

    with transaction.atomic():
        alert = create_alert_record(
            user=alert_user,
            qr_badge=incident.qr_badge,
            severity=AlertSeverity.HIGH,
            latitude=incident.latitude,
            longitude=incident.longitude,
            location_address=incident.location_address,
            notes=notes
        )
        incident.alert = alert
        incident.save(update_fields=['alert', 'updated_at'])

        log_audit_event(
            action='INCIDENT_UPGRADED_TO_ALERT',
            actor=actor,
            target_model='IncidentRecord',
            target_id=str(incident.id),
            payload={
                'incident_number': incident.incident_number,
                'alert_id': str(alert.id),
                'severity': alert.severity,
            }
        )
    return alert
