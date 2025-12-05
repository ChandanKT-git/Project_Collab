"""
Test script to verify email configuration is working.
Run with: python manage.py shell < test_email.py
"""
from django.core.mail import send_mail
from django.conf import settings

print("Testing email configuration...")
print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")

try:
    send_mail(
        subject='Test Email from Project Collaboration Portal',
        message='This is a test email to verify the email configuration is working correctly.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.EMAIL_HOST_USER],
        fail_silently=False,
    )
    print("\n✓ Email sent successfully!")
    print("Check your inbox for the test email.")
except Exception as e:
    print(f"\n✗ Failed to send email: {str(e)}")
    print("\nPlease check your email configuration in .env file:")
    print("- EMAIL_HOST_USER should be a valid Gmail address")
    print("- EMAIL_HOST_PASSWORD should be an App Password (not your regular password)")
    print("- Make sure 2-factor authentication is enabled on your Gmail account")
    print("- Generate an App Password at: https://myaccount.google.com/apppasswords")
