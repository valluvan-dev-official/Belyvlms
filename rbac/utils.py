from .models import UserRole, RolePermission, Permission
from django.core.cache import cache

def get_user_permissions(user, active_role_code=None):
    """
    Fetches all permission codes for a given user based on their assigned Role.
    Supports Multi-Role Context:
    - If active_role_code is provided, checks permissions for THAT role.
    - If active_role_code is None, defaults to the FIRST assigned role (Compatibility).
    """
    if not user.is_authenticated:
        return []

    # 1. Superuser Bypass (God Mode)
    if user.is_superuser:
        # Cache key for superuser (global)
        su_cache_key = "rbac_perms_superuser"
        cached_su = cache.get(su_cache_key)
        if cached_su:
            return cached_su
            
        all_perms = list(Permission.objects.values_list('code', flat=True))
        cache.set(su_cache_key, all_perms, 60 * 60)
        return all_perms

    # 2. Fetch User's Role (Multi-Role Logic)
    # We don't cache the "User -> Role" mapping here to ensure instant revocation if user is removed from role.
    # The DB query is fast (indexed).
    try:
        if active_role_code:
            # Specific Role Context
            user_role = UserRole.objects.select_related('role').get(user=user, role__code=active_role_code)
        else:
            # Default Role (First one)
            user_role = UserRole.objects.select_related('role').filter(user=user).first()
            
        if not user_role:
            return []
            
        role = user_role.role
    except UserRole.DoesNotExist:
        return []

    if not getattr(role, "is_active", True):
        return []

    # 3. Fetch Permissions for that Role (Cached by Role)
    # This ensures that if we update Role permissions, ALL users get updated immediately (after cache clear).
    role_cache_key = f"rbac_role_perms_{role.code}"
    cached_role_perms = cache.get(role_cache_key)
    
    if cached_role_perms is not None:
        return cached_role_perms

    permission_codes = RolePermission.objects.filter(role=role).values_list('permission__code', flat=True)
    
    perms_list = list(permission_codes)
    cache.set(role_cache_key, perms_list, 60 * 60 * 24) # Cache for 24 hours

    return perms_list

def has_permission(user, permission_code, active_role_code=None):
    """
    Utility to check if a user has a specific permission.
    """
    if user.is_superuser:
        return True

    perms = get_user_permissions(user, active_role_code)
    return permission_code in perms
