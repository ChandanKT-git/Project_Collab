"""Context processors for notifications."""
from .services import NotificationService


def notification_count(request):
    """Add unread notification count to template context."""
    if request.user.is_authenticated:
        return {
            'unread_notification_count': NotificationService.get_unread_count(request.user)
        }
    return {
        'unread_notification_count': 0
    }
