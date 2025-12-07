"""
Script to fix duplicate users with the same email address.

This script identifies users with duplicate email addresses and merges them,
keeping the oldest account and removing duplicates.
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from django.db.models import Count
from allauth.socialaccount.models import SocialAccount


def find_duplicate_emails():
    """Find all email addresses that have multiple users."""
    duplicates = (
        User.objects.values('email')
        .annotate(count=Count('id'))
        .filter(count__gt=1)
        .order_by('-count')
    )
    return duplicates


def fix_duplicate_users(email, dry_run=True):
    """
    Fix duplicate users for a given email.
    
    Keeps the oldest user and removes duplicates.
    Transfers social accounts to the kept user.
    """
    users = User.objects.filter(email=email).order_by('date_joined')
    
    if users.count() <= 1:
        print(f"No duplicates found for {email}")
        return
    
    # Keep the oldest user
    primary_user = users.first()
    duplicate_users = users[1:]
    
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Processing email: {email}")
    print(f"  Primary user (keeping): {primary_user.username} (ID: {primary_user.id}, joined: {primary_user.date_joined})")
    print(f"  Duplicate users (removing): {duplicate_users.count()}")
    
    for dup_user in duplicate_users:
        print(f"    - {dup_user.username} (ID: {dup_user.id}, joined: {dup_user.date_joined})")
        
        # Transfer social accounts
        social_accounts = SocialAccount.objects.filter(user=dup_user)
        if social_accounts.exists():
            print(f"      Found {social_accounts.count()} social account(s)")
            if not dry_run:
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
                        print(f"      Transferred social account: {social_account.provider}")
                    else:
                        print(f"      Skipped duplicate social account: {social_account.provider}")
        
        # Delete duplicate user
        if not dry_run:
            dup_user.delete()
            print(f"      Deleted user: {dup_user.username}")


def main():
    """Main function to fix all duplicate users."""
    print("=" * 80)
    print("DUPLICATE USER CLEANUP SCRIPT")
    print("=" * 80)
    
    # Find duplicates
    duplicates = find_duplicate_emails()
    
    if not duplicates:
        print("\n✓ No duplicate email addresses found!")
        return
    
    print(f"\nFound {duplicates.count()} email address(es) with duplicates:")
    for dup in duplicates:
        print(f"  - {dup['email']}: {dup['count']} users")
    
    # Ask for confirmation
    print("\n" + "=" * 80)
    print("DRY RUN - No changes will be made")
    print("=" * 80)
    
    # Process each duplicate (dry run first)
    for dup in duplicates:
        fix_duplicate_users(dup['email'], dry_run=True)
    
    print("\n" + "=" * 80)
    response = input("\nDo you want to proceed with the cleanup? (yes/no): ")
    
    if response.lower() == 'yes':
        print("\n" + "=" * 80)
        print("EXECUTING CLEANUP")
        print("=" * 80)
        
        for dup in duplicates:
            fix_duplicate_users(dup['email'], dry_run=False)
        
        print("\n" + "=" * 80)
        print("✓ Cleanup completed!")
        print("=" * 80)
    else:
        print("\nCleanup cancelled.")


if __name__ == '__main__':
    main()
