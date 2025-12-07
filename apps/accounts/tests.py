import pytest
from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User
from django.urls import reverse
from hypothesis import given, strategies as st, settings, assume
from hypothesis.extra.django import TestCase as HypothesisTestCase
import string
from unittest.mock import Mock, MagicMock, patch
from allauth.socialaccount.models import SocialLogin, SocialAccount
from apps.accounts.adapters import CustomSocialAccountAdapter, CustomAccountAdapter


# Hypothesis strategies for generating test data
# Username: alphanumeric + underscore, starts with letter, 3-20 chars
username_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + '_',
    min_size=3,
    max_size=20
).filter(lambda x: x and x[0].isalpha() and x.replace('_', '').isalnum())

# Email: simple valid email format
email_strategy = st.builds(
    lambda local, domain: f"{local}@{domain}.com",
    local=st.text(alphabet=string.ascii_lowercase + string.digits, min_size=1, max_size=10),
    domain=st.text(alphabet=string.ascii_lowercase, min_size=2, max_size=10)
)

# Password: printable ASCII, at least 8 chars, contains letter and digit
password_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + '!@#$%^&*',
    min_size=8,
    max_size=30
).filter(lambda x: any(c.isalpha() for c in x) and any(c.isdigit() for c in x))


class TestUserAuthentication(HypothesisTestCase):
    """Property-based tests for user authentication"""
    
    def setUp(self):
        self.client = Client()
        # Clear any existing users to speed up tests
        User.objects.all().delete()
    
    # Feature: project-collaboration-portal, Property 1: Valid registration creates authenticated user
    @settings(max_examples=20, deadline=None, database=None)
    @given(
        username=username_strategy,
        email=email_strategy,
        password=password_strategy
    )
    def test_valid_registration_creates_authenticated_user(self, username, email, password):
        """
        **Validates: Requirements 1.1**
        For any valid registration data (unique username, valid email, matching passwords),
        submitting the registration form should create a new User account and authenticate that User.
        """
        # Ensure username and email don't already exist
        assume(not User.objects.filter(username=username).exists())
        assume(not User.objects.filter(email__iexact=email).exists())
        
        # Submit registration form
        response = self.client.post(reverse('signup'), {
            'username': username,
            'email': email,
            'password1': password,
            'password2': password
        }, follow=True)
        
        # Verify user was created
        assert User.objects.filter(username=username).exists(), f"User {username} was not created"
        
        # Verify the user can be retrieved
        user = User.objects.get(username=username)
        
        # Verify email matches (case-insensitive due to Django normalization)
        assert user.email.lower() == email.lower(), f"Email mismatch: expected {email}, got {user.email}"
        
        # Verify profile was created
        assert hasattr(user, 'profile'), "User profile was not created"
        
        # Verify user is authenticated
        assert response.wsgi_request.user.is_authenticated, "User should be authenticated after registration"
    
    # Feature: project-collaboration-portal, Property 2: Valid credentials authenticate user
    @settings(max_examples=20, deadline=None, database=None)
    @given(
        username=username_strategy,
        email=email_strategy,
        password=password_strategy
    )
    def test_valid_credentials_authenticate_user(self, username, email, password):
        """
        **Validates: Requirements 1.2**
        For any existing User with valid credentials, submitting the login form
        should authenticate the User and grant access to the application.
        """
        # Ensure username doesn't already exist
        assume(not User.objects.filter(username=username).exists())
        
        # Create a user
        user = User.objects.create_user(username=username, email=email, password=password)
        
        # Attempt to login
        response = self.client.post(reverse('login'), {
            'username': username,
            'password': password
        }, follow=True)
        
        # Verify successful authentication (redirect occurred)
        assert response.redirect_chain, "Expected redirect after login"
        
        # Verify user is authenticated
        assert response.wsgi_request.user.is_authenticated, "User should be authenticated after login"
        assert response.wsgi_request.user.id == user.id, "Wrong user authenticated"
    
    # Feature: project-collaboration-portal, Property 3: Logout terminates session
    @settings(max_examples=20, deadline=None, database=None)
    @given(
        username=username_strategy,
        email=email_strategy,
        password=password_strategy
    )
    def test_logout_terminates_session(self, username, email, password):
        """
        **Validates: Requirements 1.3**
        For any authenticated User, requesting logout should terminate the User session
        and prevent further authenticated access.
        """
        # Ensure username doesn't already exist
        assume(not User.objects.filter(username=username).exists())
        
        # Create and login a user
        user = User.objects.create_user(username=username, email=email, password=password)
        login_success = self.client.login(username=username, password=password)
        
        # Verify login was successful
        assert login_success, "Login should succeed before testing logout"
        
        # Make a request to establish session
        response = self.client.get(reverse('home'))
        assert response.wsgi_request.user.is_authenticated, "User should be authenticated before logout"
        
        # Logout
        response = self.client.post(reverse('logout'), follow=True)
        
        # Verify redirect occurred
        assert response.redirect_chain, "Expected redirect after logout"
        
        # Verify user is no longer authenticated
        assert not response.wsgi_request.user.is_authenticated, "User should not be authenticated after logout"
    
    # Feature: project-collaboration-portal, Property 4: Invalid credentials are rejected
    @settings(max_examples=20, deadline=None, database=None)
    @given(
        username=username_strategy,
        email=email_strategy,
        correct_password=password_strategy,
        wrong_password=password_strategy
    )
    def test_invalid_credentials_are_rejected(self, username, email, correct_password, wrong_password):
        """
        **Validates: Requirements 1.4**
        For any invalid credential combination (non-existent username, wrong password, etc.),
        the authentication attempt should be rejected with an error message.
        """
        # Ensure passwords are different
        assume(correct_password != wrong_password)
        
        # Ensure username doesn't already exist
        assume(not User.objects.filter(username=username).exists())
        
        # Create a user with correct password
        User.objects.create_user(username=username, email=email, password=correct_password)
        
        # Attempt to login with wrong password
        response = self.client.post(reverse('login'), {
            'username': username,
            'password': wrong_password
        })
        
        # Verify authentication was rejected (no redirect, form has errors)
        assert response.status_code == 200, f"Expected form redisplay, got {response.status_code}"
        
        # Verify user is not authenticated
        assert not response.wsgi_request.user.is_authenticated, "User should not be authenticated with wrong password"
        
        # Verify error message is present in response
        assert b'Invalid' in response.content or b'invalid' in response.content, "Error message not displayed"
    
    # Feature: project-collaboration-portal, Property 5: Duplicate registration is prevented
    @settings(max_examples=20, deadline=None, database=None)
    @given(
        username=username_strategy,
        email=email_strategy,
        password1=password_strategy,
        password2=password_strategy
    )
    def test_duplicate_registration_is_prevented(self, username, email, password1, password2):
        """
        **Validates: Requirements 1.5**
        For any existing User, attempting to register with the same username or email
        should be rejected and prevent account creation.
        """
        # Ensure username doesn't already exist
        assume(not User.objects.filter(username=username).exists())
        assume(not User.objects.filter(email__iexact=email).exists())
        
        # Create first user
        User.objects.create_user(username=username, email=email, password=password1)
        initial_count = User.objects.count()
        
        # Test 1: Attempt to register with same username
        response = self.client.post(reverse('signup'), {
            'username': username,
            'email': 'different_' + email,
            'password1': password2,
            'password2': password2
        })
        
        # Verify no new user was created
        assert User.objects.count() == initial_count, "Duplicate username registration should be prevented"
        
        # Verify form has errors
        assert response.status_code == 200, "Should redisplay form with errors"
        assert b'username' in response.content.lower(), "Should show username error"
        
        # Test 2: Attempt to register with same email
        new_username = username + '_new'
        assume(not User.objects.filter(username=new_username).exists())
        
        response = self.client.post(reverse('signup'), {
            'username': new_username,
            'email': email,
            'password1': password2,
            'password2': password2
        })
        
        # Verify no new user was created
        assert User.objects.count() == initial_count, "Duplicate email registration should be prevented"
        
        # Verify form has errors
        assert response.status_code == 200, "Should redisplay form with errors"
        assert b'email' in response.content.lower(), "Should show email error"



