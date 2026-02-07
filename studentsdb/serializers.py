from rest_framework import serializers
from .models import Student
from batchdb.models import BatchStudent
from paymentdb.models import Payment
from placementdb.models import Placement

class StudentSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.course_name', read_only=True)
    profile_picture = serializers.ImageField(source='user.profile_picture', read_only=True)
    consultant_name = serializers.CharField(source='consultant.name', read_only=True)
    
    # Extended Details for Profile Modal
    trainer_name = serializers.CharField(source='trainer.name', read_only=True)
    batch_details = serializers.SerializerMethodField()
    payment_details = serializers.SerializerMethodField()
    placement_details = serializers.SerializerMethodField()
    interview_details = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = '__all__'

    def get_batch_details(self, obj):
        history = {
            'current_batch': None,
            'batch_history': []
        }
        qs = BatchStudent.objects.filter(student=obj).select_related('batch__course', 'batch__trainer').order_by('activated_at')
        for bs in qs:
            info = {
                'pk': bs.batch.id if bs.batch_id else None,
                'batch_id': bs.batch.batch_id if bs.batch_id else None,
                'course': str(bs.batch.course) if bs.batch and bs.batch.course else 'N/A',
                'trainer': str(bs.batch.trainer) if bs.batch and bs.batch.trainer else 'N/A',
                'slot_time': bs.batch.get_slottime if bs.batch else 'Not Set',
                'activated_at': bs.activated_at.isoformat() if bs.activated_at else None,
                'deactivated_at': bs.deactivated_at.isoformat() if bs.deactivated_at else None,
                'status': 'Active' if bs.is_active else 'Inactive'
            }
            if bs.is_active:
                history['current_batch'] = info
            else:
                history['batch_history'].append(info)
        return history

    def get_payment_details(self, obj):
        try:
            payment = obj.payment
            return {
                "total_fees": payment.total_fees,
                "amount_paid": payment.amount_paid,
                "pending_amount": payment.total_pending_amount,
                "status": payment.get_payment_status()
            }
        except Exception:
            return None

    def get_placement_details(self, obj):
        details = {
            "onboarding_call": "Completed" if obj.onboardingcalldone else "Pending",
            "placement_session": "Completed" if obj.placement_session_completed else "Pending",
            "interview_questions": "Shared" if obj.interviewquestion_shared else "Pending",
            "resume_templates": "Shared" if obj.resume_template_shared else "Pending",
            "mock_interview": "Completed" if obj.mock_interview_completed else "Pending",
            "placed_status": "Placed" if obj.course_status == 'P' else "Not Placed",
            "resume_link": None
        }
        try:
            if hasattr(obj, 'placement') and obj.placement.resume_link:
                details['resume_link'] = obj.placement.resume_link.url
        except:
            pass
        return details

    def get_interview_details(self, obj):
        try:
            if hasattr(obj, 'placement'):
                interviews = obj.placement.interviews.all().order_by('-interview_date')
                return [
                    {
                        "company": i.company.company_name if i.company else "N/A",
                        "round": i.interview_round,
                        "date": i.interview_date.isoformat() if i.interview_date else None,
                        "status": "Selected" if i.selected else ("Attended" if i.attended else "Scheduled")
                    }
                    for i in interviews
                ]
        except:
            pass
        return []

class StudentProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for Student Profile Updates by the Student (User).
    Enforces strict Field Ownership: Admin fields are Read-Only.
    """
    class Meta:
        model = Student
        fields = [
            'first_name', 'last_name', 'it_experience', 
            'course_status', 'mode_of_class', 'week_type',
            'course_id', 'trainer'
        ]
        read_only_fields = [
            'course_status', 'mode_of_class', 'week_type',
            'course_id', 'trainer'
        ]
