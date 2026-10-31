from django.db import models
from django.conf import settings
from apps.common.models import BaseModel

class QRCodeStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Active'
    REVOKED = 'REVOKED', 'Revoked'
    INACTIVE = 'INACTIVE', 'Inactive'

class QRCodeBadge(BaseModel):
    """
    Safe-QR Vehicle & Personal Emergency Badge foundation.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='qr_badges'
    )
    code_identifier = models.CharField(max_length=64, unique=True, db_index=True)
    token_hash = models.CharField(max_length=64, unique=True, db_index=True, null=True, blank=True)
    generation = models.PositiveSmallIntegerField(default=1)
    vehicle_registration = models.CharField(max_length=32, blank=True, db_index=True)
    vehicle_model = models.CharField(max_length=64, blank=True)
    status = models.CharField(
        max_length=16,
        choices=QRCodeStatus.choices,
        default=QRCodeStatus.ACTIVE,
        db_index=True
    )
    scan_count = models.PositiveIntegerField(default=0)
    last_scanned_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"QR Badge [{self.code_identifier}] - {self.vehicle_registration or 'Personal'}"
