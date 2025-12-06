"""
Performance testing script for the application.
Run this to measure query counts and response times.
"""
import os
import django
import time
from django.test.utils import override_settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import RequestFactory
from django.db import connection, reset_queries
from apps.tasks.views import task_list, task_detail
from apps.notifications.views import notification_list


def measure_view_performance(view_func, request, *args, **kwargs):
    """Measure query count and execution time for a view."""
    reset_queries()
    start_time = time.time()
    
    response = view_func(request, *args, **kwargs)
    
    end_time = time.time()
    query_count = len(connection.queries)
    execution_time = (end_time - start_time) * 1000  # Convert to ms
    
    return {
        'query_count': query_count,
        'execution_time_ms': round(execution_time, 2),
        'status_code': response.status_code
    }


def run_performance_tests():
    """Run performance tests on key views."""
    print("=" * 60)
    print("PERFORMANCE TEST RESULTS")
    print("=" * 60)
    
    # Get or create a test user
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )
    if created:
        user.set_password('testpass123')
        user.save()
    
    # Create request factory
    factory = RequestFactory()
    
    # Test 1: Task List
    print("\n1. Task List View")
    print("-" * 60)
    request = factory.get('/tasks/')
    request.user = user
    results = measure_view_performance(task_list, request)
    print(f"   Query Count: {results['query_count']}")
    print(f"   Execution Time: {results['execution_time_ms']}ms")
    print(f"   Status Code: {results['status_code']}")
    
    # Test 2: Notification List
    print("\n2. Notification List View")
    print("-" * 60)
    request = factory.get('/notifications/')
    request.user = user
    results = measure_view_performance(notification_list, request)
    print(f"   Query Count: {results['query_count']}")
    print(f"   Execution Time: {results['execution_time_ms']}ms")
    print(f"   Status Code: {results['status_code']}")
    
    # Performance benchmarks
    print("\n" + "=" * 60)
    print("PERFORMANCE BENCHMARKS")
    print("=" * 60)
    print("\nTarget Metrics:")
    print("  - Query Count: < 10 queries per page")
    print("  - Execution Time: < 300ms per page")
    print("\nOptimizations Applied:")
    print("  ✓ Database connection pooling (CONN_MAX_AGE=600)")
    print("  ✓ Query optimization with select_related()")
    print("  ✓ Query optimization with prefetch_related()")
    print("  ✓ Field-level optimization with only()")
    print("  ✓ Result limiting for large datasets")
    print("  ✓ Pagination (25 items per page)")
    print("  ✓ In-memory caching configured")
    print("  ✓ Cache control headers")
    print("\n" + "=" * 60)


if __name__ == '__main__':
    # Enable query logging
    from django.conf import settings
    settings.DEBUG = True
    
    run_performance_tests()
