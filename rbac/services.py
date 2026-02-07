from django.db import transaction
from .models import Role, RoleSequence, UserRole
from django.core.exceptions import ValidationError
from django.core import signing
from django.utils import timezone
from datetime import timedelta
from urllib.parse import quote
from .serializers import UserRoleSerializer, RoleSerializer
# from accounts.serializers import UserSerializer  <-- This import was failing
# Use CustomUserSerializer or define a minimal one locally to avoid circular deps
from .utils import get_user_permissions
from django.core.cache import cache

def serialize_user_minimal(user):
    return {
        'id': user.id,
        'email': user.email,
        'name': user.name if hasattr(user, 'name') else '',
        'is_superuser': user.is_superuser,
        'is_staff': user.is_staff
    }

def build_auth_context(user, active_role_code=None):
    """
    Builds a consistent auth response for Login, Get-Me, and Switch-Role.
    
    Args:
        user (CustomUser): The authenticated user.
        active_role_code (str, optional): The requested role code (e.g., 'TRN'). 
                                          If None or 'undefined', logic attempts to fallback.

    Returns:
        dict: Standardized auth context containing user info, active role, available roles, and permissions.
    """
    
    # 1. Sanitize Input
    if active_role_code in ['undefined', 'null', '']:
        active_role_code = None

    # 2. Fetch User's Available Roles
    available_roles_data = []
    
    # Helper to resolve role object based on code
    def get_role_by_code(code):
        return None

    # Unified Logic: All users (including Superusers) only see roles explicitly assigned to them.
    # We fetch only the roles assigned in the UserRole table.
    user_roles_qs = UserRole.objects.select_related('role').filter(user=user)
    user_roles = list(user_roles_qs) # Evaluate once to save DB calls

    for ur in user_roles:
        available_roles_data.append({'code': ur.role.code, 'name': ur.role.name})
        
    def get_role_by_code(code):
        # In-memory lookup since we already fetched them
        return next((ur.role for ur in user_roles if ur.role.code == code), None)

    active_role_obj = None
    target_role_code = active_role_code

    # 3. Determine Active Role Priority
    # Priority A: Explicitly requested active_role_code (if valid)
    if target_role_code:
        active_role_obj = get_role_by_code(target_role_code)
        if not active_role_obj:
            # Requested role invalid for this user -> Fallback needed
            target_role_code = None
    
    # Priority B: Last Active Role (from DB)
    if not active_role_obj and not target_role_code:
        last_role = getattr(user, 'last_active_role', None)
        if last_role:
            active_role_obj = get_role_by_code(last_role)
            if active_role_obj:
                target_role_code = last_role
    
    # Priority C: Default (First Available Role)
    if not active_role_obj:
        if available_roles_data:
            # Pick the first one from the list
            first_code = available_roles_data[0]['code']
            active_role_obj = get_role_by_code(first_code)
            if active_role_obj:
                target_role_code = active_role_obj.code


    # 4. Prepare Response Data
    
    # Available Roles already populated in Step 2


    active_role_data = None
    if active_role_obj:
        active_role_data = {
            'code': active_role_obj.code,
            'name': active_role_obj.name
        }

    # 5. Fetch Permissions (Strictly for the resolved target role)
    # Note: get_user_permissions handles the caching and superuser logic
    permissions = get_user_permissions(user, target_role_code)

    return {
        "user": serialize_user_minimal(user),
        "active_role": active_role_data,
        "available_roles": available_roles_data,
        "permissions": permissions
    }

class IDGeneratorService:
    """
    Service to generate role-based IDs atomically.
    Usage:
        new_id = IDGeneratorService.generate_next_id('Student', user_obj)
        # Returns 'BTR0801'
    """
    
    @staticmethod
    def generate_next_id(role_name, triggered_by_user=None):
        try:
            with transaction.atomic():
                # 1. Lock the sequence row
                role = Role.objects.get(name=role_name)
                # Ensure sequence exists (it should, thanks to our seed script)
                sequence, _ = RoleSequence.objects.select_for_update().get_or_create(role=role)
                
                # 2. Increment
                sequence.current_sequence += 1
                
                # 3. Audit
                if triggered_by_user and triggered_by_user.is_authenticated:
                    sequence.last_updated_by = triggered_by_user
                
                sequence.save()
                
                # 4. Format ID
                # Use override if present, else use role code
                prefix = sequence.prefix_override if sequence.prefix_override else role.code
                
                # Format: PREFIX + 4-digit Number (e.g., BTR0001)
                # Note: Enterprise systems often use 0-padding
                formatted_id = f"{prefix}{sequence.current_sequence:04d}"
                
                return formatted_id
                
        except Role.DoesNotExist:
            raise ValidationError(f"Role '{role_name}' does not exist.")
        except Exception as e:
            raise ValidationError(f"ID Generation failed: {str(e)}")


