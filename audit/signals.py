from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.db.models.signals import post_save, post_delete, pre_delete
from django.conf import settings
from .utils import log_event


@receiver(user_logged_in)
def on_user_login(sender, user, request, **kwargs):
    role = getattr(user, "last_active_role", None)
    log_event(user.id, role, "LOGIN", "Auth", user.id, None, None, "UI", request)


@receiver(user_logged_out)
def on_user_logout(sender, request, user, **kwargs):
    role = getattr(user, "last_active_role", None)
    actor_id = getattr(user, "id", None)
    log_event(actor_id, role, "LOGOUT", "Auth", actor_id, None, None, "UI", request)


@receiver(user_login_failed)
def on_user_login_failed(sender, credentials, request, **kwargs):
    uid = credentials.get("username") if isinstance(credentials, dict) else None
    log_event(None, None, "FAILED_LOGIN", "Auth", uid, None, None, "UI", request)


def _try_import(path):
    try:
        module_path, name = path.rsplit(".", 1)
        mod = __import__(module_path, fromlist=[name])
        return getattr(mod, name)
    except Exception:
        return None


UserRole = _try_import("rbac.models.UserRole")
RolePermission = _try_import("rbac.models.RolePermission")
Permission = _try_import("rbac.models.Permission")
CustomUser = _try_import("accounts.models.CustomUser")
RoleProfileConfig = _try_import("profiles.models.RoleProfileConfig")


if UserRole:
    @receiver(post_save, sender=UserRole)
    def on_role_assign(sender, instance, created, **kwargs):
        if created:
            log_event(instance.user_id, instance.role.code, "ROLE_ASSIGN", "Role", instance.role_id, None, {"role": instance.role.code}, "SYSTEM", None)

    @receiver(post_delete, sender=UserRole)
    def on_role_remove(sender, instance, **kwargs):
        log_event(instance.user_id, instance.role.code, "ROLE_REMOVE", "Role", instance.role_id, {"role": instance.role.code}, None, "SYSTEM", None)


if RolePermission and Permission:
    @receiver(post_save, sender=RolePermission)
    def on_permission_grant(sender, instance, created, **kwargs):
        if created:
            code = getattr(instance.permission, "code", None)
            log_event(None, instance.role.code, "PERMISSION_GRANT", "Permission", instance.permission_id, None, {"role": instance.role.code, "permission": code}, "SYSTEM", None)

    @receiver(post_delete, sender=RolePermission)
    def on_permission_revoke(sender, instance, **kwargs):
        code = getattr(instance.permission, "code", None)
        log_event(None, instance.role.code, "PERMISSION_REVOKE", "Permission", instance.permission_id, {"role": instance.role.code, "permission": code}, None, "SYSTEM", None)


if CustomUser:
    @receiver(post_save, sender=CustomUser)
    def on_user_save(sender, instance, created, **kwargs):
        if created:
            log_event(instance.id, None, "CREATE", "User", instance.id, None, {"email": instance.email}, "SYSTEM", None)
        else:
            log_event(instance.id, None, "UPDATE", "User", instance.id, None, {"email": instance.email}, "SYSTEM", None)

    @receiver(pre_delete, sender=CustomUser)
    def on_user_delete(sender, instance, **kwargs):
        log_event(instance.id, None, "DELETE", "User", instance.id, {"email": instance.email}, None, "SYSTEM", None)


if RoleProfileConfig:
    @receiver(post_save, sender=RoleProfileConfig)
    def on_profile_config_change(sender, instance, created, **kwargs):
        action = "CREATE" if created else "UPDATE"
        log_event(None, None, action, "Config", instance.id, None, {"role": instance.role.code if instance.role else None}, "SYSTEM", None)
