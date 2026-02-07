from django.contrib.auth import get_user_model
from rest_framework import viewsets, permissions
from rbac.permissions import HasRBACPermission
from rest_framework.pagination import PageNumberPagination
from drf_yasg.utils import swagger_auto_schema
from .serializers import CustomUserSerializer, LogoutSerializer, UserMeSerializer
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken

# Pagination for consistent result sizes
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

User = get_user_model()

class UserMeView(generics.RetrieveUpdateAPIView):
    """
    API endpoint for users to view and update their own profile.
    """
    serializer_class = UserMeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    @swagger_auto_schema(tags=["User Me"], operation_summary="Get Current User Profile")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(tags=["User Me"], operation_summary="Update Current User Profile", request_body=UserMeSerializer)
    def patch(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
        
    @swagger_auto_schema(tags=["User Me"], operation_summary="Update Current User Profile (Full)", request_body=UserMeSerializer)
    def put(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('id')
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAuthenticated, HasRBACPermission]
    pagination_class = StandardResultsSetPagination

    @property
    def required_permission(self):
        if self.action in ['list', 'retrieve']:
            return 'USER_MANAGEMENT_VIEW'
        if self.action == 'create':
            return 'USER_MANAGEMENT_CREATE'
        if self.action in ['update', 'partial_update']:
            return 'USER_MANAGEMENT_EDIT'
        if self.action == 'destroy':
            return 'USER_MANAGEMENT_DELETE'
        if self.action == 'export':
            return 'USER_MANAGEMENT_EXPORT'
        if self.action == 'assign_role':
            return 'USER_MANAGEMENT_ASSIGN_ROLE'
        return 'USER_MANAGEMENT_VIEW'

    @swagger_auto_schema(tags=["CustomUser"], request_body=CustomUserSerializer)
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(tags=["CustomUser"], request_body=CustomUserSerializer)
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(tags=["CustomUser"], request_body=CustomUserSerializer)
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(tags=["CustomUser"])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=["CustomUser"])
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(tags=["CustomUser"])
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['post'])
    def export(self, request):
        return Response({"status": "success", "message": "User export endpoint"})

    @action(detail=True, methods=['post'], url_path='assign-role')
    def assign_role(self, request, pk=None):
        return Response({"status": "success", "message": "Role assigned"})

class LogoutView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LogoutSerializer

    @swagger_auto_schema(tags=["Auth"], request_body=LogoutSerializer)
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            token = RefreshToken(serializer.validated_data["refresh"])
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)
