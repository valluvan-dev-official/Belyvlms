from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    RoleViewSet, 
    PermissionViewSet, 
    RolePermissionView,
    UserRoleAssignmentView
)

router = DefaultRouter()
router.register(r'roles', RoleViewSet, basename='rbac-roles')
router.register(r'permissions', PermissionViewSet, basename='rbac-permissions')

urlpatterns = [
    path('', include(router.urls)),
    path('role-permissions/', RolePermissionView.as_view(), name='rbac-role-permissions'),
    path('assign-role/', UserRoleAssignmentView.as_view(), name='rbac-assign-role'),
]
