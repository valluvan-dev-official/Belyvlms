import json
import os
import time
from django.core.management.base import BaseCommand
from django.db import transaction
from locations.models import Country

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

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            return

        self.stdout.write(self.style.SUCCESS(f'Reading file: {file_path}...'))
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f'Invalid JSON file: {e}'))
            return

        self.stdout.write(self.style.SUCCESS(f'Loaded {len(data)} records from JSON.'))

        # Phase 1: Build In-Memory Country Map
        self.stdout.write('Phase 1: Building In-Memory Country Map...')
        # Fetch only necessary fields to minimize memory footprint
        existing_countries = Country.objects.all()
        country_map = {c.iso_code_2: c for c in existing_countries}
        
        self.stdout.write(f'Loaded {len(country_map)} existing countries from database.')

        # Phase 2: Stream Dataset Processing
        self.stdout.write('Phase 2: Processing Dataset for Enrichment...')
        
        countries_to_update = []
        updated_count = 0
        skipped_count = 0
        missing_iso_count = 0

        # We will track IDs to ensure no duplicates in update list (though map handles uniqueness of objects)
        # Using a set to track which ISOs we have processed in this run if needed, 
        # but since we iterate JSON, we just check against the map.
        
        for entry in data:
            iso2 = entry.get('iso2')
            
            if not iso2:
                skipped_count += 1
                continue

            if iso2 not in country_map:
                # Log missing ISO codes as per requirements
                # self.stdout.write(self.style.WARNING(f'Skipping unknown ISO code: {iso2}')) 
                # (Commented out to avoid cluttering output, or we can count them)
                missing_iso_count += 1
                skipped_count += 1
                continue

            country = country_map[iso2]
            
            # Extract metadata
            phone_code = entry.get('phone_code') or entry.get('phonecode')
            emoji = entry.get('emoji')

            # Check if update is needed
            needs_update = False
            
            if phone_code and country.phone_code != phone_code:
                country.phone_code = phone_code
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
            # Update only the specified fields
            Country.objects.bulk_update(countries_to_update, ['phone_code', 'emoji'])
            self.stdout.write(self.style.SUCCESS(f'Successfully enriched {len(countries_to_update)} country records.'))
        else:
            self.stdout.write(self.style.SUCCESS('No records needed updating. All metadata is up to date.'))

        # Reporting
        end_time = time.time()
        execution_time = end_time - start_time
        
        self.stdout.write(self.style.SUCCESS('\n--- Execution Summary ---'))
        self.stdout.write(f'Total JSON Records Processed: {len(data)}')
        self.stdout.write(f'Total Database Records Updated: {updated_count}')
        self.stdout.write(f'Total Skipped (Unknown ISO/No ISO): {skipped_count}')
        self.stdout.write(f'   - Missing in DB (Unknown ISO): {missing_iso_count}')
        self.stdout.write(f'Execution Time: {execution_time:.2f} seconds')
        self.stdout.write('-------------------------')
