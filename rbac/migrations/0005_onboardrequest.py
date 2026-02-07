from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('rbac', '0004_role_deleted_at_role_deleted_by_role_deletion_reason_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='OnboardRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('code', models.CharField(blank=True, max_length=20, unique=True)),
                ('email', models.EmailField(max_length=254)),
                ('status', models.CharField(choices=[('PENDING_USER_INPUT', 'Pending User Input'), ('SUBMITTED', 'Submitted'), ('UNDER_REVIEW', 'Under Review'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected'), ('PROVISIONED', 'Provisioned'), ('EXPIRED', 'Expired'), ('ERROR', 'Error')], default='PENDING_USER_INPUT', max_length=30)),
                ('user_payload', models.JSONField(blank=True, default=dict)),
                ('admin_payload', models.JSONField(blank=True, default=dict)),
                ('submitted_at', models.DateTimeField(blank=True, null=True)),
                ('approved_at', models.DateTimeField(blank=True, null=True)),
                ('registration_nonce', models.CharField(blank=True, max_length=64, null=True)),
                ('registration_token_sent_at', models.DateTimeField(blank=True, null=True)),
                ('registration_token_used_at', models.DateTimeField(blank=True, null=True)),
                ('registration_expires_at', models.DateTimeField(blank=True, null=True)),
                ('rejection_reason', models.TextField(blank=True, null=True)),
                ('last_error', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='onboard_requests_approved', to=settings.AUTH_USER_MODEL)),
                ('initiated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='onboard_requests_initiated', to=settings.AUTH_USER_MODEL)),
                ('provisioned_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='onboard_requests_provisioned_user', to=settings.AUTH_USER_MODEL)),
                ('role', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='onboard_requests', to='rbac.role')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]

