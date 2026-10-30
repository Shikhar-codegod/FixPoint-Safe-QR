from django.urls import path
from .views import (
    IncidentsListView,
    PublicIncidentReportView,
    IncidentQueueView,
    IncidentDetailView,
    IncidentPhotosView,
    IncidentPhotoDetailView,
    IncidentUpgradeToAlertView,
)

app_name = 'incidents'

urlpatterns = [
    path('', IncidentsListView.as_view(), name='incidents-list-create'),
    path('queue/', IncidentQueueView.as_view(), name='incident-queue'),
    path('report/<str:code_identifier>/', PublicIncidentReportView.as_view(), name='incident-public-report'),
    path('<str:incident_number>/', IncidentDetailView.as_view(), name='incident-detail'),
    path('<str:incident_number>/upgrade-to-alert/', IncidentUpgradeToAlertView.as_view(), name='incident-upgrade-to-alert'),
    path('<str:incident_number>/photos/', IncidentPhotosView.as_view(), name='incident-photos'),
    path('<str:incident_number>/photos/<uuid:photo_id>/', IncidentPhotoDetailView.as_view(), name='incident-photo-detail'),
]
