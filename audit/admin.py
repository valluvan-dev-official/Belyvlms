from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("id", "timestamp", "actor_user_id", "actor_role", "action_type", "entity_type", "entity_id", "source")
    search_fields = ("actor_user_id", "action_type", "entity_type", "entity_id", "correlation_id")
    list_filter = ("action_type", "entity_type", "source")
    readonly_fields = ("timestamp", "actor_user_id", "actor_role", "action_type", "entity_type", "entity_id", "old_value", "new_value", "source", "ip_address", "user_agent", "correlation_id")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
