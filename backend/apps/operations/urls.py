from django.urls import path
from .views import (
    OperationsLogView,
    OperationsAlertQueueView,
    OperationsAlertClaimView,
    OperationsAlertNotesView,
)

app_name = 'operations'

urlpatterns = [
    path('log/', OperationsLogView.as_view(), name='operations-log'),
    path('alerts/', OperationsAlertQueueView.as_view(), name='operations-alert-queue'),
    path('alerts/<uuid:alert_id>/claim/', OperationsAlertClaimView.as_view(), name='operations-alert-claim'),
    path('alerts/<uuid:alert_id>/notes/', OperationsAlertNotesView.as_view(), name='operations-alert-notes'),
]
