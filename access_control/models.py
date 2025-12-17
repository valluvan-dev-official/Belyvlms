from django.db import models
from django.conf import settings
from django.utils.text import slugify
from accounts.models import CustomUser

class EnterpriseUser(CustomUser):
    class Meta:
        proxy = True
        verbose_name = 'Enterprise User'
        verbose_name_plural = 'Enterprise Users'

class Module(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Permission(models.Model):
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('view', 'View'),
        ('edit', 'Edit'),
        ('delete', 'Delete'),
        ('approve', 'Approve'),
        ('export', 'Export'),
        ('all', 'All Actions'),
    ]

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=100, unique=True, help_text="Unique code like course_create, batch_delete")
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='permissions', null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=10, unique=True, help_text="Unique code like AD, TR, ST")
    is_active = models.BooleanField(default=True)
    is_system_role = models.BooleanField(default=False, help_text="If True, this is a special system role like Super Admin")
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.code = self.code.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.code})"

class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='permissions')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name='roles')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('role', 'permission')

    def __str__(self):
        return f"{self.role.code} -> {self.permission.code}"

class UserRole(models.Model):
    """
    Manages additional roles assigned to a user.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='additional_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='assigned_users')
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='role_assignments')

    class Meta:
        unique_together = ('user', 'role')

    def __str__(self):
        return f"{self.user} - {self.role}"

class UserPermissionOverride(models.Model):
    """
    Explicitly Allow or Deny a permission for a specific user.
    DENY overrides ALLOW.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='permission_overrides')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    is_granted = models.BooleanField(default=True, help_text="True = Explicit Allow, False = Explicit Deny")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    granted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='permission_grants')

    class Meta:
        unique_together = ('user', 'permission')

    def __str__(self):
        status = "ALLOW" if self.is_granted else "DENY"
        return f"{self.user} - {self.permission.code} ({status})"

class UserProfile(models.Model):
    """
    Links User to their PRIMARY Role and stores metadata.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='access_profile')
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name='primary_users')
    role_based_id = models.CharField(max_length=20, unique=True, help_text="Auto-generated ID like TR001")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.role.code} ({self.role_based_id})"

class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('ROLE_CREATE', 'Role Created'),
        ('ROLE_UPDATE', 'Role Updated'),
        ('PERM_ASSIGN', 'Permission Assigned'),
        ('USER_ROLE_ADD', 'User Role Added'),
        ('USER_OVERRIDE', 'User Permission Override'),
    ]
    
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    target = models.CharField(max_length=255)
    details = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.timestamp} - {self.action} by {self.actor}"
