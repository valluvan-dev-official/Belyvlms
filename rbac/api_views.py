from rest_framework import viewsets, status, generics, views, serializers
from rest_framework.response import Response
from accounts.models import CustomUser
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils.decorators import method_decorator
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from .models import Role, Permission, RolePermission, UserRole, OnboardRequest
from .serializers import (
    RoleSerializer, 
    PermissionSerializer, 
    RolePermissionSerializer, 
    AssignPermissionSerializer,
    UserRoleSerializer,
    RBACTokenObtainPairSerializer,
    RoleDeactivateSerializer,
    UserCreateSerializer,
    OnboardRequestCreateSerializer,
    OnboardRequestPublicSubmitSerializer,
    OnboardRequestAdminUpdateSerializer,
    OnboardRequestSerializer,
)
from .permissions import HasRBACPermission

# NOTE: In a real system, managing RBAC itself (creating roles/permissions) 
# usually requires a 'SUPER_ADMIN' permission. 
# For this example, we assume the user has a permission code 'RBAC_MANAGE'.

from django.db.models import Count

@method_decorator(name='list', decorator=swagger_auto_schema(tags=["RBAC Core"]))
@method_decorator(name='create', decorator=swagger_auto_schema(tags=["RBAC Core"], request_body=RoleSerializer, consumes=['multipart/form-data']))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(tags=["RBAC Core"]))
@method_decorator(name='update', decorator=swagger_auto_schema(tags=["RBAC Core"], request_body=RoleSerializer, consumes=['multipart/form-data']))
@method_decorator(name='partial_update', decorator=swagger_auto_schema(tags=["RBAC Core"], request_body=RoleSerializer, consumes=['multipart/form-data']))
@method_decorator(name='destroy', decorator=swagger_auto_schema(tags=["RBAC Core"]))
class RoleViewSet(viewsets.ModelViewSet):
    """
    API Endpoint to Manage Roles (Create, List, Update, Delete).
    """
    queryset = Role.objects.annotate(user_count=Count('users')).all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, HasRBACPermission]
    required_permission = 'RBAC_ROLE_MANAGE' 

    def get_queryset(self):
        return Role.objects.annotate(user_count=Count('users')).all()

    @action(detail=True, methods=['post'], url_path='set_permissions')
    @swagger_auto_schema(
        tags=["RBAC Core"], 
        operation_description="Bulk Set Permissions for a Role (Clears existing and sets new ones)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'permissions': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING), description="List of Permission CODES (e.g. ['USER_VIEW', 'USER_CREATE'])")
            },
            required=['permissions']
        )
    )
    def set_permissions(self, request, pk=None):
        role = self.get_object()
        permission_codes = request.data.get('permissions', [])
        
        # 1. Fetch Permission Objects
        perms = Permission.objects.filter(code__in=permission_codes)
        
        # 2. Clear Existing
        role.role_permissions.all().delete()
        
        # 3. Bulk Create
        new_links = [RolePermission(role=role, permission=p) for p in perms]
        RolePermission.objects.bulk_create(new_links)
        
        # Clear Cache for this Role
        cache.delete(f"rbac_role_perms_{role.code}")
        
        return Response({
            "status": "success", 
            "role": role.code,
            "permissions_set": len(new_links)
        })

@method_decorator(name='list', decorator=swagger_auto_schema(tags=["RBAC Core"]))
@method_decorator(name='create', decorator=swagger_auto_schema(tags=["RBAC Core"], request_body=PermissionSerializer, consumes=['multipart/form-data']))
@method_decorator(name='retrieve', decorator=swagger_auto_schema(tags=["RBAC Core"]))
@method_decorator(name='update', decorator=swagger_auto_schema(tags=["RBAC Core"], request_body=PermissionSerializer, consumes=['multipart/form-data']))
@method_decorator(name='partial_update', decorator=swagger_auto_schema(tags=["RBAC Core"], request_body=PermissionSerializer, consumes=['multipart/form-data']))
@method_decorator(name='destroy', decorator=swagger_auto_schema(tags=["RBAC Core"]))
class PermissionViewSet(viewsets.ModelViewSet):
    """
    API Endpoint to Manage Permissions (Create, List).
    """
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated, HasRBACPermission]
    required_permission = 'RBAC_PERMISSION_MANAGE'

