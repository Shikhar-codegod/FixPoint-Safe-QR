from django.db import models
from django.conf import settings
from apps.common.models import BaseModel
from apps.incidents.models import IncidentRecord

class OperationsLogEntry(BaseModel):
    """
    Command operations log for supervisors and operators managing active incidents.
    """
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='operations_log_entries'
    )
    incident = models.ForeignKey(
        IncidentRecord,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='operations_log'
    )
    action = models.CharField(max_length=120, db_index=True)
    details = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[OpsLog] {self.action} by {getattr(self.operator, 'email', 'SYSTEM')} @ {self.created_at}"
