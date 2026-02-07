from rest_framework import generics, filters
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from .models import Country, State, City
from .serializers import CountrySerializer, StateSerializer, CitySerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class CountryListView(generics.ListAPIView):
    serializer_class = CountrySerializer
    permission_classes = [AllowAny]
    queryset = Country.objects.filter(is_active=True).order_by('name')

class StateListView(generics.ListAPIView):
    serializer_class = StateSerializer
    permission_classes = [AllowAny]
    pagination_class = None # Dropdowns usually don't need pagination for states

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('country', openapi.IN_QUERY, description="Country ISO Code (e.g. 'IN', 'US') or ID", type=openapi.TYPE_STRING)
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        country_code = self.request.query_params.get('country')
        
        # If no country provided, return empty list (Dependent Dropdown Logic)
        if not country_code:
            return State.objects.none()

        # Handle both ID and ISO Code
        if country_code.isdigit():
             return State.objects.filter(country__id=country_code, is_active=True).order_by('name')
        
        # Default to India if not specified or specific ISO
        if len(country_code) == 2:
            return State.objects.filter(country__iso_code_2__iexact=country_code, is_active=True).order_by('name')
            
        return State.objects.filter(country__name__iexact=country_code, is_active=True).order_by('name')

class CityListView(generics.ListAPIView):
    serializer_class = CitySerializer
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('state', openapi.IN_QUERY, description="State Name or Code", type=openapi.TYPE_STRING)
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        state_name = self.request.query_params.get('state')
        if not state_name:
            return City.objects.none()
            
        return City.objects.filter(state__name__iexact=state_name, is_active=True).order_by('name')

class CitySearchView(generics.ListAPIView):
    serializer_class = CitySerializer
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'state__name', 'state__country__name']

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('q', openapi.IN_QUERY, description="Search term for cities (e.g. 'Chen')", type=openapi.TYPE_STRING)
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = City.objects.filter(is_active=True)
        q = self.request.query_params.get('q', None)
        if q:
            queryset = queryset.filter(name__icontains=q)
        return queryset.order_by('name')