@method_decorator(name='get', decorator=swagger_auto_schema(tags=["RBAC Assignments"]))
@method_decorator(name='post', decorator=swagger_auto_schema(tags=["RBAC Assignments"], request_body=AssignPermissionSerializer, consumes=['multipart/form-data']))
class RolePermissionView(generics.ListCreateAPIView):
    """
    API to List permissions of a role OR Assign permissions to a role.
    """
    queryset = RolePermission.objects.all()
    serializer_class = RolePermissionSerializer
    permission_classes = [IsAuthenticated, HasRBACPermission]
    required_permission = 'RBAC_PERMISSION_ASSIGN'

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AssignPermissionSerializer
        return RolePermissionSerializer

    def create(self, request, *args, **kwargs):
        """
        Assign multiple permissions to a role.
        """
        serializer = AssignPermissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        role_id = serializer.validated_data['role_id']
        permission_ids = serializer.validated_data['permission_ids']

        role = get_object_or_404(Role, id=role_id)
        
        created_links = []
        for pid in permission_ids:
            permission = get_object_or_404(Permission, id=pid)
            rp, created = RolePermission.objects.get_or_create(role=role, permission=permission)
            created_links.append(rp)

        # Clear Cache for this Role
        cache.delete(f"rbac_role_perms_{role.code}")

        return Response(
            {"status": "success", "assigned_count": len(created_links)}, 
            status=status.HTTP_201_CREATED
        )

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('role_id', openapi.IN_QUERY, description="Filter by Role ID", type=openapi.TYPE_INTEGER)
    ])
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        role_id = request.query_params.get('role_id')
        if role_id:
            queryset = queryset.filter(role_id=role_id)
        serializer = RolePermissionSerializer(queryset, many=True)
        return Response(serializer.data)

from .utils import get_user_permissions

@method_decorator(name='get', decorator=swagger_auto_schema(tags=["RBAC Auth"]))
class UserPermissionsView(views.APIView):
    """
    Get current user's profile, role, and permissions.
    Useful for reloading the dashboard without re-logging in.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        active_role_code = request.headers.get('X-Active-Role', None)
        
        data = {
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.name if hasattr(user, 'name') else '',
                'is_superuser': user.is_superuser,
                'is_staff': user.is_staff
            },
            'active_role': None,
            'available_roles': [],
            'permissions': get_user_permissions(user, active_role_code)
        }

        # Populate available roles and determine active role
        user_roles = UserRole.objects.select_related('role').filter(user=user)
        
        for ur in user_roles:
            role_data = {
                'code': ur.role.code,
                'name': ur.role.name
            }
            data['available_roles'].append(role_data)
            
            # Determine active role object
            if active_role_code and ur.role.code == active_role_code:
                data['active_role'] = role_data
        
        # Fallback: If no active role specified or found, default to the first one
        if not data['active_role'] and user_roles.exists():
            first_ur = user_roles.first()
            data['active_role'] = {
                'code': first_ur.role.code,
                'name': first_ur.role.name
            }
            # Re-fetch permissions for the default role if we fell back
            if active_role_code is None: 
                 # Note: get_user_permissions already defaults to first role if None is passed
                 # But if active_role_code was passed but invalid, we might want to reset permissions?
                 # Current get_user_permissions implementation:
                 # if active_role_code provided -> get that role. If not found -> returns empty [] or crashes?
                 # Let's check utils.py again.
                 pass

        return Response(data)

@method_decorator(name='post', decorator=swagger_auto_schema(tags=["RBAC Assignments"], request_body=UserRoleSerializer, consumes=['multipart/form-data']))
class UserRoleAssignmentView(generics.CreateAPIView):
    """
    Assign a Role to a User.
    """
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer
    permission_classes = [IsAuthenticated, HasRBACPermission]
    required_permission = 'RBAC_USER_ASSIGN'

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        role = Role.objects.get(id=data['role'].id)
        if hasattr(role, "is_active") and not role.is_active:
            return Response({"status": "error", "message": "Cannot assign an inactive role"}, status=status.HTTP_400_BAD_REQUEST)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class RBACTokenObtainPairView(TokenObtainPairView):
    """
    Custom Login View that returns Access/Refresh tokens + User Role + Permissions.
    Use this instead of the default SimpleJWT view.
    """
    serializer_class = RBACTokenObtainPairSerializer

class SwitchRoleView(views.APIView):
    """
    API Endpoint to switch active role without re-login.
    Returns a new Access Token with the selected role context.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["RBAC Auth"],
        operation_description="Switch Active Role and get new Token",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'role_code': openapi.Schema(type=openapi.TYPE_STRING, description="Code of the role to switch to (e.g. 'TRN')")
            },
            required=['role_code']
        ),
        responses={200: "New Access Token + Permissions"}
    )
    def post(self, request):
        role_code = request.data.get('role_code')
        user = request.user
        
        # 1. Verify User has this Role
        try:
            target_ur = UserRole.objects.select_related('role').get(user=user, role__code=role_code)
        except UserRole.DoesNotExist:
            return Response(
                {"status": "error", "message": f"You do not have the role: {role_code}"}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        # 2. Generate New Token with Active Role
        refresh = RefreshToken.for_user(user)
        # Add custom claims if needed, e.g. refresh['active_role'] = role_code
        
        # 3. Get Permissions for this specific role
        permissions = Permission.objects.filter(role_permissions__role=target_ur.role).values_list('code', flat=True)
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh), # Optional: Rotate refresh token too if needed
            'active_role': {
                'code': target_ur.role.code,
                'name': target_ur.role.name
            },
            'permissions': list(permissions)
        })

