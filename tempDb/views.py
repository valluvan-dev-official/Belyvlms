from django.shortcuts import render
from rest_framework import viewsets
from .models import temp_student
from .serializers import StudentSerializer

# Create your views here.


class StudentViewSet(viewsets.ModelViewSet):

    queryset = temp_student.objects.all()
    serializer_class = StudentSerializer