from django.db import models
from django.conf import settings
from apps.common.models import BaseModel
from apps.common.encryption import EncryptedCharField

class EmergencyContact(BaseModel):
    """
    Emergency contact records with AES/Fernet field-level encryption for phone and email.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='emergency_contacts'
    )
    name = models.CharField(max_length=120)
    relationship = models.CharField(max_length=64)
    # Field-level encrypted at rest
    phone_number = EncryptedCharField(max_length=512)
    email = EncryptedCharField(max_length=512, blank=True)
    
    priority_order = models.PositiveSmallIntegerField(default=1)
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ['priority_order', '-created_at']

    def __str__(self):
        return f"{self.name} ({self.relationship}) - User: {self.user.email}"
