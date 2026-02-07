from rest_framework import serializers
from .models import RoleUIDefault, UIModule

class UIConfigSerializer(serializers.ModelSerializer):
    """
    Serializer to return the final UI Configuration to the frontend.
    """
    class Meta:
        model = RoleUIDefault
        fields = ['config', 'version']
