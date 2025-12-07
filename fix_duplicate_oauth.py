#!/usr/bin/env python
"""
Fix duplicate Google OAuth Social Applications.
This script removes duplicate entries and keeps only one.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site


def fix_duplicates():
    """Remove duplicate Google OAuth applications."""
    print("\n=== Checking for duplicate Google OAuth applications ===\n")
    
    # Get all Google OAuth apps
    google_apps = SocialApp.objects.filter(provider='google')
    count = google_apps.count()
    
    print(f"Found {count} Google OAuth application(s)")
    
    if count == 0:
        print("✗ No Google OAuth applications found!")
        print("Please run: python setup_google_oauth.py")
        return False
    
    if count == 1:
        print("✓ No duplicates found. Configuration is correct.")
        app = google_apps.first()
        print(f"\nCurrent configuration:")
        print(f"  Provider: {app.provider}")
        print(f"  Name: {app.name}")
        print(f"  Client ID: {app.client_id[:20]}...")
        print(f"  Sites: {', '.join([s.domain for s in app.sites.all()])}")
        return True
    
    # Multiple apps found - need to clean up
    print(f"\n⚠ Found {count} duplicate Google OAuth applications!")
    print("\nListing all applications:")
    
    for i, app in enumerate(google_apps, 1):
        print(f"\n{i}. ID: {app.id}")
        print(f"   Name: {app.name}")
        print(f"   Client ID: {app.client_id[:30]}...")
        print(f"   Sites: {', '.join([s.domain for s in app.sites.all()])}")
    
    # Keep the first one, delete the rest
    print("\n=== Cleaning up duplicates ===")
    
    keep_app = google_apps.first()
    print(f"\nKeeping application ID {keep_app.id}: {keep_app.name}")
    
    # Delete duplicates
    duplicates = google_apps.exclude(id=keep_app.id)
    deleted_count = duplicates.count()
    
    if deleted_count > 0:
        duplicates.delete()
        print(f"✓ Deleted {deleted_count} duplicate application(s)")
    
    # Verify the remaining app has the correct site
    site = Site.objects.get(id=1)
    if site not in keep_app.sites.all():
        keep_app.sites.add(site)
        print(f"✓ Added site '{site.domain}' to the application")
    
    print("\n=== Cleanup Complete ===")
    print(f"\nRemaining configuration:")
    print(f"  Provider: {keep_app.provider}")
    print(f"  Name: {keep_app.name}")
    print(f"  Client ID: {keep_app.client_id[:30]}...")
    print(f"  Sites: {', '.join([s.domain for s in keep_app.sites.all()])}")
    
    return True


def main():
    """Main function."""
    print("\n" + "="*60)
    print("Google OAuth Duplicate Cleanup")
    print("="*60)
    
    try:
        success = fix_duplicates()
        
        if success:
            print("\n" + "="*60)
            print("✓ Configuration is now correct!")
            print("="*60)
            print("\nYou can now test Google OAuth:")
            print("1. Start your server: python manage.py runserver")
            print("2. Visit: http://localhost:8000/accounts/login/")
            print("3. Click 'Sign in with Google'")
            print("\n" + "="*60 + "\n")
        else:
            print("\n✗ Please configure Google OAuth first")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✗ Cleanup cancelled by user")
        sys.exit(1)
