from django.db import models
from django.conf import settings
from apps.common.models import BaseModel
from apps.common.encryption import EncryptedTextField

class BloodGroup(models.TextChoices):
    A_POS = 'A+', 'A+'
    A_NEG = 'A-', 'A-'
    B_POS = 'B+', 'B+'
    B_NEG = 'B-', 'B-'
    AB_POS = 'AB+', 'AB+'
    AB_NEG = 'AB-', 'AB-'
    O_POS = 'O+', 'O+'
    O_NEG = 'O-', 'O-'
    UNKNOWN = 'UNKNOWN', 'Unknown'

class MedicalProfile(BaseModel):
    """
    Medical emergency record for drivers/citizens.
    Sensitive medical information is encrypted at rest using AES-128/Fernet.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='medical_profile'
    )
    blood_group = models.CharField(
        max_length=10,
        choices=BloodGroup.choices,
        default=BloodGroup.UNKNOWN
    )
    # Field-level encrypted fields
    allergies = EncryptedTextField(blank=True, help_text="Encrypted known allergies")
    medications = EncryptedTextField(blank=True, help_text="Encrypted current medications")
    chronic_conditions = EncryptedTextField(blank=True, help_text="Encrypted chronic conditions")
    emergency_notes = EncryptedTextField(blank=True, help_text="Encrypted emergency medical instructions")
    organ_donor = models.BooleanField(default=False)

    def __str__(self):
        return f"Medical Profile ({self.blood_group}) - {self.user.email}"
