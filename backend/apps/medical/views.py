from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from apps.common.responses import api_response
from .serializers import MedicalProfileSerializer
from .services import get_or_create_medical_profile, update_medical_profile

@extend_schema(summary="Get or Update Encrypted Medical Profile")
class MedicalProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = get_or_create_medical_profile(request.user)
        return api_response(data=MedicalProfileSerializer(profile).data)

    def patch(self, request):
        profile = update_medical_profile(request.user, **request.data)
        return api_response(
            data=MedicalProfileSerializer(profile).data,
            message="Medical profile updated successfully."
        )
