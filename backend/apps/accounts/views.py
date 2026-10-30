from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.utils import extend_schema
from apps.common.responses import api_response
from apps.common.permissions import IsSupervisor
from .models import CustomUser
from .serializers import (
    UserRegisterSerializer,
    UserSummarySerializer,
    CustomTokenObtainPairSerializer,
)
from .services import register_user, set_responder_verification
from .selectors import list_unverified_responders

@extend_schema(summary="JWT Authentication: Obtain Token Pair")
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

@extend_schema(summary="JWT Authentication: Refresh Access Token")
class CustomTokenRefreshView(TokenRefreshView):
    pass

@extend_schema(summary="User Registration", description="Registers a new customer, public citizen, or pending responder.")
class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        serializer = UserRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return api_response(
            data=UserSummarySerializer(user).data,
            message="User registered successfully.",
            status_code=status.HTTP_201_CREATED
        )

@extend_schema(summary="Current User Profile", description="Returns authenticated user details and role status.")
class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        serializer = UserSummarySerializer(request.user)
        return api_response(data=serializer.data)

@extend_schema(summary="Verify Responder Status", description="Restricted to Supervisors and Administrators.")
class ResponderVerificationView(APIView):
    permission_classes = [IsAuthenticated, IsSupervisor]

    def post(self, request, user_id, *args, **kwargs):
        is_verified = request.data.get('is_verified', True)
        notes = request.data.get('notes', '')
        user = set_responder_verification(
            user_id=user_id,
            is_verified=bool(is_verified),
            verified_by=request.user,
            notes=notes
        )
        return api_response(
            data=UserSummarySerializer(user).data,
            message=f"Responder verification status updated to {is_verified}."
        )

@extend_schema(summary="List Unverified Responders", description="Lists responders pending verification.")
class UnverifiedRespondersListView(generics.ListAPIView):
    serializer_class = UserSummarySerializer
    permission_classes = [IsAuthenticated, IsSupervisor]

    def get_queryset(self):
        return list_unverified_responders()
