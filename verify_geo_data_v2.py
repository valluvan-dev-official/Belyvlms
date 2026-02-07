import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from locations.models import Country

def check_data():
    count = Country.objects.count()
    print(f"Total Countries: {count}")
    
    countries = Country.objects.filter(iso_code_2__in=['IN', 'US', 'AF'])
    print(f"{'Name':<20} | {'ISO2':<5} | {'Phone':<10} | {'Emoji':<10}")
    print("-" * 55)
    for c in countries:
        print(f"{c.name:<20} | {c.iso_code_2:<5} | {c.phone_code or 'N/A':<10} | {c.emoji or 'N/A':<10}")

if __name__ == "__main__":
    check_data()
