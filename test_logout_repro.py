import os
import django
import requests
import sys

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()
user = User.objects.first()

if not user:
    print("No user found")
    sys.exit(1)

refresh = RefreshToken.for_user(user)
access = str(refresh.access_token)
refresh_token = str(refresh)

print(f"Testing Logout for user: {user.email}")
print(f"Access: {access[:10]}...")
print(f"Refresh: {refresh_token[:10]}...")

url = "http://127.0.0.1:8000/api/rbac/auth/logout/"
headers = {
    "Authorization": f"Bearer {access}",
    "Content-Type": "application/json"
}
data = {
    "refresh": refresh_token
}

try:
    response = requests.post(url, json=data, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Request failed: {e}")
