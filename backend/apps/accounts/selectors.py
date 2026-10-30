from typing import Optional
from django.db.models import QuerySet
from .models import CustomUser

def get_user_by_id(user_id: str) -> Optional[CustomUser]:
    try:
        return CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        return None

def get_user_by_email(email: str) -> Optional[CustomUser]:
    try:
        return CustomUser.objects.get(email__iexact=email)
    except CustomUser.DoesNotExist:
        return None

def list_users_by_role(role: str) -> QuerySet[CustomUser]:
    return CustomUser.objects.filter(role=role, is_active=True)

def list_unverified_responders() -> QuerySet[CustomUser]:
    return CustomUser.objects.filter(
        role__in=['POLICE_RESPONDER', 'MEDICAL_RESPONDER'],
        is_verified_responder=False,
        is_active=True
    )
