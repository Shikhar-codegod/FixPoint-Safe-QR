from typing import Optional
from django.db.models import QuerySet
from .models import ResponderDispatch

def list_dispatches_for_responder(responder) -> QuerySet[ResponderDispatch]:
    return ResponderDispatch.objects.filter(responder=responder).select_related('incident')

def list_dispatches_for_incident(incident) -> QuerySet[ResponderDispatch]:
    return ResponderDispatch.objects.filter(incident=incident).select_related('responder')
