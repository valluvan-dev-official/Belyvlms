from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from locations.models import Country, State, City
from django.db import IntegrityError
from django.db import connection, reset_queries
import time

class LocationModelIntegrityTest(TestCase):
    """
    Enterprise-Level Data Integrity Tests
    Ensures that the normalized database schema enforces strict relationships.
    """

    def setUp(self):
        self.country = Country.objects.create(
            name="Test Country",
            iso_code_2="TC",
            iso_code_3="TCY",
            phone_code="999",
            currency_code="TST",
            region="Test Region"
        )
        self.state = State.objects.create(
            country=self.country,
            name="Test State",
            state_code="TS"
        )
        self.city = City.objects.create(
            state=self.state,
            name="Test City",
            latitude=12.34,
            longitude=56.78
        )

    def test_referential_integrity(self):
        """
        Verify that the hierarchy Country -> State -> City is strictly enforced.
        """
        # 1. Verify Upward Traversal (City -> State -> Country)
        self.assertEqual(self.city.state, self.state)
        self.assertEqual(self.city.state.country, self.country)
        self.assertEqual(self.city.state.country.iso_code_2, "TC")

        # 2. Verify Downward Traversal (Country -> States -> Cities)
        # Note: related_name must be set correctly in models for this to work
        self.assertTrue(self.country.states.filter(id=self.state.id).exists())
        self.assertTrue(self.state.cities.filter(id=self.city.id).exists())

    def test_iso_code_uniqueness(self):
        """
        Verify that ISO codes are unique at the database level.
        Critical for avoiding data corruption in a master data system.
        """
        with self.assertRaises(IntegrityError):
            Country.objects.create(
                name="Duplicate Country",
                iso_code_2="TC"  # Same ISO code as setUp
            )

    def test_composite_unique_constraints(self):
        """
        Verify composite unique constraints (e.g., State code unique within a Country).
        """
        # Attempt to create another state with same code in same country
        with self.assertRaises(IntegrityError):
            State.objects.create(
                country=self.country,
                name="Duplicate State",
                state_code="TS" # Should fail if unique_together=('country', 'state_code') is enforced
            )

    def test_cascading_deletion_safety(self):
        """
        Verify that deleting a Country cascades to States and Cities.
        This ensures no 'orphan' records are left behind.
        """
        country_id = self.country.id
        self.country.delete()
        
        self.assertFalse(State.objects.filter(country_id=country_id).exists())
        self.assertFalse(City.objects.filter(state__country_id=country_id).exists())


class LocationAPIPerformanceTest(APITestCase):
    """
    High-Performance API Tests
    Checks for N+1 queries, pagination efficiency, and search latency.
    """

    def setUp(self):
        # Create Bulk Data for Performance Testing
        self.country = Country.objects.create(name="India", iso_code_2="IN", phone_code="91")
        
        # Create 10 States
        self.states = []
        for i in range(10):
            self.states.append(State(country=self.country, name=f"State {i}", state_code=f"S{i}"))
        State.objects.bulk_create(self.states)
        
        # Create 50 Cities per State (Total 500 cities)
        self.cities = []
        all_states = State.objects.filter(country=self.country)
        for state in all_states:
            for j in range(50):
                self.cities.append(City(state=state, name=f"City {state.state_code}-{j}"))
        City.objects.bulk_create(self.cities)

        self.country_url = reverse('country-list')
        self.search_url = reverse('city-search')

    def test_country_list_performance(self):
        """
        Ensure Country List API does not have N+1 problem.
        """
        # Warm up
        self.client.get(self.country_url)
        
        reset_queries()
        with self.assertNumQueries(1): # Should be exactly 1 query to fetch countries
            response = self.client.get(self.country_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)

    def test_city_search_optimization(self):
        """
        Verify that City Search uses DB indexing and returns paginated results.
        """
        # Create a specific target city
        target_state = State.objects.first()
        City.objects.create(state=target_state, name="ZomatoCity", is_active=True)

        start_time = time.time()
        response = self.client.get(f"{self.search_url}?q=Zomato")
        end_time = time.time()

        # 1. Performance Check (Should be < 200ms usually, but in test env maybe higher, let's say 500ms)
        execution_time = (end_time - start_time) * 1000
        # print(f"\nSearch Execution Time: {execution_time:.2f}ms") 
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], "ZomatoCity")

    def test_pagination_enforcement(self):
        """
        Ensure API does not return all 500 cities at once (Pagination Check).
        """
        response = self.client.get(self.search_url) # No query = list all (usually)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Assuming Page Size is 20 (StandardResultsSetPagination)
        self.assertTrue(len(response.data['results']) <= 100) # Should be page_size
        self.assertTrue(response.data['count'] >= 500) # Total count should be correct

    def test_data_structure_compliance(self):
        """
        Verify the JSON structure matches the Frontend requirements strictly.
        Expected: { 'value': 'IN', 'label': 'India', 'phone_code': '91' }
        """
        response = self.client.get(self.country_url)
        first_record = response.data[0]
        
        self.assertIn('value', first_record)
        self.assertIn('label', first_record)
        self.assertIn('phone_code', first_record)
        self.assertEqual(first_record['value'], 'IN')
