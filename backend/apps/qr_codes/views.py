from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_spectacular.utils import extend_schema
from apps.common.responses import api_response
from apps.common.exceptions import custom_exception_handler
from .models import QRCodeBadge
from .serializers import QRCodeBadgeSerializer
from .services import create_qr_badge
from .selectors import list_user_badges, get_badge_by_code

@extend_schema(summary="List/Create Safe-QR Badges")
class UserQRCodeBadgesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        badges = list_user_badges(request.user)
        return api_response(data=QRCodeBadgeSerializer(badges, many=True).data)

    def post(self, request):
        badge = create_qr_badge(
            user=request.user,
            vehicle_registration=request.data.get('vehicle_registration', ''),
            vehicle_model=request.data.get('vehicle_model', '')
        )
        return api_response(
            data=QRCodeBadgeSerializer(badge).data,
            message="Safe-QR badge registered successfully.",
            status_code=status.HTTP_201_CREATED
        )

@extend_schema(summary="Public QR Code Resolver", description="Verifies badge status when public scans physical QR badge.")
class QRCodePublicResolveView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, code_identifier):
        badge = get_badge_by_code(code_identifier)
        if not badge:
            return api_response(
                data=None,
                message="Safe-QR badge not found or invalid.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        return api_response(
            data={
                'code_identifier': badge.code_identifier,
                'status': badge.status,
                'vehicle_model': badge.vehicle_model,
                'is_active': badge.status == 'ACTIVE'
            },
            message="Safe-QR badge verified."
        )
