from rest_framework import serializers
from .models import Trainer
from coursedb.models import Course

class TrainerSerializer(serializers.ModelSerializer):
    stack_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Trainer
        fields = '__all__'
        read_only_fields = ['trainer_id', 'date_of_joining']

    def get_stack_details(self, obj):
        return [{"id": c.id, "code": c.code, "title": c.title} for c in obj.stack.all()]
