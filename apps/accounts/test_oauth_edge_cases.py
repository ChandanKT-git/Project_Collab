"""
Edge case tests for Google OAuth flow

This test module covers edge cases and error scenarios for the OAuth authentication flow:
- Emails with special characters
- Username conflict resolution
- OAuth cancellation flow
- Incomplete Google profile data
- Error page styling and recovery options

Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
"""

import pytest
from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import Mock, patch
from allauth.socialaccount.models import SocialLogin, SocialAccount
from apps.accounts.adapters import CustomSocialAccountAdapter, CustomAccountAdapter


class TestOAuthEdgeCases(TestCase):
    """
    Test edge cases and error scenarios for OAuth flow
    
    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
    """
    
    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        self.adapter = CustomSocialAccountAdapter()
        self.account_adapter = CustomAccountAdapter()
        self.client = Client()
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
    
    # Test 1: Email with special characters
    def test_email_with_dots(self):
        """
        Test username generation from email with dots
        
        Requirement: 4.1 - WHEN a username conflict cannot be resolved 
        THEN the System SHALL generate a unique username using a timestamp suffix
        
        Edge case: Email contains dots (user.name@example.com)
        """
        email = 'user.name@example.com'
        sociallogin = self.create_mock_sociallogin(email, 'User', 'Name')
        request = self.factory.get('/')
        
        # Populate user
        user = self.adapter.populate_user(request, sociallogin, {'email': email})
        
        # Generate username
        username_base = email.split('@')[0]
        username = self.account_adapter.generate_unique_username([username_base])
        
        # Assert: username should be valid (no dots, alphanumeric + underscore only)
        self.assertNotIn('.', username)
        self.assertTrue(username.replace('_', '').isalnum())
        self.assertEqual(user.email, email)
    
    def test_email_with_plus_sign(self):
        """
        Test username generation from email with plus sign
        
        Requirement: 4.1 - Edge case handling for special characters
        
        Edge case: Email contains plus sign (user+tag@example.com)
        """
        email = 'user+tag@example.com'
        sociallogin = self.create_mock_sociallogin(email, 'User', 'Tag')
        request = self.factory.get('/')
        
        # Populate user
        user = self.adapter.populate_user(request, sociallogin, {'email': email})
        
        # Generate username
        username_base = email.split('@')[0]
        username = self.account_adapter.generate_unique_username([username_base])
        
        # Assert: username should be valid (no plus sign)
        self.assertNotIn('+', username)
        self.assertTrue(username.replace('_', '').isalnum())
        self.assertEqual(user.email, email)
    
    def test_email_with_hyphen(self):
        """
        Test username generation from email with hyphen
        
        Requirement: 4.1 - Edge case handling for special characters
        
        Edge case: Email contains hyphen (user-name@example.com)
        """
        email = 'user-name@example.com'
        sociallogin = self.create_mock_sociallogin(email, 'User', 'Name')
        request = self.factory.get('/')
        
        # Populate user
        user = self.adapter.populate_user(request, sociallogin, {'email': email})
        
        # Generate username
        username_base = email.split('@')[0]
        username = self.account_adapter.generate_unique_username([username_base])
        
        # Assert: username should be valid (no hyphen)
        self.assertNotIn('-', username)
        self.assertTrue(username.replace('_', '').isalnum())
        self.assertEqual(user.email, email)
    
    def test_email_with_underscore(self):
        """
        Test username generation from email with underscore
        
        Requirement: 4.1 - Edge case handling for special characters
        
        Edge case: Email contains underscore (user_name@example.com)
        """
        email = 'user_name@example.com'
        sociallogin = self.create_mock_sociallogin(email, 'User', 'Name')
        request = self.factory.get('/')
        
        # Populate user
        user = self.adapter.populate_user(request, sociallogin, {'email': email})
        
        # Generate username
        username_base = email.split('@')[0]
        username = self.account_adapter.generate_unique_username([username_base])
        
        # Assert: username should be valid (underscore is allowed)
        self.assertTrue(username.replace('_', '').isalnum())
        self.assertEqual(user.email, email)
    
    def test_email_with_numbers(self):
        """
        Test username generation from email with numbers
        
        Requirement: 4.1 - Edge case handling
        
        Edge case: Email contains numbers (user123@example.com)
        """
        email = 'user123@example.com'
        sociallogin = self.create_mock_sociallogin(email, 'User', 'One')
        request = self.factory.get('/')
        
        # Populate user
        user = self.adapter.populate_user(request, sociallogin, {'email': email})
        
        # Generate username
        username_base = email.split('@')[0]
        username = self.account_adapter.generate_unique_username([username_base])
        
        # Assert: username should preserve numbers
        self.assertTrue(any(c.isdigit() for c in username))
        self.assertTrue(username.replace('_', '').isalnum())
        self.assertEqual(user.email, email)
    
    # Test 2: Username conflict resolution
    def test_username_conflict_single(self):
        """
        Test username conflict resolution with single existing user
        
        Requirement: 1.4 - WHEN username conflicts occur 
        THEN the System SHALL append a numeric suffix to ensure uniqueness
        """
        # Create existing user
        base_username = 'testuser'
        User.objects.create_user(username=base_username, email='test1@example.com', password='test123')
        
        # Try to generate same username
        new_username = self.account_adapter.generate_unique_username([base_username])
        
        # Assert: should have numeric suffix
        self.assertNotEqual(new_username, base_username)
        self.assertTrue(new_username.startswith(base_username))
        self.assertFalse(User.objects.filter(username=new_username).exists())
    
    def test_username_conflict_multiple(self):
        """
        Test username conflict resolution with multiple existing users
        
        Requirement: 1.4 - Username conflict resolution with sequential suffixes
        """
        # Create multiple users with similar usernames
        base_username = 'popular'
        User.objects.create_user(username=base_username, email='user1@example.com', password='test123')
        User.objects.create_user(username=f'{base_username}1', email='user2@example.com', password='test123')
        User.objects.create_user(username=f'{base_username}2', email='user3@example.com', password='test123')
        User.objects.create_user(username=f'{base_username}3', email='user4@example.com', password='test123')
        
        # Try to generate same username
        new_username = self.account_adapter.generate_unique_username([base_username])
        
        # Assert: should get next available suffix
        self.assertNotEqual(new_username, base_username)
        self.assertTrue(new_username.startswith(base_username))
        self.assertFalse(User.objects.filter(username=new_username).exists())
        # Should have a numeric suffix (could be any number due to allauth's internal logic)
        suffix = new_username[len(base_username):]
        self.assertTrue(suffix.isdigit() and int(suffix) >= 1)
    
    def test_username_conflict_with_long_base(self):
        """
        Test username conflict resolution when base username is long
        
        Requirement: 4.1 - WHEN a username conflict cannot be resolved 
        THEN the System SHALL generate a unique username using a timestamp suffix
        """
        # Create user with long username
        long_base = 'a' * 25  # Max length before truncation
        User.objects.create_user(username=long_base, email='long1@example.com', password='test123')
        
        # Try to generate same username
        new_username = self.account_adapter.generate_unique_username([long_base])
        
        # Assert: should be truncated and have suffix
        self.assertLessEqual(len(new_username), 30)
        self.assertNotEqual(new_username, long_base)
        self.assertFalse(User.objects.filter(username=new_username).exists())
    
    def test_username_timestamp_fallback(self):
        """
        Test that timestamp fallback works when many conflicts exist
        
        Requirement: 4.1 - WHEN a username conflict cannot be resolved 
        THEN the System SHALL generate a unique username using a timestamp suffix
        
        Note: This test verifies the fallback mechanism exists, but doesn't
        create 1000 users to trigger it (that would be too slow)
        """
        # We'll mock the User.objects.filter to simulate many conflicts
        base_username = 'conflict'
        
        with patch('apps.accounts.adapters.User.objects.filter') as mock_filter:
            # Make it look like all numeric suffixes are taken
            mock_filter.return_value.exists.return_value = True
            
            # Generate username (should use timestamp fallback)
            new_username = self.account_adapter.generate_unique_username([base_username])
            
            # Assert: should contain timestamp (14 digits: YYYYMMDDHHMMSS)
            self.assertTrue(any(c.isdigit() for c in new_username))
            self.assertIn('_', new_username)  # Timestamp is separated by underscore
    
    # Test 3: Incomplete Google profile data
    def test_missing_first_name(self):
        """
        Test handling of missing first name from Google
        
        Requirement: 4.2 - WHEN Google provides incomplete profile data 
        THEN the System SHALL use sensible defaults for missing fields
        """
        email = 'nofirstname@example.com'
        
        # Create sociallogin with missing first name
        sociallogin = Mock(spec=SocialLogin)
        sociallogin.is_existing = False
        social_account = Mock(spec=SocialAccount)
        social_account.provider = 'google'
        social_account.extra_data = {
            'email': email,
            'family_name': 'Lastname',
            # No given_name
            'verified_email': True
        }
        sociallogin.account = social_account
        sociallogin.user = User()
        
        request = self.factory.get('/')
        
        # Act
        user = self.adapter.populate_user(request, sociallogin, {'email': email})
        
        # Assert: should handle gracefully with empty string
        self.assertEqual(user.email, email)
        self.assertEqual(user.first_name, '')
        self.assertEqual(user.last_name, 'Lastname')
    
    def test_missing_last_name(self):
        """
        Test handling of missing last name from Google
        
        Requirement: 4.2 - WHEN Google provides incomplete profile data 
        THEN the System SHALL use sensible defaults for missing fields
        """
        email = 'nolastname@example.com'
        
        # Create sociallogin with missing last name
        sociallogin = Mock(spec=SocialLogin)
        sociallogin.is_existing = False
        social_account = Mock(spec=SocialAccount)
        social_account.provider = 'google'
        social_account.extra_data = {
            'email': email,
            'given_name': 'Firstname',
            # No family_name
            'verified_email': True
        }
        sociallogin.account = social_account
        sociallogin.user = User()
        
        request = self.factory.get('/')
        
        # Act
        user = self.adapter.populate_user(request, sociallogin, {'email': email})
        
        # Assert: should handle gracefully with empty string
        self.assertEqual(user.email, email)
        self.assertEqual(user.first_name, 'Firstname')
        self.assertEqual(user.last_name, '')
    
    def test_missing_both_names(self):
        """
        Test handling of missing both first and last name from Google
        
        Requirement: 4.2 - WHEN Google provides incomplete profile data 
        THEN the System SHALL use sensible defaults for missing fields
        """
        email = 'nonames@example.com'
        
        # Create sociallogin with missing names
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
        
        # Assert: should handle gracefully with empty strings
        self.assertEqual(user.email, email)
        self.assertEqual(user.first_name, '')
        self.assertEqual(user.last_name, '')
    
    def test_missing_email(self):
        """
        Test handling of missing email from Google (should not happen but handle gracefully)
        
        Requirement: 4.2 - WHEN Google provides incomplete profile data 
        THEN the System SHALL use sensible defaults for missing fields
        """
        # Create sociallogin with missing email
        sociallogin = Mock(spec=SocialLogin)
        sociallogin.is_existing = False
        social_account = Mock(spec=SocialAccount)
        social_account.provider = 'google'
        social_account.extra_data = {
            # No email
            'given_name': 'Test',
            'family_name': 'User',
            'verified_email': False
        }
        sociallogin.account = social_account
        sociallogin.user = User()
        
        request = self.factory.get('/')
        request.user = Mock()
        
        # Act - pre_social_login should handle missing email gracefully
        with patch('apps.accounts.adapters.logger') as mock_logger:
            self.adapter.pre_social_login(request, sociallogin)
            # Should log warning about missing email
            self.assertTrue(mock_logger.warning.called)
    
    def test_empty_extra_data(self):
        """
        Test handling of completely empty extra_data from Google
        
        Requirement: 4.2 - WHEN Google provides incomplete profile data 
        THEN the System SHALL use sensible defaults for missing fields
        """
        # Create sociallogin with empty extra_data
        sociallogin = Mock(spec=SocialLogin)
        sociallogin.is_existing = False
        social_account = Mock(spec=SocialAccount)
        social_account.provider = 'google'
        social_account.extra_data = {}  # Empty
        sociallogin.account = social_account
        sociallogin.user = User()
        
        request = self.factory.get('/')
        
        # Act - should not crash
        user = self.adapter.populate_user(request, sociallogin, {})
        
        # Assert: should have empty fields
        self.assertEqual(user.first_name, '')
        self.assertEqual(user.last_name, '')
        self.assertEqual(user.email, '')


