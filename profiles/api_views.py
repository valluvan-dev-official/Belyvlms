from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils.decorators import method_decorator

from rbac.permissions import HasRBACPermission
from .models import RoleProfileConfig
from .serializers import RoleProfileConfigSerializer, OnboardingSerializer
from .services import OnboardingService

@method_decorator(name='get', decorator=swagger_auto_schema(tags=["Profiles Config"]))
class RoleProfileConfigListView(generics.ListAPIView):
    """
    List all Role Profile Configurations.
    Useful for frontend to know which fields to render for a given role.
    """
    queryset = RoleProfileConfig.objects.all()
    serializer_class = RoleProfileConfigSerializer
    permission_classes = [IsAuthenticated, HasRBACPermission]
    required_permission = 'PROFILE_CONFIG_VIEW'

@method_decorator(name='post', decorator=swagger_auto_schema(
    tags=["Onboarding"],
    operation_description="Centralized Onboarding Endpoint. Creates User + Role + Profile (Static & Dynamic).",
    responses={
        201: openapi.Response("User Created Successfully", schema=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'status': openapi.Schema(type=openapi.TYPE_STRING),
                'user_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'email': openapi.Schema(type=openapi.TYPE_STRING)
            }
        )),
        400: "Validation Error"
    }
))
class OnboardingView(views.APIView):
    permission_classes = [IsAuthenticated, HasRBACPermission]
    required_permission = 'USER_ONBOARD'

    def post(self, request):
        serializer = OnboardingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        try:
            user = OnboardingService.onboard_user(
                email=data['email'],
                name=data['name'],
                password=data['password'],
                role_code=data['role_code'],
                profile_data=data.get('profile_data'),
                extra_data=data.get('extra_data')
            )
            
            return Response({
                "status": "success",
                "user_id": user.id,
                "email": user.email
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
