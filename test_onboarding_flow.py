
print("DEBUG: Top of script", flush=True)
import os
import sys

# Direct file logging
with open('success_proof.txt', 'w', encoding='utf-8') as log_file:
    def log(msg):
        print(msg, flush=True)
        log_file.write(msg + "\n")
        log_file.flush()

    log("[INFO] Script started...")
    
    try:
        import django
        from django.conf import settings
        log("Imports successful.")
        
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
        django.setup()
        log("Django setup successful.")
        
        from rbac.services import get_onboard_field_schema, provision_user_from_payload
        from rbac.models import Role
        from accounts.models import CustomUser
        from studentsdb.models import Student, StudentProfessionalProfile
        log("Model imports successful.")

        log("[INFO] Starting Onboarding Flow Test...")

        # 1. Verify Schema
        log("[CHECK] Checking Schema for Student Registration...")
        try:
            student_role = Role.objects.get(name='Student')
        except Role.DoesNotExist:
            log("[WARN] 'Student' role not found. Creating temporary role for test.")
            student_role = Role.objects.create(name='Student', code='STUDENT', is_active=True)

        schema = get_onboard_field_schema(student_role, 'registration')
        
        # Check for mandatory fields
        required_fields_to_check = ['profile.alternative_phone', 'profile.profile_picture']
        missing_requirements = []
        
        schema_map = {field['key']: field for field in schema}
        
        for key in required_fields_to_check:
            if key not in schema_map:
                missing_requirements.append(f"[FAIL] Missing field: {key}")
            elif not schema_map[key]['required']:
                missing_requirements.append(f"[FAIL] Field {key} is NOT required (Expected: True)")
            else:
                log(f"[PASS] Verified: {key} is present and REQUIRED.")

        if missing_requirements:
            log("\n".join(missing_requirements))
            log("\n[FAIL] Test Failed at Schema Verification.")
        else:
            log("[PASS] Schema Verification Passed.\n")

            # 2. Test Provisioning (Simulate Form Submission)
            log("[INFO] Testing User Provisioning with Full Payload...")
            
            test_email = "test_student_onboard@example.com"
            
            # Cleanup previous test run
            CustomUser.objects.filter(email=test_email).delete()
            
            payload = {
                "role_code": student_role.code,
                "first_name": "Test",
                "last_name": "Student",
                "email": test_email,
                "profile": {
                    "phone": "9876543210",
                    "alternative_phone": "1234567890",
                    "country_code": "+91",
                    "location": "Chennai",
                    "mode_of_class": "ON",
                    "week_type": "WD",
                    "working_status": "YES",
                    
                    # Professional Profile JSON Block
                    "professional_profile": {
                        "is_currently_employed": True,
                        "has_prior_work_experience": True,
                        "current_employment_details": {
                            "company_name": "Tech Corp",
                            "job_title": "Junior Dev",
                            "current_ctc": 5.5,
                            "notice_period_days": 30
                        },
                        "prior_experience_details": {
                            "last_company": "Startup Inc",
                            "years": 2
                        }
                    }
                }
            }

            # Mocking an initiator user (e.g., admin) - using the first superuser or creating one
            initiator = CustomUser.objects.filter(is_superuser=True).first()
            if not initiator:
                 initiator = CustomUser.objects.create_superuser('admin_test', 'admin@test.com', 'password')

            provision_user_from_payload(initiator, payload, send_welcome_email=False)
            log("[PASS] provision_user_from_payload executed successfully.")
            
            # 3. Verify Database Records
            created_user = CustomUser.objects.get(email=test_email)
            student_record = Student.objects.get(user=created_user)
            
            log(f"[PASS] User Created: {created_user.email}")
            log(f"[PASS] Student Record Created: {student_record.student_id}")
            
            # Verify Student Fields
            if student_record.alternative_phone != "1234567890":
                log(f"[FAIL] Alternative Phone mismatch: {student_record.alternative_phone}")
            else:
                log("[PASS] Student.alternative_phone verified.")
            
            # Verify Professional Profile
            prof_profile = StudentProfessionalProfile.objects.get(student=student_record)
            log("[PASS] StudentProfessionalProfile Record Found.")
            
            if prof_profile.is_currently_employed is not True:
                log("[FAIL] is_currently_employed mismatch")
            elif prof_profile.current_employment_details['company_name'] != "Tech Corp":
                log("[FAIL] JSON Data (Company Name) mismatch")
            else:
                log("[PASS] StudentProfessionalProfile JSON Data verified.")
                log("\n[SUCCESS] ALL TESTS PASSED SUCCESSFULLY!")

    except Exception as e:
        log(f"\n[FAIL] Test Failed during Provisioning/Verification: {str(e)}")
        import traceback
        traceback.print_exc(file=log_file)
