from django.core.management.base import BaseCommand
from rbac.models import Role
from profiles.models import RoleProfileConfig, ProfileFieldDefinition

class Command(BaseCommand):
    help = 'Sets up Enterprise Profile Configurations for Student and Trainer roles'

    def handle(self, *args, **kwargs):
        self.stdout.write("Setting up Enterprise Profiles...")

        def get_or_create_role(code, name):
            # Try by code first
            role = Role.objects.filter(code=code).first()
            if role:
                return role
            
            # Try by name (case insensitive)
            role = Role.objects.filter(name__iexact=name).first()
            if role:
                return role
                
            # Create
            return Role.objects.create(code=code, name=name)

        # 1. Student Configuration
        student_role = get_or_create_role('student', 'Student')
        
        student_config, created = RoleProfileConfig.objects.get_or_create(role=student_role)
        student_config.model_path = 'studentsdb.Student'
        student_config.is_required = True
        student_config.save()
        
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created Config for {student_role.name} -> studentsdb.Student"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Updated Config for {student_role.name} -> studentsdb.Student"))

        # 2. Trainer Configuration
        trainer_role = get_or_create_role('trainer', 'Trainer')
        
        trainer_config, created = RoleProfileConfig.objects.get_or_create(role=trainer_role)
        trainer_config.model_path = 'trainersdb.Trainer'
        trainer_config.is_required = True
        trainer_config.save()

        if created:
            self.stdout.write(self.style.SUCCESS(f"Created Config for {trainer_role.name} -> trainersdb.Trainer"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Updated Config for {trainer_role.name} -> trainersdb.Trainer"))

        # 3. Placement Officer (Example of Generic Profile)
        po_role = get_or_create_role('placement_officer', 'Placement Officer')
        
        po_config, created = RoleProfileConfig.objects.get_or_create(role=po_role)
        po_config.model_path = None # Use GenericProfile
        po_config.is_required = True
        po_config.save()

        if created:
            self.stdout.write(self.style.SUCCESS(f"Created Config for {po_role.name} -> GenericProfile"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Updated Config for {po_role.name} -> GenericProfile"))

        # Add Default Enterprise Fields (Aadhar, Pan, Address)
        default_fields = [
            ('aadhar_number', 'Aadhar Number', 'NUMBER'),
            ('pan_number', 'Pan Number', 'TEXT'),
            ('current_address', 'Current Address', 'TEXT'),
            ('permanent_address', 'Permanent Address', 'TEXT'),
        ]

        valid_field_names = []
        for field_name, label, ftype in default_fields:
            field, created = ProfileFieldDefinition.objects.update_or_create(
                config=po_config,
                name=field_name,
                defaults={
                    'label': label,
                    'field_type': ftype,
                    'is_required': True
                }
            )
            valid_field_names.append(field_name)
        
        # STRICT SYNC: Delete fields not in valid_field_names for this config
        deleted_count, _ = ProfileFieldDefinition.objects.filter(config=po_config).exclude(name__in=valid_field_names).delete()
        if deleted_count > 0:
             self.stdout.write(self.style.WARNING(f"Removed {deleted_count} stale fields from {po_role.name}"))

        self.stdout.write(self.style.SUCCESS(f"Added default enterprise fields to {po_role.name}"))

        self.stdout.write(self.style.SUCCESS("All Enterprise Profiles Configured Successfully!"))
