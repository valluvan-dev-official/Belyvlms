from django.core.management.base import BaseCommand
from rbac.models import Permission, Role, RolePermission

class Command(BaseCommand):
    help = 'Seeds initial RBAC Permissions and Roles based on Project Structure'

    def handle(self, *args, **options):
        # 1. Define Standard Permissions
        # I analyzed your project folders: 
        # studentsdb, trainersdb, batchdb, coursedb, placementdb, paymentdb, consultantdb
        
        permissions = [
            # User Management (accounts)
            ('USER_VIEW', 'View Users', 'Users'),
            ('USER_CREATE', 'Create Users', 'Users'),
            ('USER_UPDATE', 'Update Users', 'Users'),
            ('USER_DELETE', 'Delete Users', 'Users'),
            
            # Student Management (studentsdb)
            ('STUDENT_VIEW', 'View Students', 'Students'),
            ('STUDENT_CREATE', 'Create Student', 'Students'),
            ('STUDENT_UPDATE', 'Update Student', 'Students'),
            ('STUDENT_DELETE', 'Delete Student', 'Students'),
            
            # Trainer Management (trainersdb)
            ('TRAINER_VIEW', 'View Trainers', 'Trainers'),
            ('TRAINER_CREATE', 'Create Trainer', 'Trainers'),
            ('TRAINER_UPDATE', 'Update Trainer', 'Trainers'),
            ('TRAINER_AVAILABILITY', 'Manage Availability', 'Trainers'),
            
            # Batch Management (batchdb)
            ('BATCH_VIEW', 'View Batches', 'Batches'),
            ('BATCH_CREATE', 'Create Batch', 'Batches'),
            ('BATCH_UPDATE', 'Update Batch', 'Batches'),
            ('BATCH_ASSIGN', 'Assign Trainer to Batch', 'Batches'),
            
            # Course Management (coursedb)
            ('COURSE_VIEW', 'View Courses', 'Courses'),
            ('COURSE_CREATE', 'Create Course', 'Courses'),
            ('COURSE_UPDATE', 'Update Course', 'Courses'),
            ('COURSE_DELETE', 'Delete Course', 'Courses'),

            # Placement Management (placementdb)
            ('PLACEMENT_VIEW', 'View Placements', 'Placements'),
            ('PLACEMENT_CREATE', 'Add Placement Record', 'Placements'),
            ('PLACEMENT_UPDATE', 'Update Placement Record', 'Placements'),
            ('PLACEMENT_DRIVE_MANAGE', 'Manage Placement Drives', 'Placements'),

            # Payment Management (paymentdb)
            ('PAYMENT_VIEW', 'View Payments', 'Payments'),
            ('PAYMENT_CREATE', 'Record Payment', 'Payments'),
            ('PAYMENT_APPROVE', 'Approve Payment', 'Payments'),

            # Consultant Management (consultantdb)
            ('CONSULTANT_VIEW', 'View Consultants', 'Consultants'),
            ('CONSULTANT_CREATE', 'Create Consultant', 'Consultants'),

            # RBAC Management (Core) - CRITICAL FOR ADMIN
            ('RBAC_ROLE_MANAGE', 'Manage Roles', 'RBAC Core'),
            ('RBAC_PERMISSION_MANAGE', 'Manage Permissions', 'RBAC Core'),
            ('RBAC_PERMISSION_ASSIGN', 'Assign Permissions to Roles', 'RBAC Assignments'),

            # Profile & Onboarding
            ('USER_ONBOARD', 'Onboard New User (Trinity)', 'User Management'),
            ('PROFILE_CONFIG_VIEW', 'View Profile Configurations', 'Profile Config'),
            ('PROFILE_CONFIG_MANAGE', 'Manage Profile Configurations', 'Profile Config'),
        ]

        self.stdout.write("Seeding Permissions...")
        for code, name, module in permissions:
            p, created = Permission.objects.get_or_create(
                code=code,
                defaults={'name': name, 'module': module}
            )
            if created:
                self.stdout.write(f"Created: {code}")

        # 2. Define Standard Roles
        # Based on CustomUser.ROLE_CHOICES in accounts/models.py
        roles = [
            'ADMIN', 
            'STAFF', 
            'TRAINER', 
            'STUDENT', 
            'PLACEMENT_OFFICER', 
            'BATCH_COORDINATOR', 
            'CONSULTANT'
        ]
        
        self.stdout.write("Seeding Roles...")
        for role_code in roles:
            r, created = Role.objects.get_or_create(
                code=role_code,
                defaults={'name': role_code.replace('_', ' ').title()}
            )
            if created:
                self.stdout.write(f"Created Role: {role_code}")

        # 3. Assign RBAC Permissions to ADMIN Role (Bootstrap)
        admin_role = Role.objects.get(code='ADMIN')
        
        # Assign RBAC_, USER_ONBOARD, and PROFILE_ permissions to ADMIN
        admin_perms = Permission.objects.filter(
            code__regex=r'^(RBAC_|USER_ONBOARD|PROFILE_)'
        )
        
        for perm in admin_perms:
            RolePermission.objects.get_or_create(role=admin_role, permission=perm)
        
        self.stdout.write("Assigned Admin Permissions to ADMIN Role")

        # 4. Assign Permissions to STUDENT Role
        student_role = Role.objects.get(code='STUDENT')
        student_perms = Permission.objects.filter(code__in=[
            'COURSE_VIEW', 
            'PROFILE_CONFIG_VIEW',
        ])
        for perm in student_perms:
            RolePermission.objects.get_or_create(role=student_role, permission=perm)
        self.stdout.write("Assigned Permissions to STUDENT Role")
            
        # 5. Assign Permissions to TRAINER Role
        trainer_role = Role.objects.get(code='TRAINER')
        trainer_perms = Permission.objects.filter(code__in=[
            'COURSE_VIEW',
            'BATCH_VIEW',
            'TRAINER_AVAILABILITY',
            'PROFILE_CONFIG_VIEW',
        ])
        for perm in trainer_perms:
            RolePermission.objects.get_or_create(role=trainer_role, permission=perm)
        self.stdout.write("Assigned Permissions to TRAINER Role")

        # 6. Assign Permissions to PLACEMENT_OFFICER Role
        po_role = Role.objects.get(code='PLACEMENT_OFFICER')
        po_perms = Permission.objects.filter(code__in=[
            'PLACEMENT_VIEW', 'PLACEMENT_CREATE', 'PLACEMENT_UPDATE', 'PLACEMENT_DRIVE_MANAGE',
            'STUDENT_VIEW', 'PROFILE_CONFIG_VIEW'
        ])
        for perm in po_perms:
            RolePermission.objects.get_or_create(role=po_role, permission=perm)
        self.stdout.write("Assigned Permissions to PLACEMENT_OFFICER Role")

        # 7. Assign Permissions to BATCH_COORDINATOR Role
        bc_role = Role.objects.get(code='BATCH_COORDINATOR')
        bc_perms = Permission.objects.filter(code__in=[
            'BATCH_VIEW', 'BATCH_CREATE', 'BATCH_UPDATE', 'BATCH_ASSIGN',
            'TRAINER_VIEW', 'STUDENT_VIEW', 'COURSE_VIEW', 'PROFILE_CONFIG_VIEW'
        ])
        for perm in bc_perms:
            RolePermission.objects.get_or_create(role=bc_role, permission=perm)
        self.stdout.write("Assigned Permissions to BATCH_COORDINATOR Role")

        # 8. Assign Permissions to STAFF Role (General Staff)
        staff_role = Role.objects.get(code='STAFF')
        staff_perms = Permission.objects.filter(code__in=[
            'USER_VIEW', 'STUDENT_VIEW', 'TRAINER_VIEW', 'BATCH_VIEW', 'COURSE_VIEW', 'PLACEMENT_VIEW', 'PAYMENT_VIEW', 'CONSULTANT_VIEW',
            'PROFILE_CONFIG_VIEW'
        ])
        for perm in staff_perms:
            RolePermission.objects.get_or_create(role=staff_role, permission=perm)
        self.stdout.write("Assigned Permissions to STAFF Role")

        self.stdout.write(self.style.SUCCESS('Successfully seeded FULL Project RBAC data!'))
