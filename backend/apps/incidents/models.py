from django.db import models
from django.conf import settings
from apps.common.models import BaseModel
from apps.alerts.models import AlertRecord
from apps.qr_codes.models import QRCodeBadge

class IncidentStatus(models.TextChoices):
    REPORTED = 'REPORTED', 'Reported'
    DISPATCHED = 'DISPATCHED', 'Dispatched'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    RESOLVED = 'RESOLVED', 'Resolved'
    CLOSED = 'CLOSED', 'Closed'

class IncidentType(models.TextChoices):
    ACCIDENT = 'ACCIDENT', 'Accident'
    DAMAGE = 'DAMAGE', 'Vehicle Damage'
    TAMPERING = 'TAMPERING', 'Vehicle Tampering'
    HAZARD = 'HAZARD', 'Road Hazard'
    OTHER = 'OTHER', 'Other Incident'

# Backward compatibility aliases for Phase 1 / foundation references
IncidentType.ROAD_ACCIDENT = IncidentType.ACCIDENT
IncidentType.FIRE_HAZARD = IncidentType.HAZARD
IncidentType.VEHICLE_BREAKDOWN = IncidentType.OTHER
IncidentType.MEDICAL_EMERGENCY = IncidentType.OTHER

class IncidentPriority(models.TextChoices):
    LOW = 'LOW', 'Low'
    MEDIUM = 'MEDIUM', 'Medium'
    HIGH = 'HIGH', 'High'
    CRITICAL = 'CRITICAL', 'Critical'

class LocationPrecision(models.TextChoices):
    PRECISE = 'PRECISE', 'Precise GPS'
    MANUAL = 'MANUAL', 'Manual Input'
    NONE = 'NONE', 'None'

class IncidentRecord(BaseModel):
    """
    Incident record tracking non-emergency vehicle incidents, road hazards, or public reports.
    Strictly decoupled from emergency alert notifications.
    """
    incident_number = models.CharField(max_length=32, unique=True, db_index=True)
    incident_type = models.CharField(
        max_length=32,
        choices=IncidentType.choices,
        default=IncidentType.ACCIDENT,
        db_index=True
    )
    status = models.CharField(
        max_length=32,
        choices=IncidentStatus.choices,
        default=IncidentStatus.REPORTED,
        db_index=True
    )
    priority = models.CharField(
        max_length=16,
        choices=IncidentPriority.choices,
        default=IncidentPriority.LOW,
        db_index=True
    )
    location_precision = models.CharField(
        max_length=16,
        choices=LocationPrecision.choices,
        default=LocationPrecision.NONE
    )
    reporter_contact_shared = models.BooleanField(default=False)

    alert = models.ForeignKey(
        AlertRecord,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incidents'
    )
    qr_badge = models.ForeignKey(
        QRCodeBadge,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incidents'
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reported_incidents'
    )
    claimed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='claimed_incidents',
    )
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location_address = models.CharField(max_length=255, blank=True)
    description = models.CharField(max_length=1000, blank=True)
    operator_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Incident #{self.incident_number} - {self.incident_type} [{self.priority}] ({self.status})"


class IncidentPhoto(BaseModel):
    """
    Secure photograph attachments for incident reports.
    Stored in private storage with EXIF/GPS metadata permanently stripped.
    """
    incident = models.ForeignKey(
        IncidentRecord,
        on_delete=models.CASCADE,
        related_name='photos'
    )
    photo_file = models.FileField(upload_to='private_incident_photos/')
    file_size = models.PositiveIntegerField(default=0)
    content_type = models.CharField(max_length=64, default='image/jpeg')

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Photo {self.id} for Incident #{self.incident.incident_number}"
