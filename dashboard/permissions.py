from rest_framework import permissions
from rbac.utils import has_permission, get_user_permissions

class DashboardRoleRequired(permissions.BasePermission):
    """
    Custom Permission class that validates the 'X-Active-Role' header
    against the user's assigned roles in RBAC.
    
    Ensures that the user is actually authorized to act as the role
    they are claiming in the dashboard header.
    """
    
    def has_permission(self, request, view):
        # 1. Authentication Check
        if not request.user or not request.user.is_authenticated:
            return False
            
        # 2. Superuser Bypass
        if request.user.is_superuser:
            return True
            
        # 3. Validate Header
        active_role_code = request.headers.get('X-Active-Role')
        if not active_role_code:
            # If header is missing, we deny access because the dashboard
            # requires a specific role context to render.
            return False
            
        # 4. Check if User actually HAS this role
        # We can use get_user_permissions logic or check UserRole directly.
        # Ideally, we should check if the user has the role assigned.
        from rbac.models import UserRole
        
        has_role = UserRole.objects.filter(
            user=request.user, 
            role__code=active_role_code,
            role__is_active=True
        ).exists()
        
        return has_role
