from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from apps.common.responses import api_response
from apps.common.permissions import IsOperator
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
        alert = create_alert_record(
            user=request.user,
            severity=request.data.get('severity', 'CRITICAL'),
            location_address=request.data.get('location_address', ''),
            notes=request.data.get('notes', '')
        )
        return api_response(
            data=AlertRecordSerializer(alert).data,
            message="Alert record initiated.",
            status_code=status.HTTP_201_CREATED
        )
