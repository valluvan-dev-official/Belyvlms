from rest_framework import serializers
from .models import Country, State, City

class CountrySerializer(serializers.ModelSerializer):
    value = serializers.CharField(source='iso_code_2') # Changed to ISO Code as per requirement
    label = serializers.CharField(source='name')
    class Meta:
        model = Country
        fields = ['id', 'name', 'iso_code_2', 'phone_code', 'value', 'label']

class StateSerializer(serializers.ModelSerializer):
    value = serializers.CharField(source='state_code')
    label = serializers.CharField(source='name')
    # Include Country details for reverse mapping if needed
    country_code = serializers.CharField(source='country.iso_code_2', read_only=True)

    class Meta:
        model = State
        fields = ['id', 'name', 'state_code', 'value', 'label', 'country_code']

class CitySerializer(serializers.ModelSerializer):
    value = serializers.CharField(source='name')
    label = serializers.CharField(source='name')
    
    # Nested Details for Auto-fill
    state_name = serializers.CharField(source='state.name', read_only=True)
    state_code = serializers.CharField(source='state.state_code', read_only=True)
    country_name = serializers.CharField(source='state.country.name', read_only=True)
    country_code = serializers.CharField(source='state.country.iso_code_2', read_only=True)

    class Meta:
        model = City
        fields = [
            'id', 'name', 'value', 'label', 'latitude', 'longitude',
            'state_name', 'state_code',
            'country_name', 'country_code'
        ]
