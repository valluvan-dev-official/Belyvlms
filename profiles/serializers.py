from rest_framework import serializers
from .models import RoleProfileConfig, ProfileFieldDefinition, GenericProfile
from accounts.models import CustomUser

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'name', 'role', 'is_active', 'last_login']

class ProfileFieldDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileFieldDefinition
        fields = ['id', 'config', 'name', 'label', 'field_type', 'is_required', 'options']

class RoleProfileConfigSerializer(serializers.ModelSerializer):
    dynamic_fields = ProfileFieldDefinitionSerializer(many=True, read_only=True)
    role_name = serializers.CharField(source='role.name', read_only=True)
    role_code = serializers.CharField(source='role.code', read_only=True)

    class Meta:
        model = RoleProfileConfig
        fields = ['id', 'role', 'role_name', 'role_code', 'is_required', 'model_path', 'dynamic_fields']

class GenericProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = GenericProfile
        fields = ['id', 'email', 'data', 'created_at']

class OnboardingSerializer(serializers.Serializer):
    email = serializers.EmailField()
    name = serializers.CharField(max_length=255)
    password = serializers.CharField(write_only=True)
    role_code = serializers.CharField(max_length=50)
    
    profile_data = serializers.DictField(required=False, default=dict)
    extra_data = serializers.DictField(required=False, default=dict)
