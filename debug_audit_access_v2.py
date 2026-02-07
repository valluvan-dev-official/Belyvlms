import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from rbac.models import UserRole, Role, RolePermission
from rest_framework.test import APIClient

User = get_user_model()

def debug_access():
    with open("debug_audit_result_v2.txt", "w") as f:
        f.write("--- Debugging Access ---\n")
        # 1. Get a Super Admin User
        user = User.objects.filter(role='admin').first()
        if not user:
            f.write("No user with role='admin' found.\n")
            return

        f.write(f"Testing with User: {user.email} (ID: {user.id})\n")

        # 2. Check UserRole Entry
        try:
            sa_role = Role.objects.get(code='SA')
            ur = UserRole.objects.filter(user=user, role=sa_role).first()
            if ur:
                f.write(f"UserRole found: User {user.email} <-> Role {ur.role.code}\n")
            else:
                f.write(f"CRITICAL: No UserRole found for user {user.email} and role SA!\n")
                roles = UserRole.objects.filter(user=user)
                f.write(f"User has these roles in UserRole table: {[r.role.code for r in roles]}\n")
                
                # AUTO-FIX: Assign SA role if missing
                f.write("Attempting AUTO-FIX: Creating UserRole SA for user...\n")
                UserRole.objects.create(user=user, role=sa_role)
                f.write("UserRole SA created.\n")
                
        except Role.DoesNotExist:
            f.write("Role 'SA' does not exist in DB.\n")
            return

        # 3. Check Permissions for SA Role
        perms = RolePermission.objects.filter(role__code='SA', permission__code='AUDIT_LOG_VIEW')
        if perms.exists():
            f.write("Permission AUDIT_LOG_VIEW is assigned to SA role.\n")
        else:
            f.write("Permission AUDIT_LOG_VIEW is NOT assigned to SA role.\n")

        # 4. Simulate API Request
        client = APIClient()
        client.force_authenticate(user=user)
        
        f.write("\n--- API Request Simulation ---\n")
        try:
            # We assume the user wants to use SA role context
            # If the backend requires a header, we might fail without it.
            # But normally default is fine.
            response = client.get('/api/audit/logs/')
            f.write(f"Status Code: {response.status_code}\n")
            if response.status_code != 200:
                f.write(f"Response: {response.data}\n")
            else:
                f.write("Access Granted (200 OK)\n")
        except Exception as e:
            f.write(f"API Request Failed with error: {e}\n")

if __name__ == "__main__":
    debug_access()
