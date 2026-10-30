from rest_framework.permissions import BasePermission

class IsAuthenticatedUser(BasePermission):
    """
    Allows access only to authenticated users.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

class IsCustomer(BasePermission):
    """
    Allows access to users with the CUSTOMER role.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == 'CUSTOMER'
        )

class IsPublicUser(BasePermission):
    """
    Allows access to users with the PUBLIC role.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == 'PUBLIC'
        )

class IsPoliceResponder(BasePermission):
    """
    Allows access to police responders.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == 'POLICE_RESPONDER'
        )

class IsMedicalResponder(BasePermission):
    """
    Allows access to medical responders.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == 'MEDICAL_RESPONDER'
        )

class IsAnyResponder(BasePermission):
    """
    Allows access to any responder role (police or medical).
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role in ['POLICE_RESPONDER', 'MEDICAL_RESPONDER']
        )

class IsVerifiedResponder(BasePermission):
    """
    Requires the user to be a responder AND have their verified responder status approved.
    Note: Selecting a responder role does NOT automatically verify the responder.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role in ['POLICE_RESPONDER', 'MEDICAL_RESPONDER'] and
            getattr(request.user, 'is_verified_responder', False)
        )

class IsOperator(BasePermission):
    """
    Allows access to operational command desk staff.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role in ['OPERATOR', 'SUPERVISOR', 'ADMIN']
        )

class IsSupervisor(BasePermission):
    """
    Allows access to supervisor level and administrators.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role in ['SUPERVISOR', 'ADMIN']
        )

class IsAdminRole(BasePermission):
    """
    Allows access only to users with the ADMIN role or superuser status.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role == 'ADMIN' or request.user.is_staff or request.user.is_superuser)
        )
