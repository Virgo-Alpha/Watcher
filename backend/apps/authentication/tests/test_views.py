"""
API tests for authentication endpoints.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class UserRegistrationViewTest(TestCase):
    """Test user registration endpoint."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.registration_url = reverse('authentication:register')
        self.valid_registration_data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'New',
            'last_name': 'User'
        }

    def test_successful_registration(self):
        """Test successful user registration with valid data."""
        response = self.client.post(
            self.registration_url,
            self.valid_registration_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('access', response.data)

        # Verify user data structure
        user_data = response.data['user']
        self.assertEqual(user_data['email'], 'newuser@example.com')
        self.assertEqual(user_data['username'], 'newuser')
        self.assertEqual(user_data['first_name'], 'New')
        self.assertEqual(user_data['last_name'], 'User')
        self.assertIn('id', user_data)
        self.assertIn('created_at', user_data)
        self.assertIn('updated_at', user_data)

        # Verify tokens are strings
        self.assertIsInstance(response.data['refresh'], str)
        self.assertIsInstance(response.data['access'], str)
        self.assertTrue(len(response.data['refresh']) > 0)
        self.assertTrue(len(response.data['access']) > 0)

        # Verify user was created in database
        user = User.objects.get(email='newuser@example.com')
        self.assertEqual(user.username, 'newuser')
        self.assertTrue(user.check_password('SecurePass123!'))

    def test_registration_response_structure(self):
        """Test that registration response has correct flat structure."""
        response = self.client.post(
            self.registration_url,
            self.valid_registration_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify flat structure (not nested under 'tokens')
        self.assertIn('refresh', response.data)
        self.assertIn('access', response.data)
        self.assertNotIn('tokens', response.data)

        # Verify tokens are at top level
        self.assertEqual(set(response.data.keys()), {'user', 'refresh', 'access'})

    def test_registration_tokens_are_valid(self):
        """Test that returned tokens are valid JWT tokens."""
        response = self.client.post(
            self.registration_url,
            self.valid_registration_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify access token can be used for authentication
        access_token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        profile_url = reverse('authentication:profile')
        profile_response = self.client.get(profile_url)
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)

    def _get_error_details(self, response):
        """Helper to extract error details from response."""
        if 'error' in response.data and 'details' in response.data['error']:
            return response.data['error']['details']
        return response.data
    
    def test_registration_missing_email(self):
        """Test registration fails without email."""
        data = self.valid_registration_data.copy()
        del data['email']

        response = self.client.post(self.registration_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        errors = self._get_error_details(response)
        self.assertIn('email', errors)

    def test_registration_missing_username(self):
        """Test registration fails without username."""
        data = self.valid_registration_data.copy()
        del data['username']

        response = self.client.post(self.registration_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        errors = self._get_error_details(response)
        self.assertIn('username', errors)

    def test_registration_missing_password(self):
        """Test registration fails without password."""
        data = self.valid_registration_data.copy()
        del data['password']

        response = self.client.post(self.registration_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        errors = self._get_error_details(response)
        self.assertIn('password', errors)

    def test_registration_password_mismatch(self):
        """Test registration fails when passwords don't match."""
        data = self.valid_registration_data.copy()
        data['password_confirm'] = 'DifferentPassword123!'

        response = self.client.post(self.registration_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        errors = self._get_error_details(response)
        self.assertIn('non_field_errors', errors)

    def test_registration_duplicate_email(self):
        """Test registration fails with duplicate email."""
        # Create existing user
        User.objects.create_user(
            email='newuser@example.com',
            username='existinguser',
            password='ExistingPass123!'
        )

        response = self.client.post(
            self.registration_url,
            self.valid_registration_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        errors = self._get_error_details(response)
        self.assertIn('email', errors)

    def test_registration_duplicate_username(self):
        """Test registration fails with duplicate username."""
        # Create existing user
        User.objects.create_user(
            email='existing@example.com',
            username='newuser',
            password='ExistingPass123!'
        )

        response = self.client.post(
            self.registration_url,
            self.valid_registration_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        errors = self._get_error_details(response)
        self.assertIn('username', errors)

    def test_registration_weak_password(self):
        """Test registration fails with weak password."""
        data = self.valid_registration_data.copy()
        data['password'] = '123'
        data['password_confirm'] = '123'

        response = self.client.post(self.registration_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        errors = self._get_error_details(response)
        self.assertIn('password', errors)

    def test_registration_invalid_email_format(self):
        """Test registration fails with invalid email format."""
        data = self.valid_registration_data.copy()
        data['email'] = 'not-an-email'

        response = self.client.post(self.registration_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        errors = self._get_error_details(response)
        self.assertIn('email', errors)

    def test_registration_without_optional_fields(self):
        """Test registration succeeds without optional fields."""
        data = {
            'email': 'minimal@example.com',
            'username': 'minimaluser',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!'
        }

        response = self.client.post(self.registration_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('access', response.data)

    def test_registration_no_authentication_required(self):
        """Test registration endpoint allows unauthenticated access."""
        # Explicitly ensure no authentication
        self.client.credentials()

        response = self.client.post(
            self.registration_url,
            self.valid_registration_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_registration_password_not_in_response(self):
        """Test that password is not included in response."""
        response = self.client.post(
            self.registration_url,
            self.valid_registration_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Password should not be in user data
        user_data = response.data['user']
        self.assertNotIn('password', user_data)
        self.assertNotIn('password_confirm', user_data)

    def test_registration_creates_active_user(self):
        """Test that registered user is active by default."""
        response = self.client.post(
            self.registration_url,
            self.valid_registration_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(email='newuser@example.com')
        self.assertTrue(user.is_active)

    def test_registration_user_not_staff(self):
        """Test that registered user is not staff by default."""
        response = self.client.post(
            self.registration_url,
            self.valid_registration_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(email='newuser@example.com')
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)


class UserLoginViewTest(TestCase):
    """Test user login endpoint."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.login_url = reverse('authentication:login')
        self.user = User.objects.create_user(
            email='testuser@example.com',
            username='testuser',
            password='TestPass123!'
        )

    def test_successful_login(self):
        """Test successful login with valid credentials."""
        data = {
            'email': 'testuser@example.com',
            'password': 'TestPass123!'
        }

        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('access', response.data)

    def test_login_response_structure(self):
        """Test that login response has correct flat structure."""
        data = {
            'email': 'testuser@example.com',
            'password': 'TestPass123!'
        }

        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify flat structure (not nested under 'tokens')
        self.assertIn('refresh', response.data)
        self.assertIn('access', response.data)
        self.assertNotIn('tokens', response.data)

    def test_login_invalid_password(self):
        """Test login fails with invalid password."""
        data = {
            'email': 'testuser@example.com',
            'password': 'WrongPassword123!'
        }

        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_nonexistent_user(self):
        """Test login fails with nonexistent user."""
        data = {
            'email': 'nonexistent@example.com',
            'password': 'TestPass123!'
        }

        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_inactive_user(self):
        """Test login fails for inactive user."""
        self.user.is_active = False
        self.user.save()

        data = {
            'email': 'testuser@example.com',
            'password': 'TestPass123!'
        }

        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserProfileViewTest(TestCase):
    """Test user profile endpoint."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.profile_url = reverse('authentication:profile')
        self.user = User.objects.create_user(
            email='testuser@example.com',
            username='testuser',
            password='TestPass123!',
            first_name='Test',
            last_name='User'
        )

    def test_get_profile_authenticated(self):
        """Test getting profile with authentication."""
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'testuser@example.com')
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['first_name'], 'Test')
        self.assertEqual(response.data['last_name'], 'User')

    def test_get_profile_unauthenticated(self):
        """Test getting profile without authentication."""
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_profile(self):
        """Test updating user profile."""
        self.client.force_authenticate(user=self.user)

        data = {
            'username': 'updateduser',
            'first_name': 'Updated',
            'last_name': 'Name'
        }

        response = self.client.patch(self.profile_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'updateduser')
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')


class ChangePasswordViewTest(TestCase):
    """Test change password endpoint."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.change_password_url = reverse('authentication:change_password')
        self.user = User.objects.create_user(
            email='testuser@example.com',
            username='testuser',
            password='OldPass123!'
        )

    def test_change_password_success(self):
        """Test successful password change."""
        self.client.force_authenticate(user=self.user)

        data = {
            'old_password': 'OldPass123!',
            'new_password': 'NewPass123!',
            'new_password_confirm': 'NewPass123!'
        }

        response = self.client.put(self.change_password_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPass123!'))

    def test_change_password_wrong_old_password(self):
        """Test password change fails with wrong old password."""
        self.client.force_authenticate(user=self.user)

        data = {
            'old_password': 'WrongOldPass123!',
            'new_password': 'NewPass123!',
            'new_password_confirm': 'NewPass123!'
        }

        response = self.client.put(self.change_password_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_mismatch(self):
        """Test password change fails when new passwords don't match."""
        self.client.force_authenticate(user=self.user)

        data = {
            'old_password': 'OldPass123!',
            'new_password': 'NewPass123!',
            'new_password_confirm': 'DifferentPass123!'
        }

        response = self.client.put(self.change_password_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_unauthenticated(self):
        """Test password change requires authentication."""
        data = {
            'old_password': 'OldPass123!',
            'new_password': 'NewPass123!',
            'new_password_confirm': 'NewPass123!'
        }

        response = self.client.put(self.change_password_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class LogoutViewTest(TestCase):
    """Test logout endpoint."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.logout_url = reverse('authentication:logout')
        self.user = User.objects.create_user(
            email='testuser@example.com',
            username='testuser',
            password='TestPass123!'
        )

    def test_logout_success(self):
        """Test successful logout."""
        self.client.force_authenticate(user=self.user)

        refresh = RefreshToken.for_user(self.user)
        data = {'refresh_token': str(refresh)}

        response = self.client.post(self.logout_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

    def test_logout_unauthenticated(self):
        """Test logout requires authentication."""
        response = self.client.post(self.logout_url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_invalid_token(self):
        """Test logout with invalid token."""
        self.client.force_authenticate(user=self.user)

        data = {'refresh_token': 'invalid-token'}

        response = self.client.post(self.logout_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
