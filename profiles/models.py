from django.db import models
from django.conf import settings
from rbac.models import Role

class RoleProfileConfig(models.Model):
    """
    Configuration to link an RBAC Role to a specific Profile Model.
    Supports both Code-backed models (Student, Trainer) and Generic profiles.
    """
    role = models.OneToOneField(Role, on_delete=models.CASCADE, related_name='profile_config')
    is_required = models.BooleanField(default=False, help_text="Does this role require a profile?")
    
    # If set, uses this Django model (app_label.ModelName). 
    # If null, uses the 'GenericProfile' model.
    model_path = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        help_text="e.g., 'studentsdb.Student'. Leave empty for Generic Profile."
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Config for {self.role.name}"

class ProfileFieldDefinition(models.Model):
    """
    Defines dynamic fields for a specific Role's profile.
    These are fields NOT present in the hardcoded model but required by business logic.
    """
    FIELD_TYPES = [
        ('TEXT', 'Text'),
        ('NUMBER', 'Number'),
        ('DATE', 'Date'),
        ('BOOLEAN', 'Boolean'),
        ('CHOICE', 'Choice (Dropdown)'),
    ]

    config = models.ForeignKey(RoleProfileConfig, on_delete=models.CASCADE, related_name='dynamic_fields')
    name = models.CharField(max_length=100, help_text="Internal field name (key)")
    label = models.CharField(max_length=255, help_text="Display label")
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES, default='TEXT')
    is_required = models.BooleanField(default=False)
    options = models.JSONField(default=list, blank=True, help_text="List of options for CHOICE type")
    
    class Meta:
        unique_together = ('config', 'name')

    def __str__(self):
        return f"{self.name} ({self.config.role.code})"

class GenericProfile(models.Model):
    """
    A fallback profile storage for roles that don't have a dedicated table.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='generic_profile')
    role_config = models.ForeignKey(RoleProfileConfig, on_delete=models.PROTECT)
    
    # Stores all dynamic data as JSON
    data = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile: {self.user.email}"
