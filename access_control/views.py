from rest_framework import viewsets, generics, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from .models import Role, Permission, RolePermission, Module, UserRole, UserPermissionOverride
from .serializers import (
    RoleSerializer, 
    PermissionSerializer, 
    RolePermissionSerializer, 
    CreateUserWithRoleSerializer,
    ModuleSerializer,
    UserRoleSerializer,
    UserPermissionOverrideSerializer,
    RBACTokenObtainPairSerializer,
    EnterpriseUserCreateSerializer
)
from .services import get_user_permissions

class IsAdminUserCustom(permissions.BasePermission):
    """
    Allows access only to admin users.
    Checks strictly against the 'admin' role string or is_superuser.
    """
    def has_permission(self, request, view):
        return bool(request.user and (request.user.is_superuser or str(request.user.role).lower() == 'admin'))

@swagger_auto_schema(tags=["Access Control"])
class RoleViewSet(viewsets.ModelViewSet):
    """
    Manage Roles (Create, List, Update, Delete).
    Only Admins can manage roles.
    """
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUserCustom]

    def get_queryset(self):
        return Role.objects.all()

    @swagger_auto_schema(tags=["Access Control"])
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def active(self, request):
        """
        List only active roles for dropdowns.
        """
        roles = Role.objects.filter(is_active=True)
        serializer = self.get_serializer(roles, many=True)
        return Response(serializer.data)

@swagger_auto_schema(tags=["Access Control"])
class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List Permissions available in the system.
    """
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUserCustom]

@method_decorator(name='get', decorator=swagger_auto_schema(tags=["Access Control"]))
@method_decorator(name='post', decorator=swagger_auto_schema(tags=["Access Control"], request_body=RolePermissionSerializer))
class RolePermissionView(generics.ListCreateAPIView):
    """
    Assign permissions to a role.
    """
    queryset = RolePermission.objects.all()
    serializer_class = RolePermissionSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUserCustom]

    def create(self, request, *args, **kwargs):
        if 'permissions' in request.data and isinstance(request.data['permissions'], list):
            role_id = request.data.get('role')
            role = get_object_or_404(Role, id=role_id)
            permission_ids = request.data['permissions']
            
            created_items = []
            for perm_id in permission_ids:
                rp, created = RolePermission.objects.get_or_create(
                    role=role,
                    permission_id=perm_id
                )
                created_items.append(rp)
            
            return Response({"status": "Permissions assigned"}, status=status.HTTP_201_CREATED)
            
        return super().create(request, *args, **kwargs)

@swagger_auto_schema(tags=["Access Control"], request_body=CreateUserWithRoleSerializer)
class CreateUserWithRoleView(generics.CreateAPIView):
    """
    Create a new user with a specific Role.
    """
    serializer_class = CreateUserWithRoleSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUserCustom]

@swagger_auto_schema(tags=["Access Control"])
class UserPermissionsView(generics.RetrieveAPIView):
    """
    Get permissions for the current user based on their assigned Role.
    Frontend uses this to hide/show UI elements.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        perms = get_user_permissions(user)
        
        # Group by module for legacy support if needed, or return flat list
        # Requirement: "final permission codes list"
        # We return both: 'codes' (flat) and 'grouped' (for UI)
        
        grouped = {}
        # Fetch permission objects to group them
        # This is a bit expensive if we just have codes. 
        # But for UI grouping we need Module slug.
        # Optimization: Fetch all permissions once and map?
        # Or just rely on the codes.
        
        # Let's return flat list of codes as primary
        
        return Response({
            "user_id": user.id,
            "role": str(user.role),
            "codes": perms
        })

@swagger_auto_schema(tags=["Access Control"])
class UserRoleViewSet(viewsets.ModelViewSet):
    """
    Assign additional roles to users.
    """
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUserCustom]

    def perform_create(self, serializer):
        serializer.save(assigned_by=self.request.user)

@swagger_auto_schema(tags=["Access Control"])
class UserPermissionOverrideViewSet(viewsets.ModelViewSet):
    """
    Explicitly Allow/Deny permissions for users.
    """
    queryset = UserPermissionOverride.objects.all()
    serializer_class = UserPermissionOverrideSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUserCustom]

    def perform_create(self, serializer):
        serializer.save(granted_by=self.request.user)

@method_decorator(name='post', decorator=swagger_auto_schema(tags=["Access Control"], request_body=RBACTokenObtainPairSerializer))
class RBACTokenObtainPairView(TokenObtainPairView):
    serializer_class = RBACTokenObtainPairSerializer

@method_decorator(name='post', decorator=swagger_auto_schema(tags=["Access Control"]))
class RBACTokenRefreshView(TokenRefreshView):
    pass

@method_decorator(name='post', decorator=swagger_auto_schema(tags=["Access Control"]))
class RBACTokenVerifyView(TokenVerifyView):
    pass

@swagger_auto_schema(tags=["Access Control"], request_body=EnterpriseUserCreateSerializer)
class EnterpriseUserCreateView(generics.CreateAPIView):
    """
    Enterprise-grade User Creation Flow.
    Supports primary role, extra roles, and permission overrides in one atomic transaction.
    """
    serializer_class = EnterpriseUserCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUserCustom]
