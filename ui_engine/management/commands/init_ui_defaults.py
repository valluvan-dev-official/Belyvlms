from django.core.management.base import BaseCommand
from ui_engine.models import UIModule, RoleUIDefault
from rbac.models import Role

class Command(BaseCommand):
    help = 'Initializes default UI configurations for Roles'

    def handle(self, *args, **options):
        # 1. Create/Get 'dashboard' Module
        dashboard_module, created = UIModule.objects.get_or_create(
            slug='dashboard',
            defaults={
                'name': 'Main Dashboard',
                'description': 'The landing page for all users'
            }
        )
        self.stdout.write(f"Module 'dashboard' {'created' if created else 'exists'}")

        # 2. Define Configurations with Frontend-Compatible Structure
        
        # --- TRAINER (TRN) ---
        trainer_config = {
          "role": "trainer",
          "tabs": [
            { "id": "overview", "label": "Overview", "icon": "BarChart3", "layoutId": "trainer-overview" },
            { "id": "schedule", "label": "Schedule", "icon": "Calendar", "layoutId": "trainer-schedule" },
            { "id": "batches", "label": "My Batches", "icon": "Layers", "layoutId": "trainer-batches" },
            { "id": "students", "label": "Students", "icon": "Users", "layoutId": "trainer-students" }
          ],
          "layouts": {
            "trainer-overview": [
              { "id": "motivational-quote", "title": "Quote", "componentId": "MotivationalQuote", "gridConfig": { "w": 12, "h": 1 }, "role": ["trainer"] },
              { "id": "trainer-overview-section", "title": "Overview", "componentId": "TrainerDashboardOverview", "gridConfig": { "w": 12, "h": 1 }, "role": ["trainer"] },
              { "id": "trainer-quick-action", "title": "Quick Actions", "componentId": "TrainerQuickActionBar", "gridConfig": { "w": 12, "h": 1 }, "role": ["trainer"] }
            ],
            "trainer-schedule": [
              { "id": "trainer-schedule-section", "title": "Schedule", "componentId": "TrainerScheduleSection", "gridConfig": { "w": 12, "h": 1 }, "role": ["trainer"] }
            ],
            "trainer-batches": [
              { "id": "trainer-batches-section", "title": "My Batches", "componentId": "TrainerBatchesSection", "gridConfig": { "w": 12, "h": 1 }, "role": ["trainer"] }
            ],
            "trainer-students": [
              { "id": "trainer-students-section", "title": "Students", "componentId": "TrainerStudentsSection", "gridConfig": { "w": 12, "h": 1 }, "role": ["trainer"] }
            ]
          }
        }

        # --- STUDENT (BTR) ---
        student_config = {
          "role": "student",
          "tabs": [
            { "id": "overview", "label": "Overview", "icon": "BarChart3", "layoutId": "student-overview" },
            { "id": "courses", "label": "My Courses", "icon": "BookOpen", "layoutId": "student-courses" },
            { "id": "schedule", "label": "Schedule", "icon": "Calendar", "layoutId": "student-schedule" },
            { "id": "progress", "label": "Progress", "icon": "TrendingUp", "layoutId": "student-progress" }
          ],
          "layouts": {
            "student-overview": [
              { "id": "student-overview-section", "title": "Overview", "componentId": "StudentDashboardOverview", "gridConfig": { "w": 12, "h": 1 }, "role": ["student"] }
            ],
            "student-courses": [
              { "id": "student-courses-section", "title": "My Courses", "componentId": "StudentCoursesSection", "gridConfig": { "w": 12, "h": 1 }, "role": ["student"] }
            ],
            "student-schedule": [
              { "id": "student-schedule-section", "title": "Schedule", "componentId": "StudentScheduleSection", "gridConfig": { "w": 12, "h": 1 }, "role": ["student"] }
            ],
            "student-progress": [
              { "id": "student-progress-section", "title": "Progress", "componentId": "StudentProgressSection", "gridConfig": { "w": 12, "h": 1 }, "role": ["student"] }
            ]
          }
        }
        
        # --- ADMIN (ADM) - Basic Placeholder (to avoid crash) ---
        admin_config = {
            "role": "admin",
            "tabs": [
                { "id": "overview", "label": "Overview", "icon": "LayoutDashboard", "layoutId": "admin-overview" }
            ],
            "layouts": {
                "admin-overview": [
                    { "id": "admin-stats", "title": "Stats", "componentId": "AdminStatsWidget", "gridConfig": { "w": 12, "h": 1 } }
                ]
            }
        }

        # 3. Save to DB
        configs = [
            ('TRN', trainer_config),
            ('BTR', student_config),
            ('ADM', admin_config)
        ]

        for role_code, config in configs:
            try:
                role = Role.objects.get(code=role_code)
                obj, created = RoleUIDefault.objects.update_or_create(
                    role=role,
                    module=dashboard_module,
                    defaults={
                        'config': config,
                        'version': 2 # Bump version to signal update
                    }
                )
                action = "Created" if created else "Updated"
                self.stdout.write(self.style.SUCCESS(f"{action} config for {role.name} ({role_code})"))
            except Role.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Role {role_code} not found. Skipping."))
