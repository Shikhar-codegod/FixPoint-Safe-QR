from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema
from apps.common.permissions import IsOperator
from apps.common.responses import api_response
from apps.alerts.selectors import list_operator_alert_queue, get_alert_by_id
from apps.alerts.serializers import AlertDetailSerializer
from apps.alerts.services import claim_alert
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


@extend_schema(summary="Operations Active Alert Queue")
class OperationsAlertQueueView(APIView):
    """
    Queue of confirmed and active emergency alerts for command desk triage.
    """
    permission_classes = [IsAuthenticated, IsOperator]

    def get(self, request):
        status_param = request.query_params.get('status')
        severity_param = request.query_params.get('severity')
        alerts = list_operator_alert_queue()
        if status_param:
            alerts = alerts.filter(status=status_param)
        if severity_param:
            alerts = alerts.filter(severity=severity_param)
        return api_response(data=AlertDetailSerializer(alerts, many=True).data)


@extend_schema(summary="Claim Emergency Alert")
class OperationsAlertClaimView(APIView):
    """
    Allows an operator to claim a CONFIRMED alert, transitioning it to ACTIVE.
    """
    permission_classes = [IsAuthenticated, IsOperator]

    def post(self, request, alert_id):
        alert = get_alert_by_id(alert_id)
        if not alert:
            return api_response(
                data=None,
                message="Emergency alert not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        try:
            claimed = claim_alert(alert_id=alert_id, operator=request.user)
        except ValidationError as exc:
            msg = str(exc.message if hasattr(exc, 'message') else exc)
            if 'already been claimed' in msg.lower():
                return Response(
                    {
                        'success': False,
                        'error': {
                            'code': 'already_claimed',
                            'message': msg,
                            'details': None
                        }
                    },
                    status=status.HTTP_409_CONFLICT
                )
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'claim_error',
                        'message': msg,
                        'details': None
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return api_response(
            data=AlertDetailSerializer(claimed).data,
            message="Alert claimed successfully."
        )


@extend_schema(summary="Add Operational Notes to Alert")
class OperationsAlertNotesView(APIView):
    """
    Allows operators to append internal notes to an emergency alert.
    """
    permission_classes = [IsAuthenticated, IsOperator]

    def post(self, request, alert_id):
        alert = get_alert_by_id(alert_id)
        if not alert:
            return api_response(
                data=None,
                message="Emergency alert not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        new_note = request.data.get('notes', '').strip()
        if not new_note:
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'validation_error',
                        'message': 'Notes content cannot be empty.',
                        'details': {'notes': ['This field is required.']}
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        operator_info = getattr(request.user, 'email', str(request.user))
        alert.notes = (alert.notes + f"\n[Ops Note by {operator_info}]: {new_note}").strip()
        alert.save(update_fields=['notes', 'updated_at'])
        from apps.audit.services import log_audit_event
        log_audit_event(
            action='ALERT_NOTE_ADDED',
            actor=request.user,
            target_model='AlertRecord',
            target_id=str(alert.id),
            payload={'operator': operator_info}
        )
        return api_response(
            data=AlertDetailSerializer(alert).data,
            message="Operational note added successfully."
        )
