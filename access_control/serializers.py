from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Role, Module, Permission, RolePermission, UserProfile, UserRole, UserPermissionOverride
from .utils import generate_role_based_id
from .services import get_user_permissions

User = get_user_model()

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'code', 'is_active', 'is_system_role', 'description', 'created_at']
        read_only_fields = ['created_at']

class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = '__all__'

class PermissionSerializer(serializers.ModelSerializer):
    module_name = serializers.CharField(source='module.name', read_only=True)

    class Meta:
        model = Permission
        fields = ['id', 'name', 'code', 'module', 'module_name', 'action', 'description']

class RolePermissionSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.name', read_only=True)
    permission_code = serializers.CharField(source='permission.code', read_only=True)

    class Meta:
        model = RolePermission
        fields = ['id', 'role', 'role_name', 'permission', 'permission_code']

class CreateUserWithRoleSerializer(serializers.ModelSerializer):
    """
    Serializer to create a User with a Role (Enterprise RBAC).
    """
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.filter(is_active=True),
        source='role',
        write_only=True
    )
    password = serializers.CharField(write_only=True)
    
    # Read-only fields for response
    role_based_id = serializers.CharField(read_only=True)
    role_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'password', 'role_id', 'role_based_id', 'role_name']
        extra_kwargs = {
            'email': {'required': True},
            'name': {'required': True},
        }

    def create(self, validated_data):
        role = validated_data.pop('role')
        password = validated_data.pop('password')
        
        # Start transaction to ensure atomicity
        with transaction.atomic():
            # Generate ID
            role_based_id = generate_role_based_id(role.code)
            
            # Create User
            # We use the role name as the string role for backward compatibility
            user = User.objects.create_user(
                email=validated_data['email'],
                name=validated_data['name'],
                password=password,
                role=role.name.lower() # Mapping Role Name to existing role field if needed, or just string
            )
            
            # Create UserProfile
            UserProfile.objects.create(
                user=user,
                role=role,
                role_based_id=role_based_id
            )
            
            # Attach extra info for response
            user.role_based_id = role_based_id
            user.role_name = role.name
            
            return user

class UserRoleSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.name', read_only=True)
    
    class Meta:
        model = UserRole
        fields = ['id', 'user', 'role', 'role_name', 'assigned_at', 'assigned_by']
        read_only_fields = ['assigned_at', 'assigned_by']

class UserPermissionOverrideSerializer(serializers.ModelSerializer):
    permission_code = serializers.CharField(source='permission.code', read_only=True)
    
    class Meta:
        model = UserPermissionOverride
        fields = ['id', 'user', 'permission', 'permission_code', 'is_granted', 'created_at', 'granted_by']
        read_only_fields = ['created_at', 'granted_by']

class RBACTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['name'] = user.name
        token['email'] = user.email
        
        # Roles
        roles = []
        if getattr(user, 'role', None):
             roles.append(str(user.role))
             
        # Additional roles
        additional_roles = UserRole.objects.filter(user=user).values_list('role__code', flat=True)
        roles.extend(additional_roles)
        
        token['roles'] = list(set(roles)) # Unique
        
        # Permissions
        token['permissions'] = get_user_permissions(user)

        return token
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add data to response body as well
        data['user_id'] = self.user.id
        data['name'] = self.user.name
        
        # Roles
        roles = []
        if getattr(self.user, 'role', None):
             roles.append(str(self.user.role))
        additional_roles = UserRole.objects.filter(user=self.user).values_list('role__code', flat=True)
        roles.extend(additional_roles)
        data['roles'] = list(set(roles))
        
        # Permissions
        data['permissions'] = get_user_permissions(self.user)
        
        return data

class EnterpriseUserCreateSerializer(serializers.Serializer):
    """
    Serializer for creating users with full RBAC support.
    """
    name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    primary_role_id = serializers.IntegerField()
    extra_role_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False
    )
    overrides = serializers.ListField(
        child=serializers.DictField(), required=False,
        help_text="List of {permission_id: int, is_granted: bool}"
    )
    
    # Read-only output
    user_id = serializers.IntegerField(read_only=True, source='id')
    role_based_id = serializers.CharField(read_only=True)
    generated_password = serializers.CharField(read_only=True)
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
        
    def validate_primary_role_id(self, value):
        if not Role.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Invalid or inactive Primary Role ID.")
        return value

    def create(self, validated_data):
        # We delegate to the service layer
        from .services import create_enterprise_user
        
        user = create_enterprise_user(
            name=validated_data['name'],
            email=validated_data['email'],
            primary_role_id=validated_data['primary_role_id'],
            extra_role_ids=validated_data.get('extra_role_ids'),
            overrides=validated_data.get('overrides'),
            actor=self.context['request'].user
        )
        
        return user
