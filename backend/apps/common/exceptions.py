import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import APIException

logger = logging.getLogger('apps.common')

def custom_exception_handler(exc, context):
    """
    Standardized API exception handler across the entire FixPoint backend.
    Produces a uniform error schema:
    {
        "success": false,
        "error": {
            "code": "<string_code>",
            "message": "<human_readable_message>",
            "details": <dict_or_list_or_null>
        }
    }
    """
    # Call REST framework's default exception handler first to get the standard response
    response = exception_handler(exc, context)

    view = context.get('view')
    view_name = view.__class__.__name__ if view else 'UnknownView'

    if response is not None:
        status_code = response.status_code
        error_code = 'error'

        if status_code == status.HTTP_400_BAD_REQUEST:
            error_code = 'validation_error'
            message = 'Invalid request payload or query parameters.'
        elif status_code == status.HTTP_401_UNAUTHORIZED:
            error_code = 'authentication_failed'
            message = 'Authentication credentials were not provided or are invalid.'
        elif status_code == status.HTTP_403_FORBIDDEN:
            error_code = 'permission_denied'
            message = 'You do not have permission to perform this action.'
        elif status_code == status.HTTP_404_NOT_FOUND:
            error_code = 'not_found'
            message = 'The requested resource was not found.'
        elif status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
            error_code = 'method_not_allowed'
            message = 'Method not allowed for this endpoint.'
        elif status_code >= 500:
            error_code = 'server_error'
            message = 'An unexpected internal server error occurred.'
        else:
            message = 'An error occurred processing the request.'

        custom_data = {
            'success': False,
            'error': {
                'code': error_code,
                'message': message,
                'details': response.data
            }
        }
        response.data = custom_data
        return response

    # Unhandled 500 exception
    logger.exception(f"Unhandled exception in {view_name}: {exc}")
    return Response(
        {
            'success': False,
            'error': {
                'code': 'internal_server_error',
                'message': 'An unexpected error occurred. Please contact system support.',
                'details': None
            }
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
