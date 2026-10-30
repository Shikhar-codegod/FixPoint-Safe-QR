from rest_framework.response import Response
from rest_framework import status

def api_response(data=None, message="Success", status_code=status.HTTP_200_OK, meta=None):
    """
    Standard envelope for all successful API responses.
    """
    payload = {
        'success': True,
        'message': message,
        'data': data
    }
    if meta is not None:
        payload['meta'] = meta
    return Response(payload, status=status_code)
