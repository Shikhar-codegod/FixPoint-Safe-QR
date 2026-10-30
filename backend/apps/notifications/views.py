from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_spectacular.utils import extend_schema
from django.conf import settings

from apps.common.responses import api_response
from apps.alerts.models import AlertRecord
from .serializers import NotificationRecordSerializer
from .selectors import list_notifications_for_user
from .providers.factory import get_provider_status
from .services import (
    get_ack_summary,
    acknowledge_chain_by_token,
    process_mock_webhook,
    get_alert_timeline,
)

@extend_schema(summary="Get Notification Provider Status")
class ProviderStatusView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        status_data = get_provider_status()
        return api_response(data=status_data, message="Notification provider status retrieved.")

@extend_schema(summary="List User Notifications")
class UserNotificationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        records = list_notifications_for_user(request.user)
        return api_response(data=NotificationRecordSerializer(records, many=True).data)

@extend_schema(summary="View Alert Notification Timeline")
class AlertNotificationTimelineView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, alert_id):
        alert = AlertRecord.objects.filter(id=alert_id).first()
        if not alert:
            return api_response(
                data=None,
                message="Alert not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Access control: user must be alert owner or staff (OPERATOR, SUPERVISOR, ADMIN)
        is_owner = alert.user == request.user
        is_staff = request.user.role in ['OPERATOR', 'SUPERVISOR', 'ADMIN']
        if not (is_owner or is_staff):
            return api_response(
                data=None,
                message="You do not have permission to view this alert timeline.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        timeline = get_alert_timeline(alert, request.user)
        return api_response(data=timeline, message="Alert notification timeline retrieved.")

@extend_schema(summary="Public Emergency Alert Acknowledgement")
class PublicNotificationAckView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, token):
        summary = get_ack_summary(token)
        if not summary:
            return api_response(
                data=None,
                message="Invalid or expired acknowledgement token.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        return api_response(data=summary, message="Alert acknowledgement details retrieved.")

    def post(self, request, token):
        success, message, chain = acknowledge_chain_by_token(token, channel='WEB')
        if not success:
            return api_response(
                data=None,
                message=message,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        return api_response(
            data={'status': chain.status, 'acknowledged_at': chain.acknowledged_at},
            message=message
        )

@extend_schema(summary="Simulated Provider Inbound Webhook")
class MockWebhookView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        mode = getattr(settings, 'NOTIFICATION_PROVIDER_MODE', 'mock').lower()
        if mode != 'mock':
            return api_response(
                data=None,
                message="Mock webhooks are disabled in non-mock provider mode.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        signature = request.headers.get('X-Signature', '')
        success, message = process_mock_webhook(request.data, signature)
        if not success:
            return api_response(
                data=None,
                message=message,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        return api_response(data=None, message=message)
