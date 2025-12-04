"""
Management command to check CSRF configuration
"""
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Check CSRF configuration for deployment'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== CSRF Configuration Check ===\n'))
        
        # Check ALLOWED_HOSTS
        self.stdout.write(f'ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}')
        
        # Check CSRF_TRUSTED_ORIGINS
        csrf_origins = getattr(settings, 'CSRF_TRUSTED_ORIGINS', [])
        self.stdout.write(f'CSRF_TRUSTED_ORIGINS: {csrf_origins}')
        
        # Check CSRF cookie settings
        self.stdout.write(f'CSRF_COOKIE_SECURE: {settings.CSRF_COOKIE_SECURE}')
        self.stdout.write(f'CSRF_COOKIE_HTTPONLY: {getattr(settings, "CSRF_COOKIE_HTTPONLY", "Not set")}')
        self.stdout.write(f'CSRF_COOKIE_SAMESITE: {getattr(settings, "CSRF_COOKIE_SAMESITE", "Not set")}')
        self.stdout.write(f'CSRF_USE_SESSIONS: {getattr(settings, "CSRF_USE_SESSIONS", "Not set")}')
        
        # Check if using production settings
        self.stdout.write(f'\nDEBUG: {settings.DEBUG}')
        self.stdout.write(f'SETTINGS_MODULE: {settings.SETTINGS_MODULE}')
        
        # Validation
        self.stdout.write(self.style.SUCCESS('\n=== Validation ==='))
        
        if not csrf_origins:
            self.stdout.write(self.style.ERROR('❌ CSRF_TRUSTED_ORIGINS is empty!'))
            self.stdout.write(self.style.WARNING('   Set CSRF_TRUSTED_ORIGINS environment variable'))
        else:
            self.stdout.write(self.style.SUCCESS(f'✅ CSRF_TRUSTED_ORIGINS has {len(csrf_origins)} origin(s)'))
            for origin in csrf_origins:
                if not origin.startswith('https://'):
                    self.stdout.write(self.style.ERROR(f'   ❌ Invalid origin (missing https://): {origin}'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'   ✅ {origin}'))
        
        if not settings.ALLOWED_HOSTS:
            self.stdout.write(self.style.ERROR('❌ ALLOWED_HOSTS is empty!'))
        else:
            self.stdout.write(self.style.SUCCESS(f'✅ ALLOWED_HOSTS has {len(settings.ALLOWED_HOSTS)} host(s)'))
            for host in settings.ALLOWED_HOSTS:
                self.stdout.write(f'   - {host}')
