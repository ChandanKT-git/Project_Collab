#!/usr/bin/env python
"""
Check email configuration in production
Run with: railway run python check_email_config.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from django.core.mail import send_mail

print("=" * 60)
print("EMAIL CONFIGURATION CHECK")
print("=" * 60)

print("\n1. Email Settings:")
print(f"   EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"   EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"   EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"   EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
print(f"   EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
print(f"   EMAIL_HOST_PASSWORD: {'*' * len(settings.EMAIL_HOST_PASSWORD) if settings.EMAIL_HOST_PASSWORD else 'NOT SET'}")
print(f"   DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
print(f"   EMAIL_TIMEOUT: {getattr(settings, 'EMAIL_TIMEOUT', 'NOT SET')}")

print("\n2. Checking if credentials are set:")
if not settings.EMAIL_HOST_USER:
    print("   ❌ EMAIL_HOST_USER is not set!")
else:
    print(f"   ✓ EMAIL_HOST_USER is set: {settings.EMAIL_HOST_USER}")

if not settings.EMAIL_HOST_PASSWORD:
    print("   ❌ EMAIL_HOST_PASSWORD is not set!")
else:
    print(f"   ✓ EMAIL_HOST_PASSWORD is set (length: {len(settings.EMAIL_HOST_PASSWORD)})")

print("\n3. Testing email send:")
try:
    result = send_mail(
        subject='Test Email from Railway',
        message='This is a test email to verify configuration.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.EMAIL_HOST_USER],  # Send to yourself
        fail_silently=False,  # Show errors
    )
    print(f"   ✓ Email sent successfully! Result: {result}")
    print(f"   Check inbox: {settings.EMAIL_HOST_USER}")
except Exception as e:
    print(f"   ❌ Failed to send email: {str(e)}")
    print(f"   Error type: {type(e).__name__}")

print("\n" + "=" * 60)