def build_onboard_request_token(onboard_request):
    return signing.dumps(
        {"rid": str(onboard_request.uuid), "nonce": onboard_request.registration_nonce},
        salt="rbac.onboard_request.registration",
        compress=True,
    )


def parse_onboard_request_token(token, max_age_seconds):
    data = signing.loads(
        token,
        salt="rbac.onboard_request.registration",
        max_age=max_age_seconds,
    )
    return data.get("rid"), data.get("nonce")


def onboard_request_expiry(default_hours=48):
    return timezone.now() + timedelta(hours=default_hours)


def build_onboard_registration_url(request, token):
    from django.conf import settings

    encoded_token = quote(str(token or ""), safe="")
    base_url = (getattr(settings, "FRONTEND_BASE_URL", "") or "").strip()
    if base_url:
        base_url = base_url.rstrip("/")
        return f"{base_url}/public/register?token={encoded_token}"
    return request.build_absolute_uri(f"/public/register?token={encoded_token}")


def get_onboard_field_schema(role, stage):
    from profiles.models import RoleProfileConfig

    fields = []

    if stage == "registration":
        fields.extend([
            {"key": "first_name", "label": "First Name", "type": "TEXT", "required": True, "section": "Personal"},
            {"key": "last_name", "label": "Last Name", "type": "TEXT", "required": False, "section": "Personal"},
            {"key": "email", "label": "Email Address", "type": "EMAIL", "required": True, "section": "Personal"}, # Added Email
        ])

        if role.name == "Student":
            fields.extend([
                # --- Section 1: Personal Information ---
                {"key": "profile.phone", "label": "Phone Number", "type": "NUMBER", "required": True, "section": "Personal"},
                {"key": "profile.alternative_phone", "label": "Alternative Phone", "type": "NUMBER", "required": True, "section": "Personal"},
                {"key": "profile.country_code", "label": "Country Code", "type": "CHOICE", "options": ["+91", "+1", "+44"], "required": False, "section": "Personal", "default": "+91"},
                {"key": "profile.profile_picture", "label": "Profile Picture", "type": "FILE", "required": True, "section": "Personal"},
                
                # Location Split (Replaces single location field)
                {"key": "profile.country", "label": "Country", "type": "CHOICE", "options": ["India"], "required": True, "section": "Personal", "default": "India"},
                {"key": "profile.state", "label": "State", "type": "API_DROPDOWN", "api_url": "/api/locations/states/", "depends_on": "profile.country", "required": True, "section": "Personal"},
                {"key": "profile.city", "label": "City", "type": "API_DROPDOWN", "api_url": "/api/locations/cities/", "depends_on": "profile.state", "required": True, "section": "Personal"},
                
                # --- Section 2: Academic Details ---
                {"key": "profile.ugdegree", "label": "UG Degree", "type": "TEXT", "required": False, "section": "Education"},
                {"key": "profile.ugbranch", "label": "UG Branch", "type": "TEXT", "required": False, "section": "Education"},
                {"key": "profile.ugpassout", "label": "UG Passout Year", "type": "NUMBER", "required": False, "section": "Education"},
                {"key": "profile.ugpercentage", "label": "UG Percentage / CGPA", "type": "NUMBER", "required": False, "section": "Education"},
                {"key": "profile.pgdegree", "label": "PG Degree", "type": "TEXT", "required": False, "section": "Education"},
                {"key": "profile.pgbranch", "label": "PG Branch", "type": "TEXT", "required": False, "section": "Education"},
                {"key": "profile.pgpassout", "label": "PG Passout Year", "type": "NUMBER", "required": False, "section": "Education"},
                {"key": "profile.pgpercentage", "label": "PG Percentage", "type": "NUMBER", "required": False, "section": "Education"},

                # --- Section 3: Professional Profile ---
                {"key": "profile.working_status", "label": "Are you currently working?", "type": "CHOICE", "options": ["YES", "NO"], "required": True, "section": "Work"},
                
                # Professional Fields (Mapped to StudentProfessionalProfile JSON structure)
                # If Working Status = YES
                {"key": "profile.professional_profile.current_employment_details.total_experience_years", "label": "Total Experience (Years)", "type": "NUMBER", "required": False, "section": "Work"},
                {"key": "profile.professional_profile.current_employment_details.total_experience_months", "label": "Total Experience (Months)", "type": "NUMBER", "required": False, "section": "Work"},
                {"key": "profile.professional_profile.current_employment_details.company_name", "label": "Current Company Name", "type": "TEXT", "required": False, "section": "Work"},
                {"key": "profile.professional_profile.current_employment_details.job_title", "label": "Current Job Title", "type": "TEXT", "required": False, "section": "Work"},
                {"key": "profile.professional_profile.current_employment_details.current_ctc", "label": "Current CTC (LPA)", "type": "NUMBER", "required": False, "section": "Work"},
                {"key": "profile.professional_profile.current_employment_details.notice_period_days", "label": "Notice Period (Days)", "type": "NUMBER", "required": False, "section": "Work"},
                {"key": "profile.professional_profile.current_employment_details.linkedin_url", "label": "LinkedIn Profile URL", "type": "TEXT", "required": False, "section": "Work"},
                
                # If Working Status = NO
                {"key": "profile.professional_profile.fresher_readiness_profile.has_internship_experience", "label": "Have you done any Internships?", "type": "BOOLEAN", "required": False, "section": "Work"},
                {"key": "profile.professional_profile.fresher_readiness_profile.has_career_gap", "label": "Any Career Gap?", "type": "BOOLEAN", "required": False, "section": "Work"},

                # --- Section 4: Course Enrollment ---
                {"key": "profile.course_id", "label": "Select Course", "type": "NUMBER", "required": False, "section": "Education"}, # Dropdown handled by frontend using ID
                {"key": "profile.mode_of_class", "label": "Mode of Training", "type": "CHOICE", "options": ["ON", "OFF"], "required": True, "section": "Education"},
                {"key": "profile.week_type", "label": "Batch Type", "type": "CHOICE", "options": ["WD", "WE"], "required": True, "section": "Education"},
                {"key": "profile.source_of_joining", "label": "Source of Joining", "type": "NUMBER", "required": False, "section": "Education"},
            ])
        elif role.name == "Trainer":
            fields.extend([
                {"key": "profile.phone", "type": "TEXT", "required": False, "section": "Personal"},
                {"key": "profile.employment_type", "type": "CHOICE", "options": ["FT", "FL"], "required": True, "section": "Work"},
                {"key": "profile.years_of_experience", "type": "NUMBER", "required": False, "section": "Work"},
                {"key": "profile.demo_link", "type": "TEXT", "required": False, "section": "Work"},
                {"key": "profile.location", "type": "TEXT", "required": False, "section": "Personal"},
                {"key": "profile.other_location", "type": "TEXT", "required": False, "section": "Personal"},
                {"key": "profile.timing_slots", "type": "JSON", "required": False, "section": "Work"},
            ])

    if stage == "admin":
        if role.name == "Student":
            fields.extend([
                {"key": "profile.consultant", "type": "NUMBER", "required": False, "section": "Work"},
                {"key": "profile.source_of_joining", "type": "NUMBER", "required": False, "section": "Work"},
                {"key": "profile.course_id", "type": "NUMBER", "required": False, "section": "Education"},
                {"key": "profile.trainer_id", "type": "NUMBER", "required": False, "section": "Education"},
                {"key": "profile.batch_id", "type": "TEXT", "required": False, "section": "Education"},
                {"key": "profile.course_status", "type": "TEXT", "required": False, "section": "Education"},
                {"key": "profile.pl_required", "type": "BOOLEAN", "required": False, "section": "Work"},
                {"key": "profile.fees_total", "type": "NUMBER", "required": False, "section": "Work"},
                {"key": "profile.fees_paid", "type": "NUMBER", "required": False, "section": "Work"},
                {"key": "profile.payment_schedule", "type": "JSON", "required": False, "section": "Work"},
            ])
        elif role.name == "Trainer":
            fields.extend([
                {"key": "profile.stack_ids", "type": "JSON", "required": False, "section": "Work"},
                {"key": "profile.is_active", "type": "BOOLEAN", "required": False, "section": "Work"},
                {"key": "profile.commercials", "type": "JSON", "required": False, "section": "Work"},
            ])

    role_config = RoleProfileConfig.objects.filter(role=role).first()
    if role_config:
        for f in role_config.dynamic_fields.all().order_by("id"):
            field = {
                "key": f"profile.{f.name}",
                "type": f.field_type,
                "required": bool(f.is_required),
                "section": "Work" # Default for dynamic fields
            }
            if f.field_type == "CHOICE":
                field["options"] = f.options or []
            fields.append(field)

    return fields


