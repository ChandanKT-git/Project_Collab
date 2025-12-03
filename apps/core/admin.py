from django.contrib import admin
from django.contrib.auth.models import User
from django.urls import path
from django.shortcuts import render
from django.db.models import Count, Q
from django.core.exceptions import PermissionDenied


def system_statistics_view(request):
    """Display system statistics - only accessible to superusers."""
    # Only superusers can access
    if not request.user.is_superuser:
        raise PermissionDenied
    
    # Import models here to avoid circular imports
    from apps.teams.models import Team
    from apps.tasks.models import Task, Comment, FileUpload, ActivityLog
    from apps.notifications.models import Notification
    
    # Gather statistics
    stats = {
        'total_users': User.objects.count(),
        'total_teams': Team.objects.count(),
        'total_tasks': Task.objects.count(),
        'total_comments': Comment.objects.count(),
        'total_file_uploads': FileUpload.objects.count(),
        'total_notifications': Notification.objects.count(),
        'total_activity_logs': ActivityLog.objects.count(),
        
        # Task statistics by status
        'tasks_todo': Task.objects.filter(status=Task.TODO).count(),
        'tasks_in_progress': Task.objects.filter(status=Task.IN_PROGRESS).count(),
        'tasks_review': Task.objects.filter(status=Task.REVIEW).count(),
        'tasks_done': Task.objects.filter(status=Task.DONE).count(),
        
        # Team statistics
        'teams_with_members': Team.objects.annotate(
            member_count=Count('memberships')
        ).filter(member_count__gt=1).count(),
        
        # User statistics
        'active_users': User.objects.filter(
            Q(created_tasks__isnull=False) | 
            Q(comments__isnull=False)
        ).distinct().count(),
        
        # Notification statistics
        'unread_notifications': Notification.objects.filter(is_read=False).count(),
    }
    
    context = {
        'title': 'System Statistics',
        'stats': stats,
        'site_header': admin.site.site_header,
        'site_title': admin.site.site_title,
        'has_permission': True,
    }
    
    return render(request, 'admin/system_statistics.html', context)


# Extend the default admin site with custom URLs
class CustomAdminSite(admin.AdminSite):
    """Custom admin site with system statistics."""
    
    def get_urls(self):
        """Add custom URL for system statistics."""
        urls = super().get_urls()
        custom_urls = [
            path('statistics/', self.admin_view(system_statistics_view), name='system_statistics'),
        ]
        return custom_urls + urls


# Create custom admin site instance
custom_admin_site = CustomAdminSite(name='custom_admin')
