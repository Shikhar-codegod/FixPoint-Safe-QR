from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from apps.common.responses import api_response
from apps.common.permissions import IsAnyResponder
from .serializers import UserProfileSerializer, ResponderProfileSerializer
from .services import get_or_create_user_profile, update_user_profile, get_or_create_responder_profile, update_responder_profile

@extend_schema(summary="Get/Update User Profile")
class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = get_or_create_user_profile(request.user)
        return api_response(data=UserProfileSerializer(profile).data)

    def patch(self, request):
        profile = update_user_profile(request.user, **request.data)
        return api_response(data=UserProfileSerializer(profile).data, message="Profile updated successfully.")

@extend_schema(summary="Get/Update Responder Profile")
class ResponderProfileView(APIView):
    permission_classes = [IsAuthenticated, IsAnyResponder]

    def get(self, request):
        profile = get_or_create_responder_profile(request.user)
        return api_response(data=ResponderProfileSerializer(profile).data)

    def patch(self, request):
        profile = update_responder_profile(request.user, **request.data)
        return api_response(data=ResponderProfileSerializer(profile).data, message="Responder profile updated.")
