"""Test to verify Django and pytest setup"""
import pytest
from django.conf import settings


def test_django_settings():
    """Verify Django settings are loaded correctly"""
    # Verify all our apps are installed
    assert 'apps.accounts' in settings.INSTALLED_APPS
    assert 'apps.teams' in settings.INSTALLED_APPS
    assert 'apps.tasks' in settings.INSTALLED_APPS
    assert 'apps.notifications' in settings.INSTALLED_APPS
    assert 'apps.core' in settings.INSTALLED_APPS
    assert 'guardian' in settings.INSTALLED_APPS
    
    # Verify guardian authentication backend is configured
    assert 'guardian.backends.ObjectPermissionBackend' in settings.AUTHENTICATION_BACKENDS


def test_hypothesis_integration():
    """Verify Hypothesis is available for property-based testing"""
    from hypothesis import given
    from hypothesis import strategies as st
    
    @given(st.integers())
    def property_test(x):
        assert isinstance(x, int)
    
    property_test()
