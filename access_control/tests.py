from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import Role, Module, Permission, RolePermission, UserProfile

User = get_user_model()

class RBACSystemTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create Admin User (superuser) to manage roles
        self.admin_user = User.objects.create_superuser(
            email='admin@example.com',
            name='Super Admin',
            password='password123'
        )
        self.client.force_authenticate(user=self.admin_user)
        
        # Create Modules
        self.module_course = Module.objects.create(name='Courses', slug='courses')
        self.module_report = Module.objects.create(name='Reports', slug='reports')

        # Create Permissions
        self.perm_course_view = Permission.objects.create(
            name='View Courses',
            code='course_view',
            module=self.module_course,
            action='view'
        )
        self.perm_course_create = Permission.objects.create(
            name='Create Courses',
            code='course_create',
            module=self.module_course,
            action='create'
        )

    def test_role_creation_flow(self):
        """
        Test that an admin can create a role.
        """
        data = {
            "name": "Trainer",
            "code": "TR",
            "is_active": True,
            "description": "Course Instructor"
        }
        response = self.client.post('/api/rbac/roles/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Role.objects.count(), 1)
        self.assertEqual(Role.objects.first().code, 'TR')

    def test_permission_assignment(self):
        """
        Test assigning permissions to a role.
        """
        role = Role.objects.create(name="Trainer", code="TR")
        
        data = {
            "role": role.id,
            "permissions": [self.perm_course_view.id, self.perm_course_create.id]
        }
        response = self.client.post('/api/rbac/role-permissions/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(RolePermission.objects.count(), 2)

    def test_user_creation_with_role(self):
        """
        Test creating a user with a specific role and ID generation.
        """
        role = Role.objects.create(name="Student", code="ST")
        
        data = {
            "email": "student1@example.com",
            "name": "John Student",
            "password": "password123",
            "role_id": role.id
        }
        
        response = self.client.post('/api/rbac/users/create/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        user = User.objects.get(email="student1@example.com")
        profile = UserProfile.objects.get(user=user)
        
        # Check ID Generation
        self.assertEqual(profile.role_based_id, "ST001")
        self.assertEqual(profile.role, role)
        
        # Create another student to check increment
        data2 = {
            "email": "student2@example.com",
            "name": "Jane Student",
            "password": "password123",
            "role_id": role.id
        }
        response2 = self.client.post('/api/rbac/users/create/', data2)
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        
        user2 = User.objects.get(email="student2@example.com")
        profile2 = UserProfile.objects.get(user=user2)
        self.assertEqual(profile2.role_based_id, "ST002")

    def test_my_permissions_api(self):
        """
        Test fetching permissions for the logged-in user.
        """
        # Setup Role and User
        role = Role.objects.create(name="Manager", code="MG")
        RolePermission.objects.create(role=role, permission=self.perm_course_view)
        
        user = User.objects.create_user(
            email='manager@example.com',
            name='Manager User',
            password='password123',
            role='manager'
        )
        UserProfile.objects.create(user=user, role=role, role_based_id="MG001")
        
        # Authenticate as Manager
        self.client.force_authenticate(user=user)
        
        response = self.client.get('/api/rbac/my-permissions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        expected_perms = {
            "courses": ["view"]
        }
        self.assertEqual(response.data['permissions'], expected_perms)
        self.assertEqual(response.data['role_code'], "MG")
