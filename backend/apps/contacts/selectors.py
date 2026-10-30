from typing import Optional
from django.db.models import QuerySet
from .models import EmergencyContact

def list_user_contacts(user) -> QuerySet[EmergencyContact]:
    return EmergencyContact.objects.filter(user=user)

def get_contact_by_id(contact_id: str, user) -> Optional[EmergencyContact]:
    return EmergencyContact.objects.filter(id=contact_id, user=user).first()
