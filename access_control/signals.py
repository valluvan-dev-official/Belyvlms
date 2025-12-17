from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import RolePermission, UserRole, UserPermissionOverride, UserProfile, Role
from .services import invalidate_user_cache, invalidate_role_cache

User = get_user_model()

@receiver([post_save, post_delete], sender=UserPermissionOverride)
def permission_override_changed(sender, instance, **kwargs):
    invalidate_user_cache(instance.user)

@receiver([post_save, post_delete], sender=UserRole)
def user_role_changed(sender, instance, **kwargs):
    invalidate_user_cache(instance.user)

@receiver([post_save, post_delete], sender=RolePermission)
def role_permission_changed(sender, instance, **kwargs):
    invalidate_role_cache(instance.role)

@receiver([post_save, post_delete], sender=UserProfile)
def user_profile_changed(sender, instance, **kwargs):
    invalidate_user_cache(instance.user)

# If we want to catch changes to the 'role' field on User model:
@receiver(post_save, sender=User)
def user_model_changed(sender, instance, **kwargs):
    # This might fire too often, but necessary if 'role' field changes
    # Optimization: Check if 'role' field actually changed using pre_save or tracking
    invalidate_user_cache(instance)
