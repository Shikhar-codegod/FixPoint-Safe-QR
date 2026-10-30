from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from apps.common.permissions import IsOperator
from .serializers import OperationsLogEntrySerializer
from .selectors import list_ops_log

@extend_schema(
    summary="Command Operations Log",
    description="Lists command operations log entries. Restricted to Operators, Supervisors, and Administrators."
)
class OperationsLogView(generics.ListAPIView):
    serializer_class = OperationsLogEntrySerializer
    permission_classes = [IsAuthenticated, IsOperator]

    def get_queryset(self):
        return list_ops_log()
