import os
import django
import sys

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from rbac.models import Permission, Role, RolePermission
from django.db import transaction

def migrate_permissions():
    print("--- STARTING PERMISSION MIGRATION ---")
    
    # 1. Get Canonical Permission
    target_code = "STUDENT_MANAGEMENT_VIEW"
    try:
        canonical_perm = Permission.objects.get(code=target_code)
        print(f"Found Canonical Permission: {canonical_perm.code}")
    except Permission.DoesNotExist:
        print(f"ERROR: Canonical permission {target_code} not found! Aborting.")
        return

    # 2. Assign to Required Roles (Admin, Trainer)
    # Business Logic: Admin and Trainer need to view students
    target_roles = ["Admin", "Trainer"]
    
    with transaction.atomic():
        for role_name in target_roles:
            try:
                role = Role.objects.get(name=role_name)
                rp, created = RolePermission.objects.get_or_create(
                    role=role,
                    permission=canonical_perm
                )
                if created:
                    print(f"ASSIGNED: {canonical_perm.code} -> {role.name} ({role.code})")
                else:
                    print(f"EXISTING: {canonical_perm.code} -> {role.name} ({role.code})")
            except Role.DoesNotExist:
                print(f"WARNING: Role '{role_name}' not found.")

        # 3. Mark Legacy Permission as Deprecated
        legacy_code = "STUDENT_VIEW"
        try:
            legacy_perm = Permission.objects.get(code=legacy_code)
            if not legacy_perm.name.startswith("[DEPRECATED]"):
                legacy_perm.name = f"[DEPRECATED] {legacy_perm.name}"
                legacy_perm.description = f"DEPRECATED. Use {target_code} instead. {legacy_perm.description}"
                legacy_perm.save()
                print(f"DEPRECATED: Marked {legacy_code} as deprecated.")
            else:
                print(f"SKIPPED: {legacy_code} already marked deprecated.")
        except Permission.DoesNotExist:
            print(f"INFO: Legacy permission {legacy_code} not found (Clean).")

    print("--- MIGRATION COMPLETE ---")

if __name__ == "__main__":
    migrate_permissions()
