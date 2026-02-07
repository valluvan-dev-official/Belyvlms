from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    RoleProfileConfigViewSet, 
    ProfileFieldDefinitionViewSet, 
    OnboardingView, 
    UserViewSet, 
    MyProfileView,
    AvailableProfileModelsView
)

router = DefaultRouter()
router.register(r'configs', RoleProfileConfigViewSet, basename='role-profile-config')
router.register(r'fields', ProfileFieldDefinitionViewSet, basename='profile-field-definition')
router.register(r'users', UserViewSet, basename='user-management')

urlpatterns = [
    path('', include(router.urls)),
    path('onboard/', OnboardingView.as_view(), name='onboard-user'),
    path('me/', MyProfileView.as_view(), name='my-profile'),
    path('utils/models/', AvailableProfileModelsView.as_view(), name='available-models'),
]
