#!/usr/bin/env python
"""
Send a test email directly
Run with: railway run python send_test_email.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

print("Sending test email...")
print(f"From: {settings.DEFAULT_FROM_EMAIL}")
print(f"To: chandukt29092004@gmail.com")

try:
    send_mail(
        subject='🔔 Test Notification from Project Collab',
        message='If you receive this email, your notification system is working!',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=['chandukt29092004@gmail.com', 'cktofficial24@gmail.com'],
        fail_silently=False,
    )
    print("✓ Email sent successfully!")
    print("Check your inbox (and spam folder)")
except Exception as e:
    print(f"✗ Failed: {str(e)}")
