from rest_framework import generics
from .models import Consultant
from .serializers import ConsultantSerializer
from rest_framework.permissions import IsAuthenticated

class ConsultantListAPIView(generics.ListAPIView):
    queryset = Consultant.objects.all()
    serializer_class = ConsultantSerializer
    permission_classes = [IsAuthenticated]
