from django.db import models
from django.conf import settings
from apps.common.models import BaseModel
from apps.qr_codes.models import QRCodeBadge

class AlertStatus(models.TextChoices):
    TRIGGERED = 'TRIGGERED', 'Triggered'
    ACKNOWLEDGED = 'ACKNOWLEDGED', 'Acknowledged'
    RESOLVED = 'RESOLVED', 'Resolved'
    CANCELLED = 'CANCELLED', 'Cancelled'

class AlertSeverity(models.TextChoices):
    CRITICAL = 'CRITICAL', 'Critical'
    HIGH = 'HIGH', 'High'
    MEDIUM = 'MEDIUM', 'Medium'
    LOW = 'LOW', 'Low'

class AlertRecord(BaseModel):
    """
    Emergency alert data foundation.
    Stores initial dispatch state and location metadata.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alerts'
    )
    qr_badge = models.ForeignKey(
        QRCodeBadge,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alerts'
    )
    status = models.CharField(
        max_length=32,
        choices=AlertStatus.choices,
        default=AlertStatus.TRIGGERED,
        db_index=True
    )
    severity = models.CharField(
        max_length=32,
        choices=AlertSeverity.choices,
        default=AlertSeverity.CRITICAL,
        db_index=True
    )
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location_address = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Alert {self.id} [{self.status}] - Severity {self.severity}"
