from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from apps.common.responses import api_response
from apps.common.permissions import IsOperator
from .serializers import IncidentRecordSerializer
from .services import create_incident, update_incident_status
from .selectors import list_incidents, get_incident_by_number

@extend_schema(summary="List or Create Incidents")
class IncidentsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        status_param = request.query_params.get('status')
        incidents = list_incidents(status=status_param)
        return api_response(data=IncidentRecordSerializer(incidents, many=True).data)

    def post(self, request):
        incident = create_incident(
            reporter=request.user,
            incident_type=request.data.get('incident_type', 'ROAD_ACCIDENT'),
            location_address=request.data.get('location_address', ''),
            description=request.data.get('description', '')
        )
        return api_response(
            data=IncidentRecordSerializer(incident).data,
            message="Incident recorded successfully.",
            status_code=status.HTTP_201_CREATED
        )

@extend_schema(summary="Incident Detail and Status Update")
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
        return api_response(data=IncidentRecordSerializer(incident).data)

    def patch(self, request, incident_number):
        incident = get_incident_by_number(incident_number)
        if not incident:
            return api_response(
                data=None,
                message="Incident not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        new_status = request.data.get('status')
        if new_status:
            update_incident_status(incident, new_status, actor=request.user)
        return api_response(
            data=IncidentRecordSerializer(incident).data,
            message="Incident status updated."
        )
