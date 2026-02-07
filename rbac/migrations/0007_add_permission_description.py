from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('rbac', '0006_alter_onboardrequest_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='permission',
            name='description',
            field=models.TextField(blank=True, help_text='Detailed description for tooltips', null=True),
        ),
    ]
