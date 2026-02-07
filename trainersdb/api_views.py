from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
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
    required_permission = 'TRAINER_MANAGEMENT_VIEW' # Default permission
    pagination_class = StandardResultsSetPagination
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = {
        'employment_type': ['exact'],
        'location': ['exact'],
        'is_active': ['exact'],
        'years_of_experience': ['gte', 'lte'],
        'stack': ['exact'],
    }
    
    search_fields = ['name', 'email', 'phone_number', 'trainer_id', 'stack__course_name']
    ordering_fields = ['years_of_experience', 'date_of_joining', 'name']

    def get_permissions(self):
        """
        Dynamic permission check based on action.
        """
        if self.action in ['list', 'retrieve']:
             self.required_permission = 'TRAINER_MANAGEMENT_VIEW'
        elif self.action == 'approve':
             self.required_permission = 'TRAINER_MANAGEMENT_APPROVE'
        elif self.action == 'reject':
             self.required_permission = 'TRAINER_MANAGEMENT_REJECT'
        elif self.action == 'create':
             self.required_permission = 'USER_MANAGEMENT_CREATE' # Fallback to User Mgmt
        elif self.action in ['update', 'partial_update']:
             self.required_permission = 'USER_MANAGEMENT_EDIT' # Fallback to User Mgmt
        elif self.action == 'destroy':
             self.required_permission = 'USER_MANAGEMENT_DELETE' # Fallback to User Mgmt
        else:
             self.required_permission = 'TRAINER_MANAGEMENT_VIEW'
            
        return super().get_permissions()

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        return Response({"status": "success", "message": "Trainer approved"})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        return Response({"status": "success", "message": "Trainer rejected"})

@api_view(['GET'])
@permission_classes([IsAuthenticated, HasRBACPermission])
def trainers_by_course(request, course_id):
    qs = Trainer.objects.filter(stack__id=course_id, is_active=True).distinct().select_related('user')
    data = []
    for t in qs:
        display_name = t.name
        if not display_name and t.user:
            display_name = getattr(t.user, 'name', '') or t.user.email
        data.append({'id': t.id, 'trainer_id': t.trainer_id, 'name': display_name})
    return Response(data)
trainers_by_course.required_permission = 'TRAINER_MANAGEMENT_VIEW'
