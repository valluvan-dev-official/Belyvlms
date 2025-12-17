from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RoleViewSet, 
    PermissionViewSet, 
    RolePermissionView, 
    CreateUserWithRoleView, 
    UserPermissionsView,
    UserRoleViewSet,
    UserPermissionOverrideViewSet,
    EnterpriseUserCreateView
)

router = DefaultRouter()
router.register(r'roles', RoleViewSet, basename='roles')
router.register(r'permissions', PermissionViewSet, basename='permissions')
router.register(r'user-roles', UserRoleViewSet, basename='user-roles')
router.register(r'user-overrides', UserPermissionOverrideViewSet, basename='user-overrides')

urlpatterns = [
    path('', include(router.urls)),
    path('role-permissions/', RolePermissionView.as_view(), name='role-permissions'),
    path('users/create/', CreateUserWithRoleView.as_view(), name='create-user-with-role'),
    path('users/create-enterprise/', EnterpriseUserCreateView.as_view(), name='create-enterprise-user'),
    path('my-permissions/', UserPermissionsView.as_view(), name='my-permissions'),
]
