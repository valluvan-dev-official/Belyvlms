from django.contrib import admin
from .models import Role, Permission, RolePermission, UserRole

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
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
    list_display = ('role', 'permission', 'created_at')
    list_filter = ('role', 'permission__module')
    search_fields = ('role__name', 'permission__code')
    autocomplete_fields = ['role', 'permission']

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'assigned_at')
    list_filter = ('role', 'assigned_at')
    search_fields = ('user__email', 'role__name')
    autocomplete_fields = ['user', 'role']
