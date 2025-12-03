from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Notification
from .services import NotificationService


@login_required
def notification_list(request):
    """Display list of notifications for the current user."""
    notifications = Notification.objects.filter(recipient=request.user)
    unread_count = NotificationService.get_unread_count(request.user)
    
    context = {
        'notifications': notifications,
        'unread_count': unread_count,
    }
    return render(request, 'notifications/notification_list.html', context)


@login_required
def mark_notification_read(request, notification_id):
    """Mark a single notification as read."""
    notification = NotificationService.mark_as_read(notification_id, request.user)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # AJAX request
        if notification:
            return JsonResponse({'success': True, 'notification_id': notification_id})
        return JsonResponse({'success': False}, status=404)
    
    # Regular request
    return redirect('notifications:notification_list')


@login_required
def mark_all_read(request):
    """Mark all notifications as read for the current user."""
    if request.method == 'POST':
        count = NotificationService.mark_all_as_read(request.user)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'count': count})
        
        return redirect('notifications:notification_list')
    
    return redirect('notifications:notification_list')


@login_required
def unread_count(request):
    """Get unread notification count (for AJAX requests)."""
    count = NotificationService.get_unread_count(request.user)
    return JsonResponse({'count': count})
