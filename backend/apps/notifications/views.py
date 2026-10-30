from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from apps.common.responses import api_response
from .serializers import NotificationRecordSerializer
from .selectors import list_notifications_for_user

@extend_schema(summary="List User Notifications")
class UserNotificationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        records = list_notifications_for_user(request.user)
        return api_response(data=NotificationRecordSerializer(records, many=True).data)
