#!/usr/bin/env python
"""
Fix Site domain configuration.
The domain should not include protocol (https://) or trailing slashes.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.sites.models import Site


def fix_site_domain():
    """Fix the Site domain to remove protocol and trailing slashes."""
    print("\n=== Fixing Site Domain Configuration ===\n")
    
    site = Site.objects.get(id=1)
    
    print(f"Current domain: '{site.domain}'")
    print(f"Current name: '{site.name}'")
    
    # Clean up the domain
    domain = site.domain
    
    # Remove protocol
    domain = domain.replace('https://', '').replace('http://', '')
    
    # Remove trailing slashes
    domain = domain.rstrip('/')
    
    # Remove www. if present (optional)
    # domain = domain.replace('www.', '')
    
    if domain != site.domain:
        print(f"\n✓ Updating domain to: '{domain}'")
        site.domain = domain
        site.save()
        print("✓ Site domain updated successfully!")
    else:
        print("\n✓ Domain is already correct!")
    
    print(f"\nFinal configuration:")
    print(f"  Domain: {site.domain}")
    print(f"  Name: {site.name}")
    
    print("\n" + "="*60)
    print("Important: Update Google Cloud Console")
    print("="*60)
    print("\nAuthorized JavaScript origins:")
    print(f"  https://{site.domain}")
    print("\nAuthorized redirect URIs:")
    print(f"  https://{site.domain}/accounts/google/login/callback/")
    print("\nFor local development, also add:")
    print("  http://localhost:8000")
    print("  http://localhost:8000/accounts/google/login/callback/")
    print("="*60 + "\n")


def main():
    """Main function."""
    try:
        fix_site_domain()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✗ Cancelled by user")
        sys.exit(1)
