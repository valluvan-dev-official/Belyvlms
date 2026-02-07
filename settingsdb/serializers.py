from rest_framework import serializers
from .models import SourceOfJoining

class SourceOfJoiningSerializer(serializers.ModelSerializer):
    class Meta:
        model = SourceOfJoining
        fields = '__all__'
