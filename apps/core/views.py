from django.shortcuts import render
from django.contrib.auth.decorators import login_required


def home(request):
    """Home page view with dashboard data for authenticated users"""
    context = {}
    
    if request.user.is_authenticated:
        from apps.teams.models import Team, TeamMembership
        from apps.tasks.models import Task
        from apps.notifications.models import Notification
        
        # Get user's teams
        user_teams = Team.objects.filter(
            memberships__user=request.user
        ).distinct()[:5]
        
        # Get recent tasks
        recent_tasks = Task.objects.filter(
            team__memberships__user=request.user
        ).distinct().order_by('-created_at')[:5]
        
        # Get counts
        user_teams_count = Team.objects.filter(
            memberships__user=request.user
        ).distinct().count()
        
        user_tasks_count = Task.objects.filter(
            team__memberships__user=request.user
        ).distinct().count()
        
        assigned_tasks_count = Task.objects.filter(
            assigned_to=request.user
        ).exclude(status='DONE').count()
        
        unread_notification_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        
        context.update({
            'user_teams': user_teams,
            'recent_tasks': recent_tasks,
            'user_teams_count': user_teams_count,
            'user_tasks_count': user_tasks_count,
            'assigned_tasks_count': assigned_tasks_count,
            'unread_notification_count': unread_notification_count,
        })
    
    return render(request, 'home.html', context)
