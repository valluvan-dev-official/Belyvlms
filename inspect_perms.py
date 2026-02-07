
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from rbac.models import Role, Permission, RolePermission

def inspect_student_permissions():
    try:
        student_role = Role.objects.get(code='BTR')
        print(f"Role: {student_role.name} ({student_role.code})")
        
        perms = RolePermission.objects.filter(role=student_role).select_related('permission')
        print(f"Assigned Permissions ({perms.count()}):")
        for rp in perms:
            print(f" - {rp.permission.code} (Name: {rp.permission.name})")
            
    except Role.DoesNotExist:
        print("Role BTR not found")

if __name__ == '__main__':
    inspect_student_permissions()
