from django.contrib import admin
from django import forms
from .models import Role, Module, Permission, RolePermission, UserProfile, UserRole, UserPermissionOverride, AuditLog, EnterpriseUser
from .services import create_enterprise_user

class EnterpriseUserCreationForm(forms.ModelForm):
    primary_role = forms.ModelChoiceField(
        queryset=Role.objects.filter(is_active=True), 
        required=True,
        help_text="Select the primary role (e.g., Trainer, Admin)."
    )
    extra_roles = forms.ModelMultipleChoiceField(
        queryset=Role.objects.filter(is_active=True), 
        required=False,
        help_text="Select additional roles if applicable."
    )
    
    class Meta:
        model = EnterpriseUser
        fields = ('email', 'name', 'primary_role', 'extra_roles')
        
    def save(self, commit=True):
        # Return unsaved instance, actual creation happens in save_model
        return super().save(commit=False)

@admin.register(EnterpriseUser)
class EnterpriseUserAdmin(admin.ModelAdmin):
    add_form = EnterpriseUserCreationForm
    list_display = ('email', 'name', 'get_primary_role', 'is_active')
    search_fields = ('email', 'name')
    
    def get_primary_role(self, obj):
        if hasattr(obj, 'access_profile'):
            return obj.access_profile.role.name
        return obj.role 
    get_primary_role.short_description = 'Primary Role'

    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            return self.add_form
        return super().get_form(request, obj, **kwargs)

    def save_model(self, request, obj, form, change):
        if change:
            super().save_model(request, obj, form, change)
        else:
            # Use Enterprise Service
            user = create_enterprise_user(
                name=form.cleaned_data['name'],
                email=form.cleaned_data['email'],
                primary_role_id=form.cleaned_data['primary_role'].id,
                extra_role_ids=[r.id for r in form.cleaned_data['extra_roles']],
                actor=request.user
            )
            self.message_user(request, f"User created successfully. Password: {user.generated_password}")
            
            # Sync obj with created user to satisfy Admin flow
            obj.id = user.id
            obj.pk = user.pk
            # No need to save obj again

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'created_at')
    search_fields = ('name', 'code')
    list_filter = ('is_active', 'created_at')
    ordering = ('name',)

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'module', 'action')
    search_fields = ('name', 'code', 'module__name')
    list_filter = ('module', 'action')

@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ('role', 'permission', 'created_at')
    search_fields = ('role__name', 'permission__code')
    list_filter = ('role', 'permission__module')
    autocomplete_fields = ['role', 'permission']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'role_based_id', 'created_at')
    search_fields = ('user__email', 'user__name', 'role_based_id', 'role__name')
    list_filter = ('role', 'created_at')
    autocomplete_fields = ['user', 'role']

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'assigned_at', 'assigned_by')
    search_fields = ('user__email', 'user__name', 'role__name')
    list_filter = ('role', 'assigned_at')
    autocomplete_fields = ['user', 'role']

@admin.register(UserPermissionOverride)
class UserPermissionOverrideAdmin(admin.ModelAdmin):
    list_display = ('user', 'permission', 'is_granted', 'created_at', 'granted_by')
    search_fields = ('user__email', 'permission__code')
    list_filter = ('is_granted', 'created_at')
    autocomplete_fields = ['user', 'permission']

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'actor', 'action', 'target', 'ip_address')
    search_fields = ('actor__email', 'action', 'target')
    list_filter = ('action', 'timestamp')
    readonly_fields = ('timestamp', 'actor', 'action', 'target', 'details', 'ip_address')

    def has_add_permission(self, request):
        return False

