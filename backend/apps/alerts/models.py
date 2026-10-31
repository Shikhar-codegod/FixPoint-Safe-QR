from django.db import models
from django.conf import settings
from apps.common.models import BaseModel
from apps.qr_codes.models import QRCodeBadge

class AlertStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    CONFIRMED = 'CONFIRMED', 'Confirmed'
    ACTIVE = 'ACTIVE', 'Active'
    CLOSED = 'CLOSED', 'Closed'

# Backward compatibility aliases for pre-Phase 2 references
AlertStatus.TRIGGERED = AlertStatus.CONFIRMED
AlertStatus.ACKNOWLEDGED = AlertStatus.ACTIVE
AlertStatus.RESOLVED = AlertStatus.CLOSED
AlertStatus.CANCELLED = AlertStatus.CLOSED

class AlertSeverity(models.TextChoices):
    CRITICAL = 'CRITICAL', 'Critical'
    HIGH = 'HIGH', 'High'
    MEDIUM = 'MEDIUM', 'Medium'
    LOW = 'LOW', 'Low'

class AlertRecord(BaseModel):
    """
    Emergency alert lifecycle tracking: DRAFT -> CONFIRMED -> ACTIVE -> CLOSED.
    Stores dispatch state and location metadata.
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
        default=AlertStatus.DRAFT,
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

    confirmed_at = models.DateTimeField(null=True, blank=True)
    activated_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='closed_alerts'
    )
    claimed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='claimed_alerts'
    )

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['qr_badge'],
                condition=models.Q(status__in=['DRAFT', 'CONFIRMED', 'ACTIVE']),
                name='unique_active_alert_per_badge'
            )
        ]

    def __str__(self):
        return f"Alert {self.id} [{self.status}] - Severity {self.severity}"


class AlertConfirmationToken(BaseModel):
    """
    Single-use confirmation token ensuring user explicitly confirms alert draft.
    Token is stored as SHA-256 hash.
    """
    alert = models.OneToOneField(
        AlertRecord,
        on_delete=models.CASCADE,
        related_name='confirmation_token'
    )
    token_hash = models.CharField(max_length=64, unique=True, db_index=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"ConfirmationToken for Alert {self.alert_id} (used={bool(self.used_at)})"


class AlertEvidence(BaseModel):
    """
    Optional photo or evidence attachment metadata.
    """
    alert = models.ForeignKey(
        AlertRecord,
        on_delete=models.CASCADE,
        related_name='evidence'
    )
    file_url = models.CharField(max_length=512)
    caption = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"Evidence for Alert {self.alert_id}: {self.file_url}"

