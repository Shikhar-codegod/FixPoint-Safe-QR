from django.db import models
from django.conf import settings
from apps.common.models import BaseModel

class NotificationChannel(models.TextChoices):
    SMS = 'SMS', 'SMS'
    WHATSAPP = 'WHATSAPP', 'WhatsApp'
    PUSH = 'PUSH', 'Push Notification'
    VOICE_CALL = 'VOICE_CALL', 'Automated Voice Call'
    EMAIL = 'EMAIL', 'Email'

class NotificationStatus(models.TextChoices):
    QUEUED = 'QUEUED', 'Queued'
    SENT = 'SENT', 'Sent'
    DELIVERED = 'DELIVERED', 'Delivered'
    FAILED = 'FAILED', 'Failed'

class NotificationRecord(BaseModel):
    """
    Foundational notification record tracking outgoing emergency communications.
    """
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )
    recipient_destination = models.CharField(max_length=128)
    channel = models.CharField(
        max_length=32,
        choices=NotificationChannel.choices,
        default=NotificationChannel.SMS,
        db_index=True
    )
    title = models.CharField(max_length=128, blank=True)
    body = models.TextField()
    status = models.CharField(
        max_length=32,
        choices=NotificationStatus.choices,
        default=NotificationStatus.QUEUED,
        db_index=True
    )
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification [{self.channel}] to {self.recipient_destination} - {self.status}"
