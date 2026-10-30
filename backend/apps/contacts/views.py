from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_spectacular.utils import extend_schema
from apps.common.responses import api_response
from .models import EmergencyContact
from .serializers import EmergencyContactSerializer, ConsentDecisionSerializer
from .services import (
    create_emergency_contact,
    update_emergency_contact,
    delete_emergency_contact,
    request_contact_consent,
    get_consent_request_info,
    process_consent_decision,
    withdraw_contact_consent,
)
from .selectors import list_user_contacts, get_contact_by_id

@extend_schema(summary="List or Add Emergency Contacts")
class EmergencyContactsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        contacts = list_user_contacts(request.user)
        return api_response(data=EmergencyContactSerializer(contacts, many=True).data)

    def post(self, request):
        serializer = EmergencyContactSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        contact = create_emergency_contact(
            user=request.user,
            name=serializer.validated_data['name'],
            relationship=serializer.validated_data['relationship'],
            phone_number=serializer.validated_data['phone_number'],
            email=serializer.validated_data.get('email', ''),
            priority_order=serializer.validated_data.get('priority_order', 1),
            is_primary=serializer.validated_data.get('is_primary', False),
            preferred_language=serializer.validated_data.get('preferred_language', 'en'),
            notify_whatsapp=serializer.validated_data.get('notify_whatsapp', True),
            notify_sms=serializer.validated_data.get('notify_sms', True),
            notify_call=serializer.validated_data.get('notify_call', True),
            wave=serializer.validated_data.get('wave', 1),
        )
        return api_response(
            data=EmergencyContactSerializer(contact).data,
            message="Emergency contact saved successfully.",
            status_code=status.HTTP_201_CREATED
        )

@extend_schema(summary="View, Edit, or Delete Emergency Contact")
class EmergencyContactDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, contact_id):
        contact = get_contact_by_id(contact_id, request.user)
        if not contact:
            return api_response(
                data=None,
                message="Emergency contact not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        return api_response(data=EmergencyContactSerializer(contact).data)

    def put(self, request, contact_id):
        contact = get_contact_by_id(contact_id, request.user)
        if not contact:
            return api_response(
                data=None,
                message="Emergency contact not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        serializer = EmergencyContactSerializer(instance=contact, data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        updated = update_emergency_contact(contact, request.user, serializer.validated_data)
        return api_response(
            data=EmergencyContactSerializer(updated).data,
            message="Emergency contact updated successfully."
        )

    def patch(self, request, contact_id):
        contact = get_contact_by_id(contact_id, request.user)
        if not contact:
            return api_response(
                data=None,
                message="Emergency contact not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        serializer = EmergencyContactSerializer(
            instance=contact,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        updated = update_emergency_contact(contact, request.user, serializer.validated_data)
        return api_response(
            data=EmergencyContactSerializer(updated).data,
            message="Emergency contact updated successfully."
        )

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

@extend_schema(summary="Request Contact Consent")
class ContactConsentRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, contact_id):
        contact = get_contact_by_id(contact_id, request.user)
        if not contact:
            return api_response(
                data=None,
                message="Emergency contact not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        contact, raw_token = request_contact_consent(contact, request.user)
        
        response_data = {
            'contact_id': str(contact.id),
            'consent_status': contact.consent_status,
            'message': 'Consent request sent successfully.'
        }
        
        # In mock mode, include debug_consent_link and debug_raw_token so demo and tests function without real SMS gateway
        if getattr(settings, 'NOTIFICATION_PROVIDER_MODE', 'mock').lower() == 'mock':
            response_data['debug_consent_link'] = f"/api/v1/contacts/consent/{raw_token}/"
            response_data['debug_raw_token'] = raw_token

        return api_response(
            data=response_data,
            message="Consent request initiated."
        )

@extend_schema(summary="Public Consent Verification and Decision Endpoint")
class PublicContactConsentView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, token):
        info = get_consent_request_info(token)
        if not info:
            return api_response(
                data=None,
                message="Consent link is invalid or has expired.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        return api_response(
            data=info,
            message="Consent request details retrieved."
        )

    def post(self, request, token):
        serializer = ConsentDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        decision = serializer.validated_data['decision']

        success, msg, contact = process_consent_decision(token, decision)
        if not success:
            return api_response(
                data=None,
                message=msg,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        return api_response(
            data={'consent_status': contact.consent_status},
            message=msg
        )

@extend_schema(summary="Withdraw Contact Consent")
class ContactConsentWithdrawView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, contact_id):
        contact = get_contact_by_id(contact_id, request.user)
        if not contact:
            return api_response(
                data=None,
                message="Emergency contact not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        updated = withdraw_contact_consent(contact, request.user)
        return api_response(
            data=EmergencyContactSerializer(updated).data,
            message="Emergency contact consent withdrawn. Active notification chains cancelled."
        )
