import os
import sys
import time
import django
from django.core.management import call_command
from django.conf import settings

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from seed_strict_permissions import seed_permissions

def print_header(title):
    print("\n" + "=" * 60)
    print(f"🚀 {title}")
    print("=" * 60)

def run_step(step_name, func, *args, **kwargs):
    print_header(f"Starting: {step_name}")
    start_time = time.time()
    try:
        func(*args, **kwargs)
        elapsed = time.time() - start_time
        print(f"\n✅ {step_name} completed successfully in {elapsed:.2f}s")
        return True
    except Exception as e:
        print(f"\n❌ {step_name} FAILED!")
        print(f"Error: {str(e)}")
        return False

def seed_server():
    total_start = time.time()
    print_header("ENTERPRISE SERVER SEEDING STARTED")
    print("This script will synchronize your server with the latest Enterprise Configuration.")

    # 1. Database Migrations
    if not run_step("Database Migrations", call_command, 'migrate'):
        return

    # 2. Geo Master Data (Heavy)
    # Using 'interactive=False' to skip prompts if any
    if not run_step("Import Geo Master Data (Countries/States/Cities)", call_command, 'import_geo_master'):
        return

    # 3. Geo Metadata (Phone/Emoji)
    if not run_step("Enrich Geo Metadata (Phone/Emoji)", call_command, 'import_country_metadata'):
        return

    # 4. Enterprise Profiles (Student/Trainer/Configs)
    if not run_step("Setup Enterprise Profiles", call_command, 'setup_enterprise_profiles'):
        return

    # 5. Role Sequences
    if not run_step("Seed Role Sequences", call_command, 'seed_role_sequences'):
        return

    # 6. Strict Permissions (The Root Script)
    # We import the function directly to avoid subprocess overhead
    if not run_step("Strict RBAC Permissions Sync", seed_permissions):
        return

    # 7. UI Defaults
    if not run_step("Initialize UI Defaults (Dashboards)", call_command, 'init_ui_defaults'):
        return

    total_elapsed = time.time() - total_start
    print_header("🎉 SEEDING COMPLETE")
    print(f"Total Time: {total_elapsed:.2f}s")
    print("Your server is now 100% synchronized with the Enterprise Codebase.")

if __name__ == '__main__':
    seed_server()
