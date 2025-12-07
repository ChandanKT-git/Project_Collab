"""
Custom django-allauth adapters for seamless OAuth authentication.

This module provides custom adapters that handle:
- Automatic account creation for new users via Google OAuth
- Automatic account linking for existing users with matching emails
- Intelligent username generation with conflict resolution
- User profile data population from Google
- Comprehensive logging of OAuth events
"""

import logging
from django.contrib.auth.models import User
from django.conf import settings
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import user_email, user_field, user_username
import re
from datetime import datetime

logger = logging.getLogger('apps.accounts')


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom social account adapter for handling Google OAuth authentication.
    
    This adapter customizes the OAuth flow to:
    - Automatically link Google accounts to existing users with matching emails
    - Populate user data from Google profile information
    - Handle edge cases gracefully with appropriate logging
    """
    
    def pre_social_login(self, request, sociallogin):
        """
        Handle existing user detection and automatic account linking.
        
        This method is called before a social login is processed. It checks if
        a user with the same email already exists and automatically links the
        social account to that user, enabling seamless login.
        
        Args:
            request: The HTTP request object
            sociallogin: The SocialLogin object containing OAuth data
            
        Requirements: 2.1, 2.2, 2.3, 2.4
        """
        # If the social account is already connected to a user, nothing to do
        if sociallogin.is_existing:
            return
        
        # Try to get the email from the social account data
        email = None
        if sociallogin.account.provider == 'google':
            email = sociallogin.account.extra_data.get('email')
        
        if not email:
            logger.warning('Google OAuth login attempted without email address')
            return
        
        # Check if a user with this email already exists
        try:
            existing_user = User.objects.get(email=email)
            
            # Link the social account to the existing user
            sociallogin.connect(request, existing_user)
            
            logger.info(
                f'Linked Google account to existing user: {existing_user.username} '
                f'(email: {email})'
            )
            
        except User.DoesNotExist:
            # No existing user with this email - will create a new one
            logger.info(f'New user will be created for email: {email}')
        except User.MultipleObjectsReturned:
            # Multiple users with same email - use the first one (oldest)
            logger.error(
                f'Multiple users found with email {email} during OAuth login. '
                'Using the first (oldest) user. This indicates a data integrity issue.'
            )
            existing_user = User.objects.filter(email=email).order_by('date_joined').first()
            if existing_user:
                sociallogin.connect(request, existing_user)
                logger.info(f'Linked Google account to user: {existing_user.username}')
    
    def populate_user(self, request, sociallogin, data):
        """
        Populate user fields from Google profile data.
        
        Extracts information from the Google OAuth response and populates
        the user model fields appropriately.
        
        Args:
            request: The HTTP request object
            sociallogin: The SocialLogin object containing OAuth data
            data: Dictionary of user data from the social provider
            
        Returns:
            User instance with populated fields
            
        Requirements: 1.2, 1.5, 4.2
        """
        user = super().populate_user(request, sociallogin, data)
        
        # Extract data from Google profile
        if sociallogin.account.provider == 'google':
            extra_data = sociallogin.account.extra_data
            
            # Populate first name
            if not user.first_name and extra_data.get('given_name'):
                user_field(user, 'first_name', extra_data.get('given_name', ''))
                logger.info(f'Populated first_name from Google: {extra_data.get("given_name")}')
            
            # Populate last name
            if not user.last_name and extra_data.get('family_name'):
                user_field(user, 'last_name', extra_data.get('family_name', ''))
                logger.info(f'Populated last_name from Google: {extra_data.get("family_name")}')
            
            # Populate email
            if not user.email and extra_data.get('email'):
                user_email(user, extra_data.get('email', ''))
                logger.info(f'Populated email from Google: {extra_data.get("email")}')
            
            # Log if data is missing
            if not extra_data.get('given_name') or not extra_data.get('family_name'):
                logger.warning(
                    f'Incomplete profile data from Google for email {extra_data.get("email")}: '
                    f'given_name={extra_data.get("given_name")}, '
                    f'family_name={extra_data.get("family_name")}'
                )
        
        return user
    
    def save_user(self, request, sociallogin, form=None):
        """
        Save the user after OAuth authentication.
        
        This method is called when creating a new user via social login.
        It ensures proper logging of account creation events.
        
        Args:
            request: The HTTP request object
            sociallogin: The SocialLogin object containing OAuth data
            form: Optional form data (usually None for auto-signup)
            
        Returns:
            The saved User instance
            
        Requirements: 1.1, 5.3
        """
        user = super().save_user(request, sociallogin, form)
        
        # Log successful account creation
        logger.info(
            f'Created new user via Google OAuth: {user.username} '
            f'(email: {user.email}, name: {user.first_name} {user.last_name})'
        )
        
        return user


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom account adapter for handling username generation and account management.
    
    This adapter provides intelligent username generation with conflict resolution
    to ensure seamless account creation without user intervention.
    """
    
    def generate_unique_username(self, txts, regex=None):
        """
        Generate a unique username from provided text inputs.
        
        This method creates usernames from email addresses or names, handling
        conflicts by appending numeric suffixes. If all numeric suffixes fail,
        it falls back to using a timestamp.
        
        Args:
            txts: List of text strings to use for username generation
            regex: Optional regex pattern for username validation
            
        Returns:
            A unique username string
            
        Requirements: 1.2, 1.4, 4.1
        """
        # Start with the default implementation
        username = super().generate_unique_username(txts, regex)
        
        # Clean the username: remove special characters, keep only alphanumeric and underscores
        username = re.sub(r'[^\w]', '', username.lower())
        
        # Ensure username is not empty
        if not username:
            username = 'user'
        
        # Truncate to reasonable length (leaving room for suffix)
        max_length = 25  # Leave room for numeric suffix
        username = username[:max_length]
        
        # Check if username already exists
        original_username = username
        if not User.objects.filter(username=username).exists():
            logger.info(f'Generated unique username: {username}')
            return username
        
        # Username exists, try numeric suffixes
        logger.warning(f'Username conflict detected for: {username}')
        
        for i in range(1, 1000):  # Try up to 999 suffixes
            candidate = f'{username}{i}'
            if not User.objects.filter(username=candidate).exists():
                logger.info(
                    f'Resolved username conflict: {original_username} → {candidate}'
                )
                return candidate
        
        # If we've exhausted numeric suffixes, use timestamp as last resort
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        fallback_username = f'{username[:15]}_{timestamp}'
        
        logger.warning(
            f'Could not resolve username conflict with numeric suffix. '
            f'Using timestamp fallback: {original_username} → {fallback_username}'
        )
        
        return fallback_username
    
    def save_user(self, request, user, form, commit=True):
        """
        Save a user account with custom logic.
        
        This method ensures proper logging when users are created through
        the standard signup flow (not OAuth).
        
        Args:
            request: The HTTP request object
            user: The User instance to save
            form: The signup form containing user data
            commit: Whether to save to database immediately
            
        Returns:
            The saved User instance
            
        Requirements: 5.3
        """
        user = super().save_user(request, user, form, commit)
        
        if commit:
            logger.info(
                f'Created new user via standard signup: {user.username} '
                f'(email: {user.email})'
            )
        
        return user
