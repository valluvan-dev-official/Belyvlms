
import os
import django
import sys

sys.stdout.reconfigure(encoding='utf-8')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from rbac.services import get_onboard_field_schema
from rbac.models import Role

try:
    role = Role.objects.get(name='Student')
    schema = get_onboard_field_schema(role, 'registration')
    
    print("--- Schema Check ---")
    for field in schema:
        if field['key'] in ['profile.alternative_phone', 'profile.profile_picture']:
            print(f"{field['key']}: required={field['required']}")
except Exception as e:
    print(e)
