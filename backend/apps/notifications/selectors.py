from django.db.models import QuerySet
from .models import NotificationRecord

def list_notifications_for_user(user) -> QuerySet[NotificationRecord]:
    return NotificationRecord.objects.filter(recipient=user)
