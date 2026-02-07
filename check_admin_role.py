import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from accounts.models import CustomUser
from rbac.models import UserRole

email = "admin@gmail.com"
try:
    user = CustomUser.objects.get(email=email)
    print(f"User found: {user.email}, ID: {user.id}")
    print(f"is_superuser: {user.is_superuser}")
    
    roles = UserRole.objects.filter(user=user)
    print(f"UserRole count: {roles.count()}")
    for ur in roles:
        print(f" - Role: {ur.role.code} ({ur.role.name})")
        
except CustomUser.DoesNotExist:
    print(f"User {email} not found")
