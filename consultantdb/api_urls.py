from django.urls import path
from .api_views import ConsultantListAPIView

urlpatterns = [
    path('consultants/', ConsultantListAPIView.as_view(), name='api_consultant_list'),
]
