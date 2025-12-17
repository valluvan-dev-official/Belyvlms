from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Role, Permission, RolePermission, UserRole
from .serializers import (
    RoleSerializer, 
    PermissionSerializer, 
    RolePermissionSerializer, 
    AssignPermissionSerializer,
    UserRoleSerializer
)
from .permissions import HasRBACPermission

from django.utils.decorators import method_decorator

# NOTE: In a real system, managing RBAC itself (creating roles/permissions) 
# usually requires a 'SUPER_ADMIN' permission. 
# For this example, we assume the user has a permission code 'RBAC_MANAGE'.

@method_decorator(name='list', decorator=swagger_auto_schema(tags=["RBAC Core"]))
@method_decorator(name='create', decorator=swagger_auto_schema(tags=["RBAC Core"]))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(tags=["RBAC Core"]))
@method_decorator(name='update', decorator=swagger_auto_schema(tags=["RBAC Core"]))
@method_decorator(name='partial_update', decorator=swagger_auto_schema(tags=["RBAC Core"]))
@method_decorator(name='destroy', decorator=swagger_auto_schema(tags=["RBAC Core"]))
class RoleViewSet(viewsets.ModelViewSet):
    """
    API Endpoint to Manage Roles (Create, List, Update, Delete).
    """
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, HasRBACPermission]
    required_permission = 'RBAC_ROLE_MANAGE' # Example permission code required to access this view

    def get_queryset(self):
        return Role.objects.all()

@method_decorator(name='list', decorator=swagger_auto_schema(tags=["RBAC Core"]))
@method_decorator(name='create', decorator=swagger_auto_schema(tags=["RBAC Core"]))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(tags=["RBAC Core"]))
@method_decorator(name='update', decorator=swagger_auto_schema(tags=["RBAC Core"]))
@method_decorator(name='partial_update', decorator=swagger_auto_schema(tags=["RBAC Core"]))
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
@method_decorator(name='post', decorator=swagger_auto_schema(tags=["RBAC Assignments"], request_body=AssignPermissionSerializer))
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
        """
        List all role-permission mappings.
        Optionally filter by ?role_id=X
        """
        role_id = request.query_params.get('role_id')
        if role_id:
            queryset = self.queryset.filter(role_id=role_id)
        else:
            queryset = self.queryset.all()
            
        serializer = RolePermissionSerializer(queryset, many=True)
        return Response(serializer.data)

@method_decorator(name='post', decorator=swagger_auto_schema(tags=["RBAC Assignments"]))
class UserRoleAssignmentView(generics.CreateAPIView):
    """
    Assign a Role to a User.
    """
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer
    permission_classes = [IsAuthenticated, HasRBACPermission]
    required_permission = 'RBAC_USER_ASSIGN'
