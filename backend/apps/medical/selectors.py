from typing import Optional
from .models import MedicalProfile

def get_medical_profile_by_user(user) -> Optional[MedicalProfile]:
    return MedicalProfile.objects.filter(user=user).select_related('user').first()