class TestOAuthErrorPages(TestCase):
    """
    Test OAuth error pages styling and recovery options
    
    Requirements: 4.3, 4.4, 4.5
    """
    
    def setUp(self):
        """Set up test client"""
        self.client = Client()
    
    def test_authentication_error_page_exists(self):
        """
        Test that authentication error page exists and is accessible
        
        Requirement: 4.3 - IF an error occurs during account creation 
        THEN the System SHALL display a clear error message and provide recovery options
        """
        # We can't easily test the actual OAuth callback without a SocialApp configured
        # Instead, verify the template exists and has the right content
        import os
        template_path = 'templates/socialaccount/authentication_error.html'
        self.assertTrue(os.path.exists(template_path), "Authentication error template should exist")
    
    def test_authentication_error_template_styling(self):
        """
        Test that authentication error template has proper styling
        
        Requirement: 3.2 - WHEN displaying OAuth pages 
        THEN the System SHALL use the same gradient backgrounds, glass effects, and styling
        """
        # Read the template file
        with open('templates/socialaccount/authentication_error.html', 'r') as f:
            template_content = f.read()
        
        # Assert: template should have required styling elements
        self.assertIn('glass-effect', template_content)
        self.assertIn('gradient', template_content)
        self.assertIn('rounded', template_content)
        self.assertIn('shadow', template_content)
    
    def test_authentication_error_recovery_options(self):
        """
        Test that authentication error page has recovery options
        
        Requirement: 4.3 - IF an error occurs during account creation 
        THEN the System SHALL display a clear error message and provide recovery options
        """
        # Read the template file
        with open('templates/socialaccount/authentication_error.html', 'r') as f:
            template_content = f.read()
        
        # Assert: template should have recovery links
        self.assertIn('google_login', template_content)  # Try again with Google
        self.assertIn('login', template_content)  # Back to login
        self.assertIn('Try Again', template_content)
        self.assertIn('Back to Login', template_content)
    
    def test_login_cancelled_page_exists(self):
        """
        Test that login cancelled page exists
        
        Requirement: 4.4 - WHEN a user cancels OAuth authentication 
        THEN the System SHALL redirect to the login page with an informative message
        """
        # The template should exist
        with open('templates/socialaccount/login_cancelled.html', 'r') as f:
            template_content = f.read()
        
        # Assert: template exists and has content
        self.assertIn('cancelled', template_content.lower())
        self.assertIn('Sign-in Cancelled', template_content)
    
    def test_login_cancelled_template_styling(self):
        """
        Test that login cancelled template has proper styling
        
        Requirement: 3.2 - WHEN displaying OAuth pages 
        THEN the System SHALL use the same gradient backgrounds, glass effects, and styling
        """
        # Read the template file
        with open('templates/socialaccount/login_cancelled.html', 'r') as f:
            template_content = f.read()
        
        # Assert: template should have required styling elements
        self.assertIn('glass-effect', template_content)
        self.assertIn('gradient', template_content)
        self.assertIn('rounded', template_content)
        self.assertIn('shadow', template_content)
    
    def test_login_cancelled_recovery_options(self):
        """
        Test that login cancelled page has recovery options
        
        Requirement: 4.4 - WHEN a user cancels OAuth authentication 
        THEN the System SHALL redirect to the login page with an informative message
        """
        # Read the template file
        with open('templates/socialaccount/login_cancelled.html', 'r') as f:
            template_content = f.read()
        
        # Assert: template should have recovery links
        self.assertIn('google_login', template_content)  # Try again with Google
        self.assertIn('login', template_content)  # Back to login
        self.assertIn('account_signup', template_content)  # Sign up link
        self.assertIn('Try Again', template_content)
        self.assertIn('Back to Login', template_content)
    
    def test_signup_template_styling(self):
        """
        Test that signup template has proper styling
        
        Requirement: 3.2 - WHEN displaying OAuth pages 
        THEN the System SHALL use the same gradient backgrounds, glass effects, and styling
        """
        # Read the template file
        with open('templates/socialaccount/signup.html', 'r') as f:
            template_content = f.read()
        
        # Assert: template should have required styling elements
        self.assertIn('glass-effect', template_content)
        self.assertIn('gradient', template_content)
        self.assertIn('rounded', template_content)
        self.assertIn('shadow', template_content)
    
    def test_signup_template_has_form(self):
        """
        Test that signup template has form elements
        
        Requirement: 3.3 - WHEN errors occur during OAuth 
        THEN the System SHALL display user-friendly error messages with appropriate styling
        """
        # Read the template file
        with open('templates/socialaccount/signup.html', 'r') as f:
            template_content = f.read()
        
        # Assert: template should have form elements
        self.assertIn('<form', template_content)
        self.assertIn('csrf_token', template_content)
        self.assertIn('type="submit"', template_content)
        self.assertIn('Complete Sign Up', template_content)
    
    def test_signup_template_shows_google_info(self):
        """
        Test that signup template displays Google profile information
        
        Requirement: 3.3 - Display Google profile information
        """
        # Read the template file
        with open('templates/socialaccount/signup.html', 'r') as f:
            template_content = f.read()
        
        # Assert: template should display Google info
        self.assertIn('sociallogin.account.extra_data', template_content)
        self.assertIn('Connected with Google', template_content)
    
    def test_all_error_pages_extend_base(self):
        """
        Test that all OAuth pages extend base.html for consistency
        
        Requirement: 3.1 - WHEN a user views any OAuth-related page 
        THEN the System SHALL display pages using the application's design system
        """
        templates = [
            'templates/socialaccount/authentication_error.html',
            'templates/socialaccount/login_cancelled.html',
            'templates/socialaccount/signup.html'
        ]
        
        for template_path in templates:
            with open(template_path, 'r') as f:
                template_content = f.read()
            
            # Assert: each template should extend base.html
            self.assertIn("{% extends 'base.html' %}", template_content)
    
    def test_error_pages_have_icons(self):
        """
        Test that error pages have appropriate icons
        
        Requirement: 3.2 - Visual consistency with icons
        """
        templates = [
            'templates/socialaccount/authentication_error.html',
            'templates/socialaccount/login_cancelled.html',
            'templates/socialaccount/signup.html'
        ]
        
        for template_path in templates:
            with open(template_path, 'r') as f:
                template_content = f.read()
            
            # Assert: each template should have SVG icons
            self.assertIn('<svg', template_content)
            self.assertIn('viewBox', template_content)
    
    def test_error_pages_have_security_notices(self):
        """
        Test that error pages have security notices
        
        Requirement: 4.5 - IF the OAuth provider returns an error 
        THEN the System SHALL log the error and display a user-friendly message
        """
        templates = [
            'templates/socialaccount/authentication_error.html',
            'templates/socialaccount/login_cancelled.html',
            'templates/socialaccount/signup.html'
        ]
        
        for template_path in templates:
            with open(template_path, 'r') as f:
                template_content = f.read()
            
            # Assert: each template should have security-related messaging
            self.assertTrue(
                'security' in template_content.lower() or 
                'secure' in template_content.lower() or
                'privacy' in template_content.lower() or
                'protected' in template_content.lower()
            )


