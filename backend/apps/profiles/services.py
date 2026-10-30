from typing import Optional
from django.utils import timezone
from .models import UserProfile, ResponderProfile, VerificationStatus

def get_or_create_user_profile(user) -> UserProfile:
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile

def update_user_profile(user, **data) -> UserProfile:
    profile = get_or_create_user_profile(user)
    for field, val in data.items():
        if hasattr(profile, field):
            setattr(profile, field, val)
    profile.save()
    return profile

def get_or_create_responder_profile(user) -> ResponderProfile:
    profile, _ = ResponderProfile.objects.get_or_create(user=user)
    return profile

def update_responder_profile(user, **data) -> ResponderProfile:
    profile = get_or_create_responder_profile(user)
    for field in ['badge_number', 'agency_name', 'service_jurisdiction', 'notes']:
        if field in data:
            setattr(profile, field, data[field])
    profile.save()
    return profile
