"""
Management command to check deployment readiness.
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.management import call_command
import os


class Command(BaseCommand):
    help = 'Check if the application is ready for deployment'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Deployment Readiness Check ===\n'))
        
        checks_passed = 0
        checks_failed = 0
        
        # Check 1: DEBUG setting
        if settings.DEBUG:
            self.stdout.write(self.style.WARNING('⚠ DEBUG is True - should be False in production'))
            checks_failed += 1
        else:
            self.stdout.write(self.style.SUCCESS('✓ DEBUG is False'))
            checks_passed += 1
        
        # Check 2: SECRET_KEY
        if settings.SECRET_KEY == 'django-insecure-b^+n-0fl1)xw+4xg3g^dm_m+&=&ah10e75e(khx(=8%-v%$^yc':
            self.stdout.write(self.style.ERROR('✗ SECRET_KEY is using default insecure value'))
            checks_failed += 1
        else:
            self.stdout.write(self.style.SUCCESS('✓ SECRET_KEY is configured'))
            checks_passed += 1
        
        # Check 3: ALLOWED_HOSTS
        if not settings.ALLOWED_HOSTS or settings.ALLOWED_HOSTS == []:
            self.stdout.write(self.style.ERROR('✗ ALLOWED_HOSTS is empty'))
            checks_failed += 1
        else:
            self.stdout.write(self.style.SUCCESS(f'✓ ALLOWED_HOSTS configured: {settings.ALLOWED_HOSTS}'))
            checks_passed += 1
        
        # Check 4: Database
        db_engine = settings.DATABASES['default']['ENGINE']
        if 'sqlite' in db_engine:
            self.stdout.write(self.style.WARNING('⚠ Using SQLite - consider PostgreSQL for production'))
            checks_failed += 1
        else:
            self.stdout.write(self.style.SUCCESS(f'✓ Database configured: {db_engine}'))
            checks_passed += 1
        
        # Check 5: Static files
        if not settings.STATIC_ROOT:
            self.stdout.write(self.style.ERROR('✗ STATIC_ROOT is not configured'))
            checks_failed += 1
        else:
            self.stdout.write(self.style.SUCCESS(f'✓ STATIC_ROOT configured: {settings.STATIC_ROOT}'))
            checks_passed += 1
        
        # Check 6: Media files
        if not settings.MEDIA_ROOT:
            self.stdout.write(self.style.ERROR('✗ MEDIA_ROOT is not configured'))
            checks_failed += 1
        else:
            self.stdout.write(self.style.SUCCESS(f'✓ MEDIA_ROOT configured: {settings.MEDIA_ROOT}'))
            checks_passed += 1
        
        # Check 7: Email backend
        if 'console' in settings.EMAIL_BACKEND:
            self.stdout.write(self.style.WARNING('⚠ Using console email backend - configure SMTP for production'))
            checks_failed += 1
        else:
            self.stdout.write(self.style.SUCCESS(f'✓ Email backend configured: {settings.EMAIL_BACKEND}'))
            checks_passed += 1
        
        # Check 8: Run Django system checks
        self.stdout.write('\n=== Running Django System Checks ===\n')
        try:
            call_command('check', '--deploy')
            self.stdout.write(self.style.SUCCESS('✓ Django system checks passed'))
            checks_passed += 1
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Django system checks failed: {e}'))
            checks_failed += 1
        
        # Summary
        self.stdout.write('\n=== Summary ===')
        self.stdout.write(f'Checks passed: {checks_passed}')
        self.stdout.write(f'Checks failed: {checks_failed}')
        
        if checks_failed == 0:
            self.stdout.write(self.style.SUCCESS('\n✓ Application is ready for deployment!'))
        else:
            self.stdout.write(self.style.WARNING(f'\n⚠ {checks_failed} issue(s) need attention before deployment'))
