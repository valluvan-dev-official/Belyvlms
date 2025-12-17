from django.db import models
from django.conf import settings

class Permission(models.Model):
    """
    Atomic permission definition.
    Example: code='USER_CREATE', name='Create User', module='User Management'
    """
    code = models.CharField(max_length=100, unique=True, help_text="Unique permission code (e.g., USER_CREATE)")
    name = models.CharField(max_length=255, help_text="Human-readable name")
    module = models.CharField(max_length=100, help_text="Logical grouping (e.g., User Management)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        ordering = ['module', 'code']


class Role(models.Model):
    """
    Role definition.
    Example: code='AD', name='Admin'
    """
    code = models.CharField(max_length=50, unique=True, help_text="Short role code (e.g., AD, TR)")
    name = models.CharField(max_length=255, unique=True, help_text="Human-readable role name")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        ordering = ['name']


class RolePermission(models.Model):
    """
    Many-to-Many link between Role and Permission.
    """
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='role_permissions')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name='role_permissions')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('role', 'permission')
        verbose_name = "Role Permission"
        verbose_name_plural = "Role Permissions"

    def __str__(self):
        return f"{self.role.code} -> {self.permission.code}"


class UserRole(models.Model):
    """
    Links a User to a Role.
    This allows RBAC to work without modifying the existing User model.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='rbac_role')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='users')
    assigned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.role.name}"
