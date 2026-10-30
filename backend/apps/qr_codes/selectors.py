from typing import Optional
from django.db.models import QuerySet
from .models import QRCodeBadge

def get_badge_by_code(code_identifier: str) -> Optional[QRCodeBadge]:
    return QRCodeBadge.objects.filter(code_identifier=code_identifier).select_related('user').first()

def list_user_badges(user) -> QuerySet[QRCodeBadge]:
    return QRCodeBadge.objects.filter(user=user)
