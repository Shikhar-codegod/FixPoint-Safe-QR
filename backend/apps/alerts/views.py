import uuid
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_spectacular.utils import extend_schema
from apps.common.responses import api_response
from apps.common.permissions import IsOperator
from apps.qr_codes.models import QRCodeBadge, QRCodeStatus
from .serializers import AlertRecordSerializer
from .services import create_alert_record
from .selectors import list_alerts_for_user, list_active_alerts

@extend_schema(summary="List User Emergency Alerts")
class UserAlertsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role in ['OPERATOR', 'SUPERVISOR', 'ADMIN']:
            alerts = list_active_alerts()
        else:
            alerts = list_alerts_for_user(request.user)
        return api_response(data=AlertRecordSerializer(alerts, many=True).data)

    def post(self, request):
        qr_badge = None
        qr_code = request.data.get('qr_code')
        if qr_code:
            qr_badge = QRCodeBadge.objects.filter(code_identifier=qr_code).first()
            if not qr_badge:
                try:
                    uuid.UUID(str(qr_code))
                    qr_badge = QRCodeBadge.objects.filter(id=qr_code).first()
                except (ValueError, TypeError):
                    pass

        alert = create_alert_record(
            user=request.user,
            qr_badge=qr_badge,
            severity=request.data.get('severity', 'CRITICAL'),
            latitude=request.data.get('latitude'),
            longitude=request.data.get('longitude'),
            location_address=request.data.get('location_address', ''),
            notes=request.data.get('notes', '')
        )
        return api_response(
            data=AlertRecordSerializer(alert).data,
            message="Alert record initiated.",
            status_code=status.HTTP_201_CREATED
        )

@extend_schema(summary="Public Safe-QR Emergency Alert")
class PublicAlertView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, code_identifier):
        qr_badge = QRCodeBadge.objects.filter(
            code_identifier=code_identifier,
            status=QRCodeStatus.ACTIVE,
        ).first()
        if not qr_badge:
            return api_response(
                data=None,
                message="Safe-QR badge is not active or does not exist.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        alert = create_alert_record(
            user=None,
            qr_badge=qr_badge,
            severity=request.data.get('severity', 'CRITICAL'),
            latitude=request.data.get('latitude'),
            longitude=request.data.get('longitude'),
            location_address=request.data.get('location_address', ''),
            notes=request.data.get('notes', ''),
        )
        return api_response(
            data=AlertRecordSerializer(alert).data,
            message="Emergency alert accepted.",
            status_code=status.HTTP_201_CREATED,
        )
