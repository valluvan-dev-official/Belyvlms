from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from django.utils.decorators import method_decorator
from rbac.permissions import HasRBACPermission
from .models import Trainer
from .serializers import TrainerSerializer
from rest_framework.pagination import PageNumberPagination

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

@method_decorator(name='list', decorator=swagger_auto_schema(tags=["Trainers"]))
@method_decorator(name='create', decorator=swagger_auto_schema(tags=["Trainers"]))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(tags=["Trainers"]))
@method_decorator(name='update', decorator=swagger_auto_schema(tags=["Trainers"]))
@method_decorator(name='partial_update', decorator=swagger_auto_schema(tags=["Trainers"]))
@method_decorator(name='destroy', decorator=swagger_auto_schema(tags=["Trainers"]))
class TrainerViewSet(viewsets.ModelViewSet):
    """
    API Endpoint for Managing Trainers.
    """
    queryset = Trainer.objects.all().order_by('-id')
    serializer_class = TrainerSerializer
    permission_classes = [IsAuthenticated, HasRBACPermission]
    required_permission = 'TRAINER_VIEW' # Default permission
    pagination_class = StandardResultsSetPagination
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = {
        'employment_type': ['exact'],
        'location': ['exact'],
        'is_active': ['exact'],
        'years_of_experience': ['gte', 'lte'],
    }
    
    search_fields = ['name', 'email', 'phone_number', 'trainer_id', 'stack__course_name']
    ordering_fields = ['years_of_experience', 'date_of_joining', 'name']

    def get_permissions(self):
        """
        Dynamic permission check based on action.
        """
        if self.action in ['create']:
            self.required_permission = 'TRAINER_CREATE'
        elif self.action in ['update', 'partial_update']:
            self.required_permission = 'TRAINER_UPDATE'
        elif self.action in ['destroy']:
            self.required_permission = 'TRAINER_DELETE' # Ensure this perm exists in seed
        else:
            self.required_permission = 'TRAINER_VIEW'
            
        return super().get_permissions()
