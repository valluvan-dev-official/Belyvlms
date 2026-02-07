
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from rbac.models import Role, Permission, RolePermission, UserRole
from django.core.cache import cache

User = get_user_model()

class AuthMePermissionTestCase(TestCase):
    def setUp(self):
        # Clear cache to ensure clean state
        cache.clear()

        # 1. Create User
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpassword123',
            name='Test User'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # 2. Create Roles
        self.role_sam = Role.objects.create(code='SAM', name='Super Admin System')
        self.role_trn = Role.objects.create(code='TRN', name='Tutor')

        # 3. Create Permissions
        self.perm_audit_view = Permission.objects.create(code='AUDIT_LOG_VIEW', name='View Audit Logs', module='Audit')
        self.perm_audit_export = Permission.objects.create(code='AUDIT_LOG_EXPORT', name='Export Audit Logs', module='Audit')
        self.perm_course_view = Permission.objects.create(code='COURSE_VIEW', name='View Courses', module='Courses')

        # 4. Assign Permissions to Roles
        # SAM gets Audit perms
        RolePermission.objects.create(role=self.role_sam, permission=self.perm_audit_view)
        RolePermission.objects.create(role=self.role_sam, permission=self.perm_audit_export)
        
        # TRN gets Course perm
        RolePermission.objects.create(role=self.role_trn, permission=self.perm_course_view)

        # 5. Assign Roles to User
        UserRole.objects.create(user=self.user, role=self.role_sam)
        UserRole.objects.create(user=self.user, role=self.role_trn)

        self.url = reverse('rbac-me')

    def test_auth_me_default_role(self):
        """
        Test /auth/me/ without header. 
        Should default to one of the roles (usually the first created/assigned).
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        active_role = data.get('active_role')
        permissions = data.get('permissions')
        
        print(f"\n[Test Default] Active Role: {active_role['code']}")
        print(f"[Test Default] Permissions: {permissions}")

        self.assertIsNotNone(active_role)
        self.assertIn(active_role['code'], ['SAM', 'TRN'])
        
        # Verify permissions match the selected role
        if active_role['code'] == 'SAM':
            self.assertIn('AUDIT_LOG_VIEW', permissions)
            self.assertNotIn('COURSE_VIEW', permissions)
        elif active_role['code'] == 'TRN':
            self.assertIn('COURSE_VIEW', permissions)
            self.assertNotIn('AUDIT_LOG_VIEW', permissions)

    def test_auth_me_explicit_sam_role(self):
        """
        Test /auth/me/ with X-Active-Role: SAM.
        MUST return Audit permissions and NO Course permissions.
        """
        self.client.credentials(HTTP_X_ACTIVE_ROLE='SAM')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        active_role = data.get('active_role')
        permissions = data.get('permissions')

        print(f"\n[Test SAM] Active Role: {active_role['code']}")
        print(f"[Test SAM] Permissions: {permissions}")

        self.assertEqual(active_role['code'], 'SAM')
        self.assertIn('AUDIT_LOG_VIEW', permissions)
        self.assertIn('AUDIT_LOG_EXPORT', permissions)
        self.assertNotIn('COURSE_VIEW', permissions) # STRICT ISOLATION CHECK

    def test_auth_me_explicit_trn_role(self):
        """
        Test /auth/me/ with X-Active-Role: TRN.
        MUST return Course permissions and NO Audit permissions.
        """
        self.client.credentials(HTTP_X_ACTIVE_ROLE='TRN')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        active_role = data.get('active_role')
        permissions = data.get('permissions')

        print(f"\n[Test TRN] Active Role: {active_role['code']}")
        print(f"[Test TRN] Permissions: {permissions}")

        self.assertEqual(active_role['code'], 'TRN')
        self.assertIn('COURSE_VIEW', permissions)
        self.assertNotIn('AUDIT_LOG_VIEW', permissions) # STRICT ISOLATION CHECK
        self.assertNotIn('AUDIT_LOG_EXPORT', permissions)

    def test_auth_me_invalid_role_fallback(self):
        """
        Test /auth/me/ with invalid role. Should fallback to default valid role.
        """
        self.client.credentials(HTTP_X_ACTIVE_ROLE='INVALID_ROLE')
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        active_role = data.get('active_role')
        
        print(f"\n[Test Fallback] Requested: INVALID -> Got: {active_role['code']}")
        self.assertIn(active_role['code'], ['SAM', 'TRN'])

