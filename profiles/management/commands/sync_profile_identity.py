from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import transaction
from studentsdb.models import Student
from trainersdb.models import Trainer

class Command(BaseCommand):
    help = 'Syncs Identity Data (Name, Email) from User table to Profile tables (Student, Trainer) for existing records.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting Profile Identity Sync...")
        
        updated_students = 0
        updated_trainers = 0

        # 1. Sync Students
        students = Student.objects.filter(user__isnull=False)
        for student in students:
            user = student.user
            changed = False
            
            # Sync Email
            if not student.email and user.email:
                student.email = user.email
                changed = True
            
            # Sync Name (First/Last)
            if not student.first_name and user.name:
                parts = user.name.strip().split(' ', 1)
                student.first_name = parts[0]
                if len(parts) > 1 and not student.last_name:
                    student.last_name = parts[1]
                changed = True
            
            if changed:
                student.save()
                updated_students += 1

        # 2. Sync Trainers
        trainers = Trainer.objects.filter(user__isnull=False)
        for trainer in trainers:
            user = trainer.user
            changed = False
            
            # Sync Email
            if not trainer.email and user.email:
                trainer.email = user.email
                changed = True
            
            # Sync Name
            if not trainer.name and user.name:
                trainer.name = user.name
                changed = True
                
            if changed:
                trainer.save()
                updated_trainers += 1

        self.stdout.write(self.style.SUCCESS(f"Sync Complete."))
        self.stdout.write(f"Updated Students: {updated_students}")
        self.stdout.write(f"Updated Trainers: {updated_trainers}")