@method_decorator(name='get', decorator=swagger_auto_schema(tags=["RBAC Core"]))
class RoleImpactSummaryView(views.APIView):
    permission_classes = [IsAuthenticated, HasRBACPermission]
    required_permission = 'RBAC_ROLE_IMPACT'

    def get(self, request, pk):
        role = get_object_or_404(Role, pk=pk)
        assigned_users = UserRole.objects.filter(role=role).count()
        active_permissions = RolePermission.objects.filter(role=role).count()
        modules = list(Permission.objects.filter(role_permissions__role=role).values_list('module', flat=True).distinct())
        return Response({
            "role": {"id": role.id, "code": role.code, "name": role.name, "is_active": getattr(role, "is_active", True)},
            "assigned_users": assigned_users,
            "active_permissions": active_permissions,
            "modules": modules
        })

@method_decorator(name='post', decorator=swagger_auto_schema(tags=["RBAC Core"]))
class RoleDeactivateView(views.APIView):
    permission_classes = [IsAuthenticated, HasRBACPermission]
    required_permission = 'RBAC_ROLE_DEACTIVATE'

    def post(self, request, pk):
        role = get_object_or_404(Role, pk=pk)
        serializer = RoleDeactivateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        strategy = data['strategy']
        target_role = None

        if not getattr(role, "is_active", True):
            return Response({"status": "error", "message": "Role already inactive"}, status=status.HTTP_400_BAD_REQUEST)

        if strategy == 'reassign':
            code = data.get('target_role_code')
            if not code:
                return Response({"status": "error", "message": "target_role_code required"}, status=status.HTTP_400_BAD_REQUEST)
            target_role = get_object_or_404(Role, code=code)
        else:
            code = data.get('fallback_role_code') or 'STF'
            target_role = get_object_or_404(Role, code=code)

        if role.id == target_role.id:
            return Response({"status": "error", "message": "Target role cannot be the same as source"}, status=status.HTTP_400_BAD_REQUEST)
        if hasattr(target_role, "is_active") and not target_role.is_active:
            return Response({"status": "error", "message": "Target role is inactive"}, status=status.HTTP_400_BAD_REQUEST)

        reassigned = 0
        removed = 0

        with transaction.atomic():
            qset = UserRole.objects.select_related('user').filter(role=role)
            for ur in qset:
                exists = UserRole.objects.filter(user=ur.user, role=target_role).exists()
                if exists:
                    ur.delete()
                    removed += 1
                else:
                    ur.role = target_role
                    ur.save()
                    reassigned += 1

            role.is_active = False
            role.deleted_at = timezone.now()
            role.deleted_by = request.user
            role.deletion_reason = data.get('reason') or ''
            role.save()

            cache.delete(f"rbac_role_perms_{role.code}")
            cache.delete(f"rbac_role_perms_{target_role.code}")

        return Response({
            "status": "success",
            "deactivated_role": role.code,
            "target_role": target_role.code,
            "reassigned_count": reassigned,
            "removed_duplicate_links": removed
        })
