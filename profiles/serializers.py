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

class GenericProfileUpdateSerializer(serializers.Serializer):
    """
    Serializer to validate and update Generic Profile JSON data
    based on the Role's ProfileFieldDefinitions.
    """
    data = serializers.DictField()

    def validate_data(self, value):
        user = self.context['request'].user
        # Find the GenericProfile for this user
        try:
            profile = GenericProfile.objects.get(user=user)
        except GenericProfile.DoesNotExist:
             raise serializers.ValidationError("No Generic Profile found for this user.")
        
        config = profile.role_config
        definitions = config.dynamic_fields.all()
        
        # Simple Validation Loop
        for field_def in definitions:
            field_name = field_def.name
            
            # Check Required
            if field_def.is_required and field_name not in value:
                raise serializers.ValidationError(f"Field '{field_def.label}' ({field_name}) is required.")
            
            # Check Type (Basic)
            if field_name in value:
                val = value[field_name]
                if field_def.field_type == 'NUMBER' and not isinstance(val, (int, float)):
                     raise serializers.ValidationError(f"Field '{field_def.label}' must be a number.")
                if field_def.field_type == 'BOOLEAN' and not isinstance(val, bool):
                     raise serializers.ValidationError(f"Field '{field_def.label}' must be a boolean.")
                # Add more type checks as needed (DATE, CHOICE)
        
        return value

class OnboardingSerializer(serializers.Serializer):
    email = serializers.EmailField()
    name = serializers.CharField(max_length=255)
    password = serializers.CharField(write_only=True)
    role_code = serializers.CharField(max_length=50)
    
    # Optional flags for admin creation
    is_superuser = serializers.BooleanField(required=False, default=False)
    
    profile_data = serializers.DictField(required=False, default=dict)
    extra_data = serializers.DictField(required=False, default=dict)
