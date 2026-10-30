from django.urls import path
from .views import IncidentsListView, IncidentDetailView

app_name = 'incidents'

urlpatterns = [
    path('', IncidentsListView.as_view(), name='incidents-list-create'),
    path('<str:incident_number>/', IncidentDetailView.as_view(), name='incident-detail'),
]
