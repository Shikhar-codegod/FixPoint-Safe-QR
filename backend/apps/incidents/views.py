from django.http import FileResponse
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
from apps.responders.models import ResponderDispatch
from .models import IncidentRecord, IncidentStatus, IncidentPhoto
from .serializers import IncidentRecordSerializer, IncidentPhotoSerializer
from .services import create_incident, update_incident, update_incident_status, add_incident_photo, upgrade_incident_to_alert
from .selectors import list_scoped_incidents, list_incidents_for_user, get_operator_queue, get_incident_by_number
from .throttles import PublicIncidentIPRateThrottle, PublicIncidentQRRateThrottle

ALLOWED_PATCH_FIELDS = {'status', 'description'}


def has_incident_access(incident: IncidentRecord, user) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.role in ['OPERATOR', 'SUPERVISOR', 'ADMIN'] or user.is_staff:
        return True
    if incident.reporter_id == user.id:
        return True
    if incident.qr_badge and incident.qr_badge.user_id == user.id:
        return True
    return False


@extend_schema(summary="List Scoped Incidents or Report Authenticated Incident")
class IncidentsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        status_param = request.query_params.get('status')
        incidents = list_incidents_for_user(request.user, status=status_param)
        return api_response(data=IncidentRecordSerializer(incidents, many=True).data)

    def post(self, request):
        serializer = IncidentRecordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        qr_badge = None
        qr_code = request.data.get('qr_code')
        if qr_code:
            qr_badge = QRCodeBadge.objects.filter(code_identifier=qr_code).first()

        incident = create_incident(
            incident_type=serializer.validated_data['incident_type'],
            reporter=request.user,
            qr_badge=qr_badge,
            priority=serializer.validated_data.get('priority', 'LOW'),
            location_precision=serializer.validated_data.get('location_precision', 'NONE'),
            reporter_contact_shared=serializer.validated_data.get('reporter_contact_shared', False),
            latitude=serializer.validated_data.get('latitude'),
            longitude=serializer.validated_data.get('longitude'),
            location_address=serializer.validated_data.get('location_address', ''),
            description=serializer.validated_data.get('description', '')
        )
        return api_response(
            data=IncidentRecordSerializer(incident, context={'request': request}).data,
            message="Incident recorded successfully.",
            status_code=status.HTTP_201_CREATED
        )


