import uuid
from django.db import models
from django.conf import settings

class AuditEvent(models.Model):
    """
    Immutable audit event recording security, administrative, and data access actions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_actions'
    )
    action = models.CharField(max_length=120, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    target_model = models.CharField(max_length=120, blank=True)
    target_id = models.CharField(max_length=255, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['actor', 'timestamp']),
        ]

    def __str__(self):
        actor_repr = self.actor.email if self.actor else 'SYSTEM/ANONYMOUS'
        return f"[{self.timestamp}] {actor_repr} -> {self.action}"
