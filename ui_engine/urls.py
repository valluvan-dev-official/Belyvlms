from django.urls import path
from .api_views import UIConfigView

urlpatterns = [
    path('config/', UIConfigView.as_view(), name='ui-config'),
]
