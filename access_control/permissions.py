from rest_framework import permissions
from functools import wraps
from django.core.exceptions import PermissionDenied
from .services import check_permission

class HasPermission(permissions.BasePermission):
    """
    DRF Permission class to check for a specific permission code.
    Usage:
    permission_classes = [HasPermission('course_create')]
    OR
    permission_classes = [HasPermission]
    def get_permissions(self): ...
    """
    def __init__(self, permission_code=None):
        self.permission_code = permission_code

    def __call__(self):
        return self

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
            
        # If used as a factory: HasPermission('code')
        if self.permission_code:
            return check_permission(request.user, self.permission_code)
            
        # If used as a class: [HasPermission]
        # Look for 'required_permission' attribute on the view
        required_perm = getattr(view, 'required_permission', None)
        if required_perm:
            return check_permission(request.user, required_perm)
            
        return True # Fallback if no code specified (or assume strict?)

def permission_required(permission_code):
    """
    Decorator for function-based views.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied
            
            if not check_permission(request.user, permission_code):
                raise PermissionDenied
                
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
