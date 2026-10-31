import hashlib
from typing import Optional
from django.db.models import QuerySet
from .models import QRCodeBadge

def get_badge_by_code(code_identifier: str) -> Optional[QRCodeBadge]:
    return QRCodeBadge.objects.filter(code_identifier=code_identifier).select_related('user').first()

def get_badge_by_token(token: str) -> Optional[QRCodeBadge]:
    """
    Resolves badge by hashing the raw token.
    Falls back to code_identifier for backward compatibility.
    """
    token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
    badge = QRCodeBadge.objects.filter(token_hash=token_hash).select_related('user').first()
    if not badge:
        badge = QRCodeBadge.objects.filter(code_identifier=token).select_related('user').first()
    return badge

def list_user_badges(user) -> QuerySet[QRCodeBadge]:
    return QRCodeBadge.objects.filter(user=user)
