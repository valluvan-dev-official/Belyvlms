from django.db import models

# Create your models here.

class temp_student(models.Model):
    
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    dept = models.CharField(max_length=50)

    def __str__(self):
        return self.name
