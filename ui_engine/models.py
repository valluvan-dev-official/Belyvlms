from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import JSONField  # This might need adjustment depending on Django version
try:
    from django.db.models import JSONField
except ImportError:
    from django.contrib.postgres.fields import JSONField

class UIModule(models.Model):
    """
    Defines available UI areas in the system.
    Example: 'dashboard', 'student_profile', 'course_catalog'
    """
    slug = models.SlugField(unique=True, primary_key=True, help_text="Unique identifier for the module (e.g., 'dashboard')")
    name = models.CharField(max_length=100, help_text="Human readable name")
    description = models.TextField(blank=True, null=True)
    
    # Optional: Schema definition for validation
    schema_def = models.JSONField(default=dict, blank=True, help_text="JSON Schema to validate configs against") 

    def __str__(self):
        return self.name

class RoleUIDefault(models.Model):
    """
    L2: The Default Configuration for a specific Role.
    Defines the standard experience (layout, widgets, tabs) for a role.
    """
    role = models.ForeignKey('rbac.Role', on_delete=models.CASCADE, related_name='ui_defaults')
    module = models.ForeignKey(UIModule, on_delete=models.CASCADE, related_name='role_defaults')
    
    # The JSON payload defining tabs, layout, default widgets
    config = models.JSONField(help_text="JSON configuration for the UI") 
    
    # Metadata
    version = models.IntegerField(default=1, help_text="Config version for migration/cache busting")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('role', 'module')
        verbose_name = "Role UI Default"
        verbose_name_plural = "Role UI Defaults"

    def __str__(self):
        return f"{self.role.code} - {self.module.slug} (v{self.version})"

class UserUIPreference(models.Model):
    """
    L3: User's Personalized Configuration.
    Overrides Role Defaults. Scoped to User + Role + Module.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ui_preferences')
    role = models.ForeignKey('rbac.Role', on_delete=models.CASCADE, related_name='user_preferences')
    module = models.ForeignKey(UIModule, on_delete=models.CASCADE, related_name='user_preferences')
    
    # The personalized JSON config
    config = models.JSONField(help_text="User personalized JSON configuration")
    
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'role', 'module')
        verbose_name = "User UI Preference"
        verbose_name_plural = "User UI Preferences"

    def __str__(self):
        return f"{self.user} - {self.role.code} - {self.module.slug}"
