import pytest
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from hypothesis import given, strategies as st, settings, assume
from hypothesis.extra.django import TestCase as HypothesisTestCase
import string


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
