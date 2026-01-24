from django.db import models
from django.conf import settings
import uuid

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
    code = models.CharField(max_length=50, unique=True, help_text="Short role code (e.g., AD, TR). Immutable.")
    name = models.CharField(max_length=255, unique=True, help_text="Human-readable role name")
    is_active = models.BooleanField(default=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='deleted_roles')
    deletion_reason = models.CharField(max_length=255, null=True, blank=True)
    
    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_roles', help_text="User who created this role")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='updated_roles', help_text="User who last updated this role")

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        ordering = ['name']


class RoleSequence(models.Model):
    """
    Centralized Sequence Manager for Role-based IDs.
    Ensures atomic, gap-free, and thread-safe ID generation.
    """
    role = models.OneToOneField(Role, on_delete=models.CASCADE, related_name='sequence')
    current_sequence = models.PositiveIntegerField(default=0, help_text="The last used number")
    prefix_override = models.CharField(max_length=10, null=True, blank=True, help_text="Optional override for the default role code prefix")
    
    # Audit Fields
    last_updated_at = models.DateTimeField(auto_now=True)
    last_updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, help_text="User who triggered the last ID generation")

    def __str__(self):
        return f"{self.role.code} Sequence: {self.current_sequence}"



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
    Changed from OneToOneField to ForeignKey to support Multiple Roles per User.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='rbac_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='users')
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'role')  # Ensure user can't have same role twice

    def __str__(self):
        return f"{self.user} - {self.role.name}"


class OnboardRequest(models.Model):
    STATUS_CHOICES = [
        ('INVITED', 'Invited'),
        ('PENDING_APPROVAL', 'Pending Approval'),
        ('ONBOARDED', 'Onboarded'),
        ('DROPPED', 'Dropped'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    code = models.CharField(max_length=20, unique=True, blank=True)

    email = models.EmailField()
    role = models.ForeignKey('rbac.Role', on_delete=models.PROTECT, related_name='onboard_requests')

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='INVITED')

    user_payload = models.JSONField(default=dict, blank=True)
    admin_payload = models.JSONField(default=dict, blank=True)

    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='onboard_requests_initiated',
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='onboard_requests_approved',
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    provisioned_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='onboard_requests_provisioned_user',
    )

    registration_nonce = models.CharField(max_length=64, null=True, blank=True)
    registration_token_sent_at = models.DateTimeField(null=True, blank=True)
    registration_token_used_at = models.DateTimeField(null=True, blank=True)
    registration_expires_at = models.DateTimeField(null=True, blank=True)

    rejection_reason = models.TextField(null=True, blank=True)
    last_error = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        creating = self.pk is None
        super().save(*args, **kwargs)
        if creating and not self.code:
            self.code = f"ORQ{self.pk:06d}"
            super().save(update_fields=['code'])

    def __str__(self):
        return f"{self.code} - {self.email} - {self.role.code}"
