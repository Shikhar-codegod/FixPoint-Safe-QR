from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from apps.common.responses import api_response
from .models import EmergencyContact
from .serializers import EmergencyContactSerializer
from .services import create_emergency_contact, delete_emergency_contact
from .selectors import list_user_contacts, get_contact_by_id

@extend_schema(summary="List or Add Emergency Contacts")
class EmergencyContactsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        contacts = list_user_contacts(request.user)
        return api_response(data=EmergencyContactSerializer(contacts, many=True).data)

    def post(self, request):
        serializer = EmergencyContactSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        contact = create_emergency_contact(
            user=request.user,
            name=serializer.validated_data['name'],
            relationship=serializer.validated_data['relationship'],
            phone_number=serializer.validated_data['phone_number'],
            email=serializer.validated_data.get('email', ''),
            priority_order=serializer.validated_data.get('priority_order', 1),
            is_primary=serializer.validated_data.get('is_primary', False)
        )
        return api_response(
            data=EmergencyContactSerializer(contact).data,
            message="Emergency contact saved successfully.",
            status_code=status.HTTP_201_CREATED
        )

@extend_schema(summary="Delete Emergency Contact")
class EmergencyContactDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, contact_id):
        contact = get_contact_by_id(contact_id, request.user)
        if not contact:
            return api_response(
                data=None,
                message="Emergency contact not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        delete_emergency_contact(contact, request.user)
        return api_response(data=None, message="Emergency contact removed successfully.")
