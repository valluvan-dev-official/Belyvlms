import os
import sys
import django
from django.conf import settings

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from rbac.models import Role, OnboardRequest
from rbac.services import build_onboard_request_token, onboard_request_expiry, build_onboard_registration_url
from django.utils import timezone
import uuid

def diagnose():
    print("--- Starting Diagnosis ---")
    
    # 1. Check Role
    print("Checking Roles...")
    role = Role.objects.first()
    if not role:
        print("ERROR: No roles found in DB.")
        return
    print(f"Using Role: {role.code}")

    # 2. Simulate Creation Logic
    print("Simulating OnboardRequest creation...")
    try:
        nonce = uuid.uuid4().hex
        expires_at = onboard_request_expiry()
        
        # We won't actually save to DB to avoid clutter, or we use transaction.atomic and rollback
        # But for diagnosis, creating one record is fine.
        
        # Mock user
        from accounts.models import CustomUser
        user = CustomUser.objects.first()
        if not user:
            print("WARNING: No users found. Using None for initiated_by.")
        
        onboard_request = OnboardRequest(
            email=f"test_debug_{uuid.uuid4().hex[:6]}@example.com",
            role=role,
            status="INVITED",
            initiated_by=user,
            registration_nonce=nonce,
            registration_token_sent_at=timezone.now(),
            registration_expires_at=expires_at,
        )
        # Don't save yet, check token generation which uses the object
        # Token generation uses uuid, so we must ensure uuid is set. 
        # OnboardRequest.uuid is auto-generated on save usually? 
        # Let's check models.py for OnboardRequest definition.
        
        # If I save, I can test full flow.
        onboard_request.save()
        print(f"OnboardRequest saved with UUID: {onboard_request.uuid}")

        # 3. Test Token Generation
        print("Testing Token Generation...")
        token = build_onboard_request_token(onboard_request)
        print(f"Token generated: {token[:20]}...")

        # 4. Test Email Sending (Mock)
        print("Testing Email Sending (Simulation)...")
        from django.core.mail import send_mail
        # checking if email config causes crash
        # We won't actually send if not configured, but we check if import/call crashes
        
        print("Diagnosis Complete: SUCCESS")
        
    except Exception as e:
        print("\n!!! EXCEPTION CAUGHT !!!")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnose()
