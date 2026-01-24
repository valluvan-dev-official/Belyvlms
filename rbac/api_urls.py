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
    UserPermissionsView,
    SwitchRoleView,
    RoleImpactSummaryView,
    RoleDeactivateView,
    UserCreateView,
    UserListView,
    OnboardingDropdownsView,
    OnboardRequestCreateView,
    OnboardRequestListView,
    OnboardRequestDetailView,
    OnboardRequestOnboardView,
    OnboardRequestActionView,
    PublicOnboardRequestSchemaView,
    PublicOnboardRequestSubmitView,
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
    path('auth/switch-role/', SwitchRoleView.as_view(), name='rbac-switch-role'),
    path('auth/me/', UserPermissionsView.as_view(), name='rbac-me'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('auth/logout/', LogoutView.as_view(), name='rbac-logout'),
    
    # Role Ops
    path('roles/<int:pk>/impact/', RoleImpactSummaryView.as_view(), name='rbac-role-impact'),
    path('roles/<int:pk>/deactivate/', RoleDeactivateView.as_view(), name='rbac-role-deactivate'),
    path('users/', UserListView.as_view(), name='rbac-user-list'),
    path('users/create/', UserCreateView.as_view(), name='rbac-user-create'),
    path('onboarding/options/', OnboardingDropdownsView.as_view(), name='onboarding_options'),
    path('onboard-requests/', OnboardRequestListView.as_view(), name='onboard-request-list'),
    path('onboard-requests/create/', OnboardRequestCreateView.as_view(), name='onboard-request-create'),
    path('onboard-requests/<str:code>/', OnboardRequestDetailView.as_view(), name='onboard-request-detail'),
    path('onboard-requests/<str:code>/onboard/', OnboardRequestOnboardView.as_view(), name='onboard-request-onboard'),
    path('onboard-requests/<str:code>/action/', OnboardRequestActionView.as_view(), name='onboard-request-action'),
    path('public/onboard/schema/', PublicOnboardRequestSchemaView.as_view(), name='public-onboard-schema'),
    path('public/onboard/submit/', PublicOnboardRequestSubmitView.as_view(), name='public-onboard-submit'),
]
