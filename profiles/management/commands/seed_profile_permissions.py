from django.core.management.base import BaseCommand
from rbac.models import Permission, Role, RolePermission

class Command(BaseCommand):
    help = 'Seeds initial permissions for Profile Management and assigns to Admin'

    def handle(self, *args, **options):
        permissions_data = [
            {
                'code': 'PROFILE_CONFIG_VIEW',
                'name': 'View Profile Configuration',
                'module': 'Profile Management'
            },
            {
                'code': 'PROFILE_CONFIG_MANAGE',
                'name': 'Manage Profile Configuration',
                'module': 'Profile Management'
            },
            {
                'code': 'USER_ONBOARD',
                'name': 'Onboard New Users',
                'module': 'User Management'
            },
            {
                'code': 'USER_VIEW',
                'name': 'View Users',
                'module': 'User Management'
            },
            {
                'code': 'USER_MANAGE',
                'name': 'Manage Users (Update/Delete)',
                'module': 'User Management'
            }
        ]

        created_count = 0
        perms_objs = []
        
        for perm_data in permissions_data:
            permission, created = Permission.objects.get_or_create(
                code=perm_data['code'],
                defaults={
                    'name': perm_data['name'],
                    'module': perm_data['module']
                }
            )
            perms_objs.append(permission)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created permission: {permission}"))
                created_count += 1
            else:
                self.stdout.write(f"Permission already exists: {permission}")

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {created_count} new permissions."))
        
        # Assign to Admin Role
        try:
            # Try to find common Admin role names
            admin_role = Role.objects.filter(name__in=['Admin', 'Administrator', 'Super Admin']).first()
            if admin_role:
                for perm in perms_objs:
                    RolePermission.objects.get_or_create(role=admin_role, permission=perm)
                self.stdout.write(self.style.SUCCESS(f"Assigned permissions to role: {admin_role.name}"))
            else:
                self.stdout.write(self.style.WARNING("No Admin role found. Permissions created but not assigned."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error assigning to role: {e}"))
