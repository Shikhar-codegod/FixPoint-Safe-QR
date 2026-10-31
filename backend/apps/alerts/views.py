import uuid
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema
from apps.common.responses import api_response
from apps.common.permissions import IsOperator
from apps.qr_codes.models import QRCodeBadge, QRCodeStatus
from .models import AlertRecord, AlertStatus
from .serializers import (
    AlertPublicSerializer,
    AlertDetailSerializer,
    AlertDraftCreateSerializer,
    AlertConfirmSerializer,
    AlertCloseSerializer,
    AlertEvidenceSerializer,
)
from .services import (
    create_alert_draft,
    create_alert_record,
    confirm_alert,
    close_alert,
    add_alert_evidence,
)
from .selectors import (
    get_alert_by_id,
    list_alerts_for_user,
    list_active_alerts,
)


def is_operator_or_above(user) -> bool:
    if not (user and user.is_authenticated):
        return False
    return bool(
        user.role in ['OPERATOR', 'SUPERVISOR', 'ADMIN']
        or getattr(user, 'is_staff', False)
        or getattr(user, 'is_superuser', False)
    )


@extend_schema(summary="List Alerts or Create Alert Draft")
class AlertListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == 'POST':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request):
        if is_operator_or_above(request.user):
            alerts = list_active_alerts()
        else:
            alerts = list_alerts_for_user(request.user)
        return api_response(data=AlertDetailSerializer(alerts, many=True).data)

    def post(self, request):
        serializer = AlertDraftCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'validation_error',
                        'message': 'Invalid alert draft payload.',
                        'details': serializer.errors
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        reporter = request.user if request.user.is_authenticated else None
        try:
            alert, raw_token = create_alert_draft(
                qr_token=serializer.validated_data['qr_token'],
                reporter=reporter,
                severity=serializer.validated_data.get('severity', 'CRITICAL'),
                latitude=serializer.validated_data.get('latitude'),
                longitude=serializer.validated_data.get('longitude'),
                location_address=serializer.validated_data.get('location_address', ''),
                notes=serializer.validated_data.get('notes', '')
            )
        except ValidationError as exc:
            msg = str(exc.message if hasattr(exc, 'message') else exc)
            if 'already exists' in msg.lower():
                return Response(
                    {
                        'success': False,
                        'error': {
                            'code': 'active_alert_exists',
                            'message': msg,
                            'details': None
                        }
                    },
                    status=status.HTTP_409_CONFLICT
                )
            if 'not found' in msg.lower():
                return Response(
                    {
                        'success': False,
                        'error': {
                            'code': 'badge_not_found',
                            'message': msg,
                            'details': None
                        }
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'validation_error',
                        'message': msg,
                        'details': None
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        conf_token = getattr(alert, 'confirmation_token', None)
        return api_response(
            data={
                'alert_id': str(alert.id),
                'status': alert.status,
                'vehicle_registration': alert.qr_badge.vehicle_registration if alert.qr_badge else None,
                'vehicle_model': alert.qr_badge.vehicle_model if alert.qr_badge else None,
                'confirmation_token': raw_token,
                'confirmation_expires_at': conf_token.expires_at if conf_token else None,
                'created_at': alert.created_at,
            },
            message="Emergency alert draft created.",
            status_code=status.HTTP_201_CREATED
        )


@extend_schema(summary="Public Safe-QR Emergency Alert (legacy — creates DRAFT)")
class PublicAlertView(APIView):
    """
    Legacy public endpoint: POST to /api/v1/alerts/public/<code_identifier>/
    Creates a DRAFT alert record using the QR badge code_identifier.
    Scanning a QR code must never automatically trigger an emergency workflow.
    """
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
            data={
                'alert_id': str(alert.id),
                'status': alert.status,
            },
            message="Emergency alert draft accepted. Please confirm to activate.",
            status_code=status.HTTP_201_CREATED,
        )


@extend_schema(summary="Alert Detail View")
class AlertDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, alert_id):
        alert = get_alert_by_id(alert_id)
        if not alert:
            return api_response(
                data=None,
                message="Emergency alert not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Full details for owner or operator/supervisor; public-safe view for all others
        if is_operator_or_above(request.user) or (
            request.user.is_authenticated and alert.user_id == request.user.id
        ):
            return api_response(data=AlertDetailSerializer(alert).data)

        return api_response(data=AlertPublicSerializer(alert).data)


@extend_schema(summary="Confirm Emergency Alert Draft")
class AlertConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, alert_id):
        serializer = AlertConfirmSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'validation_error',
                        'message': 'Invalid confirmation payload.',
                        'details': serializer.errors
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        actor = request.user if request.user.is_authenticated else None
        try:
            alert = confirm_alert(
                alert_id=alert_id,
                confirmation_token=serializer.validated_data['confirmation_token'],
                actor=actor
            )
        except ValidationError as exc:
            msg = str(exc.message if hasattr(exc, 'message') else exc)
            if 'not found' in msg.lower():
                return Response(
                    {
                        'success': False,
                        'error': {
                            'code': 'alert_not_found',
                            'message': msg,
                            'details': None
                        }
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'invalid_token',
                        'message': msg,
                        'details': None
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return api_response(
            data=AlertPublicSerializer(alert).data,
            message="Emergency alert confirmed. Notifications dispatched."
        )


@extend_schema(summary="Close Emergency Alert")
class AlertCloseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, alert_id):
        alert = get_alert_by_id(alert_id)
        if not alert:
            return api_response(
                data=None,
                message="Emergency alert not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # Authorization check:
        # Operators, Supervisors, and Admins can close any alert.
        # Customers can only close their own alerts.
        is_op = is_operator_or_above(request.user)
        is_owner = alert.user_id == request.user.id

        if not (is_op or is_owner):
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'permission_denied',
                        'message': 'You do not have permission to close this alert.',
                        'details': None
                    }
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # Responders cannot close alerts
        if request.user.role in ['POLICE_RESPONDER', 'MEDICAL_RESPONDER']:
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'permission_denied',
                        'message': 'Responders are not permitted to close emergency alerts.',
                        'details': None
                    }
                },
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = AlertCloseSerializer(data=request.data)
        serializer.is_valid()
        reason = serializer.validated_data.get('reason', '') if serializer.validated_data else ''

        try:
            closed = close_alert(alert_id=alert_id, actor=request.user, reason=reason)
        except ValidationError as exc:
            msg = str(exc.message if hasattr(exc, 'message') else exc)
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'closure_error',
                        'message': msg,
                        'details': None
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return api_response(
            data=AlertDetailSerializer(closed).data,
            message="Alert closed successfully."
        )


@extend_schema(summary="Attach Evidence to Alert")
class AlertEvidenceView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, alert_id):
        alert = get_alert_by_id(alert_id)
        if not alert:
            return api_response(
                data=None,
                message="Emergency alert not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        file_url = request.data.get('file_url')
        if not file_url:
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'validation_error',
                        'message': 'file_url is required.',
                        'details': {'file_url': ['This field is required.']}
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        evidence = add_alert_evidence(
            alert=alert,
            file_url=file_url,
            caption=request.data.get('caption', '')
        )
        return api_response(
            data=AlertEvidenceSerializer(evidence).data,
            message="Evidence attached successfully.",
            status_code=status.HTTP_201_CREATED
        )


# Backward compatibility alias
UserAlertsView = AlertListCreateView
