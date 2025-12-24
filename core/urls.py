from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import home

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
# from access_control.views import RBACTokenObtainPairView, RBACTokenRefreshView, RBACTokenVerifyView

schema_view = get_schema_view(
    openapi.Info(
        title = "Belyvlms API",
        default_version = 'v1',
        description = "API for Belyvlms App",
        contact = openapi.Contact(email = "support@example.com")
    ),
    public = True,
    permission_classes = [permissions.AllowAny],
    # url="https://dissimilar-madyson-uncriticisably.ngrok-free.dev",
)

urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')), 
    path('students/', include('studentsdb.urls')),
    path('placements/', include('placementdb.urls')),
    path('batches/', include('batchdb.urls')),
    path('trainers/', include('trainersdb.urls')),
    path('consultants/', include('consultantdb.urls')),
    path('settings/', include('settingsdb.urls')),
    path('payments/', include('paymentdb.urls')),
    path('coursedb/', include('coursedb.urls')),
    path('placement-drive/', include('placementdrive.urls')),
    path('api/', include('coursedb.api_urls')),
    path('api/', include('batchdb.api_urls')),
    path('api/', include('trainersdb.api_urls')),

    path('api/', include('tempDb.urls')),
    path('api/', include('accounts.api_urls')),
    path('api/rbac/', include('rbac.api_urls')),
    path('api/profiles/', include('profiles.api_urls')),
    # path('api/rbac/', include('access_control.urls')),
    # path('api/auth/login/', RBACTokenObtainPairView.as_view(), name='token_obtain_pair'),
    # path('api/auth/login/refresh/', RBACTokenRefreshView.as_view(), name='token_refresh'),
    # path('api/auth/login/verify/', RBACTokenVerifyView.as_view(), name='token_verify'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'core.views.custom_404'
