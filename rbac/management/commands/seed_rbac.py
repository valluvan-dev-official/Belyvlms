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
        rbac_perms = Permission.objects.filter(code__startswith='RBAC_')
        
        for perm in rbac_perms:
            RolePermission.objects.get_or_create(role=admin_role, permission=perm)
        
        self.stdout.write("Assigned RBAC Permissions to ADMIN Role")

        self.stdout.write(self.style.SUCCESS('Successfully seeded FULL Project RBAC data!'))
