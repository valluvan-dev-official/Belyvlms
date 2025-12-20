from django.urls import path
from .views import (
    create_student,
    student_list,
    update_student,
    delete_student,
    download_student_template,
    import_students,
    download_error_report,
    delete_all_students,
    student_report,
)
from rbac.decorators import rbac_required

urlpatterns = [
    # --- Standard Routes (Unchanged) ---
    path('', student_list, name='student_list'),
    path('create/', create_student, name='create_student'),
    path('<str:student_id>/update/', update_student, name='update_student'),
    path('<str:student_id>/delete/', delete_student, name='delete_student'),
    path('import/', import_students, name='import_students'),
    path('template/', download_student_template, name='download_student_template'),
    path('error-report/', download_error_report, name='download_error_report'),
    path('<str:student_id>/report/', student_report, name='student_report'),
    path('delete-all/', delete_all_students, name='delete_all_students'),

    # --- Enterprise RBAC Routes (Secure Zone) ---
    # These URLs are protected by the dynamic Permission System
    path('secure/list/', rbac_required('STUDENT_VIEW')(student_list), name='rbac_student_list'),
    path('secure/create/', rbac_required('STUDENT_CREATE')(create_student), name='rbac_create_student'),
    path('secure/<str:student_id>/update/', rbac_required('STUDENT_UPDATE')(update_student), name='rbac_update_student'),
    path('secure/<str:student_id>/delete/', rbac_required('STUDENT_DELETE')(delete_student), name='rbac_delete_student'),
]
