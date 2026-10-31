from typing import Optional
from django.db.models import QuerySet
from .models import ResponderDispatch

def list_dispatches_for_responder(responder) -> QuerySet[ResponderDispatch]:
    return ResponderDispatch.objects.filter(responder=responder).select_related('incident')

def list_dispatches_for_incident(incident) -> QuerySet[ResponderDispatch]:
    return ResponderDispatch.objects.filter(incident=incident).select_related('responder')

def list_all_dispatches() -> QuerySet[ResponderDispatch]:
    return ResponderDispatch.objects.select_related('responder', 'incident').all()

def get_dispatch_by_id(dispatch_id) -> Optional[ResponderDispatch]:
    return ResponderDispatch.objects.filter(id=dispatch_id).select_related('responder', 'incident').first()

