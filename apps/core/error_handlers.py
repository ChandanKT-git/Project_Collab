"""
Custom error handlers for the application.
"""
import logging
from django.shortcuts import render

logger = logging.getLogger(__name__)


def handler400(request, exception=None):
    """Handle 400 Bad Request errors."""
    logger.warning(f'Bad Request (400) at {request.path}', extra={
        'status_code': 400,
        'request': request,
    })
    return render(request, '400.html', status=400)


def handler403(request, exception=None):
    """Handle 403 Forbidden errors."""
    logger.warning(f'Forbidden (403) at {request.path}', extra={
        'status_code': 403,
        'request': request,
    })
    return render(request, '403.html', status=403)


def handler404(request, exception=None):
    """Handle 404 Not Found errors."""
    logger.info(f'Not Found (404) at {request.path}', extra={
        'status_code': 404,
        'request': request,
    })
    return render(request, '404.html', status=404)


def handler500(request):
    """Handle 500 Internal Server Error."""
    logger.error(f'Server Error (500) at {request.path}', extra={
        'status_code': 500,
        'request': request,
    }, exc_info=True)
    return render(request, '500.html', status=500)
