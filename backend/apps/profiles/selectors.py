from typing import Optional
from django.db.models import QuerySet
from .models import UserProfile, ResponderProfile

def get_profile_by_user(user) -> Optional[UserProfile]:
    return UserProfile.objects.filter(user=user).select_related('user').first()

def get_responder_profile_by_user(user) -> Optional[ResponderProfile]:
    return ResponderProfile.objects.filter(user=user).select_related('user').first()

def list_responder_profiles(status: Optional[str] = None) -> QuerySet[ResponderProfile]:
    qs = ResponderProfile.objects.select_related('user').all()
    if status:
        qs = qs.filter(verification_status=status)
    return qs
