import json
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from locations.models import Country, State, City

class Command(BaseCommand):
    help = 'Import Countries, States, and Cities from JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file', 
            type=str, 
            default='locations/countries+states+cities.json',
            help='Path to the JSON file'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            return

        self.stdout.write(self.style.SUCCESS(f'Reading file: {file_path}...'))
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.stdout.write(self.style.SUCCESS(f'Loaded {len(data)} countries. Starting import...'))

        # 1. Process Countries
        self.process_countries(data)

    def process_countries(self, data):
        self.stdout.write('Processing Countries...')
        
        # Cache existing countries to avoid excessive queries
        # Map: iso_code_2 -> Country Object
        existing_countries = {c.iso_code_2: c for c in Country.objects.all()}
        
        countries_to_create = []
        countries_to_update = []
        
        country_map = {} # iso2 -> country_obj (for state processing)

        with transaction.atomic():
            for entry in data:
                iso2 = entry.get('iso2')
                if not iso2:
                    continue

                country_data = {
                    'name': entry.get('name'),
                    'iso_code_3': entry.get('iso3'),
                    'phone_code': entry.get('phone_code') or entry.get('phonecode'),
                    'currency_code': entry.get('currency'),
                    'emoji': entry.get('emoji'),
                    'region': entry.get('region'),
                    'is_active': True
                }

                if iso2 in existing_countries:
                    country = existing_countries[iso2]
                    updated = False
                    for key, value in country_data.items():
                        if getattr(country, key) != value:
                            setattr(country, key, value)
                            updated = True
                    if updated:
                        countries_to_update.append(country)
                    country_map[iso2] = country
                else:
                    country = Country(iso_code_2=iso2, **country_data)
                    countries_to_create.append(country)

            # Bulk Create
            if countries_to_create:
                Country.objects.bulk_create(countries_to_create)
                self.stdout.write(self.style.SUCCESS(f'Created {len(countries_to_create)} countries.'))
            
            # Bulk Update
            if countries_to_update:
                Country.objects.bulk_update(countries_to_update, ['name', 'iso_code_3', 'phone_code', 'currency_code', 'emoji', 'region', 'is_active'])
                self.stdout.write(self.style.SUCCESS(f'Updated {len(countries_to_update)} countries.'))

            # Refresh map with IDs for newly created ones
            all_countries = Country.objects.filter(iso_code_2__in=[c['iso2'] for c in data if c.get('iso2')])
            country_map = {c.iso_code_2: c for c in all_countries}

        # 2. Process States
        self.process_states(data, country_map)

    def process_states(self, data, country_map):
        self.stdout.write('Processing States...')
        
        # Pre-fetch all states to minimize DB hits during check
        # Map: (country_id, state_code) -> State Object
        # Note: state_code might be null or duplicate in some bad data, but we rely on it.
        # Ideally, we should use a more robust check, but for speed we'll use a composite key.
        
        existing_states = set(
            State.objects.values_list('country_id', 'state_code')
        )

        states_to_create = []
        state_map = {} # (country_id, state_code) -> state_obj (for city processing)
        
        # To handle FK mapping for cities later, we need to save states first.
        
        batch_size = 5000
        
        for entry in data:
            country_iso = entry.get('iso2')
            country = country_map.get(country_iso)
            if not country:
                continue

            states_data = entry.get('states', [])
            for state_entry in states_data:
                state_code = state_entry.get('state_code') or state_entry.get('iso2')
                state_name = state_entry.get('name')
                
                if not state_name:
                    continue

                # Unique check key
                key = (country.id, state_code)
                
                # If we rely purely on bulk_create, we can't easily get IDs back for City mapping
                # without re-querying.
                # Strategy: 
                # 1. Create all States.
                # 2. Re-query all States to build the map for Cities.
                
                if key not in existing_states:
                    states_to_create.append(
                        State(
                            country=country,
                            name=state_name,
                            state_code=state_code,
                            is_active=True
                        )
                    )
                    existing_states.add(key) # Prevent duplicates within this run

        # Bulk Create States
        if states_to_create:
            self.stdout.write(f'Creating {len(states_to_create)} states...')
            with transaction.atomic():
                for i in range(0, len(states_to_create), batch_size):
                    batch = states_to_create[i:i + batch_size]
                    State.objects.bulk_create(batch)
                    self.stdout.write(f'  Batch {i//batch_size + 1} done.')
        
        self.stdout.write(self.style.SUCCESS('States processed. Reloading State Map for Cities...'))
        
        # 3. Process Cities
        # We need a way to look up state_id by (country_iso, state_code)
        # Re-fetching is safer.
        self.process_cities(data, country_map)

    def process_cities(self, data, country_map):
        self.stdout.write('Processing Cities (this may take a while)...')
        
        # Build State Map: (country_id, state_code) -> state_id
        # Note: If state_code is missing/null in JSON, we might have issues matching.
        # Fallback: (country_id, state_name) -> state_id?
        # Let's try both.
        
        # Fetch minimal fields to save memory
        states_qs = State.objects.all().values('id', 'country_id', 'state_code', 'name')
        
        state_lookup_by_code = {}
        state_lookup_by_name = {}
        
        for s in states_qs:
            c_id = s['country_id']
            s_id = s['id']
            code = s['state_code']
            name = s['name']
            
            if code:
                state_lookup_by_code[(c_id, code)] = s_id
            state_lookup_by_name[(c_id, name)] = s_id

        cities_to_create = []
        batch_size = 5000
        total_cities = 0
        
        # Optimization: Check existing cities?
        # Checking 100k+ cities one by one is slow.
        # If we assume this is a fresh import or we want to add missing ones...
        # Let's assume we append missing ones.
        # Ideally, we should have a unique constraint on City (state, name).
        # Assuming database handles uniqueness or we accept duplicates if run twice?
        # Better: Check existence for batch.
        
        # For Enterprise High Performance:
        # We will collect ALL cities from JSON, filter out those that exist, then bulk create.
        
        existing_cities_set = set(
            City.objects.values_list('state_id', 'name')
        )

        for entry in data:
            country_iso = entry.get('iso2')
            country = country_map.get(country_iso)
            if not country:
                continue

            for state_entry in entry.get('states', []):
                state_code = state_entry.get('state_code') or state_entry.get('iso2')
                state_name = state_entry.get('name')
                
                # Resolve State ID
                state_id = None
                if state_code:
                    state_id = state_lookup_by_code.get((country.id, state_code))
                
                if not state_id:
                    state_id = state_lookup_by_name.get((country.id, state_name))
                
                if not state_id:
                    # self.stdout.write(self.style.WARNING(f"Skipping cities for state {state_name} ({state_code}) - State not found"))
                    continue

                cities_data = state_entry.get('cities', [])
                for city_entry in cities_data:
                    city_name = city_entry.get('name')
                    lat = city_entry.get('latitude')
                    lon = city_entry.get('longitude')
                    
                    if not city_name:
                        continue
                        
                    key = (state_id, city_name)
                    if key not in existing_cities_set:
                        cities_to_create.append(
                            City(
                                state_id=state_id,
                                name=city_name,
                                latitude=lat,
                                longitude=lon,
                                is_active=True
                            )
                        )
                        existing_cities_set.add(key)
                        
                        if len(cities_to_create) >= batch_size:
                            City.objects.bulk_create(cities_to_create)
                            total_cities += len(cities_to_create)
                            self.stdout.write(f'  Inserted {total_cities} cities...')
                            cities_to_create = []

        # Remaining cities
        if cities_to_create:
            City.objects.bulk_create(cities_to_create)
            total_cities += len(cities_to_create)
            self.stdout.write(f'  Inserted {total_cities} cities.')

        self.stdout.write(self.style.SUCCESS('Import Complete!'))
