
import os
import sqlite3
import django
from django.conf import settings

# Direct file logging
with open('cleanup_log.txt', 'w', encoding='utf-8') as f:
    def log(msg):
        print(msg)
        f.write(msg + "\n")

    log("🚀 Starting Force Cleanup of Access Control Tables...")
    
    # Connect to SQLite directly
    try:
        # Assuming db.sqlite3 is in the root
        db_path = 'db.sqlite3'
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Disable foreign keys to allow dropping tables without constraint errors
        cursor.execute("PRAGMA foreign_keys = OFF;")
        log("ℹ️ Foreign keys disabled.")

        # Find all tables starting with access_control_
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'access_control_%';")
        tables = cursor.fetchall()
        
        if not tables:
            log("✅ No access_control tables found.")
        else:
            for (table_name,) in tables:
                log(f"🔥 Dropping table: {table_name}")
                cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
            
            conn.commit()
            log("✅ All access_control tables dropped.")
            
        # Re-enable foreign keys (optional, but good practice if we were continuing)
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        conn.close()
        
    except Exception as e:
        log(f"❌ Error: {e}")
        import traceback
        traceback.print_exc(file=f)
