from rest_framework import serializers
from .models import Trainer
from coursedb.models import Course

class TrainerSerializer(serializers.ModelSerializer):
    stack_details = serializers.SerializerMethodField()
    profile_picture = serializers.ImageField(source='user.profile_picture', read_only=True)
    
    class Meta:
        model = Trainer
        fields = '__all__'
        read_only_fields = ['trainer_id', 'date_of_joining']

    def get_stack_details(self, obj):
        return [{"id": c.id, "code": c.code, "title": c.course_name} for c in obj.stack.all()]

class TrainerProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for Trainer Profile Updates by the Trainer (User).
    Enforces strict Field Ownership: Admin fields are Read-Only.
    """
    class Meta:
        model = Trainer
        fields = [
            'name', 'phone_number', 'location', 'other_location',
            'years_of_experience', 'demo_link',
            'trainer_id', 'email', 'employment_type', 'is_active',
            'extra_data'
        ]
        read_only_fields = [
            'trainer_id', 'email', 'employment_type', 'is_active'
        ]
