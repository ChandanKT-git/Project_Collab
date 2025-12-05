#!/usr/bin/env python
"""
Test notification system
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from apps.tasks.models import Task
from apps.teams.models import Team, TeamMembership
from apps.notifications.services import NotificationService, EmailService

print("=" * 60)
print("NOTIFICATION SYSTEM TEST")
print("=" * 60)

print("\n1. Email Configuration:")
print(f"   EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"   EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"   EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"   EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
print(f"   DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")

print("\n2. Testing basic email sending...")
try:
    send_mail(
        subject='Test Email - Project Collaboration Portal',
        message='This is a test email to verify email configuration.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.EMAIL_HOST_USER],
        fail_silently=False,
    )
    print("   ✓ Basic email sent successfully!")
except Exception as e:
    print(f"   ✗ Failed to send email: {str(e)}")
    print("\n   Troubleshooting:")
    print("   - Ensure EMAIL_HOST_USER is a valid Gmail address")
    print("   - Use an App Password, not your regular password")
    print("   - Enable 2FA on Gmail and generate App Password at:")
    print("     https://myaccount.google.com/apppasswords")

print("\n3. Checking database for test data...")
users = User.objects.all()
teams = Team.objects.all()
tasks = Task.objects.all()

print(f"   Users: {users.count()}")
print(f"   Teams: {teams.count()}")
print(f"   Tasks: {tasks.count()}")

if users.count() >= 2:
    print("\n4. Testing notification creation...")
    user1 = users.first()
    user2 = users.last()
    
    if tasks.exists():
        task = tasks.first()
        print(f"   Using task: {task.title}")
        print(f"   Recipient: {user2.username} ({user2.email})")
        
        # Create a test notification
        notification = NotificationService.create_notification(
            recipient=user2,
            sender=user1,
            notification_type='assignment',
            message=f"TEST: {user1.username} assigned you to task '{task.title}'",
            content_object=task
        )
        print(f"   ✓ Notification created: ID {notification.id}")
        
        # Try to send email
        print("\n5. Testing notification email...")
        try:
            result = EmailService.send_notification_email(notification)
            if result:
                print(f"   ✓ Notification email sent to {user2.email}")
            else:
                print(f"   ✗ Failed to send notification email")
        except Exception as e:
            print(f"   ✗ Error sending notification email: {str(e)}")
    else:
        print("   No tasks found. Create a task to test notifications.")
else:
    print("   Need at least 2 users to test notifications.")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
