from rest_framework import serializers
from .models import Student

class StudentSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.course_name', read_only=True)
    profile_picture = serializers.ImageField(source='user.profile_picture', read_only=True)
    
    class Meta:
        model = Student
        fields = '__all__'