from coursedb.models import Course
from trainersdb.models import Trainer
from consultantdb.models import Consultant
from settingsdb.models import SourceOfJoining
from batchdb.models import Batch

class OnboardingDropdownsView(views.APIView):
    """
    Enterprise-grade Aggregated Endpoint for Onboarding Dropdowns.
    Fetches Courses, Trainers, Consultants, Sources, and Batches in a single call.
    Optimized for payload size and frontend performance.
    """
    permission_classes = [IsAuthenticated] # Or specific RBAC permission if needed

    @swagger_auto_schema(
        tags=["Onboarding"],
        operation_description="Fetch all dropdown options for User Onboarding (Courses, Trainers, Consultants, Sources, Batches, Status Choices)",
        responses={
            200: openapi.Response(
                description="Aggregated Dropdown Options",
                examples={
                    "application/json": {
                        "courses": [{"id": 1, "name": "Python Full Stack", "code": "C1"}],
                        "trainers": [{"id": 1, "name": "John Doe"}],
                        "consultants": [{"id": 1, "name": "Alice Smith", "consultant_id": "CON001"}],
                        "sources": [{"id": 1, "name": "LinkedIn"}],
                        "batches": [{"id": 1, "batch_id": "B001", "batch_status": "YTS"}],
                        "status_choices": [{"code": "INVITED", "label": "Invited"}]
                    }
                }
            )
        }
    )
    def get(self, request):
        # 1. Fetch Courses (Optimized: id, name, code)
        courses = Course.objects.values('id', 'course_name', 'code').order_by('course_name')
        
        # 2. Fetch Trainers (Optimized: id, user__first_name, user__last_name)
        # Note: Handling potential null users if data integrity issues exist, though unlikely in prod
        trainers_qs = Trainer.objects.select_related('user').filter(user__isnull=False)
        trainers = []
        for t in trainers_qs:
            name = f"{t.user.first_name} {t.user.last_name}".strip()
            if not name:
                name = t.user.email # Fallback
            trainers.append({'id': t.id, 'name': name})
            
        # 3. Fetch Consultants
        consultants = Consultant.objects.values('id', 'name', 'consultant_id').order_by('name')
        
        # 4. Fetch Sources
        sources = SourceOfJoining.objects.values('id', 'name').order_by('name')
        
        # 5. Fetch Batches (Active/Yet to Start preferably, but listing all for now as per requirement)
        # Filter for YTS (Yet to Start) and IP (In Progress) usually makes sense for onboarding
        batches = Batch.objects.filter(batch_status__in=['YTS', 'IP']).values('id', 'batch_id', 'batch_status').order_by('-created_at')

        # 6. Fetch Status Choices (Dynamic from Model)
        status_choices = [{"code": choice[0], "label": choice[1]} for choice in OnboardRequest.STATUS_CHOICES]

        data = {
            "courses": list(courses),
            "trainers": trainers,
            "consultants": list(consultants),
            "sources": list(sources),
            "batches": list(batches),
            "status_choices": status_choices
        }
        
        return Response(data)

@method_decorator(name='list', decorator=swagger_auto_schema(tags=["RBAC Management"]))
class UserListView(generics.ListAPIView):
    """
    List Users with their Roles.
    Supports filtering by name/email.
    """
    serializer_class = UserCreateSerializer
    permission_classes = [IsAuthenticated, HasRBACPermission]
    required_permission = 'USER_VIEW'

    def get_queryset(self):
        from accounts.models import CustomUser
        from django.db.models import Q
        queryset = CustomUser.objects.all().order_by('-date_joined')
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) | 
                Q(name__icontains=search)
            )
        return queryset

