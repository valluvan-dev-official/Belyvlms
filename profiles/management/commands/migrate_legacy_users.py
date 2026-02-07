from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction
from studentsdb.models import Student
from trainersdb.models import Trainer
from accounts.models import CustomUser
from rbac.models import Role, UserRole

class Command(BaseCommand):
    help = 'Migrates legacy Student and Trainer records to CustomUser identities with RBAC roles'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Starting Legacy User Migration...'))

        # 1. Fetch RBAC Roles
        try:
            # Look up by Name for stability, or fall back to known codes
            try:
                student_role = Role.objects.get(name='Student')
            except Role.DoesNotExist:
                student_role = Role.objects.get(code__in=['BTR', 'STUDENT'])
                
            try:
                trainer_role = Role.objects.get(name='Trainer')
            except Role.DoesNotExist:
                trainer_role = Role.objects.get(code__in=['TRN', 'TRAINER'])
                
        except Role.DoesNotExist as e:
            self.stdout.write(self.style.ERROR(f"Critical Error: RBAC Roles missing. Run 'seed_rbac' first. {str(e)}"))
            return

        # 2. Process Students
        self.process_students(student_role)

        # 3. Process Trainers
        self.process_trainers(trainer_role)

        self.stdout.write(self.style.SUCCESS('Migration Completed Successfully.'))

    def process_students(self, role):
        students = Student.objects.filter(user__isnull=True)
        count = students.count()
        self.stdout.write(f"Found {count} unlinked Students.")

        success_count = 0
        skipped_count = 0

        for student in students:
            try:
                with transaction.atomic():
                    # Generate Credentials
                    student_id_lower = student.student_id.lower() if student.student_id else f"unknown_st_{student.id}"
                    
                    # Email Strategy: Use Real Email or Fallback to ID-based Email
                    email = student.email
                    if not email:
                        email = f"{student_id_lower}@belyv.com"
                    
                    # Password Strategy: lowercase_id@123 (e.g., btr0001@123)
                    password = f"{student_id_lower}@123"

                    # Create User
                    # Handle potential duplicate email by appending random suffix if needed? 
                    # For now, try primary email, if fail, try fallback.
                    user = self.create_user_safe(
                        email=email,
                        name=f"{student.first_name} {student.last_name or ''}".strip(),
                        role='student',
                        password=password,
                        fallback_email_base=student_id_lower
                    )

                    if user:
                        # Assign RBAC Role
                        UserRole.objects.get_or_create(user=user, role=role)

                        # Link to Profile
                        student.user = user
                        student.save()
                        
                        success_count += 1
                        self.stdout.write(self.style.SUCCESS(f"Migrated Student: {student.student_id} -> {user.email}"))
                    else:
                        skipped_count += 1
                        self.stdout.write(self.style.ERROR(f"Failed to create user for Student: {student.student_id}"))

            except Exception as e:
                skipped_count += 1
                self.stdout.write(self.style.ERROR(f"Error processing student {student.student_id}: {str(e)}"))

        self.stdout.write(f"Student Migration: {success_count} Success, {skipped_count} Failed.")

    def process_trainers(self, role):
        trainers = Trainer.objects.filter(user__isnull=True)
        count = trainers.count()
        self.stdout.write(f"Found {count} unlinked Trainers.")

        success_count = 0
        skipped_count = 0

        for trainer in trainers:
            try:
                with transaction.atomic():
                    # Generate Credentials
                    trainer_id_lower = trainer.trainer_id.lower() if trainer.trainer_id else f"unknown_tr_{trainer.id}"
                    
                    # Email Strategy
                    email = trainer.email
                    if not email:
                        email = f"{trainer_id_lower}@belyv.com"
                    
                    # Password Strategy
                    password = f"{trainer_id_lower}@123"

                    # Create User
                    user = self.create_user_safe(
                        email=email,
                        name=trainer.name,
                        role='trainer',
                        password=password,
                        fallback_email_base=trainer_id_lower
                    )

                    if user:
                        # Assign RBAC Role
                        UserRole.objects.get_or_create(user=user, role=role)

                        # Link to Profile
                        trainer.user = user
                        trainer.save()
                        
                        success_count += 1
                        self.stdout.write(self.style.SUCCESS(f"Migrated Trainer: {trainer.trainer_id} -> {user.email}"))
                    else:
                        skipped_count += 1
                        self.stdout.write(self.style.ERROR(f"Failed to create user for Trainer: {trainer.trainer_id}"))

            except Exception as e:
                skipped_count += 1
                self.stdout.write(self.style.ERROR(f"Error processing trainer {trainer.trainer_id}: {str(e)}"))

        self.stdout.write(f"Trainer Migration: {success_count} Success, {skipped_count} Failed.")

    def create_user_safe(self, email, name, role, password, fallback_email_base):
        """
        Attempts to create a user. If email exists, tries fallback email.
        """
        try:
            return CustomUser.objects.create_user(
                email=email,
                name=name,
                role=role,
                password=password
            )
        except (IntegrityError, ValueError):
            # Email likely taken or invalid. Try fallback ID-based email.
            fallback_email = f"{fallback_email_base}@belyv.com"
            if fallback_email == email:
                # If we already tried the fallback and it failed, we can't do much.
                # Maybe append a random suffix?
                import random
                fallback_email = f"{fallback_email_base}_{random.randint(100,999)}@belyv.com"
            
            try:
                self.stdout.write(self.style.WARNING(f"Email {email} failed. Retrying with {fallback_email}"))
                return CustomUser.objects.create_user(
                    email=fallback_email,
                    name=name,
                    role=role,
                    password=password
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Could not create user even with fallback: {str(e)}"))
                return None
