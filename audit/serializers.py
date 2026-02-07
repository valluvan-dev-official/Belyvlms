from rest_framework import serializers
from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = [
            "id",
            "timestamp",
            "actor_user_id",
            "actor_role",
            "action_type",
            "entity_type",
            "entity_id",
            "old_value",
            "new_value",
            "source",
            "ip_address",
            "user_agent",
            "correlation_id",
        ]
