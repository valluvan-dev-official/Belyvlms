from django.db import models
from django.utils import timezone

class Country(models.Model):
    name = models.CharField(max_length=100)
    iso_code_2 = models.CharField(max_length=2, unique=True, db_index=True)
    iso_code_3 = models.CharField(max_length=3, blank=True, null=True)
    phone_code = models.CharField(max_length=20, blank=True, null=True)
    currency_code = models.CharField(max_length=10, blank=True, null=True)
    emoji = models.CharField(max_length=20, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Countries"
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['iso_code_2']),
        ]

    def __str__(self):
        return f"{self.name} ({self.iso_code_2})"

class State(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='states')
    name = models.CharField(max_length=100)
    state_code = models.CharField(max_length=20, blank=True, null=True, help_text="ISO subdivision code (e.g., TN, CA)")
    
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('country', 'state_code', 'name') # Combined constraint to allow same code in diff countries, but logic usually handled by country filter
        indexes = [
            models.Index(fields=['state_code']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return f"{self.name}, {self.country.iso_code_2}"

class City(models.Model):
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='cities')
    name = models.CharField(max_length=100, db_index=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Cities"
        indexes = [
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return self.name
