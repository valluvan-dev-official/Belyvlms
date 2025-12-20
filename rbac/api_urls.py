from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from .api_views import (
    RoleViewSet, 
    PermissionViewSet, 
    RolePermissionView,
    UserRoleAssignmentView,
    RBACTokenObtainPairView,
    LogoutView,
    UserPermissionsView
)

router = DefaultRouter()
router.register(r'roles', RoleViewSet, basename='rbac-roles')
router.register(r'permissions', PermissionViewSet, basename='rbac-permissions')

urlpatterns = [
    path('', include(router.urls)),
    path('role-permissions/', RolePermissionView.as_view(), name='rbac-role-permissions'),
    path('assign-role/', UserRoleAssignmentView.as_view(), name='rbac-assign-role'),
    
    # Auth Endpoints
    path('auth/login/', RBACTokenObtainPairView.as_view(), name='rbac-login'),
    path('auth/me/', UserPermissionsView.as_view(), name='rbac-me'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('auth/logout/', LogoutView.as_view(), name='rbac-logout'),
]
