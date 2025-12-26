from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Student
from .serializers import StudentSerializer
from rest_framework.permissions import IsAuthenticated
from rbac.permissions import HasRBACPermission
from drf_yasg.utils import swagger_auto_schema
from django.utils.decorators import method_decorator
from rest_framework.pagination import PageNumberPagination

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

@method_decorator(name='list', decorator=swagger_auto_schema(tags=["Students"]))
@method_decorator(name='create', decorator=swagger_auto_schema(tags=["Students"]))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(tags=["Students"]))
@method_decorator(name='update', decorator=swagger_auto_schema(tags=["Students"]))
@method_decorator(name='partial_update', decorator=swagger_auto_schema(tags=["Students"]))
@method_decorator(name='destroy', decorator=swagger_auto_schema(tags=["Students"]))
class StudentViewSet(viewsets.ModelViewSet):
    """
    API Endpoint for Managing Students.
    """
    queryset = Student.objects.all().order_by('-id')
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated, HasRBACPermission]
    required_permission = 'STUDENT_VIEW'
    pagination_class = StandardResultsSetPagination

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = {
        'course_status': ['exact'],
        'location': ['exact'],
        'mode_of_class': ['exact'],
        'week_type': ['exact'],
        'working_status': ['exact'],
        'course_id': ['exact'],
        'consultant': ['exact'],
    }
    
    search_fields = ['student_id', 'first_name', 'last_name', 'email', 'phone', 'location', 'alternative_phone']
    ordering_fields = ['enrollment_date', 'student_id', 'first_name']

    def get_permissions(self):
        if self.action in ['create']:
            self.required_permission = 'STUDENT_CREATE'
        elif self.action in ['update', 'partial_update']:
            self.required_permission = 'STUDENT_UPDATE'
        elif self.action in ['destroy']:
            self.required_permission = 'STUDENT_DELETE'
        else:
            self.required_permission = 'STUDENT_VIEW'
            
        return super().get_permissions()
