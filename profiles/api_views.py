from rest_framework import viewsets, generics, status, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend

from rbac.permissions import HasRBACPermission
from .models import RoleProfileConfig, ProfileFieldDefinition, GenericProfile
from .serializers import RoleProfileConfigSerializer, ProfileFieldDefinitionSerializer, OnboardingSerializer, UserSerializer, GenericProfileSerializer, GenericProfileUpdateSerializer
from .services import OnboardingService
from accounts.models import CustomUser

@method_decorator(name='get', decorator=swagger_auto_schema(
    tags=["Generic Profile"],
    operation_description="Get Current User's Generic Profile (if applicable)",
    responses={200: GenericProfileSerializer()}
))
@method_decorator(name='put', decorator=swagger_auto_schema(
    tags=["Generic Profile"],
    operation_description="Update Generic Profile Data (JSON)",
    request_body=GenericProfileUpdateSerializer,
    responses={200: GenericProfileSerializer()}
))
class GenericProfileView(views.APIView):
    """
    Self-Service Endpoint for users with 'Generic Profiles'.
    Allows them to View and Update their dynamic profile data.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = GenericProfile.objects.get(user=request.user)
            serializer = GenericProfileSerializer(profile)
            return Response(serializer.data)
        except GenericProfile.DoesNotExist:
            return Response({"detail": "No Generic Profile found for this user."}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request):
        serializer = GenericProfileUpdateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        # Save Data
        profile = GenericProfile.objects.get(user=request.user)
        # Merge or Replace? Let's Merge.
        # If replace is needed, use serializer.validated_data['data'] directly.
        # Here we merge to prevent data loss of other fields.
        profile.data.update(serializer.validated_data['data'])
        profile.save()
        
        return Response(GenericProfileSerializer(profile).data)

@method_decorator(name='list', decorator=swagger_auto_schema(tags=["Profiles Config"]))
@method_decorator(name='create', decorator=swagger_auto_schema(tags=["Profiles Config"]))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(tags=["Profiles Config"]))
@method_decorator(name='update', decorator=swagger_auto_schema(tags=["Profiles Config"]))
@method_decorator(name='partial_update', decorator=swagger_auto_schema(tags=["Profiles Config"]))
@method_decorator(name='destroy', decorator=swagger_auto_schema(tags=["Profiles Config"]))
class RoleProfileConfigViewSet(viewsets.ModelViewSet):
    """
    Manage Role Profile Configurations.
    Admin can define which roles use Generic Profiles vs Dedicated Models.
    """
    queryset = RoleProfileConfig.objects.all()
    serializer_class = RoleProfileConfigSerializer
    permission_classes = [IsAuthenticated, HasRBACPermission]
    required_permission = 'PROFILE_CONFIG_MANAGE'

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.required_permission = 'PROFILE_CONFIG_VIEW'
        else:
            self.required_permission = 'PROFILE_CONFIG_MANAGE'
        return super().get_permissions()

@method_decorator(name='list', decorator=swagger_auto_schema(tags=["Profiles Config Fields"]))
@method_decorator(name='create', decorator=swagger_auto_schema(tags=["Profiles Config Fields"]))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(tags=["Profiles Config Fields"]))
@method_decorator(name='update', decorator=swagger_auto_schema(tags=["Profiles Config Fields"]))
@method_decorator(name='partial_update', decorator=swagger_auto_schema(tags=["Profiles Config Fields"]))
@method_decorator(name='destroy', decorator=swagger_auto_schema(tags=["Profiles Config Fields"]))
class ProfileFieldDefinitionViewSet(viewsets.ModelViewSet):
    """
    Manage Dynamic Fields for a Role Configuration.
    Example: Add 'University Name' to 'Guest Lecturer' role.
    """
    queryset = ProfileFieldDefinition.objects.all()
    serializer_class = ProfileFieldDefinitionSerializer
    permission_classes = [IsAuthenticated, HasRBACPermission]
    required_permission = 'PROFILE_CONFIG_MANAGE'
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['config'] # Allow filtering by config ID

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.required_permission = 'PROFILE_CONFIG_VIEW'
        else:
            self.required_permission = 'PROFILE_CONFIG_MANAGE'
        return super().get_permissions()

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
    required_permission = 'USER_MANAGEMENT_CREATE'

    def post(self, request):
        serializer = OnboardingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data

        # Security Check: Superuser Privilege Escalation Prevention
        # If the request asks to make a user a 'superuser' or 'staff', ensure the requestor IS a superuser.
        # Currently, OnboardingSerializer does not expose 'is_superuser' or 'is_staff'.
        # However, we must ensure 'role_code' logic doesn't implicitly grant it.
        
        # If we later add 'is_superuser' to serializer, this check is mandatory:
        is_superuser_request = data.get('is_superuser', False)
        if is_superuser_request and not request.user.is_superuser:
             return Response(
                 {"detail": "Only an existing Superuser can create another Superuser."},
                 status=status.HTTP_403_FORBIDDEN
             )
        
        try:
            user = OnboardingService.onboard_user(
                email=data['email'],
                name=data['name'],
                password=data['password'],
                role_code=data['role_code'],
                profile_data=data.get('profile_data'),
                extra_data=data.get('extra_data'),
                # Explicitly pass these based on request or default to False
                is_superuser=is_superuser_request
            )
            
            return Response({
                "status": "success",
                "user_id": user.id,
                "email": user.email
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(name='list', decorator=swagger_auto_schema(tags=["User Management"]))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(tags=["User Management"]))
class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List and Retrieve Users.
    Used by Frontend Service Layer to display user lists.
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, HasRBACPermission]
    required_permission = 'USER_MANAGEMENT_VIEW'
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['role', 'is_active', 'email']

    def get_queryset(self):
        # Optional: Filter by role if passed in query params (handled by DjangoFilterBackend)
        return CustomUser.objects.all().order_by('-id')
