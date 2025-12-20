from django.urls import path
from .views import trainer_list, create_trainer, update_trainer, delete_trainer, delete_all_trainers
from rbac.decorators import rbac_required

urlpatterns = [
    # --- Standard Routes ---
    path('', trainer_list, name='trainer_list'),
    path('create/', create_trainer, name='create_trainer'),
    path('update/<int:pk>/', update_trainer, name='update_trainer'),
    path('delete/<int:pk>/', delete_trainer, name='delete_trainer'),
    path('delete-all/', delete_all_trainers, name='delete_all_trainers'),

    # --- Enterprise RBAC Routes (Secure Zone) ---
    path('secure/list/', rbac_required('TRAINER_VIEW')(trainer_list), name='rbac_trainer_list'),
    path('secure/create/', rbac_required('TRAINER_CREATE')(create_trainer), name='rbac_create_trainer'),
    path('secure/update/<int:pk>/', rbac_required('TRAINER_UPDATE')(update_trainer), name='rbac_update_trainer'),
    path('secure/delete/<int:pk>/', rbac_required('TRAINER_UPDATE')(delete_trainer), name='rbac_delete_trainer'),
]
