
import os
import sys
import django
from django.core.management import call_command
from django.db import connection

# Direct file logging
with open('migration_debug.log', 'w', encoding='utf-8') as f:
    def log(msg):
        print(msg)
        f.write(msg + "\n")

    log("🚀 Script started...")
    
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
        django.setup()
        log("Django setup done.")
        
        # Check before
        tables = connection.introspection.table_names()
        if 'studentsdb_studentprofessionalprofile' in tables:
            log("ℹ️ Table ALREADY exists before migration.")
        else:
            log("ℹ️ Table missing before migration.")

        log("🚀 Applying migrations for studentsdb...")
        call_command('migrate', 'studentsdb', interactive=False)
        log("✅ Migration command executed.")
        
        # Check after
        tables = connection.introspection.table_names()
        if 'studentsdb_studentprofessionalprofile' in tables:
            log("✅ Table NOW exists!")
        else:
            log("❌ Table STILL MISSING after migration!")

    except Exception as e:
        log(f"❌ Error: {e}")
        import traceback
        traceback.print_exc(file=f)
