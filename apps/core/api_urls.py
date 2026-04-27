"""
REST API URL configuration for CollabHub.
"""

from django.urls import path
from . import api_views

app_name = 'api'

urlpatterns = [
    # Auth
    path('auth/csrf/', api_views.csrf_token_view, name='csrf_token'),
    path('auth/user/', api_views.current_user_view, name='current_user'),
    path('auth/login/', api_views.login_view, name='login'),
    path('auth/signup/', api_views.signup_view, name='signup'),
    path('auth/logout/', api_views.logout_view, name='logout'),

    # Dashboard
    path('dashboard/', api_views.dashboard_view, name='dashboard'),

    # Teams
    path('teams/', api_views.team_list_create_view, name='team_list_create'),
    path('teams/<int:pk>/', api_views.team_detail_view, name='team_detail'),
    path('teams/<int:pk>/members/', api_views.team_add_member_view, name='team_add_member'),
    path('teams/<int:pk>/members/<int:user_id>/', api_views.team_member_view, name='team_member'),

    # Tasks
    path('tasks/', api_views.task_list_create_view, name='task_list_create'),
    path('tasks/<int:pk>/', api_views.task_detail_view, name='task_detail'),
    path('tasks/<int:task_pk>/comments/', api_views.comment_create_view, name='comment_create'),
    path('tasks/<int:task_pk>/files/', api_views.file_upload_task_view, name='file_upload_task'),
    path('tasks/status-choices/', api_views.task_status_choices_view, name='task_status_choices'),

    # Team members (for dropdowns)
    path('teams/<int:team_id>/team-members/', api_views.team_members_view, name='team_members'),
    path('user-teams/', api_views.user_teams_view, name='user_teams'),

    # Comments
    path('comments/<int:comment_pk>/reply/', api_views.comment_reply_view, name='comment_reply'),
    path('comments/<int:comment_pk>/', api_views.comment_delete_view, name='comment_delete'),

    # Files
    path('files/<int:file_pk>/download/', api_views.file_download_view, name='file_download'),
    path('files/<int:file_pk>/', api_views.file_delete_view, name='file_delete'),

    # Notifications
    path('notifications/', api_views.notification_list_view, name='notification_list'),
    path('notifications/<int:notification_id>/read/', api_views.notification_mark_read_view, name='notification_mark_read'),
    path('notifications/mark-all-read/', api_views.notification_mark_all_read_view, name='notification_mark_all_read'),
    path('notifications/unread-count/', api_views.notification_unread_count_view, name='notification_unread_count'),
]
