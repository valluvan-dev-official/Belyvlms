import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from accounts.models import CustomUser

def fix_users():
    # Find all users who are forced to change password
    users = CustomUser.objects.filter(must_change_password=True)
    count = users.count()
    
    print(f"Found {count} users stuck on 'Password Reset Required'.")
    
    if count > 0:
        # Bulk update them to False
        users.update(must_change_password=False)
        print(f"✅ FIXED: Successfully updated {count} users. They will now see the Dashboard directly.")
    else:
        print("✅ No users found with this flag. Everyone is already clear.")

if __name__ == "__main__":
    fix_users()
