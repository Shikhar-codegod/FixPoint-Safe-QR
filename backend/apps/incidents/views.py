from django.http import FileResponse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.utils import extend_schema

from apps.common.responses import api_response
from apps.common.permissions import IsOperator
from apps.qr_codes.models import QRCodeBadge, QRCodeStatus
from .models import IncidentRecord, IncidentPhoto
from .serializers import IncidentRecordSerializer, IncidentPhotoSerializer
from .services import create_incident, update_incident_status, add_incident_photo, upgrade_incident_to_alert
from .selectors import list_scoped_incidents, get_operator_queue, get_incident_by_number
from .throttles import PublicIncidentIPRateThrottle, PublicIncidentQRRateThrottle

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
        incidents = list_scoped_incidents(request.user)
        serializer = IncidentRecordSerializer(incidents, many=True, context={'request': request})
        return api_response(data=serializer.data)

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

    def get(self, request, incident_number):
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
                message="You do not have permission to view this incident.",
                status_code=status.HTTP_403_FORBIDDEN
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

        # Security check: updating incident status requires IsOperator
        is_operator = request.user.role in ['OPERATOR', 'SUPERVISOR', 'ADMIN'] or request.user.is_staff
        if not is_operator:
            return api_response(
                data=None,
                message="Only system operators and supervisors may update incident status.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        if request.data.get('claim') is True:
            incident.claimed_by = request.user
            incident.save(update_fields=['claimed_by', 'updated_at'])

        new_status = request.data.get('status')
        if new_status:
            incident = update_incident_status(incident, new_status, actor=request.user)
        if 'operator_notes' in request.data:
            incident.operator_notes = request.data['operator_notes']
            incident.save(update_fields=['operator_notes', 'updated_at'])

        return api_response(
            data=IncidentRecordSerializer(incident, context={'request': request}).data,
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
                message="Incident successfully upgraded to emergency alert.",
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
