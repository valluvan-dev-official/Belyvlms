from django.core.cache import cache
from .models import UserRole, RolePermission

def get_user_permissions(user):
    """
    Fetches all permission codes for a given user based on their assigned Role.
    
    Args:
        user: The user instance (authenticated).
        
    Returns:
        List[str]: A list of permission codes (e.g., ['USER_CREATE', 'BATCH_VIEW']).
    """
    if not user.is_authenticated:
        return []

    # Cache key structure: rbac_perms_<user_id>
    cache_key = f"rbac_perms_{user.id}"
    cached_perms = cache.get(cache_key)

    if cached_perms is not None:
        return cached_perms

    # 1. Fetch User's Role (Optimized)
    try:
        user_role = UserRole.objects.select_related('role').get(user=user)
        role = user_role.role
    except UserRole.DoesNotExist:
        return []

    # 2. Fetch Permissions for that Role (Optimized)
    # values_list avoids fetching full Permission objects, just the codes
    permission_codes = RolePermission.objects.filter(role=role).values_list('permission__code', flat=True)
    
    # Convert to list for serialization/caching
    perms_list = list(permission_codes)

    # Cache for 1 hour (adjustable)
    cache.set(cache_key, perms_list, 60 * 60)

    return perms_list

def has_permission(user, permission_code):
    """
    Utility to check if a user has a specific permission.
    """
    if user.is_superuser:
        return True

    perms = get_user_permissions(user)
    return permission_code in perms