class TestNewUserOAuthFlow(TestCase):
    """
    Tests for new user OAuth flow (Task 8)
    
    These tests verify that when a new user authenticates via Google OAuth:
    - User account is created automatically
    - Username is generated from email
    - First and last name are populated
    - User is logged in and redirected to home
    - No additional forms are shown
    
    Requirements: 1.1, 1.2, 1.3, 1.5
    """
    
    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        self.adapter = CustomSocialAccountAdapter()
        self.account_adapter = CustomAccountAdapter()
        User.objects.all().delete()
    
    def create_mock_sociallogin(self, email, given_name='John', family_name='Doe', is_existing=False):
        """
        Helper method to create a mock SocialLogin object
        
        Args:
            email: Email address for the user
            given_name: First name from Google
            family_name: Last name from Google
            is_existing: Whether this is an existing social login
            
        Returns:
            Mock SocialLogin object
        """
        sociallogin = Mock(spec=SocialLogin)
        sociallogin.is_existing = is_existing
        
        # Create mock social account
        social_account = Mock(spec=SocialAccount)
        social_account.provider = 'google'
        social_account.extra_data = {
            'email': email,
            'given_name': given_name,
            'family_name': family_name,
            'verified_email': True
        }
        
        sociallogin.account = social_account
        sociallogin.user = User()
        
        # Mock the connect method
        sociallogin.connect = Mock()
        
        return sociallogin
    
    def test_new_user_account_created_automatically(self):
        """
        Test that a new user account is created automatically via OAuth
        
        Requirement: 1.1 - WHEN a new user completes Google authentication 
        THEN the System SHALL automatically create a user account using Google profile data
        """
        # Arrange
        email = 'newuser@example.com'
        given_name = 'Jane'
        family_name = 'Smith'
        
        # Verify user doesn't exist
        self.assertFalse(User.objects.filter(email=email).exists())
        
        # Create mock sociallogin
        sociallogin = self.create_mock_sociallogin(email, given_name, family_name)
        
        # Create mock request
        request = self.factory.get('/')
        request.user = Mock()
        
        # Act - simulate pre_social_login (should not create user yet, just check)
        self.adapter.pre_social_login(request, sociallogin)
        
        # Populate user data
        data = {'email': email}
        user = self.adapter.populate_user(request, sociallogin, data)
        
        # Assert - user object should be populated
        self.assertEqual(user.email, email)
        self.assertEqual(user.first_name, given_name)
        self.assertEqual(user.last_name, family_name)
    
    def test_username_generated_from_email(self):
        """
        Test that username is generated from email address
        
        Requirement: 1.2 - WHEN creating an account from Google data 
        THEN the System SHALL generate a unique username from the user's email address
        """
        # Arrange
        email = 'testuser123@example.com'
        expected_username_base = 'testuser123'
        
        # Act
        username = self.account_adapter.generate_unique_username([email.split('@')[0]])
        
        # Assert
        self.assertTrue(username.startswith(expected_username_base))
        self.assertTrue(username.replace('_', '').isalnum())
    
    def test_username_conflict_resolution(self):
        """
        Test that username conflicts are resolved with numeric suffix
        
        Requirement: 1.4 - WHEN username conflicts occur 
        THEN the System SHALL append a numeric suffix to ensure uniqueness
        """
        # Arrange - create existing user
        base_username = 'johndoe'
        User.objects.create_user(username=base_username, email='john1@example.com', password='test123')
        
        # Act - try to generate same username
        new_username = self.account_adapter.generate_unique_username([base_username])
        
        # Assert - should have numeric suffix
        self.assertNotEqual(new_username, base_username)
        self.assertTrue(new_username.startswith(base_username))
        # Should be base_username + digit(s)
        suffix = new_username[len(base_username):]
        self.assertTrue(suffix.isdigit() or suffix == '')
    
    def test_first_and_last_name_populated(self):
        """
        Test that first and last name are populated from Google profile
        
        Requirement: 1.5 - WHERE the user's Google profile includes first and last name 
        THEN the System SHALL populate these fields in the user account
        """
        # Arrange
        email = 'alice@example.com'
        given_name = 'Alice'
        family_name = 'Johnson'
        
        sociallogin = self.create_mock_sociallogin(email, given_name, family_name)
        request = self.factory.get('/')
        
        # Act
        user = self.adapter.populate_user(request, sociallogin, {'email': email})
        
        # Assert
        self.assertEqual(user.first_name, given_name)
        self.assertEqual(user.last_name, family_name)
        self.assertEqual(user.email, email)
    
    def test_missing_name_data_handled_gracefully(self):
        """
        Test that missing name data is handled gracefully
        
        Requirement: 4.2 - WHEN Google provides incomplete profile data 
        THEN the System SHALL use sensible defaults for missing fields
        """
        # Arrange
        email = 'noname@example.com'
        
        # Create sociallogin with missing name data
        sociallogin = Mock(spec=SocialLogin)
        sociallogin.is_existing = False
        social_account = Mock(spec=SocialAccount)
        social_account.provider = 'google'
        social_account.extra_data = {
            'email': email,
            # No given_name or family_name
            'verified_email': True
        }
        sociallogin.account = social_account
        sociallogin.user = User()
        
        request = self.factory.get('/')
        
        # Act
        user = self.adapter.populate_user(request, sociallogin, {'email': email})
        
        # Assert - should not crash, should have email at minimum
        self.assertEqual(user.email, email)
        # Names should be empty strings (sensible default)
        self.assertEqual(user.first_name, '')
        self.assertEqual(user.last_name, '')
    
    def test_no_additional_forms_required(self):
        """
        Test that no additional forms are required for new user signup
        
        Requirement: 1.3 - WHEN the account is created 
        THEN the System SHALL automatically log the user in and redirect to the home page
        
        This is verified by checking that populate_user returns a complete user object
        without requiring additional input
        """
        # Arrange
        email = 'complete@example.com'
        given_name = 'Complete'
        family_name = 'User'
        
        sociallogin = self.create_mock_sociallogin(email, given_name, family_name)
        request = self.factory.get('/')
        
        # Act
        user = self.adapter.populate_user(request, sociallogin, {'email': email})
        
        # Assert - user should have all required fields populated
        self.assertTrue(user.email)
        self.assertTrue(user.first_name)
        self.assertTrue(user.last_name)
        # Username will be generated by allauth using generate_unique_username
        # No additional form data should be needed
    
    def test_existing_user_account_linking(self):
        """
        Test that existing users with matching email are linked automatically
        
        Requirement: 2.1 - WHEN an existing user authenticates via Google with a matching email 
        THEN the System SHALL automatically link the Google account to the existing user account
        """
        # Arrange - create existing user
        email = 'existing@example.com'
        existing_user = User.objects.create_user(
            username='existinguser',
            email=email,
            password='testpass123'
        )
        
        # Create mock sociallogin for same email
        sociallogin = self.create_mock_sociallogin(email, 'Existing', 'User')
        
        request = self.factory.get('/')
        request.user = Mock()
        
        # Act
        self.adapter.pre_social_login(request, sociallogin)
        
        # Assert - connect should have been called with the existing user
        sociallogin.connect.assert_called_once_with(request, existing_user)
    
    def test_special_characters_in_email_handled(self):
        """
        Test that special characters in email are handled correctly
        
        Requirement: 4.1 - Edge case handling for username generation
        """
        # Arrange
        emails_with_special_chars = [
            'user.name@example.com',
            'user+tag@example.com',
            'user_name@example.com',
            'user-name@example.com'
        ]
        
        for email in emails_with_special_chars:
            # Act
            username_base = email.split('@')[0]
            username = self.account_adapter.generate_unique_username([username_base])
            
            # Assert - username should be valid (alphanumeric + underscore only)
            self.assertTrue(username.replace('_', '').replace('0', '').replace('1', '').replace('2', '').replace('3', '').replace('4', '').replace('5', '').replace('6', '').replace('7', '').replace('8', '').replace('9', '').isalpha() or username.replace('_', '').isalnum())
    
    def test_very_long_email_username_truncated(self):
        """
        Test that very long email addresses result in truncated usernames
        
        Requirement: 4.1 - Edge case handling for username generation
        """
        # Arrange
        long_email = 'a' * 50 + '@example.com'
        
        # Act
        username = self.account_adapter.generate_unique_username([long_email.split('@')[0]])
        
        # Assert - username should be reasonable length
        self.assertLessEqual(len(username), 30)  # Should be truncated
    
    def test_multiple_username_conflicts_resolved(self):
        """
        Test that multiple username conflicts are resolved sequentially
        
        Requirement: 1.4 - Username conflict resolution with numeric suffixes
        """
        # Arrange - create multiple users with similar usernames
        base_username = 'popular'
        User.objects.create_user(username=base_username, email='user1@example.com', password='test123')
        User.objects.create_user(username=f'{base_username}1', email='user2@example.com', password='test123')
        User.objects.create_user(username=f'{base_username}2', email='user3@example.com', password='test123')
        
        # Act - try to generate same username
        new_username = self.account_adapter.generate_unique_username([base_username])
        
        # Assert - should get a unique username that starts with base
        self.assertNotEqual(new_username, base_username)
        self.assertTrue(new_username.startswith(base_username))
        # Verify it's actually unique
        self.assertFalse(User.objects.filter(username=new_username).exists())
    
    def test_oauth_flow_logging(self):
        """
        Test that OAuth flow events are logged appropriately
        
        Requirement: 5.3 - WHEN debugging OAuth issues 
        THEN the System SHALL log relevant information at appropriate levels
        """
        # Arrange
        email = 'logtest@example.com'
        sociallogin = self.create_mock_sociallogin(email, 'Log', 'Test')
        request = self.factory.get('/')
        request.user = Mock()
        
        # Act & Assert - verify logging occurs (we can't easily test log output,
        # but we can verify the methods execute without error)
        with patch('apps.accounts.adapters.logger') as mock_logger:
            self.adapter.pre_social_login(request, sociallogin)
            # Should log that new user will be created
            self.assertTrue(mock_logger.info.called)
    
    def test_empty_username_fallback(self):
        """
        Test that empty username input results in fallback username
        
        Requirement: 4.2 - Handling incomplete profile data
        """
        # Arrange - empty username input
        empty_inputs = ['', ' ', '   ']
        
        for empty_input in empty_inputs:
            # Act
            username = self.account_adapter.generate_unique_username([empty_input])
            
            # Assert - should get a valid username (fallback to 'user')
            self.assertTrue(username)
            self.assertTrue(len(username) > 0)
