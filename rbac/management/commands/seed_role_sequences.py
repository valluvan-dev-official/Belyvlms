from django.core.management.base import BaseCommand
from django.db import transaction
from rbac.models import Role, RoleSequence
from studentsdb.models import Student
from trainersdb.models import Trainer
from consultantdb.models import Consultant

class Command(BaseCommand):
    help = 'Seeds the RoleSequence table with current maximum IDs to ensure continuity.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting RoleSequence seeding...")
        
        with transaction.atomic():
            # 1. Seed Student Sequence (BTR)
            student_role, _ = Role.objects.get_or_create(name='Student', defaults={'code': 'BTR'})
            if student_role.code != 'BTR':
                self.stdout.write(self.style.WARNING(f"Role 'Student' has code '{student_role.code}', expected 'BTR'. Using existing code."))
            
            last_student = Student.objects.order_by('-id').first()
            max_id = 0
            if last_student and last_student.student_id and last_student.student_id.startswith('BTR'):
                try:
                    max_id = int(last_student.student_id.replace('BTR', ''))
                except ValueError:
                    self.stdout.write(self.style.ERROR(f"Invalid Student ID format: {last_student.student_id}"))

            seq, created = RoleSequence.objects.get_or_create(role=student_role)
            if created or seq.current_sequence < max_id:
                seq.current_sequence = max_id
                seq.save()
                self.stdout.write(self.style.SUCCESS(f"Seeded Student Sequence: {max_id}"))
            else:
                self.stdout.write(f"Student Sequence already at {seq.current_sequence} (Max ID: {max_id})")

            # 2. Seed Trainer Sequence (TRN)
            trainer_role, _ = Role.objects.get_or_create(name='Trainer', defaults={'code': 'TRN'})
            last_trainer = Trainer.objects.order_by('-id').first()
            max_trn_id = 0
            if last_trainer and last_trainer.trainer_id and last_trainer.trainer_id.startswith('TRN'):
                try:
                    max_trn_id = int(last_trainer.trainer_id.replace('TRN', ''))
                except ValueError:
                    pass

            seq_trn, created_trn = RoleSequence.objects.get_or_create(role=trainer_role)
            if created_trn or seq_trn.current_sequence < max_trn_id:
                seq_trn.current_sequence = max_trn_id
                seq_trn.save()
                self.stdout.write(self.style.SUCCESS(f"Seeded Trainer Sequence: {max_trn_id}"))
            
            # 3. Seed Consultant Sequence (CON)
            consultant_role, _ = Role.objects.get_or_create(name='Consultant', defaults={'code': 'CON'})
            last_con = Consultant.objects.order_by('-id').first()
            max_con_id = 0
            if last_con and last_con.consultant_id and last_con.consultant_id.startswith('CON'):
                try:
                    max_con_id = int(last_con.consultant_id.replace('CON', ''))
                except ValueError:
                    pass
            
            seq_con, created_con = RoleSequence.objects.get_or_create(role=consultant_role)
            if created_con or seq_con.current_sequence < max_con_id:
                seq_con.current_sequence = max_con_id
                seq_con.save()
                self.stdout.write(self.style.SUCCESS(f"Seeded Consultant Sequence: {max_con_id}"))

        self.stdout.write(self.style.SUCCESS("RoleSequence seeding completed successfully."))
