import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from rbac.models import Role, RolePermission
from django.core.cache import cache

def verify():
    try:
        sa_role = Role.objects.get(code="SA")
        perms = RolePermission.objects.filter(role=sa_role).values_list('permission__code', flat=True)
        print(f"SA Role Permissions in DB: {list(perms)}")
        
        # Check Cache
        cache_key = f"rbac_role_perms_SA"
        cached = cache.get(cache_key)
        print(f"Cached Permissions for SA: {cached}")
        
        if "AUDIT_LOG_VIEW" in perms:
            print("SUCCESS: AUDIT_LOG_VIEW is assigned to SA.")
        else:
            print("FAILURE: AUDIT_LOG_VIEW is NOT assigned to SA.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify()
