from django.db import models
from django.conf import settings
from apps.common.models import BaseModel

class VerificationStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    VERIFIED = 'VERIFIED', 'Verified'
    REJECTED = 'REJECTED', 'Rejected'
    SUSPENDED = 'SUSPENDED', 'Suspended'

class UserProfile(BaseModel):
    """
    Standard customer or citizen profile details.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    avatar_url = models.URLField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    preferred_language = models.CharField(max_length=10, default='en')

    def __str__(self):
        return f"Profile for {self.user.email}"

class ResponderProfile(BaseModel):
    """
    Operational profile for police and medical responders.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='responder_profile'
    )
    badge_number = models.CharField(max_length=64, blank=True, db_index=True)
    agency_name = models.CharField(max_length=128, blank=True)
    service_jurisdiction = models.CharField(max_length=128, blank=True)
    verification_status = models.CharField(
        max_length=32,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
        db_index=True
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Responder Profile [{self.badge_number}] {self.user.email} - {self.verification_status}"
