import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from locations.models import Country

def verify():
    output_file = 'verify_result_v2.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        countries = ['IN', 'US', 'GB', 'AU', 'AE']
        f.write(f"{'ISO':<5} | {'Phone':<10} | {'Emoji':<10}\n")
        f.write("-" * 30 + "\n")
        for iso in countries:
            try:
                c = Country.objects.get(iso_code_2=iso)
                line = f"{c.iso_code_2:<5} | {c.phone_code or 'MISSING':<10} | {c.emoji or 'MISSING':<10}\n"
                f.write(line)
                print(line.strip())
            except Country.DoesNotExist:
                f.write(f"{iso:<5} | NOT FOUND  | NOT FOUND\n")
                print(f"{iso} NOT FOUND")
    print(f"Verification written to {output_file}")

if __name__ == "__main__":
    verify()
