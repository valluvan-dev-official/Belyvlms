import json
import os
import time
from django.core.management.base import BaseCommand
from django.db import transaction
from locations.models import Country
from tqdm import tqdm

class Command(BaseCommand):
    help = 'Enrich Country master table with phone_code and emoji metadata from JSON dataset'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='locations/countries+states+cities.json',
            help='Path to the JSON file'
        )

    def handle(self, *args, **options):
        start_time = time.time()
        file_path = options['file']

        self.stdout.write(self.style.SUCCESS(f'--- Starting Metadata Enrichment ---'))
        
        # Strategy: Prefer JSON, but if missing/slow, we could use libs (future enhancement)
        # For now, we optimize JSON processing.

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            return

        self.stdout.write(f'Reading file: {file_path} (Size: {os.path.getsize(file_path)/1024/1024:.2f} MB)...')
        
        try:
            # Optimization: 45MB is small enough for modern RAM.
            # If this is slow, it's likely the decoding.
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f'Invalid JSON file: {e}'))
            return
        except MemoryError:
             self.stdout.write(self.style.ERROR('Memory Error: JSON file too large.'))
             return

        self.stdout.write(self.style.SUCCESS(f'Loaded {len(data)} records from JSON.'))

        # Phase 1: Build In-Memory Country Map
        self.stdout.write('Phase 1: Building In-Memory Country Map...')
        existing_countries = Country.objects.all()
        country_map = {c.iso_code_2: c for c in existing_countries}
        
        self.stdout.write(f'Loaded {len(country_map)} existing countries from database.')

        # Phase 2: Stream Dataset Processing
        self.stdout.write('Phase 2: Processing Dataset for Enrichment...')
        
        countries_to_update = []
        updated_count = 0
        skipped_count = 0
        
        # Safe Progress Bar (Works even if tqdm is missing or fails)
        try:
            from tqdm import tqdm
            iterator = tqdm(data, desc="Processing Countries", unit="country")
        except ImportError:
            self.stdout.write("tqdm not installed. Running without progress bar...")
            iterator = data

        for entry in iterator:
            iso2 = entry.get('iso2')
            
            if not iso2 or iso2 not in country_map:
                skipped_count += 1
                continue

            country = country_map[iso2]
            
            # Extract metadata
            phone_code = entry.get('phone_code') or entry.get('phonecode')
            emoji = entry.get('emoji')

            # Normalization
            if phone_code and str(phone_code).startswith('+'):
                 phone_code = str(phone_code)[1:]

            # Check if update is needed
            needs_update = False
            
            if phone_code and country.phone_code != str(phone_code):
                country.phone_code = str(phone_code)
                needs_update = True
            
            if emoji and country.emoji != emoji:
                country.emoji = emoji
                needs_update = True

            if needs_update:
                countries_to_update.append(country)
                updated_count += 1

        # Phase 3: Bulk Update Execution
        self.stdout.write('Phase 3: Executing Bulk Update...')
        
        if countries_to_update:
            # Batch updates to avoid DB timeouts if list is huge
            batch_size = 500
            total_updates = len(countries_to_update)
            
            try:
                from tqdm import tqdm
                pbar = tqdm(total=total_updates, desc="Updating DB", unit="rec")
                has_tqdm = True
            except ImportError:
                has_tqdm = False
                self.stdout.write(f"Updating {total_updates} records...")

            for i in range(0, total_updates, batch_size):
                batch = countries_to_update[i:i + batch_size]
                Country.objects.bulk_update(batch, ['phone_code', 'emoji'])
                if has_tqdm:
                    pbar.update(len(batch))
            
            if has_tqdm:
                pbar.close()
            
            self.stdout.write(self.style.SUCCESS(f'Successfully enriched {updated_count} country records.'))
        else:
            self.stdout.write(self.style.SUCCESS('No records needed updating. All metadata is up to date.'))

        # Reporting
        execution_time = time.time() - start_time
        
        self.stdout.write(self.style.SUCCESS('\n--- Execution Summary ---'))
        self.stdout.write(f'Total JSON Records: {len(data)}')
        self.stdout.write(f'Updated: {updated_count}')
        self.stdout.write(f'Skipped: {skipped_count}')
        self.stdout.write(f'Time: {execution_time:.2f}s')
        self.stdout.write('-------------------------')
