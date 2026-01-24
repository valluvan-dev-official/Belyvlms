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
        # Format: (Code, Name)
        roles_data = [
            ('ADM', 'Admin'),                 # Changed from ADMIN
            ('SAM', 'Super Admin'),           # New Role
            ('STF', 'Staff'),                 # Changed from STAFF
            ('TRN', 'Trainer'),               
            ('BTR', 'Student'),               
            ('PLO', 'Placement Officer'),     # Changed from PLACEMENT_OFFICER
            ('BTC', 'Batch Coordinator'),     # Changed from BATCH_COORDINATOR
            ('CON', 'Consultant')             
        ]
        
        self.stdout.write("Seeding Roles...")
        for role_code, role_name in roles_data:
            r, created = Role.objects.get_or_create(
                name=role_name,  # Match by Name first to avoid duplicates if code changed
                defaults={'code': role_code}
            )
            
            # If role exists but code is old (e.g. ADMIN -> ADM), update it
            if not created and r.code != role_code:
                self.stdout.write(f"Updating Role Code for {role_name}: {r.code} -> {role_code}")
                r.code = role_code
                r.save()

            if created:
                self.stdout.write(f"Created Role: {role_name} ({role_code})")

        # 3. Assign RBAC Permissions to ADMIN Role (Bootstrap)
        # Note: We use ADM now
        admin_role = Role.objects.get(code='ADM')
        
        # 3a. Assign ALL Permissions to SUPER ADMIN (SAM)
        # Super Admin should have everything by default or at least critical access
        super_admin_role, _ = Role.objects.get_or_create(name='Super Admin', defaults={'code': 'SAM'})
        
        # Assign ALL permissions to Super Admin
        all_perms = Permission.objects.all()
        for perm in all_perms:
            RolePermission.objects.get_or_create(role=super_admin_role, permission=perm)
            
        # 3b. AUTOMATICALLY ASSIGN SUPERUSERS TO SAM ROLE
        # Find all users with is_superuser=True and ensure they are assigned to SAM
        from django.contrib.auth import get_user_model
        from rbac.models import UserRole
        User = get_user_model()
        
        superusers = User.objects.filter(is_superuser=True)
        for su in superusers:
            # Check if they have a role, if so, update it to SAM, or create new
            ur, created = UserRole.objects.get_or_create(user=su, defaults={'role': super_admin_role})
            
            if not created and ur.role != super_admin_role:
                self.stdout.write(f"Migrating Superuser {su.email} from {ur.role.code} to SAM")
                ur.role = super_admin_role
                ur.save()
            elif created:
                self.stdout.write(f"Assigned Superuser {su.email} to SAM Role")

        # Assign RBAC_, USER_ONBOARD, and PROFILE_ permissions to ADMIN (ADM)
        admin_perms = Permission.objects.filter(
            code__regex=r'^(RBAC_|USER_ONBOARD|PROFILE_)'
        )
        
        for perm in admin_perms:
            RolePermission.objects.get_or_create(role=admin_role, permission=perm)
        
        self.stdout.write("Assigned Admin Permissions to ADM & SAM Roles")

        # 4. Assign Permissions to STUDENT Role
        student_role = Role.objects.get(code='BTR')
        student_perms = Permission.objects.filter(code__in=[
            'COURSE_VIEW', 
            'PROFILE_CONFIG_VIEW',
        ])
        for perm in student_perms:
            RolePermission.objects.get_or_create(role=student_role, permission=perm)
        self.stdout.write("Assigned Permissions to STUDENT Role")
            
        # 5. Assign Permissions to TRAINER Role
        trainer_role = Role.objects.get(code='TRN')
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
        po_role = Role.objects.get(code='PLO')
        po_perms = Permission.objects.filter(code__in=[
            'PLACEMENT_VIEW', 'PLACEMENT_CREATE', 'PLACEMENT_UPDATE', 'PLACEMENT_DRIVE_MANAGE',
            'STUDENT_VIEW', 'PROFILE_CONFIG_VIEW'
        ])
        for perm in po_perms:
            RolePermission.objects.get_or_create(role=po_role, permission=perm)
        self.stdout.write("Assigned Permissions to PLACEMENT_OFFICER Role")

        # 7. Assign Permissions to BATCH_COORDINATOR Role
        bc_role = Role.objects.get(code='BTC')
        bc_perms = Permission.objects.filter(code__in=[
            'BATCH_VIEW', 'BATCH_CREATE', 'BATCH_UPDATE', 'BATCH_ASSIGN',
            'TRAINER_VIEW', 'STUDENT_VIEW', 'COURSE_VIEW', 'PROFILE_CONFIG_VIEW'
        ])
        for perm in bc_perms:
            RolePermission.objects.get_or_create(role=bc_role, permission=perm)
        self.stdout.write("Assigned Permissions to BATCH_COORDINATOR Role")

        # 8. Assign Permissions to STAFF Role (General Staff)
        staff_role = Role.objects.get(code='STF')
        staff_perms = Permission.objects.filter(code__in=[
            'USER_VIEW', 'STUDENT_VIEW', 'TRAINER_VIEW', 'BATCH_VIEW', 'COURSE_VIEW', 'PLACEMENT_VIEW', 'PAYMENT_VIEW', 'CONSULTANT_VIEW',
            'PROFILE_CONFIG_VIEW'
        ])
        for perm in staff_perms:
            RolePermission.objects.get_or_create(role=staff_role, permission=perm)
        self.stdout.write("Assigned Permissions to STAFF Role")

        self.stdout.write(self.style.SUCCESS('Successfully seeded FULL Project RBAC data!'))
