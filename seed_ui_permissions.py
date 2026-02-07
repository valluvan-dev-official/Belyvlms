
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from rbac.models import Permission

required_perms = {
    'VIEW_ACCESS_CONTROL': {'name': 'View Access Control Sidebar', 'module': 'RBAC UI'},
    'VIEW_MATRIX': {'name': 'View Permission Matrix Tab', 'module': 'RBAC UI'},
    'VIEW_ROLE_MANAGEMENT': {'name': 'View Role Management Tab', 'module': 'RBAC UI'},
    'VIEW_PERMISSION_LIBRARY': {'name': 'View Permission Library Tab', 'module': 'RBAC UI'},
    'MANAGE_ROLES': {'name': 'Manage Roles (Create/Edit)', 'module': 'RBAC UI'},
}

def check_and_seed():
    print("--- Checking Permissions ---")
    for code, defaults in required_perms.items():
        obj, created = Permission.objects.get_or_create(
            code=code,
            defaults=defaults
        )
        if created:
            print(f"[CREATED] {code}")
        else:
            print(f"[EXISTS]  {code}")

if __name__ == "__main__":
    check_and_seed()
