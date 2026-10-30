from django.db import models
from django.conf import settings
from apps.common.models import BaseModel
from apps.incidents.models import IncidentRecord

class DispatchStatus(models.TextChoices):
    ASSIGNED = 'ASSIGNED', 'Assigned'
    EN_ROUTE = 'EN_ROUTE', 'En Route'
    ON_SCENE = 'ON_SCENE', 'On Scene'
    COMPLETED = 'COMPLETED', 'Completed'
    CANCELLED = 'CANCELLED', 'Cancelled'

class ResponderDispatch(BaseModel):
    """
    Tracks individual responder assignment to an incident.
    """
    responder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='dispatches'
    )
    incident = models.ForeignKey(
        IncidentRecord,
        on_delete=models.CASCADE,
        related_name='dispatches'
    )
    status = models.CharField(
        max_length=32,
        choices=DispatchStatus.choices,
        default=DispatchStatus.ASSIGNED,
        db_index=True
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    arrived_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-assigned_at']
        unique_together = [('responder', 'incident')]

    def __str__(self):
        return f"Dispatch: {getattr(self.responder, 'email', 'Unknown')} → Incident {self.incident.incident_number} [{self.status}]"
