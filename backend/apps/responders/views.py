from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from apps.common.responses import api_response
from apps.common.permissions import IsAnyResponder
from .serializers import ResponderDispatchSerializer
from .selectors import list_dispatches_for_responder

@extend_schema(summary="Responder Active Dispatches")
class ResponderDispatchListView(APIView):
    permission_classes = [IsAuthenticated, IsAnyResponder]

    def get(self, request):
        dispatches = list_dispatches_for_responder(request.user)
        return api_response(data=ResponderDispatchSerializer(dispatches, many=True).data)
