from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema
from apps.common.responses import api_response
from apps.common.permissions import IsDispatchAssigneeOrOperator
from .models import DispatchStatus
from .serializers import ResponderDispatchSerializer
from .selectors import list_dispatches_for_responder, list_all_dispatches, get_dispatch_by_id
from .services import update_dispatch_status

@extend_schema(summary="Responder Active Dispatches")
class ResponderDispatchListView(APIView):
    """
    Lists dispatches:
    - Verified responders see only dispatches assigned directly to them.
    - Operators and supervisors see all dispatches for operational command.
    - Unverified responders and customers are rejected with HTTP 403 Forbidden.
    """
    permission_classes = [IsAuthenticated, IsDispatchAssigneeOrOperator]

    def get(self, request):
        if (
            request.user.role in ['OPERATOR', 'SUPERVISOR', 'ADMIN']
            or request.user.is_staff
            or request.user.is_superuser
        ):
            dispatches = list_all_dispatches()
        else:
            dispatches = list_dispatches_for_responder(request.user)
        return api_response(data=ResponderDispatchSerializer(dispatches, many=True).data)

@extend_schema(summary="Responder Dispatch Detail")
class ResponderDispatchDetailView(APIView):
    """
    Enforces object-level permissions on individual dispatch records:
    - Assigned verified responder or operator/supervisor can view or update.
    - Other responders receive HTTP 403 Forbidden.
    """
    permission_classes = [IsAuthenticated, IsDispatchAssigneeOrOperator]

    def get(self, request, dispatch_id):
        dispatch = get_dispatch_by_id(dispatch_id)
        if not dispatch:
            return api_response(
                data=None,
                message="Dispatch record not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        self.check_object_permissions(request, dispatch)
        return api_response(data=ResponderDispatchSerializer(dispatch).data)

    def patch(self, request, dispatch_id):
        dispatch = get_dispatch_by_id(dispatch_id)
        if not dispatch:
            return api_response(
                data=None,
                message="Dispatch record not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        self.check_object_permissions(request, dispatch)

        new_status = request.data.get('status')
        notes = request.data.get('notes')

        if not new_status and notes is None:
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'validation_error',
                        'message': 'No valid update fields provided.',
                        'details': None
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if new_status and new_status not in DispatchStatus.values:
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'validation_error',
                        'message': f"'{new_status}' is not a valid dispatch status.",
                        'details': {'status': [f"'{new_status}' is not a valid choice."]}
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            dispatch = update_dispatch_status(
                dispatch,
                new_status=new_status,
                notes=notes,
                actor=request.user
            )
        except ValidationError as exc:
            msg = str(exc.message if hasattr(exc, 'message') else exc)
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'invalid_transition',
                        'message': msg,
                        'details': {'status': [msg]}
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        return api_response(
            data=ResponderDispatchSerializer(dispatch).data,
            message="Dispatch updated successfully."
        )

