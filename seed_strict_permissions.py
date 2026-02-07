import os
import django
from django.conf import settings

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from rbac.models import Permission, Role, RolePermission
from django.db import transaction

def seed_permissions():
    print("Seeding Strict Permissions...")
    with open('seed_log.txt', 'w') as f:
        f.write("Seeding Strict Permissions...\n")

    # Define the STRICT permission list
    # Format: CODE: (Name, Module, Description)
    permissions_map = {
        # Permission Library (Granular)
        'PERMISSION_LIBRARY_VIEW': ('View Library', 'Permission Library', 'View all defined permissions in the system'),
        'PERMISSION_LIBRARY_CREATE': ('Create Permission', 'Permission Library', 'Create new permission codes'),
        'PERMISSION_LIBRARY_UPDATE': ('Update Permission', 'Permission Library', 'Modify existing permission details'),
        'PERMISSION_LIBRARY_DELETE': ('Delete Permission', 'Permission Library', 'Remove permissions from the system'),

        # Access Control Module (Matrix & Role Management)
        'ACCESS_CONTROL_MATRIX_VIEW': ('View Matrix', 'Access Control', 'View the Role-Permission matrix'),
        'ACCESS_CONTROL_MATRIX_EDIT': ('Edit Matrix', 'Access Control', 'Modify Role-Permission assignments'),
        
        'ROLE_VIEW': ('View Roles', 'Access Control', 'View defined roles'),
        'ROLE_CREATE': ('Create Role', 'Access Control', 'Create new roles'),
        'ROLE_UPDATE': ('Update Role', 'Access Control', 'Modify existing roles'),
        'ROLE_DELETE': ('Delete Role', 'Access Control', 'Remove roles from the system'),

        # User Management
        'USER_MANAGEMENT_VIEW': ('View Users', 'User Management', 'View user list and details'),
        'USER_MANAGEMENT_CREATE': ('Create Users', 'User Management', 'Create new user accounts'),
        'USER_MANAGEMENT_EDIT': ('Edit Users', 'User Management', 'Modify user details'),
        'USER_MANAGEMENT_DELETE': ('Delete Users', 'User Management', 'Deactivate or remove users'),
        'USER_MANAGEMENT_EXPORT': ('Export Users', 'User Management', 'Export user data to file'),
        'USER_MANAGEMENT_ASSIGN_ROLE': ('Assign Role', 'User Management', 'Assign roles to users'),

        # Student Management
        'STUDENT_MANAGEMENT_VIEW': ('View Students', 'Student Management', 'View student list'),
        'STUDENT_MANAGEMENT_PROFILE_VIEW': ('View Student Profiles', 'Student Management', 'View detailed student profiles'),
        'STUDENT_MANAGEMENT_STATS_VIEW': ('View Student Stats', 'Student Management', 'View student statistics'),
        'STUDENT_MANAGEMENT_EXPORT': ('Export Students', 'Student Management', 'Export student data'),

        # Trainer Management
        'TRAINER_MANAGEMENT_VIEW': ('View Trainers', 'Trainer Management', 'View trainer list and details'),
        'TRAINER_MANAGEMENT_APPROVE': ('Approve Trainer', 'Trainer Management', 'Approve trainer onboarding'),
        'TRAINER_MANAGEMENT_REJECT': ('Reject Trainer', 'Trainer Management', 'Reject trainer onboarding'),

        # Dashboard
        'DASHBOARD_VIEW_GLOBAL': ('View Dashboard', 'Dashboard', 'Access global dashboard metrics'),
        'DASHBOARD_WIDGET_GROWTH_VIEW': ('View Growth Trends Widget', 'Dashboard', 'Allows viewing the Growth Trends chart on the dashboard'),

        # Profile Configuration (Dynamic Profiles)
        'PROFILE_CONFIG_VIEW': ('View Profile Config', 'Profile Config', 'View role profile configurations'),
        'PROFILE_CONFIG_MANAGE': ('Manage Profile Config', 'Profile Config', 'Manage role profile configurations'),
    }

    created_count = 0
    updated_count = 0

    with transaction.atomic():
        with open('seed_log.txt', 'a') as f:
            for code, (name, module, description) in permissions_map.items():
                perm, created = Permission.objects.get_or_create(code=code)
                
                # Update name/module/description if changed or new
                if created or perm.name != name or perm.module != module or perm.description != description:
                    perm.name = name
                    perm.module = module
                    perm.description = description
                    perm.save()
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                    f.write(f"{'Created' if created else 'Updated'}: {code}\n")
                    print(f"{'Created' if created else 'Updated'}: {code}")
    
    with open('seed_log.txt', 'a') as f:
        f.write(f"Finished. Created: {created_count}, Updated: {updated_count}\n")

    # Assign all permissions to Super Admin (SAM)
    try:
        sa_role = Role.objects.get(code='SAM')
        with open('seed_log.txt', 'a') as f:
            f.write(f"Assigning all permissions to {sa_role.name}...\n")
        
        current_perms = set(sa_role.role_permissions.values_list('permission__code', flat=True))
        
        new_assignments = []
        for code in permissions_map.keys():
            if code not in current_perms:
                perm = Permission.objects.get(code=code)
                new_assignments.append(RolePermission(role=sa_role, permission=perm))
        
        with open('seed_log.txt', 'a') as f:
            if new_assignments:
                RolePermission.objects.bulk_create(new_assignments)
                f.write(f"Assigned {len(new_assignments)} new permissions to SA.\n")
                print(f"Assigned {len(new_assignments)} new permissions to SA.")
            else:
                f.write("SA already has all permissions.\n")
                print("SA already has all permissions.")

        # STRICT MODE: REVOKE ALL PERMISSIONS FROM NON-ADMIN ROLES
        # This ensures no "Ghost Permissions" exist for Students/Trainers
        other_roles = Role.objects.exclude(code__in=['SAM', 'ADM'])
        for role in other_roles:
            count = role.role_permissions.count()
            if count > 0:
                with open('seed_log.txt', 'a') as f:
                    f.write(f"Revoking {count} stale permissions from {role.name} ({role.code})...\n")
                    print(f"Revoking {count} stale permissions from {role.name} ({role.code})...")
                role.role_permissions.all().delete()
            
    except Role.DoesNotExist:
        with open('seed_log.txt', 'a') as f:
            f.write("Role 'SA' not found. Skipping assignment.\n")
            print("Role 'SA' not found. Skipping assignment.")

if __name__ == '__main__':
    seed_permissions()
