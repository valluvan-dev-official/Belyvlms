from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from rbac.models import Permission, Role, RolePermission, UserRole


class Command(BaseCommand):
    help = "Post-seed RBAC sync: add missing permissions from provided list, ensure roles, assign all to SAM, map superusers to SAM"

    USER_PROVIDED_CODES = [
        "USER_VIEW", "USER_CREATE", "USER_UPDATE", "USER_DELETE",
        "STUDENT_VIEW", "STUDENT_CREATE", "STUDENT_UPDATE", "STUDENT_DELETE",
        "TRAINER_VIEW", "TRAINER_CREATE", "TRAINER_UPDATE", "TRAINER_AVAILABILITY",
        "BATCH_VIEW", "BATCH_CREATE", "BATCH_UPDATE", "BATCH_DELETE", "BATCH_ASSIGN",
        "COURSE_VIEW", "COURSE_CREATE", "COURSE_UPDATE", "COURSE_DELETE",
        "PLACEMENT_VIEW", "PLACEMENT_CREATE", "PLACEMENT_UPDATE", "PLACEMENT_DRIVE_MANAGE", "PLACEMENT_DELETE",
        "PAYMENT_VIEW", "PAYMENT_CREATE", "PAYMENT_APPROVE",
        "CONSULTANT_VIEW", "CONSULTANT_CREATE",
        "RBAC_ROLE_MANAGE", "RBAC_PERMISSION_MANAGE", "RBAC_PERMISSION_ASSIGN",
        "USER_ONBOARD",
        "PROFILE_CONFIG_VIEW", "PROFILE_CONFIG_MANAGE",
        "VIEW_MATRIX", "VIEW_PERMISSION_LIBRARY",
        "DASHBOARD_VIEW_GLOBAL", "DASHBOARD_WIDGET_GROWTH_VIEW",
        "USER_MANAGEMENT_VIEW", "USER_MANAGEMENT_CREATE", "USER_MANAGEMENT_EDIT", "USER_MANAGEMENT_DELETE", "USER_MANAGEMENT_EXPORT", "USER_MANAGEMENT_ASSIGN_ROLE",
        "STUDENT_MANAGEMENT_VIEW", "STUDENT_MANAGEMENT_PROFILE_VIEW", "STUDENT_MANAGEMENT_STATS_VIEW", "STUDENT_MANAGEMENT_EXPORT",
        "TRAINER_MANAGEMENT_VIEW", "TRAINER_MANAGEMENT_APPROVE", "TRAINER_MANAGEMENT_REJECT",
        "ACCESS_CONTROL_VIEW", "ACCESS_CONTROL_MATRIX_VIEW", "ACCESS_CONTROL_MATRIX_EDIT",
        "ACCESS_CONTROL_ROLE_VIEW", "ACCESS_CONTROL_ROLE_CREATE", "ACCESS_CONTROL_ROLE_DELETE",
        "PERMISSION_LIBRARY_VIEW", "PERMISSION_LIBRARY_CREATE", "PERMISSION_LIBRARY_UPDATE", "PERMISSION_LIBRARY_DELETE",
        "ROLE_VIEW", "ROLE_CREATE", "ROLE_UPDATE", "ROLE_DELETE",
        "AUDIT_LOG_VIEW", "AUDIT_LOG_EXPORT",
    ]

    MODULE_MAP = {
        "USER": "User Management",
        "STUDENT": "Student Management",
        "TRAINER": "Trainer Management",
        "BATCH": "Batch Management",
        "COURSE": "Course Management",
        "PLACEMENT": "Placement Management",
        "PAYMENT": "Payment Management",
        "CONSULTANT": "Consultant Management",
        "RBAC": "RBAC Core",
        "PROFILE_CONFIG": "Profile Config",
        "VIEW": "RBAC UI",
        "DASHBOARD": "Dashboard",
        "ACCESS_CONTROL": "Access Control",
        "PERMISSION_LIBRARY": "Permission Library",
        "ROLE": "Access Control",
        "AUDIT_LOG": "Audit Log",
        "USER_MANAGEMENT": "User Management",
        "STUDENT_MANAGEMENT": "Student Management",
        "TRAINER_MANAGEMENT": "Trainer Management",
    }

    ROLE_DEFS = [
        ("SAM", "Super Admin"),
        ("ADM", "Admin"),
        ("STF", "Staff"),
        ("TRN", "Trainer"),
        ("BTR", "Student"),
        ("CON", "Consultant"),
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--assign-superusers",
            action="store_true",
            default=True,
            help="Assign all is_superuser users to SAM role",
        )

    def _titleize(self, code: str) -> str:
        return code.replace("_", " ").title()

    def _module_for(self, code: str) -> str:
        parts = code.split("_")
        for i in range(len(parts), 0, -1):
            prefix = "_".join(parts[:i])
            if prefix in self.MODULE_MAP:
                return self.MODULE_MAP[prefix]
        return "General"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting post-seed RBAC sync"))

        created_perms = 0
        updated_perms = 0
        for code in self.USER_PROVIDED_CODES:
            perm, created = Permission.objects.get_or_create(code=code)
            name = self._titleize(code)
            module = self._module_for(code)
            if created or perm.name != name or perm.module != module:
                perm.name = name
                perm.module = module
                perm.save()
                if created:
                    created_perms += 1
                else:
                    updated_perms += 1

        self.stdout.write(f"Permissions created: {created_perms}, updated: {updated_perms}")

        role_objs = {}
        for code, name in self.ROLE_DEFS:
            role, _ = Role.objects.get_or_create(code=code, defaults={"name": name, "is_active": True})
            if not role.is_active:
                role.is_active = True
                role.save(update_fields=["is_active"])
            role_objs[code] = role
        self.stdout.write("Roles ensured: " + ", ".join(role_objs.keys()))

        sam = role_objs["SAM"]
        sam_current = set(sam.role_permissions.values_list("permission__code", flat=True))
        missing_codes = [c for c in self.USER_PROVIDED_CODES if c not in sam_current]
        if missing_codes:
            to_link = []
            for code in missing_codes:
                try:
                    perm = Permission.objects.get(code=code)
                except Permission.DoesNotExist:
                    continue
                to_link.append(RolePermission(role=sam, permission=perm))
            RolePermission.objects.bulk_create(to_link)
            self.stdout.write(f"Assigned {len(to_link)} permissions to SAM")
        else:
            self.stdout.write("SAM already has all provided permissions")

        if options.get("assign_superusers", True):
            User = get_user_model()
            superusers = User.objects.filter(is_superuser=True)
            created_links = 0
            for su in superusers:
                if not UserRole.objects.filter(user=su, role=sam).exists():
                    UserRole.objects.create(user=su, role=sam)
                    created_links += 1
            self.stdout.write(f"Superusers linked to SAM: {created_links}")

        self.stdout.write(self.style.SUCCESS("Post-seed RBAC sync complete"))
