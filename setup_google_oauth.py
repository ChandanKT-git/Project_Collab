#!/usr/bin/env python
"""
Quick setup script for Google OAuth configuration.
Run this after installing django-allauth and running migrations.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from django.conf import settings


def setup_site():
    """Configure the Site object for django-allauth."""
    print("\n=== Setting up Site Configuration ===")
    
    # Get domain from user
    domain = input("Enter your domain (e.g., localhost:8000 for dev, yourdomain.com for prod): ").strip()
    if not domain:
        domain = "localhost:8000"
    
    site_name = input("Enter site name (default: CollabHub): ").strip()
    if not site_name:
        site_name = "CollabHub"
    
    try:
        site = Site.objects.get(id=1)
        site.domain = domain
        site.name = site_name
        site.save()
        print(f"✓ Site configured: {site_name} ({domain})")
    except Site.DoesNotExist:
        site = Site.objects.create(id=1, domain=domain, name=site_name)
        print(f"✓ Site created: {site_name} ({domain})")
    
    return site


def setup_google_oauth(site):
    """Configure Google OAuth Social Application."""
    print("\n=== Setting up Google OAuth ===")
    
    # Check if credentials are in environment
    client_id = os.getenv('GOOGLE_OAUTH_CLIENT_ID', '')
    client_secret = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET', '')
    
    if not client_id or not client_secret:
        print("\n⚠ Google OAuth credentials not found in environment variables.")
        print("Please add them to your .env file:")
        print("  GOOGLE_OAUTH_CLIENT_ID=your-client-id")
        print("  GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret")
        print("\nYou can also enter them now:")
        
        client_id = input("Enter Google OAuth Client ID: ").strip()
        client_secret = input("Enter Google OAuth Client Secret: ").strip()
    
    if not client_id or not client_secret:
        print("✗ Cannot proceed without OAuth credentials")
        return False
    
    # Check if Google OAuth app already exists
    try:
        social_app = SocialApp.objects.get(provider='google')
        social_app.client_id = client_id
        social_app.secret = client_secret
        social_app.save()
        social_app.sites.add(site)
        print("✓ Google OAuth application updated")
    except SocialApp.DoesNotExist:
        social_app = SocialApp.objects.create(
            provider='google',
            name='Google OAuth',
            client_id=client_id,
            secret=client_secret
        )
        social_app.sites.add(site)
        print("✓ Google OAuth application created")
    
    return True


def display_next_steps(site):
    """Display next steps for the user."""
    print("\n" + "="*60)
    print("✓ Google OAuth Setup Complete!")
    print("="*60)
    
    print("\nNext Steps:")
    print("\n1. Configure Google Cloud Console:")
    print(f"   - Authorized JavaScript origins: http://{site.domain}")
    print(f"   - Authorized redirect URIs: http://{site.domain}/accounts/google/login/callback/")
    
    print("\n2. Test the integration:")
    print("   - Start your server: python manage.py runserver")
    print("   - Visit: http://localhost:8000/accounts/login/")
    print("   - Click 'Sign in with Google'")
    
    print("\n3. For production:")
    print("   - Use HTTPS URLs in Google Console")
    print("   - Update Site domain to your production domain")
    print("   - Set environment variables on your hosting platform")
    
    print("\n📖 For detailed instructions, see: GOOGLE_OAUTH_SETUP.md")
    print("="*60 + "\n")


def main():
    """Main setup function."""
    print("\n" + "="*60)
    print("Google OAuth Setup for Django")
    print("="*60)
    
    # Check if migrations have been run
    try:
        Site.objects.count()
    except Exception as e:
        print("\n✗ Error: Database not ready. Please run migrations first:")
        print("  python manage.py migrate")
        sys.exit(1)
    
    # Setup site
    site = setup_site()
    
    # Setup Google OAuth
    success = setup_google_oauth(site)
    
    if success:
        display_next_steps(site)
    else:
        print("\n✗ Setup incomplete. Please configure OAuth credentials and try again.")
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✗ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error during setup: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