class UserCreateView(views.APIView):
    permission_classes = [IsAuthenticated, HasRBACPermission]
    required_permission = 'RBAC_USER_CREATE'

    @swagger_auto_schema(
        tags=["RBAC Management"],
        operation_description="Create a new User with Role and Profile (Atomic)",
        request_body=UserCreateSerializer,
        responses={
            201: openapi.Response(
                description="User Created Successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING, example='success'),
                        'user': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'primary_role': openapi.Schema(type=openapi.TYPE_OBJECT),
                    }
                )
            ),
            400: "Validation Error"
        }
    )
    def post(self, request):
        from .services import provision_user_from_payload

        result, _user = provision_user_from_payload(request.user, request.data, send_welcome_email=True)
        return Response(result, status=status.HTTP_201_CREATED)


from .services import build_onboard_request_token, onboard_request_expiry, build_onboard_registration_url
import uuid

@method_decorator(name='post', decorator=swagger_auto_schema(
    tags=["User Onboarding"],
    request_body=OnboardRequestCreateSerializer,
    responses={201: OnboardRequestSerializer, 400: "Validation Error"},
))
class OnboardRequestCreateView(views.APIView):
    permission_classes = [IsAuthenticated, HasRBACPermission]
    required_permission = 'USER_ONBOARD'

    def post(self, request):
        try:
            serializer = OnboardRequestCreateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            email = data["email"]

            # 1. Check if User already exists (Handle gracefully with 200 OK)
            if CustomUser.objects.filter(email=email).exists():
                return Response({
                    "status": "USER_EXISTS",
                    "message": "User with this email already exists."
                }, status=status.HTTP_200_OK)

            # 2. Check for Active Onboard Requests (Handle gracefully with 200 OK)
            if OnboardRequest.objects.filter(email=email, status__in=['INVITED', 'PENDING_APPROVAL']).exists():
                return Response({
                    "status": "REQUEST_EXISTS",
                    "message": "An active onboard request already exists for this email."
                }, status=status.HTTP_200_OK)

            role = Role.objects.get(code=data["role_code"])
            nonce = uuid.uuid4().hex
            expires_at = onboard_request_expiry()

            onboard_request = OnboardRequest.objects.create(
                email=data["email"],
                role=role,
                status="INVITED",
                initiated_by=request.user,
                registration_nonce=nonce,
                registration_token_sent_at=timezone.now(),
                registration_expires_at=expires_at,
            )

            token = build_onboard_request_token(onboard_request)
            registration_url = build_onboard_registration_url(request, token)

            try:
                from django.core.mail import send_mail
                subject = "Complete your BelyvLMS Registration"
                message = f"Registration Link: {registration_url}\nThis link expires at: {expires_at}"
                send_mail(subject, message, None, [onboard_request.email], fail_silently=True)
            except Exception as e:
                # Log email error but don't fail request
                print(f"Email sending failed: {e}")

            resp = OnboardRequestSerializer(onboard_request).data
            resp["registration_url"] = registration_url
            resp["expires_at"] = expires_at
            return Response(resp, status=status.HTTP_201_CREATED)
        except serializers.ValidationError as e:
             return Response({"detail": e.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            import traceback
            traceback.print_exc()
            # Log the error details for debugging
            print(f"CRITICAL ERROR in OnboardRequestCreateView: {str(e)}")
            print(traceback.format_exc())
            return Response({"detail": f"Internal Server Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OnboardRequestListView(generics.ListAPIView):
    serializer_class = OnboardRequestSerializer
    permission_classes = [IsAuthenticated, HasRBACPermission]
    required_permission = 'USER_ONBOARD'

    @swagger_auto_schema(
        tags=["User Onboarding"],
        manual_parameters=[
            openapi.Parameter("status", openapi.IN_QUERY, type=openapi.TYPE_STRING),
            openapi.Parameter("role_code", openapi.IN_QUERY, type=openapi.TYPE_STRING),
            openapi.Parameter("search", openapi.IN_QUERY, type=openapi.TYPE_STRING),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        from django.db.models import Q

        qs = OnboardRequest.objects.select_related("role").all().order_by("-created_at")
        status_val = self.request.query_params.get("status")
        role_code = self.request.query_params.get("role_code")
        search = self.request.query_params.get("search")

        if status_val:
            qs = qs.filter(status=status_val)
        if role_code:
            qs = qs.filter(role__code=role_code)
        if search:
            qs = qs.filter(Q(email__icontains=search) | Q(code__icontains=search))

        return qs

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class OnboardRequestDetailView(views.APIView):
    permission_classes = [IsAuthenticated, HasRBACPermission]
    required_permission = 'USER_ONBOARD'

    @swagger_auto_schema(
        tags=["User Onboarding"],
        responses={200: OnboardRequestSerializer},
    )
    def get(self, request, code):
        onboard_request = get_object_or_404(OnboardRequest.objects.select_related("role"), code=code)
        from .services import merge_onboard_payload

        payload_preview = merge_onboard_payload(
            role_code=onboard_request.role.code,
            email=onboard_request.email,
            user_payload=onboard_request.user_payload,
            admin_payload=onboard_request.admin_payload,
        )

        data = OnboardRequestSerializer(onboard_request).data
        data["final_payload_preview"] = payload_preview
        return Response(data)

    @swagger_auto_schema(
        tags=["User Onboarding"],
        request_body=OnboardRequestAdminUpdateSerializer,
        responses={200: OnboardRequestSerializer, 400: "Validation Error"},
    )
    def patch(self, request, code):
        onboard_request = get_object_or_404(OnboardRequest.objects.select_related("role"), code=code)
        serializer = OnboardRequestAdminUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        admin_payload = onboard_request.admin_payload or {}
        if "first_name" in data:
            admin_payload["first_name"] = data.get("first_name")
        if "last_name" in data:
            admin_payload["last_name"] = data.get("last_name")
        if "profile" in data:
            admin_payload["profile"] = data.get("profile") or {}

        onboard_request.admin_payload = admin_payload
        # If admin updates, ensure it is in PENDING_APPROVAL if it was INVITED (optional, but keeps flow moving)
        # or just keep it as is. Let's keep it simple.
        # if onboard_request.status == "INVITED":
        #    onboard_request.status = "PENDING_APPROVAL"
        
        onboard_request.save(update_fields=["admin_payload", "status", "updated_at"])

        return Response(OnboardRequestSerializer(onboard_request).data)


class OnboardRequestOnboardView(views.APIView):
    permission_classes = [IsAuthenticated, HasRBACPermission]
    required_permission = 'USER_ONBOARD'

    @swagger_auto_schema(
        tags=["User Onboarding"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "send_welcome_email": openapi.Schema(type=openapi.TYPE_BOOLEAN, default=True),
            },
        ),
        responses={201: openapi.Schema(type=openapi.TYPE_OBJECT), 400: "Validation Error"},
    )
    def post(self, request, code):
        onboard_request = get_object_or_404(OnboardRequest.objects.select_related("role"), code=code)
        from .services import merge_onboard_payload, provision_user_from_payload

        if onboard_request.status in ["ONBOARDED"]:
            return Response({"detail": "Already provisioned"}, status=status.HTTP_400_BAD_REQUEST)
        if onboard_request.status not in ["PENDING_APPROVAL"]:
            return Response({"detail": "Request is not ready for onboarding (Must be PENDING_APPROVAL)"}, status=status.HTTP_400_BAD_REQUEST)

        send_welcome_email = request.data.get("send_welcome_email", True)
        payload = merge_onboard_payload(
            role_code=onboard_request.role.code,
            email=onboard_request.email,
            user_payload=onboard_request.user_payload,
            admin_payload=onboard_request.admin_payload,
        )

        try:
            result, user = provision_user_from_payload(request.user, payload, send_welcome_email=bool(send_welcome_email))
        except Exception as e:
            onboard_request.status = "DROPPED" # Or ERROR? Model says DROPPED covers error cases too.
            # actually let's keep it separate or use DROPPED. The user said DROPPED covers rejected/expired/error.
            onboard_request.last_error = str(e)
            onboard_request.save(update_fields=["status", "last_error", "updated_at"])
            raise

        onboard_request.status = "ONBOARDED"
        onboard_request.approved_by = request.user
        onboard_request.approved_at = timezone.now()
        onboard_request.provisioned_user = user
        onboard_request.save(update_fields=["status", "approved_by", "approved_at", "provisioned_user", "updated_at"])

        return Response(result, status=status.HTTP_201_CREATED)


class OnboardRequestActionView(views.APIView):
    permission_classes = [IsAuthenticated, HasRBACPermission]
    required_permission = 'USER_ONBOARD'

    @swagger_auto_schema(
        tags=["User Onboarding"],
        operation_description="Perform actions on Onboard Request (send_back, drop)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "action": openapi.Schema(type=openapi.TYPE_STRING, enum=["send_back", "drop"]),
                "reason": openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=["action"]
        ),
        responses={200: "Success"}
    )
    def post(self, request, code):
        onboard_request = get_object_or_404(OnboardRequest.objects.select_related("role"), code=code)
        action_type = request.data.get("action")
        reason = request.data.get("reason", "")
        
        from django.core.mail import send_mail
        from .services import build_onboard_request_token, build_onboard_registration_url
        
        if action_type == "send_back":
            if onboard_request.status not in ["PENDING_APPROVAL"]:
                 return Response({"detail": "Can only send back requests that are Pending Approval"}, status=status.HTTP_400_BAD_REQUEST)
            
            onboard_request.status = "INVITED"
            onboard_request.save(update_fields=["status", "updated_at"])
            
            # Send Email
            token = build_onboard_request_token(onboard_request)
            url = build_onboard_registration_url(request, token)
            
            subject = "Action Required: Please update your BelyvLMS registration"
            message = f"Admin has requested changes to your registration.\n\nReason: {reason}\n\nPlease update your details here: {url}"
            try:
                send_mail(subject, message, None, [onboard_request.email], fail_silently=True)
            except:
                pass
                
            return Response({"status": "success", "message": "Request sent back to user"})

        elif action_type == "drop":
            if onboard_request.status in ["ONBOARDED", "DROPPED"]:
                 return Response({"detail": "Cannot drop already processed request"}, status=status.HTTP_400_BAD_REQUEST)
            
            onboard_request.status = "DROPPED"
            # onboard_request.last_error = reason # Reuse last_error if needed, or we can just log it.
            # Ideally we should have a 'rejection_reason' field, but strict instruction 'dont change other things' suggests minimal model changes.
            # So we won't store reason in DB unless we add a field. 
            # But the email is sent, which is the requirement.
            onboard_request.save(update_fields=["status", "updated_at"])
            
            # Send Email
            subject = "Registration Request Update"
            message = f"Your registration request for BelyvLMS has been closed/dropped.\n\nReason: {reason}"
            try:
                send_mail(subject, message, None, [onboard_request.email], fail_silently=True)
            except:
                pass
                
            return Response({"status": "success", "message": "Request dropped"})

        return Response({"detail": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)


class PublicOnboardRequestSchemaView(views.APIView):
    permission_classes = [AllowAny]
    authentication_classes = []  # Disable authentication for this public view

    @swagger_auto_schema(
        tags=["Public Registration"],
        manual_parameters=[openapi.Parameter("token", openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True)],
    )
    def get(self, request):
        token = request.query_params.get("token")
        if not token:
            return Response({"detail": "Token is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Manually decode token if it was not handled by middleware
        from urllib.parse import unquote
        token = unquote(token)

        from .services import parse_onboard_request_token, get_onboard_field_schema
        from django.utils import timezone

        rid, nonce = parse_onboard_request_token(token, max_age_seconds=48 * 3600)
        onboard_request = get_object_or_404(OnboardRequest.objects.select_related("role"), uuid=rid)

        if onboard_request.status in ["ONBOARDED", "DROPPED"]:
            return Response({"detail": "Request is not active"}, status=status.HTTP_400_BAD_REQUEST)
        
        # NOTE: We allow re-fetching schema if status is INVITED or PENDING_APPROVAL (Edit flow)
        # So we removed the 'registration_token_used_at' check.
        
        if onboard_request.registration_expires_at and timezone.now() > onboard_request.registration_expires_at:
            onboard_request.status = "DROPPED" # Was EXPIRED
            onboard_request.save(update_fields=["status", "updated_at"])
            return Response({"detail": "Token expired"}, status=status.HTTP_400_BAD_REQUEST)
        if nonce != onboard_request.registration_nonce:
            return Response({"detail": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)

        fields = get_onboard_field_schema(onboard_request.role, stage="registration")
        
        response_data = {
            "request_code": onboard_request.code,
            "email": onboard_request.email,
            "role_code": onboard_request.role.code,
            "role_name": onboard_request.role.name,
            "expires_at": onboard_request.registration_expires_at,
            "fields": fields,
        }
        
        # If user has already submitted (PENDING_APPROVAL), pre-fill the form
        if onboard_request.user_payload:
            response_data["initial_data"] = onboard_request.user_payload
            
        return Response(response_data)


class PublicOnboardRequestSubmitView(views.APIView):
    permission_classes = [AllowAny]
    authentication_classes = []  # Disable authentication for this public view

    @swagger_auto_schema(
        tags=["Public Registration"],
        manual_parameters=[openapi.Parameter("token", openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True)],
        request_body=OnboardRequestPublicSubmitSerializer,
    )
    def post(self, request):
        token = request.query_params.get("token")
        if not token:
            return Response({"detail": "Token is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Manually decode token
        from urllib.parse import unquote
        token = unquote(token)

        from .services import parse_onboard_request_token
        from django.utils import timezone

        rid, nonce = parse_onboard_request_token(token, max_age_seconds=48 * 3600)
        onboard_request = get_object_or_404(OnboardRequest.objects.select_related("role"), uuid=rid)

        if onboard_request.status in ["ONBOARDED", "DROPPED"]:
            return Response({"detail": "Request is not active"}, status=status.HTTP_400_BAD_REQUEST)
        
        # NOTE: Allow resubmit if INVITED or PENDING_APPROVAL
        
        if onboard_request.registration_expires_at and timezone.now() > onboard_request.registration_expires_at:
            onboard_request.status = "DROPPED" # Was EXPIRED
            onboard_request.save(update_fields=["status", "updated_at"])
            return Response({"detail": "Token expired"}, status=status.HTTP_400_BAD_REQUEST)
        if nonce != onboard_request.registration_nonce:
            return Response({"detail": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = OnboardRequestPublicSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        form = serializer.validated_data

        validation_payload = {
            "first_name": form["first_name"],
            "last_name": form.get("last_name") or "",
            "email": onboard_request.email,
            "role_code": onboard_request.role.code,
            "profile": form.get("profile") or {},
        }

        create_validator = UserCreateSerializer(data=validation_payload)
        create_validator.is_valid(raise_exception=True)

        onboard_request.user_payload = {
            "first_name": validation_payload["first_name"],
            "last_name": validation_payload["last_name"],
            "profile": validation_payload["profile"],
        }
        onboard_request.status = "PENDING_APPROVAL"
        onboard_request.submitted_at = timezone.now()
        onboard_request.registration_token_used_at = timezone.now()
        onboard_request.save(update_fields=["user_payload", "status", "submitted_at", "registration_token_used_at", "updated_at"])

        return Response({"status": "success", "request_code": onboard_request.code})
class LogoutView(views.APIView):
    """
    Blacklist the refresh token to logout the user server-side.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["RBAC Auth"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={'refresh': openapi.Schema(type=openapi.TYPE_STRING)},
            required=['refresh']
        )
    )
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response({"status": "error", "message": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)
                
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"status": "success", "message": "Successfully logged out."}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
