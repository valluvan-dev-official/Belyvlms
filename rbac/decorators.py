from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from .models import UserRole, RolePermission

def rbac_required(permission_code):
    """
    Decorator for Function-Based Views (Django Templates).
    Checks if the user has the required RBAC permission.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')

            # Superuser bypass
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Check Permission
            has_permission = False
            try:
                # 1. Get User's Role
                user_role = UserRole.objects.select_related('role').get(user=request.user)
                
                # 2. Check if Role has the specific Permission
                has_permission = RolePermission.objects.filter(
                    role=user_role.role, 
                    permission__code=permission_code
                ).exists()

            except UserRole.DoesNotExist:
                has_permission = False

            if not has_permission:
                # Option A: Raise 403 (Best for APIs)
                # raise PermissionDenied 
                
                # Option B: Redirect with Message (Best for UI)
                messages.error(request, "You do not have permission to access this page.")
                return redirect(request.META.get('HTTP_REFERER', 'home'))

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
