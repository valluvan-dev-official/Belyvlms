from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import TrainerViewSet, trainers_by_course

router = DefaultRouter()
router.register(r'trainers', TrainerViewSet, basename='trainers')

urlpatterns = [
    path('', include(router.urls)),
    path('trainers-by-course/<int:course_id>/', trainers_by_course, name='trainers_by_course'),
]