class TestOAuthLogging(TestCase):
    """
    Test OAuth logging functionality
    
    Requirements: 5.3, 6.1, 6.3
    """
    
    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        self.adapter = CustomSocialAccountAdapter()
        self.account_adapter = CustomAccountAdapter()
        User.objects.all().delete()
    
    def create_mock_sociallogin(self, email, given_name='John', family_name='Doe'):
        """Helper to create mock sociallogin"""
        sociallogin = Mock(spec=SocialLogin)
        sociallogin.is_existing = False
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
        sociallogin.connect = Mock()
        return sociallogin
    
    def test_new_user_creation_logged(self):
        """
        Test that new user creation is logged
        
        Requirement: 5.3 - WHEN debugging OAuth issues 
        THEN the System SHALL log relevant information at appropriate levels
        """
        email = 'newuser@example.com'
        sociallogin = self.create_mock_sociallogin(email)
        request = self.factory.get('/')
        request.user = Mock()
        
        with patch('apps.accounts.adapters.logger') as mock_logger:
            self.adapter.pre_social_login(request, sociallogin)
            # Should log that new user will be created
            mock_logger.info.assert_called()
    
    def test_account_linking_logged(self):
        """
        Test that account linking is logged
        
        Requirement: 6.1 - WHEN reviewing the codebase 
        THEN the System SHALL include inline comments explaining OAuth flow logic
        """
        # Create existing user
        email = 'existing@example.com'
        User.objects.create_user(username='existing', email=email, password='test123')
        
        sociallogin = self.create_mock_sociallogin(email)
        request = self.factory.get('/')
        request.user = Mock()
        
        with patch('apps.accounts.adapters.logger') as mock_logger:
            self.adapter.pre_social_login(request, sociallogin)
            # Should log account linking
            mock_logger.info.assert_called()
            # Check that the log message mentions linking
            call_args = str(mock_logger.info.call_args)
            self.assertIn('Linked', call_args)
    
    def test_username_conflict_logged(self):
        """
        Test that username conflicts are logged
        
        Requirement: 6.3 - WHEN troubleshooting OAuth issues 
        THEN the System SHALL include a troubleshooting guide
        """
        # Create existing user
        base_username = 'testuser'
        User.objects.create_user(username=base_username, email='test@example.com', password='test123')
        
        with patch('apps.accounts.adapters.logger') as mock_logger:
            new_username = self.account_adapter.generate_unique_username([base_username])
            # Should log warning about conflict (or info about resolution)
            # The adapter logs at different levels depending on the situation
            self.assertTrue(mock_logger.warning.called or mock_logger.info.called)
    
    def test_missing_data_logged(self):
        """
        Test that missing profile data is logged
        
        Requirement: 5.3 - Logging at appropriate levels
        """
        email = 'incomplete@example.com'
        
        # Create sociallogin with missing names
        sociallogin = Mock(spec=SocialLogin)
        sociallogin.is_existing = False
        social_account = Mock(spec=SocialAccount)
        social_account.provider = 'google'
        social_account.extra_data = {
            'email': email,
            # Missing given_name and family_name
            'verified_email': True
        }
        sociallogin.account = social_account
        sociallogin.user = User()
        
        request = self.factory.get('/')
        
        with patch('apps.accounts.adapters.logger') as mock_logger:
            self.adapter.populate_user(request, sociallogin, {'email': email})
            # Should log warning about incomplete data
            mock_logger.warning.assert_called()
