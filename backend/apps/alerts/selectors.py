from typing import Optional
from django.db.models import QuerySet
from .models import AlertRecord

def list_alerts_for_user(user) -> QuerySet[AlertRecord]:
    return AlertRecord.objects.filter(user=user)

def list_active_alerts() -> QuerySet[AlertRecord]:
    return AlertRecord.objects.filter(status__in=['TRIGGERED', 'ACKNOWLEDGED'])
