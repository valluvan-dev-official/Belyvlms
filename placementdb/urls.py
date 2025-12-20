from django.urls import path
from .views import placement_list, update_placement, pending_resumes_list, update_interview, delete_placement
from rbac.decorators import rbac_required

app_name = 'placementdb'

urlpatterns = [
    path('', placement_list, name='placement_list'),
    path('<int:pk>/update/', update_placement, name='update_placement'),
    path('interview/<int:pk>/update/', update_interview, name='update_interview'),
    path('pending-resumes/', pending_resumes_list, name='pending_resumes_list'),
    path('<int:pk>/delete/', delete_placement, name='delete_placement'),

    # --- Enterprise RBAC Routes (Secure Zone) ---
    path('secure/list/', rbac_required('PLACEMENT_VIEW')(placement_list), name='rbac_placement_list'),
    path('secure/<int:pk>/update/', rbac_required('PLACEMENT_UPDATE')(update_placement), name='rbac_update_placement'),
    path('secure/interview/<int:pk>/update/', rbac_required('PLACEMENT_DRIVE_MANAGE')(update_interview), name='rbac_update_interview'),
    path('secure/<int:pk>/delete/', rbac_required('PLACEMENT_UPDATE')(delete_placement), name='rbac_delete_placement'),
]
