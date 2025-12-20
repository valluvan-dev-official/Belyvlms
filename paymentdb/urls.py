from django.urls import path
from . import views
from rbac.decorators import rbac_required

urlpatterns = [
    path('', views.payment_list, name='payment_list'),
    path('<str:payment_id>/update/', views.payment_update, name='payment_update'),
    path('<str:payment_id>/update_emi_date/', views.update_emi_date, name='update_emi_date'),
    path('api/payment-details/<str:student_id>/', views.get_payment_details, name='get_payment_details'),

    # --- Enterprise RBAC Routes (Secure Zone) ---
    path('secure/list/', rbac_required('PAYMENT_VIEW')(views.payment_list), name='rbac_payment_list'),
    path('secure/<str:payment_id>/update/', rbac_required('PAYMENT_APPROVE')(views.payment_update), name='rbac_payment_update'),
]
