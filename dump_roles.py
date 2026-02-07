import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from rbac.models import Role

with open("roles_dump.txt", "w") as f:
    roles = Role.objects.all()
    for r in roles:
        f.write(f"Code: {r.code}, Name: {r.name}\n")
