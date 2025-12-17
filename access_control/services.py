from django.core.cache import cache
from django.conf import settings
from django.db import transaction
from django.utils.crypto import get_random_string
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from .models import Role, Permission, RolePermission, UserRole, UserPermissionOverride, UserProfile, AuditLog
from .utils import generate_role_based_id

User = get_user_model()

CACHE_TIMEOUT = 60 * 60 * 24  # 24 Hours
CACHE_KEY_PREFIX = "rbac_perms_"

def get_cache_key(user_id):
    return f"{CACHE_KEY_PREFIX}{user_id}"

def get_user_permissions(user):
    """
    Calculates the final list of permission codes for a user.
    Priorities:
    1. Superuser / System Admin Role -> ALL Permissions
    2. Union of Primary Role + Additional Roles
    3. User Overrides (Allow adds, Deny removes)
    """
    if not user.is_authenticated:
        return []

    cache_key = get_cache_key(user.id)
    cached_perms = cache.get(cache_key)

    if cached_perms is not None:
        return cached_perms

    # 1. Superuser Check
    if user.is_superuser:
        return _get_all_permissions_wildcard()

    # 2. System Role Check (e.g. Super Admin role assigned via RBAC)
    # Check primary role
    primary_role_code = getattr(user, 'role', None)
    
    # We need to find if this user has any role that is_system_role=True
    # Check primary role object
    has_system_role = False
    
    # Try to find primary role in DB
    if primary_role_code:
        # We assume the string in user.role matches Role.name or Role.code? 
        # Previous context suggests user.role is a string like 'admin', 'trainer'.
        # Let's match case-insensitive against Role.name or Role.code
        try:
            # Try matching name first as per previous serializer logic
            primary_role_obj = Role.objects.filter(name__iexact=primary_role_code).first()
            if not primary_role_obj:
                 primary_role_obj = Role.objects.filter(code__iexact=primary_role_code).first()
            
            if primary_role_obj and primary_role_obj.is_system_role:
                has_system_role = True
        except Exception:
            pass

    if not has_system_role:
        # Check additional roles
        if UserRole.objects.filter(user=user, role__is_system_role=True).exists():
            has_system_role = True

    if has_system_role:
        all_perms = _get_all_permissions_wildcard()
        cache.set(cache_key, all_perms, CACHE_TIMEOUT)
        return all_perms

    # 3. Calculate Permissions
    permissions = set()

    # A. Primary Role Permissions
    if primary_role_code:
         # Re-fetch primary role obj if needed
         primary_role_obj = Role.objects.filter(name__iexact=primary_role_code).first()
         if not primary_role_obj:
             primary_role_obj = Role.objects.filter(code__iexact=primary_role_code).first()
         
         if primary_role_obj and primary_role_obj.is_active:
             role_perms = RolePermission.objects.filter(role=primary_role_obj).values_list('permission__code', flat=True)
             permissions.update(role_perms)

    # B. Additional Roles Permissions
    additional_role_perms = RolePermission.objects.filter(
        role__assigned_users__user=user,
        role__is_active=True
    ).values_list('permission__code', flat=True)
    permissions.update(additional_role_perms)

    # C. User Overrides
    overrides = UserPermissionOverride.objects.filter(user=user).select_related('permission')
    
    allowed_codes = {o.permission.code for o in overrides if o.is_granted}
    denied_codes = {o.permission.code for o in overrides if not o.is_granted}

    # Apply Allow (Union)
    permissions.update(allowed_codes)
    
    # Apply Deny (Difference)
    permissions = permissions - denied_codes

    final_perms = list(permissions)
    cache.set(cache_key, final_perms, CACHE_TIMEOUT)
    return final_perms

def _get_all_permissions_wildcard():
    # We can return ['*'] if the frontend supports it, 
    # but the requirement says "final permission codes list".
    # Returning all actual codes is safer for explicit checks.
    return list(Permission.objects.values_list('code', flat=True))

