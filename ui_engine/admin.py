from django.contrib import admin
from django.utils.html import format_html
from .models import UIModule, RoleUIDefault
import json

@admin.register(UIModule)
class UIModuleAdmin(admin.ModelAdmin):
    list_display = ('slug', 'name', 'description')
    search_fields = ('slug', 'name')

@admin.register(RoleUIDefault)
class RoleUIDefaultAdmin(admin.ModelAdmin):
    list_display = ('role', 'module', 'version', 'is_active', 'updated_at')
    list_filter = ('role', 'module', 'is_active')
    search_fields = ('role__code', 'role__name', 'module__slug')
    readonly_fields = ('pretty_config',)

    fieldsets = (
        ('Context', {
            'fields': ('role', 'module', 'version', 'is_active')
        }),
        ('Configuration', {
            'fields': ('config',),
            'description': 'Enter valid JSON configuration here.'
        }),
        ('Preview', {
            'fields': ('pretty_config',),
            'classes': ('collapse',),
        }),
    )

    def pretty_config(self, instance):
        """Displays the JSON config in a readable format"""
        response = json.dumps(instance.config, sort_keys=True, indent=2)
        # Using <pre> tag to preserve formatting
        return format_html('<pre>{}</pre>', response)

    pretty_config.short_description = 'Config Preview'
