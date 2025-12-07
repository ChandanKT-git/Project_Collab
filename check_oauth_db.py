#!/usr/bin/env python
"""
Check the actual database state for OAuth configuration.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site


def check_database():
    """Check what's actually in the database."""
    print("\n=== Checking Database State ===\n")
    
    # Check Sites
    print("SITES:")
    sites = Site.objects.all()
    for site in sites:
        print(f"  ID: {site.id}, Domain: '{site.domain}', Name: '{site.name}'")
    
    print(f"\nTotal sites: {sites.count()}\n")
    
    # Check Social Apps
    print("SOCIAL APPLICATIONS:")
    apps = SocialApp.objects.all()
    for app in apps:
        print(f"\n  ID: {app.id}")
        print(f"  Provider: {app.provider}")
        print(f"  Name: {app.name}")
        print(f"  Client ID: {app.client_id}")
        print(f"  Secret: {app.secret[:20]}...")
        print(f"  Sites: {[s.domain for s in app.sites.all()]}")
    
    print(f"\nTotal social apps: {apps.count()}\n")
    
    # Check for Google apps specifically
    google_apps = SocialApp.objects.filter(provider='google')
    print(f"Google OAuth apps: {google_apps.count()}")
    
    if google_apps.count() > 1:
        print("\n⚠ WARNING: Multiple Google OAuth apps found!")
        print("This is causing the MultipleObjectsReturned error.")
        print("\nDeleting duplicates...")
        
        # Keep the first one
        keep = google_apps.first()
        print(f"Keeping app ID {keep.id}")
        
        # Delete the rest
        for app in google_apps.exclude(id=keep.id):
            print(f"Deleting app ID {app.id}")
            app.delete()
        
        print("\n✓ Duplicates removed!")
        
        # Verify
        remaining = SocialApp.objects.filter(provider='google').count()
        print(f"Remaining Google OAuth apps: {remaining}")


if __name__ == '__main__':
    try:
        check_database()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
