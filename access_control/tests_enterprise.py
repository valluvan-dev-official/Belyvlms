from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework import status
from .models import Role, Permission, RolePermission, UserRole, UserPermissionOverride
from .services import get_user_permissions, get_cache_key

User = get_user_model()

class EnterpriseRBACTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        cache.clear()

        # Users
        self.user = User.objects.create_user(email='user@example.com', name='Test User', password='password', role='student')
        self.admin = User.objects.create_superuser(email='admin@example.com', name='Admin', password='password')

        # Permissions
        self.perm1 = Permission.objects.create(name='P1', code='p1')
        self.perm2 = Permission.objects.create(name='P2', code='p2')
        self.perm3 = Permission.objects.create(name='P3', code='p3')

        # Roles
        self.role_a = Role.objects.create(name='Role A', code='RA')
        self.role_b = Role.objects.create(name='Role B', code='RB')
        
        # Assign perms to roles
        RolePermission.objects.create(role=self.role_a, permission=self.perm1) # Role A -> p1
        RolePermission.objects.create(role=self.role_b, permission=self.perm2) # Role B -> p2

    def test_primary_role_permissions(self):
        # Assign Role A as primary (simulated via name matching)
        self.user.role = 'Role A' 
        self.user.save()
        
        perms = get_user_permissions(self.user)
        self.assertIn('p1', perms)
        self.assertNotIn('p2', perms)

    def test_additional_role_permissions(self):
        # Primary: Role A (p1)
        self.user.role = 'Role A'
        self.user.save()
        
        # Additional: Role B (p2)
        UserRole.objects.create(user=self.user, role=self.role_b)
        
        perms = get_user_permissions(self.user)
        self.assertIn('p1', perms)
        self.assertIn('p2', perms)
        self.assertNotIn('p3', perms)

    def test_user_override_allow(self):
        # User has no roles initially
        self.user.role = 'guest'
        self.user.save()
        
        # Explicitly allow p3
        UserPermissionOverride.objects.create(user=self.user, permission=self.perm3, is_granted=True)
        
        perms = get_user_permissions(self.user)
        self.assertIn('p3', perms)

    def test_user_override_deny(self):
        # Primary: Role A (p1)
        self.user.role = 'Role A'
        self.user.save()
        
        # Explicitly DENY p1
        UserPermissionOverride.objects.create(user=self.user, permission=self.perm1, is_granted=False)
        
        perms = get_user_permissions(self.user)
        self.assertNotIn('p1', perms) # Should be removed

    def test_super_admin_bypass(self):
        # Assign system role
        super_role = Role.objects.create(name='Super Admin', code='SA', is_system_role=True)
        UserRole.objects.create(user=self.user, role=super_role)
        
        perms = get_user_permissions(self.user)
        self.assertIn('p1', perms)
        self.assertIn('p2', perms)
        self.assertIn('p3', perms) # Should have ALL

    def test_cache_invalidation(self):
        self.user.role = 'Role A'
        self.user.save()
        
        # First fetch caches it
        get_user_permissions(self.user)
        self.assertIsNotNone(cache.get(get_cache_key(self.user.id)))
        
        # Add override -> Should invalidate
        UserPermissionOverride.objects.create(user=self.user, permission=self.perm3, is_granted=True)
        self.assertIsNone(cache.get(get_cache_key(self.user.id)))
        
        # Fetch again -> new result
        perms = get_user_permissions(self.user)
        self.assertIn('p3', perms)

    def test_jwt_payload(self):
        # Assign Role A
        self.user.role = 'Role A'
        self.user.save()
        
        url = '/api/auth/login/'
        data = {'email': 'user@example.com', 'password': 'password'}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token_payload = self.client.post('/api/auth/login/verify/', {'token': response.data['access']})
        
        # Decode token manually or check response body if we added it there (we did)
        self.assertIn('permissions', response.data)
        self.assertIn('p1', response.data['permissions'])
