from .models import UserProfile
from django.db.models import Max
import re

def generate_role_based_id(role_code):
    """
    Generates a unique ID based on the role code.
    Format: {ROLE_CODE}{001}
    Example: TR001, ST005
    """
    role_code = role_code.upper()
    prefix_len = len(role_code)
    
    # Filter profiles where role_based_id starts with role_code
    last_profile = UserProfile.objects.filter(
        role__code=role_code
    ).order_by('-role_based_id').first()

    if not last_profile:
        return f"{role_code}001"

    last_id = last_profile.role_based_id
    
    # Extract the numeric part
    # Assuming the format is strictly PREFIX + DIGITS
    try:
        # Check if it starts with the code
        if not last_id.startswith(role_code):
             return f"{role_code}001"
             
        numeric_part = last_id[prefix_len:]
        if not numeric_part.isdigit():
             return f"{role_code}001"
             
        next_num = int(numeric_part) + 1
        return f"{role_code}{next_num:03d}"
    except (ValueError, IndexError):
        return f"{role_code}001"
