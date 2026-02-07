from django.urls import path
from .api_views import SourceOfJoiningListAPIView

urlpatterns = [
    path('sources/', SourceOfJoiningListAPIView.as_view(), name='api_source_list'),
]
