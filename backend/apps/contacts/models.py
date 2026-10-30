from django.db import models
from django.conf import settings
from apps.common.models import BaseModel
from apps.common.encryption import EncryptedCharField

class ConsentStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    GRANTED = 'GRANTED', 'Granted'
    DECLINED = 'DECLINED', 'Declined'
    WITHDRAWN = 'WITHDRAWN', 'Withdrawn'

class PreferredLanguage(models.TextChoices):
    EN = 'en', 'English'
    HI = 'hi', 'Hindi'

class EmergencyContact(BaseModel):
    """
    Emergency contact records with AES/Fernet field-level encryption for phone and email,
    explicit consent tracking, notification channel preferences, and unique phone hash.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='emergency_contacts'
    )
    name = models.CharField(max_length=120)
    relationship = models.CharField(max_length=64)
    
    # Field-level encrypted at rest with Fernet
    phone_number = EncryptedCharField(max_length=512)
    email = EncryptedCharField(max_length=512, blank=True)
    
    # Deterministic HMAC-SHA256 hash of normalised E.164 phone number
    phone_hash = models.CharField(max_length=64, db_index=True, blank=True)
    
    priority_order = models.PositiveSmallIntegerField(default=1)
    is_primary = models.BooleanField(default=False)

    # Consent and verification
    consent_status = models.CharField(
        max_length=16,
        choices=ConsentStatus.choices,
        default=ConsentStatus.PENDING,
        db_index=True
    )
    consent_given_at = models.DateTimeField(null=True, blank=True)
    consent_withdrawn_at = models.DateTimeField(null=True, blank=True)
    consent_token_hash = models.CharField(max_length=64, blank=True, db_index=True)
    consent_token_expires_at = models.DateTimeField(null=True, blank=True)

    # Communication Preferences
    preferred_language = models.CharField(
        max_length=8,
        choices=PreferredLanguage.choices,
        default=PreferredLanguage.EN
    )
    notify_whatsapp = models.BooleanField(default=True)
    notify_sms = models.BooleanField(default=True)
    notify_call = models.BooleanField(default=True)
    wave = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ['priority_order', '-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'phone_hash'],
                name='unique_user_phone_hash'
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.relationship}) - User: {self.user.email} [{self.consent_status}]"
