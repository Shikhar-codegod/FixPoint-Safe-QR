from django.db import models
from django.conf import settings
from apps.common.models import BaseModel
from apps.alerts.models import AlertRecord
from apps.contacts.models import EmergencyContact

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
    Stores masked recipient destination to prevent plaintext phone exposure.
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


class ChainStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Active'
    ACKNOWLEDGED = 'ACKNOWLEDGED', 'Acknowledged'
    EXHAUSTED = 'EXHAUSTED', 'Exhausted'
    CANCELLED = 'CANCELLED', 'Cancelled'

class ChainStep(models.TextChoices):
    WHATSAPP = 'WHATSAPP', 'WhatsApp'
    SMS = 'SMS', 'SMS'
    CALL = 'CALL', 'Automated Voice Call'
    DONE = 'DONE', 'Done'

class AttemptStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    ACCEPTED = 'ACCEPTED', 'Accepted'
    DELIVERED = 'DELIVERED', 'Delivered'
    FAILED = 'FAILED', 'Failed'
    CANCELLED = 'CANCELLED', 'Cancelled'

class ContactNotificationChain(BaseModel):
    """
    Independent notification chain for a single contact linked to an alert.
    Orchestrates WhatsApp -> SMS -> Automated Voice Call progression.
    UNIQUE (alert, contact) prevents duplicate chains.
    """
    alert = models.ForeignKey(
        AlertRecord,
        on_delete=models.CASCADE,
        related_name='notification_chains'
    )
    contact = models.ForeignKey(
        EmergencyContact,
        on_delete=models.CASCADE,
        related_name='notification_chains'
    )
    status = models.CharField(
        max_length=20,
        choices=ChainStatus.choices,
        default=ChainStatus.ACTIVE,
        db_index=True
    )
    current_step = models.CharField(
        max_length=20,
        choices=ChainStep.choices,
        default=ChainStep.WHATSAPP,
        db_index=True
    )
    next_action_at = models.DateTimeField(null=True, blank=True, db_index=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    ack_channel = models.CharField(max_length=32, blank=True)
    ack_token_hash = models.CharField(max_length=64, blank=True, db_index=True)
    call_attempts = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['alert', 'contact'],
                name='unique_alert_contact_chain'
            )
        ]

    def __str__(self):
        return f"Chain [{self.status}:{self.current_step}] Alert {self.alert_id} -> Contact {self.contact_id}"


class DeliveryAttempt(BaseModel):
    """
    Persistent attempt record per channel and attempt number.
    Tracks simulated vs real provider metadata and masked destinations.
    """
    chain = models.ForeignKey(
        ContactNotificationChain,
        on_delete=models.CASCADE,
        related_name='delivery_attempts'
    )
    channel = models.CharField(max_length=32, db_index=True)
    attempt_no = models.PositiveSmallIntegerField(default=1)
    status = models.CharField(
        max_length=20,
        choices=AttemptStatus.choices,
        default=AttemptStatus.PENDING,
        db_index=True
    )
    idempotency_key = models.CharField(max_length=128, unique=True, db_index=True)
    provider_name = models.CharField(max_length=64, default="MOCK")
    is_simulated = models.BooleanField(default=True)
    provider_message_id = models.CharField(max_length=128, blank=True)
    error_code = models.CharField(max_length=64, blank=True)
    error_message = models.TextField(blank=True)
    masked_destination = models.CharField(max_length=32)
    requested_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Attempt #{self.attempt_no} [{self.channel}:{self.status}] Chain {self.chain_id}"
