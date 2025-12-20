from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import TrainerViewSet

router = DefaultRouter()
router.register(r'trainers', TrainerViewSet, basename='trainers')

urlpatterns = [
    path('', include(router.urls)),
]
