import sqlite3
import os

db_path = 'd:\\BelyvLMS\\db.sqlite3'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Scanning for zombie tables (starting with 'access_control_')...")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'access_control_%';")
tables = cursor.fetchall()

if tables:
    print("\nFound the following ZOMBIE tables:")
    for t in tables:
        print(f" - {t[0]}")
else:
    print("\nNo 'access_control' tables found.")

conn.close()