def _sanitize_val(val):
    if val is None:
        return None
    s_val = str(val).lower().strip()
    if s_val in ["nan", "null", "undefined", ""]:
        return None
    return val


def _sanitize_int(val):
    cleaned = _sanitize_val(val)
    if cleaned is None:
        return None
    try:
        return int(float(cleaned))
    except (ValueError, TypeError):
        if isinstance(cleaned, str) and " - " in cleaned:
            try:
                potential_id = cleaned.split(" - ")[0]
                return int(float(potential_id))
            except (ValueError, TypeError):
                return None
        return None


def merge_onboard_payload(role_code, email, user_payload, admin_payload):
    user_payload = user_payload or {}
    admin_payload = admin_payload or {}

    first_name = admin_payload.get("first_name") or user_payload.get("first_name")
    last_name = admin_payload.get("last_name") if "last_name" in admin_payload else user_payload.get("last_name")

    user_profile = (user_payload.get("profile") or {}) if isinstance(user_payload, dict) else {}
    admin_profile = (admin_payload.get("profile") or {}) if isinstance(admin_payload, dict) else {}

    merged_profile = {**user_profile, **admin_profile}

    return {
        "first_name": first_name,
        "last_name": last_name or "",
        "email": email,
        "role_code": role_code,
        "profile": merged_profile,
    }


