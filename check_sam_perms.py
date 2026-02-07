import os
import django
import sys

print("Starting check...", flush=True)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
try:
    django.setup()
    print("Django setup complete.", flush=True)
except Exception as e:
    print(f"Django setup failed: {e}", flush=True)
    sys.exit(1)

from rbac.models import Role, RolePermission, Permission

try:
    sam_role = Role.objects.get(code='SAM')
    perm_count = RolePermission.objects.filter(role=sam_role).count()
    total_perms = Permission.objects.count()
    print(f"SAM Role exists. Permission Count: {perm_count} / {total_perms}", flush=True)
    
    if perm_count == 0:
        print("WARNING: SAM has 0 permissions!", flush=True)
    
    # List first 5 to verify
    perms = RolePermission.objects.filter(role=sam_role)[:5]
    for p in perms:
        print(f"- {p.permission.code}", flush=True)

except Role.DoesNotExist:
    print("SAM Role not found!", flush=True)
