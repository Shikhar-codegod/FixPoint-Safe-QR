from typing import Optional
from django.db.models import QuerySet
from .models import IncidentRecord

def list_incidents(status: Optional[str] = None) -> QuerySet[IncidentRecord]:
    qs = IncidentRecord.objects.select_related('reporter').all()
    if status:
        qs = qs.filter(status=status)
    return qs

def get_incident_by_number(incident_number: str) -> Optional[IncidentRecord]:
    return IncidentRecord.objects.filter(incident_number=incident_number).select_related('reporter').first()
