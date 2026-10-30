from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from apps.common.permissions import IsSupervisor
from .models import AuditEvent
from .serializers import AuditEventSerializer
from .selectors import list_audit_events

@extend_schema(
    summary="List Audit Events",
    description="Lists system audit events. Restricted to Supervisors and Administrators."
)
class AuditEventListView(generics.ListAPIView):
    serializer_class = AuditEventSerializer
    permission_classes = [IsAuthenticated, IsSupervisor]

    def get_queryset(self):
        return list_audit_events()
