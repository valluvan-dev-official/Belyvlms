from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()

class CustomUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'name', 'role', 'profile_picture',
            'is_active', 'is_staff', 'is_superuser', 'totp_secret', 'password'
        ]
        read_only_fields = ['is_staff', 'is_superuser', 'totp_secret']

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = super().create(validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Fetch RBAC roles (fixes legacy role mismatch)
        # The 'rbac_roles' relation comes from rbac.models.UserRole
        rbac_entries = instance.rbac_roles.select_related('role').all()
        
        if rbac_entries:
            # Use the first RBAC role as the primary display role
            primary_role = rbac_entries[0].role
            ret['role'] = primary_role.name  # Override legacy field
            
            # Add explicit roles list for multi-role support
            ret['roles'] = [
                {'code': entry.role.code, 'name': entry.role.name} 
                for entry in rbac_entries
            ]
        
        return ret

class UserMeSerializer(CustomUserSerializer):
    class Meta(CustomUserSerializer.Meta):
        read_only_fields = CustomUserSerializer.Meta.read_only_fields + ['role', 'is_active', 'email']

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user
