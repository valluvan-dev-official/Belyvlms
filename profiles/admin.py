from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db import transaction
from django.core.exceptions import ValidationError

from accounts.admin import CustomUserCreationForm, CustomUserAdmin
from .models import RoleProfileConfig, ProfileFieldDefinition, GenericProfile
from .services import OnboardingService
from rbac.models import Role

User = get_user_model()

# 1. Extend the User Creation Form
class EnterpriseUserCreationForm(CustomUserCreationForm):
    """
    Enhanced User Creation Form that supports RBAC Roles and Profile Data.
    """
    role_code = forms.ModelChoiceField(
        queryset=Role.objects.all(),
        required=True,
        label="Assign RBAC Role",
        to_field_name="code"
    )

    # HIDE the legacy 'role' field from CustomUserCreationForm
    # We don't want admins to use the hardcoded dropdown anymore.
    role = forms.CharField(widget=forms.HiddenInput(), required=False)
    
    # We can add a simple JSON field for extra profile data if needed,
    # but for Admin UI, it's often cleaner to just handle the basic fields.
    
    def save(self, commit=True):
        # We override save to use the OnboardingService
        # This ensures User + Role + Profile are created atomically
        
        email = self.cleaned_data['email']
        name = self.cleaned_data['name']
        password = self.cleaned_data['password1']
        role = self.cleaned_data['role_code'] # This is a Role object
        is_staff = self.cleaned_data.get('is_staff', False)
        is_superuser = self.cleaned_data.get('is_superuser', False)
        
        try:
            # Call our Enterprise Service
            user = OnboardingService.onboard_user(
                email=email,
                name=name,
                password=password,
                role_code=role.code,
                is_staff=is_staff,
                is_superuser=is_superuser,
                profile_data={}, # Admin can edit profile later
                extra_data={},
                skip_profile_validation=True # Admin bypass
            )
            # IMPORTANT: Django Admin expects the form to return a saved object
            # AND it tries to call save_m2m() later if commit=False (though we ignore it).
            # We must satisfy the form contract.
            self.instance = user
            return user
        except ValidationError as e:
            self.add_error(None, str(e))
            raise e
            
    def save_m2m(self):
        """
        Django Admin requires this method to exist when using ModelAdmin.
        Since we handle M2M (like roles) inside OnboardingService, 
        we can leave this empty or use it for other M2M fields if needed.
        """
        pass

# 2. Register the Proxy Model
class EnterpriseUser(User):
    class Meta:
        proxy = True
        verbose_name = "Enterprise User (Onboarding)"
        verbose_name_plural = "Enterprise Users (Onboarding)"

@admin.register(EnterpriseUser)
class EnterpriseUserAdmin(CustomUserAdmin):
    """
    Special Admin Interface for creating users via the Onboarding Service.
    """
    add_form = EnterpriseUserCreationForm
    
    list_display = ('email', 'name', 'get_rbac_role', 'is_active')
    
    # We MUST override add_fieldsets to show 'role_code' instead of the legacy 'role'
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'role_code', 'password1', 'password2', 'is_staff', 'is_superuser')}
        ),
    )
    
    def get_rbac_role(self, obj):
        try:
            return obj.rbac_role.role.name
        except:
            return "No Role"
    get_rbac_role.short_description = "RBAC Role"

# 3. Register Config Models
class ProfileFieldDefinitionInline(admin.TabularInline):
    model = ProfileFieldDefinition
    extra = 1

@admin.register(RoleProfileConfig)
class RoleProfileConfigAdmin(admin.ModelAdmin):
    list_display = ('role', 'is_required', 'model_path')
    inlines = [ProfileFieldDefinitionInline]
    search_fields = ('role__name', 'model_path')

@admin.register(GenericProfile)
class GenericProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role_config', 'created_at')
    search_fields = ('user__email',)
