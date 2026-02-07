from django.urls import path
from .views import CountryListView, StateListView, CityListView, CitySearchView

urlpatterns = [
    path('countries/', CountryListView.as_view(), name='country-list'),
    path('states/', StateListView.as_view(), name='state-list'),
    path('cities/', CityListView.as_view(), name='city-list'),
    path('cities/search/', CitySearchView.as_view(), name='city-search'),
]
