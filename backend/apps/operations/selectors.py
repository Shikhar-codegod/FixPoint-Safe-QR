from django.db.models import QuerySet
from .models import OperationsLogEntry

def list_ops_log(incident=None) -> QuerySet[OperationsLogEntry]:
    qs = OperationsLogEntry.objects.select_related('operator', 'incident').all()
    if incident:
        qs = qs.filter(incident=incident)
    return qs
