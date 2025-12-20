from django.db import transaction
from django.apps import apps
from django.conf import settings
from django.core.exceptions import ValidationError
from accounts.models import CustomUser
from rbac.models import Role, UserRole
from .models import RoleProfileConfig, GenericProfile, ProfileFieldDefinition

class OnboardingService:
    """
    Centralized Service for creating Users, assigning Roles, and initializing Profiles.
    Follows the 'Trinity Architecture': Identity -> Authorization -> Profile.
    """

    @staticmethod
    @transaction.atomic
    def onboard_user(email, name, password, role_code, is_staff=False, is_superuser=False, profile_data=None, extra_data=None, skip_profile_validation=False):
        """
        Creates a User, assigns a Role, and creates the corresponding Profile.
        
        Args:
            email (str): User email (Identity)
            name (str): User name (Identity)
            password (str): User password
            role_code (str): RBAC Role Code (Authorization)
            is_staff (bool): Whether the user can access admin site
            is_superuser (bool): Whether the user has all permissions
            profile_data (dict): Data for the static profile fields (e.g., student_id, phone)
            extra_data (dict): Data for the dynamic profile fields (JSON)
            skip_profile_validation (bool): If True, skips strict profile validation (useful for Admin panel creation)
        
        Returns:
            user (CustomUser): The created user instance.
        """
        if profile_data is None: profile_data = {}
        if extra_data is None: extra_data = {}

        # 1. IDENTITY: Create CustomUser
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError(f"User with email {email} already exists.")
            
        # We use create_user helper but need to handle flags manually if helper doesn't support them all
        user = CustomUser.objects.create_user(
            email=email,
            name=name,
            password=password,
            role='staff' # DEPRECATED: Keeping for backward compatibility
        )
        
        # Apply Admin/Staff flags
        if is_staff or is_superuser:
            user.is_staff = is_staff or is_superuser # Superuser implies staff usually
            user.is_superuser = is_superuser
            user.save()

        # 2. AUTHORIZATION: Assign RBAC Role
        try:
            role = Role.objects.get(code=role_code)
        except Role.DoesNotExist:
            raise ValidationError(f"Role code '{role_code}' does not exist.")
            
        UserRole.objects.create(user=user, role=role)

        # 3. PROFILE: Create Role-Specific Profile
        try:
            config = RoleProfileConfig.objects.get(role=role)
        except RoleProfileConfig.DoesNotExist:
            # If no config exists, we assume no profile is needed UNLESS strict mode is on.
            # For now, we just return the user.
            return user

        if not config.is_required:
            return user

        # Validate Dynamic Fields
        if not skip_profile_validation:
            OnboardingService._validate_dynamic_fields(config, extra_data)

        if config.model_path:
            # Code-backed Profile (e.g., Student, Trainer)
            try:
                app_label, model_name = config.model_path.split('.')
                ProfileModel = apps.get_model(app_label, model_name)
            except LookupError:
                raise ValidationError(f"Profile model '{config.model_path}' not found.")
            
            # Create the profile instance
            # We assume the profile model has a 'user' field and 'extra_data' field
            profile_instance = ProfileModel(user=user, extra_data=extra_data, **profile_data)
            profile_instance.save()
            
        else:
            # Generic Profile
            GenericProfile.objects.create(
                user=user,
                role_config=config,
                data=extra_data # Generic profile stores everything in 'data'
            )

        return user

    @staticmethod
    def _validate_dynamic_fields(config, data):
        """
        Validates that required dynamic fields are present and correct.
        """
        defined_fields = ProfileFieldDefinition.objects.filter(config=config)
        
        for field in defined_fields:
            value = data.get(field.name)
            
            if field.is_required and value is None:
                raise ValidationError(f"Missing required profile field: {field.label} ({field.name})")
            
            if value is not None:
                if field.field_type == 'NUMBER' and not isinstance(value, (int, float)):
                     raise ValidationError(f"Field {field.label} must be a number.")
                if field.field_type == 'BOOLEAN' and not isinstance(value, bool):
                     raise ValidationError(f"Field {field.label} must be a boolean.")
                # Add more type checks as needed
