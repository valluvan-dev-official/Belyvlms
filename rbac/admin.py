from django.contrib import admin
from .models import Role, Permission, RolePermission, UserRole
from .forms import RolePermissionForm, RoleForm

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    form = RoleForm
    list_display = ('code', 'name', 'created_at')
    search_fields = ('code', 'name')
    ordering = ('name',)

@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'module', 'created_at')
    list_filter = ('module',)
    search_fields = ('code', 'name', 'module')
    ordering = ('module', 'code')

@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    form = RolePermissionForm
    list_display = ('role', 'permission', 'created_at')
    list_filter = ('role', 'permission__module')
    search_fields = ('role__name', 'permission__code')
    
    def save_model(self, request, obj, form, change):
        if not change:
            # BULK CREATE MODE (Adding)
            role = form.cleaned_data['role']
            permissions = form.cleaned_data['permissions']
            
            first_instance = None
            for permission in permissions:
                instance, created = RolePermission.objects.get_or_create(role=role, permission=permission)
                if not first_instance:
                    first_instance = instance
            
            # Fix for "RelatedObjectDoesNotExist":
            # The Admin needs 'obj' to be a valid, saved object for logging and messages.
            # We assign the properties of the first created permission to 'obj'.
            if first_instance:
                obj.permission = first_instance.permission
                obj.pk = first_instance.pk
                # We don't call obj.save() because it's already saved via get_or_create
        else:
            # EDIT MODE (Single)
            # Fallback to standard save if they somehow edit a single row
            super().save_model(request, obj, form, change)

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'assigned_at')
    list_filter = ('role', 'assigned_at')
    search_fields = ('user__email', 'role__name')
    autocomplete_fields = ['user', 'role']
