import logging
from django.db import connection
from django.core.cache import cache
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse

logger = logging.getLogger('apps.common')

def api_root(request):
    return JsonResponse({
        'name': 'FixPoint Drive Safe-QR SOS API',
        'health': '/api/v1/health/',
        'docs': '/api/v1/docs/',
    })

class HealthCheckView(APIView):
    """
    Production health-check endpoint.
    Verifies application liveness and database/cache connectivity without exposing internal topology.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        summary="Service Health Check",
        description="Verifies API availability and core service connectivity.",
        responses={
            200: OpenApiResponse(description="All services operational"),
            503: OpenApiResponse(description="One or more critical services unavailable"),
        }
    )
    def get(self, request, *args, **kwargs):
        services = {}
        all_healthy = True

        # Database connectivity check
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1;")
                row = cursor.fetchone()
                if row and row[0] == 1:
                    services['database'] = 'operational'
                else:
                    services['database'] = 'degraded'
                    all_healthy = False
        except Exception as exc:
            logger.error(f"Health check database failure: {exc}")
            services['database'] = 'unavailable'
            all_healthy = False

        # Cache connectivity check
        try:
            cache.set('_health_test', 1, timeout=5)
            val = cache.get('_health_test')
            services['cache'] = 'operational' if val == 1 else 'degraded'
        except Exception as exc:
            logger.warning(f"Health check cache degraded: {exc}")
            services['cache'] = 'degraded'

        overall_status = 'healthy' if all_healthy else 'unhealthy'
        http_status = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

        return Response(
            {
                'status': overall_status,
                'version': '1.0.0',
                'services': services
            },
            status=http_status
        )
