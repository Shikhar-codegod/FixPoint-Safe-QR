from django.urls import path
from .views import (
    AlertListCreateView,
    AlertDetailView,
    AlertConfirmView,
    AlertCloseView,
    AlertEvidenceView,
    PublicAlertView,
)

app_name = 'alerts'

urlpatterns = [
    path('', AlertListCreateView.as_view(), name='alerts-list-create'),
    path('<uuid:alert_id>/', AlertDetailView.as_view(), name='alert-detail'),
    path('<uuid:alert_id>/confirm/', AlertConfirmView.as_view(), name='alert-confirm'),
    path('<uuid:alert_id>/close/', AlertCloseView.as_view(), name='alert-close'),
    path('<uuid:alert_id>/evidence/', AlertEvidenceView.as_view(), name='alert-evidence'),
    # Public endpoint: scan QR and report emergency (Yashasvi's route — creates DRAFT via code_identifier)
    path('public/<str:code_identifier>/', PublicAlertView.as_view(), name='public-alert'),
]
