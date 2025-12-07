"""
Automatic script to fix duplicate users with the same email address.
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from django.db.models import Count
from allauth.socialaccount.models import SocialAccount


def fix_duplicate_users(email):
    """Fix duplicate users for a given email."""
    users = User.objects.filter(email=email).order_by('date_joined')
    
    if users.count() <= 1:
        return
    
    # Keep the oldest user
    primary_user = users.first()
    duplicate_users = users[1:]
    
    print(f"\nProcessing email: {email}")
    print(f"  Keeping: {primary_user.username} (ID: {primary_user.id})")
    
    for dup_user in duplicate_users:
        print(f"  Removing: {dup_user.username} (ID: {dup_user.id})")
        
        # Transfer social accounts
        social_accounts = SocialAccount.objects.filter(user=dup_user)
        for social_account in social_accounts:
            # Check if primary user already has this social account
            existing = SocialAccount.objects.filter(
                user=primary_user,
                provider=social_account.provider,
                uid=social_account.uid
            ).exists()
            
            if not existing:
                social_account.user = primary_user
                social_account.save()
                print(f"    Transferred social account: {social_account.provider}")
            else:
                social_account.delete()
                print(f"    Removed duplicate social account: {social_account.provider}")
        
        # Delete duplicate user
        dup_user.delete()
        print(f"    Deleted user")


def main():
    """Main function."""
    print("Fixing duplicate users...")
    
    # Find duplicates
    duplicates = (
        User.objects.values('email')
        .annotate(count=Count('id'))
        .filter(count__gt=1, email__isnull=False)
        .exclude(email='')
        .order_by('-count')
    )
    
    if not duplicates:
        print("No duplicates found!")
        return
    
    print(f"Found {duplicates.count()} email(s) with duplicates")
    
    for dup in duplicates:
        fix_duplicate_users(dup['email'])
    
    print("\n✓ Cleanup completed!")


if __name__ == '__main__':
    main()
