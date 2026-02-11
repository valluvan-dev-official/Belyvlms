import json
import os

INPUT_FILE = 'enterprise_data.json'
OUTPUT_FILE = 'enterprise_data_clean.json'

# Models where 'user' field should be set to null (because field is nullable)
MODELS_TO_NULLIFY_USER = [
    'studentsdb.student',
    'trainersdb.trainer',
]

# Models to completely remove (because they require a user and we can't provide one)
MODELS_TO_REMOVE = [
    'consultantdb.consultantprofile',
]

def clean_data():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found. Please run dumpdata first.")
        return

    print(f"Reading {INPUT_FILE}...")
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print("Error: JSON file is invalid or empty. Check if dumpdata ran successfully.")
        return
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    cleaned_data = []
    removed_count = 0
    modified_count = 0

    for entry in data:
        model = entry.get('model')

        # 1. Skip models that need to be removed
        if model in MODELS_TO_REMOVE:
            removed_count += 1
            continue

        # 2. Modify models that need user=null
        if model in MODELS_TO_NULLIFY_USER:
            if 'fields' in entry and 'user' in entry['fields']:
                entry['fields']['user'] = None
                modified_count += 1
        
        cleaned_data.append(entry)

    print(f"Writing {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, indent=2)

    print("-" * 30)
    print(f"Done! Summary:")
    print(f" - Records Modified (user -> null): {modified_count}")
    print(f" - Records Removed (linked profiles): {removed_count}")
    print(f" - Output File: {OUTPUT_FILE}")
    print("-" * 30)
    print("You can now upload 'enterprise_data_clean.json' to the server.")

if __name__ == "__main__":
    clean_data()
