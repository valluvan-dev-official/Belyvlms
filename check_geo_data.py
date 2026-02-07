
import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from locations.models import Country

def check_data():
    codes = ['IN', 'US', 'AF', 'GB']
    print(f"{'ISO':<5} {'Name':<20} {'Phone':<10} {'Emoji':<10} {'Region':<15}")
    print("-" * 65)
    
    for code in codes:
        try:
            c = Country.objects.get(iso_code_2=code)
            print(f"{c.iso_code_2:<5} {c.name:<20} {str(c.phone_code):<10} {str(c.emoji):<10} {str(c.region):<15}")
        except Country.DoesNotExist:
            print(f"{code:<5} NOT FOUND")

if __name__ == "__main__":
    check_data()
