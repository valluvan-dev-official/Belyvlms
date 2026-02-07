from rest_framework import generics
from .models import SourceOfJoining
from .serializers import SourceOfJoiningSerializer
from rest_framework.permissions import IsAuthenticated

class SourceOfJoiningListAPIView(generics.ListAPIView):
    queryset = SourceOfJoining.objects.all()
    serializer_class = SourceOfJoiningSerializer
    permission_classes = [IsAuthenticated]
