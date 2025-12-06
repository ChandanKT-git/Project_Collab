"""Custom middleware for performance optimization."""
from django.utils.cache import patch_cache_control
from django.core.cache import cache


class CacheControlMiddleware:
    """Add cache control headers to responses."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Add cache headers for static content
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            # Cache static files for 1 year
            patch_cache_control(response, max_age=31536000, public=True, immutable=True)
        elif request.method == 'GET' and not request.user.is_authenticated:
            # Cache public pages for 5 minutes
            patch_cache_control(response, max_age=300, public=True)
        
        return response


class CompressionMiddleware:
    """Add compression hints to responses."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Add Vary header for proper caching with compression
        if 'Vary' not in response:
            response['Vary'] = 'Accept-Encoding'
        
        return response
