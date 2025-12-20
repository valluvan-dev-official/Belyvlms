from rest_framework import viewsets, status, generics, views
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils.decorators import method_decorator
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Role, Permission, RolePermission, UserRole
from .serializers import (
    RoleSerializer, 
    PermissionSerializer, 
    RolePermissionSerializer, 
    AssignPermissionSerializer,
    UserRoleSerializer,
    RBACTokenObtainPairSerializer
)
from .permissions import HasRBACPermission

# NOTE: In a real system, managing RBAC itself (creating roles/permissions) 
# usually requires a 'SUPER_ADMIN' permission. 
# For this example, we assume the user has a permission code 'RBAC_MANAGE'.

@method_decorator(name='list', decorator=swagger_auto_schema(tags=["RBAC Core"]))
@method_decorator(name='create', decorator=swagger_auto_schema(tags=["RBAC Core"], request_body=RoleSerializer, consumes=['multipart/form-data']))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(tags=["RBAC Core"]))
@method_decorator(name='update', decorator=swagger_auto_schema(tags=["RBAC Core"], request_body=RoleSerializer, consumes=['multipart/form-data']))
@method_decorator(name='partial_update', decorator=swagger_auto_schema(tags=["RBAC Core"], request_body=RoleSerializer, consumes=['multipart/form-data']))
@method_decorator(name='destroy', decorator=swagger_auto_schema(tags=["RBAC Core"]))
class RoleViewSet(viewsets.ModelViewSet):
    """
    API Endpoint to Manage Roles (Create, List, Update, Delete).
    """
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, HasRBACPermission]
    required_permission = 'RBAC_ROLE_MANAGE' 

    def get_queryset(self):
        return Role.objects.all()

@method_decorator(name='list', decorator=swagger_auto_schema(tags=["RBAC Core"]))
@method_decorator(name='create', decorator=swagger_auto_schema(tags=["RBAC Core"], request_body=PermissionSerializer, consumes=['multipart/form-data']))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(tags=["RBAC Core"]))
@method_decorator(name='update', decorator=swagger_auto_schema(tags=["RBAC Core"], request_body=PermissionSerializer, consumes=['multipart/form-data']))
@method_decorator(name='partial_update', decorator=swagger_auto_schema(tags=["RBAC Core"], request_body=PermissionSerializer, consumes=['multipart/form-data']))
@method_decorator(name='destroy', decorator=swagger_auto_schema(tags=["RBAC Core"]))
class PermissionViewSet(viewsets.ModelViewSet):
    """
    API Endpoint to Manage Permissions (Create, List).
    """
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated, HasRBACPermission]
    required_permission = 'RBAC_PERMISSION_MANAGE'

@method_decorator(name='get', decorator=swagger_auto_schema(tags=["RBAC Assignments"]))
@method_decorator(name='post', decorator=swagger_auto_schema(tags=["RBAC Assignments"], request_body=AssignPermissionSerializer, consumes=['multipart/form-data']))
class RolePermissionView(generics.ListCreateAPIView):
    """
    API to List permissions of a role OR Assign permissions to a role.
    """
    queryset = RolePermission.objects.all()
    serializer_class = RolePermissionSerializer
    permission_classes = [IsAuthenticated, HasRBACPermission]
    required_permission = 'RBAC_PERMISSION_ASSIGN'

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AssignPermissionSerializer
        return RolePermissionSerializer

    def create(self, request, *args, **kwargs):
        """
        Assign multiple permissions to a role.
        """
        serializer = AssignPermissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        role_id = serializer.validated_data['role_id']
        permission_ids = serializer.validated_data['permission_ids']

        role = get_object_or_404(Role, id=role_id)
        
        created_links = []
        for pid in permission_ids:
            permission = get_object_or_404(Permission, id=pid)
            rp, created = RolePermission.objects.get_or_create(role=role, permission=permission)
            created_links.append(rp)

        return Response(
            {"status": "success", "assigned_count": len(created_links)}, 
            status=status.HTTP_201_CREATED
        )

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('role_id', openapi.IN_QUERY, description="Filter by Role ID", type=openapi.TYPE_INTEGER)
    ])
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        role_id = request.query_params.get('role_id')
        if role_id:
            queryset = queryset.filter(role_id=role_id)
        serializer = RolePermissionSerializer(queryset, many=True)
        return Response(serializer.data)

from .utils import get_user_permissions

@method_decorator(name='get', decorator=swagger_auto_schema(tags=["RBAC Auth"]))
class UserPermissionsView(views.APIView):
    """
    Get current user's profile, role, and permissions.
    Useful for reloading the dashboard without re-logging in.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        data = {
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.name if hasattr(user, 'name') else '',
                'is_superuser': user.is_superuser,
                'is_staff': user.is_staff
            },
            'role': None,
            'permissions': get_user_permissions(user)
        }

        try:
            user_role = UserRole.objects.select_related('role').get(user=user)
            data['role'] = {
                'code': user_role.role.code,
                'name': user_role.role.name
            }
        except UserRole.DoesNotExist:
            pass
            
        return Response(data)

@method_decorator(name='post', decorator=swagger_auto_schema(tags=["RBAC Assignments"], request_body=UserRoleSerializer, consumes=['multipart/form-data']))
class UserRoleAssignmentView(generics.CreateAPIView):
    """
    Assign a Role to a User.
    """
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer
    permission_classes = [IsAuthenticated, HasRBACPermission]
    required_permission = 'RBAC_USER_ASSIGN'

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class RBACTokenObtainPairView(TokenObtainPairView):
    """
    Custom Login View that returns Access/Refresh tokens + User Role + Permissions.
    Use this instead of the default SimpleJWT view.
    """
    serializer_class = RBACTokenObtainPairSerializer

class LogoutView(views.APIView):
    """
    Blacklist the refresh token to logout the user server-side.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["RBAC Auth"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={'refresh': openapi.Schema(type=openapi.TYPE_STRING)},
            required=['refresh']
        )
    )
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response({"status": "error", "message": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)
                
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"status": "success", "message": "Successfully logged out."}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
