from rest_framework import serializers
from .models import Role, Permission, RolePermission, UserRole
from django.contrib.auth import get_user_model

User = get_user_model()

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'code', 'name', 'module', 'created_at']

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'code', 'name', 'created_at']

class RolePermissionSerializer(serializers.ModelSerializer):
    role_code = serializers.CharField(source='role.code', read_only=True)
    permission_code = serializers.CharField(source='permission.code', read_only=True)
    
    class Meta:
        model = RolePermission
        fields = ['id', 'role', 'permission', 'role_code', 'permission_code']
        
class AssignPermissionSerializer(serializers.Serializer):
    """
    Serializer for bulk assignment or single assignment.
    """
    role_id = serializers.IntegerField()
    permission_ids = serializers.ListField(child=serializers.IntegerField())

class UserRoleSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.name', read_only=True)
    
    class Meta:
        model = UserRole
        fields = ['id', 'user', 'role', 'role_name', 'assigned_at']
