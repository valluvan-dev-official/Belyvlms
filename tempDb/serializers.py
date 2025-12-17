from rest_framework import serializers
from .models import temp_student


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = temp_student
        fields = '__all__'