from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import RoleProfileConfigViewSet, ProfileFieldDefinitionViewSet, OnboardingView, UserViewSet, GenericProfileView

router = DefaultRouter()
router.register(r'configs', RoleProfileConfigViewSet, basename='profile-config')
router.register(r'fields', ProfileFieldDefinitionViewSet, basename='profile-field')
router.register(r'users', UserViewSet, basename='profile-user')

urlpatterns = [
    path('onboard/', OnboardingView.as_view(), name='user-onboard'),
    path('me/', GenericProfileView.as_view(), name='generic-profile-me'),
    path('', include(router.urls)),
]
