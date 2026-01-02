from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Role, Permission, RolePermission, UserRole

class RoleSerializer(serializers.ModelSerializer):
    user_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Role
        fields = ['id', 'code', 'name', 'user_count']

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'code', 'name', 'module']

class RBACTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add User Role and Permissions to response
        user = self.user
        
        try:
            user_role = UserRole.objects.select_related('role').get(user=user)
            role = user_role.role
            
            # Get all permissions for this role
            permissions = Permission.objects.filter(role_permissions__role=role).values_list('code', flat=True)
            
            data['role'] = {
                'code': role.code,
                'name': role.name
            }
            data['permissions'] = list(permissions)
            
        except UserRole.DoesNotExist:
            data['role'] = None
            data['permissions'] = []
            
        data['user'] = {
            'id': user.id,
            'email': user.email,
            'name': user.name if hasattr(user, 'name') else '',
            'is_superuser': user.is_superuser,
            'is_staff': user.is_staff
        }
        
        return data

class RolePermissionSerializer(serializers.ModelSerializer):
    role_name = serializers.ReadOnlyField(source='role.name')
    permission_code = serializers.ReadOnlyField(source='permission.code')
    
    class Meta:
        model = RolePermission
        fields = ['id', 'role', 'role_name', 'permission', 'permission_code', 'created_at']

class AssignPermissionSerializer(serializers.Serializer):
    role_id = serializers.IntegerField()
    permission_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )

class UserRoleSerializer(serializers.ModelSerializer):
    email = serializers.ReadOnlyField(source='user.email')
    role_name = serializers.ReadOnlyField(source='role.name')
    
    class Meta:
        model = UserRole
        fields = ['id', 'user', 'email', 'role', 'role_name', 'assigned_at']
