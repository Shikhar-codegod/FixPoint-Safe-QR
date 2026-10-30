import uuid
from django.db import models
from django.conf import settings
from apps.common.models import BaseModel
from apps.alerts.models import AlertRecord

class IncidentStatus(models.TextChoices):
    REPORTED = 'REPORTED', 'Reported'
    DISPATCHED = 'DISPATCHED', 'Dispatched'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    RESOLVED = 'RESOLVED', 'Resolved'
    CLOSED = 'CLOSED', 'Closed'

class IncidentType(models.TextChoices):
    ROAD_ACCIDENT = 'ROAD_ACCIDENT', 'Road Accident'
    VEHICLE_BREAKDOWN = 'VEHICLE_BREAKDOWN', 'Vehicle Breakdown'
    MEDICAL_EMERGENCY = 'MEDICAL_EMERGENCY', 'Medical Emergency'
    FIRE_HAZARD = 'FIRE_HAZARD', 'Fire Hazard'
    OTHER = 'OTHER', 'Other'

class IncidentRecord(BaseModel):
    """
    Core incident record tracking lifecycle from dispatch through resolution.
    """
    incident_number = models.CharField(max_length=32, unique=True, db_index=True)
    incident_type = models.CharField(
        max_length=32,
        choices=IncidentType.choices,
        default=IncidentType.ROAD_ACCIDENT,
        db_index=True
    )
    status = models.CharField(
        max_length=32,
        choices=IncidentStatus.choices,
        default=IncidentStatus.REPORTED,
        db_index=True
    )
    alert = models.ForeignKey(
        AlertRecord,
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
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location_address = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Incident #{self.incident_number} - {self.incident_type} ({self.status})"