@extend_schema(summary="Public Incident Reporting by Safe-QR Badge")
class PublicIncidentReportView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [PublicIncidentIPRateThrottle, PublicIncidentQRRateThrottle]

    def post(self, request, code_identifier):
        badge = QRCodeBadge.objects.filter(code_identifier=code_identifier).first()
        if not badge or badge.status != QRCodeStatus.ACTIVE:
            return api_response(
                data=None,
                message="Safe-QR badge is not active or does not exist.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        serializer = IncidentRecordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        reporter = request.user if request.user and request.user.is_authenticated else None

        incident = create_incident(
            incident_type=serializer.validated_data['incident_type'],
            reporter=reporter,
            qr_badge=badge,
            priority=serializer.validated_data.get('priority', 'LOW'),
            location_precision=serializer.validated_data.get('location_precision', 'NONE'),
            reporter_contact_shared=serializer.validated_data.get('reporter_contact_shared', False),
            latitude=serializer.validated_data.get('latitude'),
            longitude=serializer.validated_data.get('longitude'),
            location_address=serializer.validated_data.get('location_address', ''),
            description=serializer.validated_data.get('description', '')
        )
        return api_response(
            data=IncidentRecordSerializer(incident, context={'request': request}).data,
            message="Incident reported via Safe-QR successfully.",
            status_code=status.HTTP_201_CREATED
        )


@extend_schema(summary="Operator Dispatch Queue")
class IncidentQueueView(APIView):
    permission_classes = [IsOperator]

    def get(self, request):
        status_param = request.query_params.get('status')
        category_param = request.query_params.get('category')
        incidents = get_operator_queue(status=status_param, category=category_param)
        return api_response(data=IncidentRecordSerializer(incidents, many=True, context={'request': request}).data)


@extend_schema(summary="Incident Detail and Operator Status Update")
class IncidentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _is_operator(self, user) -> bool:
        return bool(
            user.role in ['OPERATOR', 'SUPERVISOR', 'ADMIN']
            or getattr(user, 'is_staff', False)
            or getattr(user, 'is_superuser', False)
        )

    # Dispatch statuses that represent an active, ongoing assignment.
    # COMPLETED and CANCELLED assignments no longer grant incident access.
    ACTIVE_DISPATCH_STATUSES = {'ASSIGNED', 'EN_ROUTE', 'ON_SCENE'}

    def _is_active_assigned_responder(self, user, incident) -> bool:
        """
        Returns True only when the user is a verified responder with an active
        (ASSIGNED, EN_ROUTE, or ON_SCENE) dispatch record for this incident.
        A COMPLETED or CANCELLED dispatch does not confer access.
        """
        if user.role not in ['POLICE_RESPONDER', 'MEDICAL_RESPONDER']:
            return False
        if not getattr(user, 'is_verified_responder', False):
            return False
        return ResponderDispatch.objects.filter(
            incident=incident,
            responder=user,
            status__in=self.ACTIVE_DISPATCH_STATUSES
        ).exists()

    def get(self, request, incident_number):
        incident = get_incident_by_number(incident_number)
        if not incident:
            return api_response(
                data=None,
                message="Incident not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        is_operator = self._is_operator(request.user)
        is_reporter = incident.reporter_id == request.user.id
        is_owner = bool(incident.qr_badge and incident.qr_badge.user_id == request.user.id)
        is_responder_role = request.user.role in ['POLICE_RESPONDER', 'MEDICAL_RESPONDER']

        # Unverified responders are denied before any further check.
        if is_responder_role and not getattr(request.user, 'is_verified_responder', False):
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'permission_denied',
                        'message': 'Unverified responders cannot access incident records.',
                        'details': None
                    }
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # Verified responders must have an active assignment to this incident.
        is_active_assigned = self._is_active_assigned_responder(request.user, incident)

        if not (is_operator or is_reporter or is_owner or is_active_assigned):
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'permission_denied',
                        'message': 'You do not have permission to view this incident.',
                        'details': None
                    }
                },
                status=status.HTTP_403_FORBIDDEN
            )

        return api_response(data=IncidentRecordSerializer(incident, context={'request': request}).data)

    def patch(self, request, incident_number):
        incident = get_incident_by_number(incident_number)
        if not incident:
            return api_response(
                data=None,
                message="Incident not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        # 1. Customers and public citizens must never modify incident statuses
        if request.user.role in ['CUSTOMER', 'PUBLIC']:
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'permission_denied',
                        'message': 'Customers and public citizens are not permitted to modify incident records.',
                        'details': None
                    }
                },
                status=status.HTTP_403_FORBIDDEN
            )

        is_operator = self._is_operator(request.user)
        is_responder = request.user.role in ['POLICE_RESPONDER', 'MEDICAL_RESPONDER']

        if is_responder:
            if not getattr(request.user, 'is_verified_responder', False):
                return Response(
                    {
                        'success': False,
                        'error': {
                            'code': 'permission_denied',
                            'message': 'Unverified responders cannot modify incident records.',
                            'details': None
                        }
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
            if not self._is_active_assigned_responder(request.user, incident):
                return Response(
                    {
                        'success': False,
                        'error': {
                            'code': 'permission_denied',
                            'message': 'Responders may only update incidents to which they are actively assigned.',
                            'details': None
                        }
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
        elif not is_operator:
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'permission_denied',
                        'message': 'You do not have permission to modify this incident.',
                        'details': None
                    }
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # 2. Reject non-permitted fields
        disallowed_keys = set(request.data.keys()) - ALLOWED_PATCH_FIELDS
        if disallowed_keys:
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'validation_error',
                        'message': f"Fields not permitted for modification: {', '.join(sorted(disallowed_keys))}.",
                        'details': {k: 'Field cannot be modified via PATCH' for k in disallowed_keys}
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        new_status = request.data.get('status')
        description = request.data.get('description')

        if not new_status and description is None:
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'validation_error',
                        'message': 'No valid editable fields provided.',
                        'details': None
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Validate status value and role constraints
        if new_status:
            if new_status not in IncidentStatus.values:
                return Response(
                    {
                        'success': False,
                        'error': {
                            'code': 'validation_error',
                            'message': f"'{new_status}' is not a valid incident status.",
                            'details': {'status': [f"'{new_status}' is not a valid choice."]}
                        }
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Responders cannot close incidents
            if is_responder and new_status == IncidentStatus.CLOSED:
                return Response(
                    {
                        'success': False,
                        'error': {
                            'code': 'permission_denied',
                            'message': 'Responders are not permitted to close incidents. Incident closure requires operator or supervisor authorization.',
                            'details': None
                        }
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

        # 4. Perform database-locked update with transition validation
        try:
            updated_incident = update_incident(
                incident=incident,
                new_status=new_status,
                description=description,
                actor=request.user
            )
        except ValidationError as exc:
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'invalid_transition',
                        'message': str(exc.message if hasattr(exc, 'message') else exc),
                        'details': {'status': [str(exc.message if hasattr(exc, 'message') else exc)]}
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return api_response(
            data=IncidentRecordSerializer(updated_incident, context={'request': request}).data,
            message="Incident status updated."
        )


@extend_schema(summary="Upload Incident Photo Attachment")
class IncidentPhotosView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, incident_number):
        incident = get_incident_by_number(incident_number)
        if not incident:
            return api_response(
                data=None,
                message="Incident not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        if not has_incident_access(incident, request.user):
            return api_response(
                data=None,
                message="You do not have permission to attach photos to this incident.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        photo_file = request.FILES.get('photo')
        if not photo_file:
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'validation_error',
                        'message': 'No photo file provided.',
                        'details': None,
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            photo = add_incident_photo(incident, photo_file, actor=request.user)
            return api_response(
                data=IncidentPhotoSerializer(photo).data,
                message="Photo attached successfully with EXIF/GPS metadata removed.",
                status_code=status.HTTP_201_CREATED
            )
        except ValueError as err:
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'validation_error',
                        'message': str(err),
                        'details': None,
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema(summary="Download Authenticated Incident Photo")
class IncidentPhotoDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, incident_number, photo_id):
        incident = get_incident_by_number(incident_number)
        if not incident:
            return api_response(
                data=None,
                message="Incident not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        if not has_incident_access(incident, request.user):
            return api_response(
                data=None,
                message="You do not have permission to access photos for this incident.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        photo = incident.photos.filter(id=photo_id).first()
        if not photo or not photo.photo_file:
            return api_response(
                data=None,
                message="Photo not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        return FileResponse(photo.photo_file.open('rb'), content_type=photo.content_type)


@extend_schema(summary="Upgrade Incident to Emergency Alert")
class IncidentUpgradeToAlertView(APIView):
    permission_classes = [IsOperator]

    def post(self, request, incident_number):
        incident = get_incident_by_number(incident_number)
        if not incident:
            return api_response(
                data=None,
                message="Incident not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        try:
            alert = upgrade_incident_to_alert(incident, actor=request.user)
            return api_response(
                data={
                    'incident_number': incident.incident_number,
                    'alert_id': str(alert.id),
                    'alert_status': alert.status,
                    'alert_severity': alert.severity,
                },
                message="Incident successfully upgraded to emergency alert draft. Alert requires confirmation before activation.",
                status_code=status.HTTP_201_CREATED
            )
        except ValueError as err:
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'validation_error',
                        'message': str(err),
                        'details': None,
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
