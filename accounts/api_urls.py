from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import CustomUserViewSet, LogoutView
from .views import trainer_availability_api, trainers_by_course, trainers_availabity

router = DefaultRouter()
router.register(r'users', CustomUserViewSet, basename='user')

urlpatterns = [
    # Router-managed endpoints for ModelViewSets
    path('', include(router.urls)),

    # Existing function-based JSON endpoints
    path('auth/logout/', LogoutView.as_view(), name='auth_logout'),
    path('trainer-availability/', trainer_availability_api, name='trainer_availability_api'),
    path('trainers-by-course/', trainers_by_course, name='trainers_by_course'),
    path('trainers/availability/', trainers_availabity, name='trainers_availability'),
]
