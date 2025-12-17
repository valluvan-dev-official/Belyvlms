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

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user
