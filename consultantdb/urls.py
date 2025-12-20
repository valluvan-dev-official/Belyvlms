from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import ConsultantProfileUpdateView
from django.urls import reverse_lazy
from rbac.decorators import rbac_required

urlpatterns = [
    path('', views.consultant_list, name='consultant_list'),
    path('create/', views.create_consultant, name='create_consultant'),
    path('update/<int:pk>/', views.update_consultant, name='update_consultant'),
    path('delete/<int:pk>/', views.delete_consultant, name='delete_consultant'),
    path('delete-all/', views.delete_all_consultants, name='delete_all_consultants'),
    path('profile/', ConsultantProfileUpdateView.as_view(), name='consultant_profile'),

    # --- Enterprise RBAC Routes (Secure Zone) ---
    path('secure/list/', rbac_required('CONSULTANT_VIEW')(views.consultant_list), name='rbac_consultant_list'),
    path('secure/create/', rbac_required('CONSULTANT_CREATE')(views.create_consultant), name='rbac_create_consultant'),
    path('secure/update/<int:pk>/', rbac_required('CONSULTANT_CREATE')(views.update_consultant), name='rbac_update_consultant'),
    path('secure/delete/<int:pk>/', rbac_required('CONSULTANT_CREATE')(views.delete_consultant), name='rbac_delete_consultant'),
]
