from django.urls import path
from .api_views import RoleProfileConfigListView, OnboardingView

urlpatterns = [
    path('configs/', RoleProfileConfigListView.as_view(), name='profile-configs'),
    path('onboard/', OnboardingView.as_view(), name='user-onboard'),
]