def provision_user_from_payload(initiator_user, payload, send_welcome_email=True):
    from rest_framework.exceptions import ValidationError as DRFValidationError
    from accounts.models import CustomUser
    from studentsdb.models import Student
    from trainersdb.models import Trainer
    from paymentdb.models import Payment
    from batchdb.models import Batch, BatchStudent, BatchTransaction
    from django.core.mail import send_mail
    from profiles.models import RoleProfileConfig, GenericProfile
    from .models import UserRole
    from .serializers import UserCreateSerializer

    serializer = UserCreateSerializer(data=payload)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    role = Role.objects.get(code=data["role_code"])
    name = f"{data['first_name']} {data.get('last_name') or ''}".strip()
    accounts_role = role.name.lower()

    with transaction.atomic():
        user = CustomUser.objects.create_user(
            email=data["email"],
            name=name,
            role=accounts_role,
            password="temp",
            must_change_password=True,
        )
        UserRole.objects.create(user=user, role=role)

        profile_data = data.get("profile") or {}
        generated_password = None

        if role.name == "Student":
            fees_total = profile_data.pop("fees_total", None)
            fees_paid = profile_data.pop("fees_paid", None)
            payment_schedule = profile_data.pop("payment_schedule", [])

            phone = profile_data.pop("phone", None)
            alternative_phone = profile_data.pop("alternative_phone", None)
            country_code = profile_data.pop("country_code", "+91")
            # alternative_country_code logic if needed, defaulting to +91
            alternative_country_code = profile_data.pop("alternative_country_code", "+91")
            location = profile_data.pop("location", None)
            
            # Location Split
            country = profile_data.pop("country", "India")
            state = profile_data.pop("state", None)
            city = profile_data.pop("city", None)
            
            # Auto-construct location string if missing
            if not location and city and state:
                location = f"{city}, {state}, {country}"
            
            # Extract Professional Profile Data
            professional_profile_data = profile_data.pop("professional_profile", {})

            pl_required = profile_data.pop("pl_required", False)
            consultant_id = _sanitize_int(profile_data.pop("consultant", None))
            soj_id = _sanitize_int(profile_data.pop("source_of_joining", None))
            batch_id = _sanitize_val(profile_data.pop("batch_id", None))

            student = Student.objects.create(
                user=user,
                first_name=data["first_name"],
                last_name=data.get("last_name") or "",
                email=data["email"],
                phone=phone,
                alternative_phone=alternative_phone,
                country_code=country_code,
                alternative_country_code=alternative_country_code,
                location=location,
                country=country,
                state=state,
                city=city,
                mode_of_class=profile_data.pop("mode_of_class", "ON"),
                week_type=profile_data.pop("week_type", "WD"),
                course_id=_sanitize_int(profile_data.pop("course_id", None)),
                trainer_id=_sanitize_int(profile_data.pop("trainer_id", None)),
                course_status=profile_data.pop("course_status", "YTS"),
                pl_required=pl_required,
                consultant_id=consultant_id,
                source_of_joining_id=soj_id,
                extra_data=profile_data,
            )
            
            # Create StudentProfessionalProfile if data exists
            if professional_profile_data:
                from studentsdb.models import StudentProfessionalProfile
                StudentProfessionalProfile.objects.create(
                    student=student,
                    is_currently_employed=professional_profile_data.get("is_currently_employed", False),
                    has_prior_work_experience=professional_profile_data.get("has_prior_work_experience", False),
                    current_employment_details=professional_profile_data.get("current_employment_details", {}),
                    prior_experience_details=professional_profile_data.get("prior_experience_details", {}),
                    technical_experience_profile=professional_profile_data.get("technical_experience_profile", {}),
                    fresher_readiness_profile=professional_profile_data.get("fresher_readiness_profile", {}),
                )

            if batch_id:
                try:
                    batch_obj = Batch.objects.get(batch_id=batch_id)
                    BatchStudent.objects.create(
                        batch=batch_obj,
                        student=student,
                        is_active=True,
                        activated_at=timezone.now(),
                    )
                    BatchTransaction.log_transaction(
                        batch=batch_obj,
                        transaction_type="STUDENT_ADDED",
                        user=initiator_user,
                        details={
                            "student_id": student.id,
                            "student_name": str(student),
                            "activated_at": str(timezone.now()),
                        },
                        affected_students=[student],
                    )
                except Batch.DoesNotExist:
                    pass

            if fees_total is not None:
                emi_count = len(payment_schedule)
                payment = Payment.objects.create(
                    student=student,
                    total_fees=fees_total,
                    amount_paid=fees_paid or 0,
                    emi_type=str(emi_count) if 1 <= emi_count <= 4 else "NONE",
                )
                for i, item in enumerate(payment_schedule, start=1):
                    if i > 4:
                        break
                    setattr(payment, f"emi_{i}_amount", item.get("amount"))
                    setattr(payment, f"emi_{i}_date", item.get("date"))
                payment.save()

            generated_password = f"{student.student_id}@{timezone.now().year}"

        elif role.name == "Trainer":
            trainer = Trainer.objects.create(
                user=user,
                name=name,
                email=data["email"],
                phone_number=profile_data.pop("phone", None),
                employment_type=profile_data.pop("employment_type", "FT"),
                years_of_experience=profile_data.pop("years_of_experience", 0),
                demo_link=profile_data.pop("demo_link", None),
                timing_slots=profile_data.pop("timing_slots", []),
                commercials=profile_data.pop("commercials", []),
                extra_data=profile_data,
            )
            generated_password = f"{trainer.trainer_id}@{timezone.now().year}"

        else:
            generated_password = f"{role.code}{timezone.now().year}"
            role_config = RoleProfileConfig.objects.filter(role=role).first()
            if role_config and not role_config.model_path:
                GenericProfile.objects.create(
                    user=user,
                    role_config=role_config,
                    data=profile_data,
                )

        if not generated_password:
            raise DRFValidationError({"detail": "Password generation failed"})

        user.set_password(generated_password)
        user.save()

    if send_welcome_email:
        try:
            subject = "Your BelyvLMS Account"
            message = f"Login Email: {user.email}\nPassword: {generated_password}"
            send_mail(subject, message, None, [user.email], fail_silently=True)
        except Exception:
            pass

    return {
        "status": "success",
        "user": {"id": user.id, "email": user.email, "name": user.name},
        "primary_role": {"code": role.code, "name": role.name},
    }, user
