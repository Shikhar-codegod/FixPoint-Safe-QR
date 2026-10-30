from django.urls import path
from .views import (
    ProviderStatusView,
    UserNotificationsView,
    AlertNotificationTimelineView,
    PublicNotificationAckView,
    MockWebhookView,
)

app_name = 'notifications'

urlpatterns = [
    path('provider-status/', ProviderStatusView.as_view(), name='provider-status'),
    path('', UserNotificationsView.as_view(), name='notifications-list'),
    path('alerts/<uuid:alert_id>/timeline/', AlertNotificationTimelineView.as_view(), name='alert-timeline'),
    path('ack/<str:token>/', PublicNotificationAckView.as_view(), name='notification-ack'),
    path('webhooks/mock/', MockWebhookView.as_view(), name='mock-webhook'),
]
