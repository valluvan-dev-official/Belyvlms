from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Role, Permission, RolePermission, UserRole, OnboardRequest
from accounts.models import CustomUser
from django.utils import timezone

class RoleSerializer(serializers.ModelSerializer):
    user_count = serializers.IntegerField(read_only=True)
    is_editable = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = ['id', 'code', 'name', 'user_count', 'is_editable']
        
    def get_is_editable(self, obj):
        # Only SUPER_ADMIN (SAM) is locked
        if obj.code == 'SAM':
            return False
        return True

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'code', 'name', 'module', 'description']

class RBACTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        
        user = self.user
        
        # Use Centralized Auth Context Service
        # We don't pass active_role_code here, so it falls back to persistence or default
        from .services import build_auth_context
        auth_context = build_auth_context(user, active_role_code=None)
        
        # Merge context into response data
        data.update(auth_context)
        
        # Add specific login flags
        data['must_change_password'] = getattr(user, 'must_change_password', False)
        
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

class RoleDeactivateSerializer(serializers.Serializer):
    strategy = serializers.ChoiceField(choices=['fallback', 'reassign'])
    target_role_code = serializers.CharField(required=False, allow_blank=True)
    fallback_role_code = serializers.CharField(required=False, allow_blank=True)
    reason = serializers.CharField(required=False, allow_blank=True, max_length=255)

class UserRoleSerializer(serializers.ModelSerializer):
    email = serializers.ReadOnlyField(source='user.email')
    role_name = serializers.ReadOnlyField(source='role.name')
    
    class Meta:
        model = UserRole
        fields = ['id', 'user', 'email', 'role', 'role_name', 'assigned_at']

class UserCreateSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    username = serializers.CharField(max_length=100, required=False, allow_blank=True)
    email = serializers.EmailField()
    role_code = serializers.CharField(max_length=50)
    profile = serializers.DictField(required=False)

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value

    def validate_role_code(self, value):
        try:
            role = Role.objects.get(code=value)
        except Role.DoesNotExist:
            raise serializers.ValidationError("Invalid role code")
        if hasattr(role, "is_active") and not role.is_active:
            raise serializers.ValidationError("Role is inactive")
        return value

    def validate(self, attrs):
        role_code = attrs.get('role_code')
        profile = attrs.get('profile') or {}
        try:
            role = Role.objects.get(code=role_code)
        except Role.DoesNotExist:
            raise serializers.ValidationError({"role_code": "Invalid role code"})
        role_name = role.name
        if role_name == 'Student':
            if 'mode_of_class' not in profile or 'week_type' not in profile:
                raise serializers.ValidationError({"profile": "mode_of_class and week_type are required for Student"})
        if role_name == 'Trainer':
            if 'employment_type' not in profile:
                raise serializers.ValidationError({"profile": "employment_type is required for Trainer"})
        return attrs


class OnboardRequestCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role_code = serializers.CharField(max_length=50)

    def validate_role_code(self, value):
        try:
            role = Role.objects.get(code=value)
        except Role.DoesNotExist:
            raise serializers.ValidationError("Invalid role code")
        if hasattr(role, "is_active") and not role.is_active:
            raise serializers.ValidationError("Role is inactive")
        return value


class OnboardRequestPublicSubmitSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    profile = serializers.DictField(required=False)


class OnboardRequestAdminUpdateSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    profile = serializers.DictField(required=False)


class OnboardRequestSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    uuid = serializers.UUIDField(read_only=True)
    code = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    role_code = serializers.CharField(source="role.code", read_only=True)
    role_name = serializers.CharField(source="role.name", read_only=True)
    status = serializers.CharField(read_only=True)
    user_payload = serializers.DictField(read_only=True)
    admin_payload = serializers.DictField(read_only=True)
    submitted_at = serializers.DateTimeField(read_only=True)
    approved_at = serializers.DateTimeField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
