#!/usr/bin/env python
"""
Verification script for OAuth settings configuration.
This script checks that all required settings for the Google OAuth flow are properly configured.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings

def verify_settings():
    """Verify all required OAuth settings are configured correctly."""
    
    print("=" * 60)
    print("OAuth Settings Verification")
    print("=" * 60)
    
    checks = []
    
    # Check 1: SOCIALACCOUNT_ADAPTER
    adapter = getattr(settings, 'SOCIALACCOUNT_ADAPTER', None)
    expected_adapter = 'apps.accounts.adapters.CustomSocialAccountAdapter'
    if adapter == expected_adapter:
        print(f"✓ SOCIALACCOUNT_ADAPTER: {adapter}")
        checks.append(True)
    else:
        print(f"✗ SOCIALACCOUNT_ADAPTER: Expected '{expected_adapter}', got '{adapter}'")
        checks.append(False)
    
    # Check 2: ACCOUNT_ADAPTER
    account_adapter = getattr(settings, 'ACCOUNT_ADAPTER', None)
    expected_account_adapter = 'apps.accounts.adapters.CustomAccountAdapter'
    if account_adapter == expected_account_adapter:
        print(f"✓ ACCOUNT_ADAPTER: {account_adapter}")
        checks.append(True)
    else:
        print(f"✗ ACCOUNT_ADAPTER: Expected '{expected_account_adapter}', got '{account_adapter}'")
        checks.append(False)
    
    # Check 3: SOCIALACCOUNT_AUTO_SIGNUP
    auto_signup = getattr(settings, 'SOCIALACCOUNT_AUTO_SIGNUP', None)
    if auto_signup is True:
        print(f"✓ SOCIALACCOUNT_AUTO_SIGNUP: {auto_signup}")
        checks.append(True)
    else:
        print(f"✗ SOCIALACCOUNT_AUTO_SIGNUP: Expected True, got {auto_signup}")
        checks.append(False)
    
    # Check 4: ACCOUNT_LOGIN_METHODS (replaces deprecated ACCOUNT_AUTHENTICATION_METHOD)
    login_methods = getattr(settings, 'ACCOUNT_LOGIN_METHODS', None)
    if 'email' in login_methods:
        print(f"✓ ACCOUNT_LOGIN_METHODS: {login_methods} (includes 'email')")
        checks.append(True)
    else:
        print(f"✗ ACCOUNT_LOGIN_METHODS: Expected to include 'email', got {login_methods}")
        checks.append(False)
    
    # Check 5: ACCOUNT_SIGNUP_FIELDS (includes email and username requirements)
    signup_fields = getattr(settings, 'ACCOUNT_SIGNUP_FIELDS', None)
    if 'email*' in signup_fields and 'username*' in signup_fields:
        print(f"✓ ACCOUNT_SIGNUP_FIELDS: {signup_fields} (includes required email and username)")
        checks.append(True)
    else:
        print(f"✗ ACCOUNT_SIGNUP_FIELDS: Expected to include 'email*' and 'username*', got {signup_fields}")
        checks.append(False)
    
    # Check 6: LOGIN_REDIRECT_URL
    redirect_url = getattr(settings, 'LOGIN_REDIRECT_URL', None)
    if redirect_url == '/':
        print(f"✓ LOGIN_REDIRECT_URL: {redirect_url}")
        checks.append(True)
    else:
        print(f"✗ LOGIN_REDIRECT_URL: Expected '/', got '{redirect_url}'")
        checks.append(False)
    
    print("=" * 60)
    
    # Summary
    passed = sum(checks)
    total = len(checks)
    
    if all(checks):
        print(f"✓ All {total} settings verified successfully!")
        print("=" * 60)
        return 0
    else:
        print(f"✗ {total - passed} out of {total} checks failed")
        print("=" * 60)
        return 1

if __name__ == '__main__':
    sys.exit(verify_settings())
