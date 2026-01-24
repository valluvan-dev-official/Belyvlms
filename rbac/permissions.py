from rest_framework import permissions
from .utils import has_permission

class HasRBACPermission(permissions.BasePermission):
    """
    Custom DRF Permission class that checks for RBAC permissions.
    
    Usage in View:
    class MyView(APIView):
        permission_classes = [HasRBACPermission]
        required_permission = 'USER_CREATE'
        
        def post(self, request):
            ...
    """

    def has_permission(self, request, view):
        # 1. Ensure user is authenticated first
        if not request.user or not request.user.is_authenticated:
            return False

        # 2. Superuser Bypass (God Mode)
        # In Enterprise systems, the "root" or "superuser" typically has implied full access.
        # This prevents lockout scenarios where no role has permission to assign permissions.
        if request.user.is_superuser:
            return True

        # 3. Check if the view has a 'required_permission' attribute
        required_perm = getattr(view, 'required_permission', None)
        
        if not required_perm:
            # If no permission is strictly required by the view, 
            # we default to True (allow access) or False (deny).
            # Usually, if this class is added, a permission SHOULD be specified.
            # We'll allow it but log a warning in a real system.
            return True

        # 3. Check against RBAC engine
        # Extract active role from request header if present
        active_role = request.headers.get('X-Active-Role', None)
        
        return has_permission(request.user, required_perm, active_role_code=active_role)