def invalidate_user_cache(user):
    cache.delete(get_cache_key(user.id))

def invalidate_role_cache(role):
    # Invalidate all users with this role
    # 1. Primary role users
    # We rely on the user.role string matching role.name or role.code
    # This is expensive if we scan all users.
    # Strategy: Just clear all RBAC caches or use a versioning scheme?
    # For now, let's try to find users.
    
    # Users with this as primary role (via UserProfile)
    users_with_profile = UserProfile.objects.filter(role=role).values_list('user_id', flat=True)
    for uid in users_with_profile:
        cache.delete(get_cache_key(uid))
        
    # Users with this as additional role
    users_additional = UserRole.objects.filter(role=role).values_list('user_id', flat=True)
    for uid in users_additional:
        cache.delete(get_cache_key(uid))

    # Also users where user.role string matches role.name (legacy support)
    # This might be too heavy. 
    # Optimization: We assume most users have UserProfile if they are using RBAC.
    pass

def check_permission(user, permission_code):
    """
    Reusable function to check a single permission.
    """
    perms = get_user_permissions(user)
    return permission_code in perms

def create_enterprise_user(name, email, primary_role_id, extra_role_ids=None, overrides=None, actor=None):
    """
    Creates a new user with full enterprise RBAC configuration.
    
    Args:
        name (str): Full name
        email (str): Email address
        primary_role_id (int): ID of the Role object
        extra_role_ids (list[int]): Optional list of Role IDs
        overrides (list[dict]): Optional list of {permission_id, is_granted}
        actor (User): The admin creating this user (for audit log)
        
    Returns:
        User: The created user instance (with .generated_password attached)
    """
    with transaction.atomic():
        # 1. Validation & Setup
        primary_role = get_object_or_404(Role, id=primary_role_id)
        if not primary_role.is_active:
             raise ValueError(f"Role {primary_role.name} is not active.")
             
        password = get_random_string(12)
        role_based_id = generate_role_based_id(primary_role.code)
        
        # 2. Create Core User
        # Using create_user handles password hashing
        user = User.objects.create_user(
            email=email,
            name=name,
            password=password,
            role=primary_role.name.lower() # Sync for backward compat
        )
        
        # 3. Create Profile
        UserProfile.objects.create(
            user=user,
            role=primary_role,
            role_based_id=role_based_id
        )
        
        # 4. Sync Primary Role to UserRole
        UserRole.objects.create(
            user=user,
            role=primary_role,
            assigned_by=actor
        )
        
        # 5. Add Extra Roles
        if extra_role_ids:
            # Deduplicate and remove primary role if present
            extra_role_ids = set(extra_role_ids)
            if primary_role.id in extra_role_ids:
                extra_role_ids.remove(primary_role.id)
                
            for rid in extra_role_ids:
                r = get_object_or_404(Role, id=rid)
                UserRole.objects.create(
                    user=user,
                    role=r,
                    assigned_by=actor
                )
        
        # 6. Apply Overrides
        if overrides:
            for ov in overrides:
                pid = ov.get('permission_id')
                # Default to True (Allow) if not specified, though explicit is better
                is_granted = ov.get('is_granted', True) 
                
                perm = get_object_or_404(Permission, id=pid)
                
                UserPermissionOverride.objects.create(
                    user=user,
                    permission=perm,
                    is_granted=is_granted,
                    granted_by=actor
                )
                
        # 7. Audit Log
        if actor:
            AuditLog.objects.create(
                actor=actor,
                action='USER_CREATE',
                target=email,
                details={
                    'user_id': user.id,
                    'role_based_id': role_based_id,
                    'primary_role': primary_role.code,
                    'extra_roles': list(extra_role_ids) if extra_role_ids else [],
                    'overrides_count': len(overrides) if overrides else 0
                }
            )
            
        # Attach password to user object for one-time return
        user.generated_password = password
        user.role_based_id = role_based_id
        
        return user
