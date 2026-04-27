"""
REST API Views for CollabHub.

Provides viewsets and views for all API endpoints:
- Auth (login, signup, logout, current user, CSRF)
- Teams (CRUD + membership management)
- Tasks (CRUD + filtering/pagination)
- Comments (create, reply, delete)
- Files (upload, download, delete)
- Notifications (list, mark read)
- Dashboard (stats)
"""

import logging
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.http import FileResponse, Http404
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.db.models import Q

from rest_framework import status, permissions, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.pagination import PageNumberPagination

from guardian.shortcuts import get_objects_for_user, assign_perm, remove_perm

from apps.teams.models import Team, TeamMembership
from apps.tasks.models import Task, Comment, FileUpload, ActivityLog
from apps.notifications.models import Notification
from apps.notifications.services import NotificationService

from .api_serializers import (
    UserSerializer, LoginSerializer, SignupSerializer,
    TeamListSerializer, TeamDetailSerializer, TeamCreateUpdateSerializer,
    TeamMembershipSerializer, AddMemberSerializer, ChangeRoleSerializer,
    TaskListSerializer, TaskDetailSerializer, TaskCreateUpdateSerializer,
    CommentSerializer, CommentCreateSerializer,
    FileUploadSerializer,
    NotificationSerializer,
    DashboardSerializer, UserMinimalSerializer,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Auth Views
# =============================================================================

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def csrf_token_view(request):
    """Return CSRF token for the frontend."""
    token = get_token(request)
    return Response({'csrfToken': token})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def current_user_view(request):
    """Return the currently authenticated user."""
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    """Authenticate and login a user."""
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    username = serializer.validated_data['username']
    password = serializer.validated_data['password']

    # Support login with email
    user = authenticate(request, username=username, password=password)
    if user is None:
        # Try email-based login
        try:
            user_obj = User.objects.get(email=username)
            user = authenticate(request, username=user_obj.username, password=password)
        except User.DoesNotExist:
            pass

    if user is not None:
        login(request, user)
        return Response(UserSerializer(user).data)
    return Response(
        {'detail': 'Invalid credentials.'},
        status=status.HTTP_401_UNAUTHORIZED
    )


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def signup_view(request):
    """Register a new user."""
    serializer = SignupSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """Logout the current user."""
    logout(request)
    return Response({'detail': 'Logged out.'})


# =============================================================================
# Dashboard
# =============================================================================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_view(request):
    """Return dashboard statistics for the current user."""
    user = request.user

    user_teams = Team.objects.filter(memberships__user=user).distinct()[:5]
    recent_tasks = Task.objects.filter(
        team__memberships__user=user
    ).distinct().order_by('-created_at')[:5]

    data = {
        'user_teams_count': Team.objects.filter(memberships__user=user).distinct().count(),
        'user_tasks_count': Task.objects.filter(team__memberships__user=user).distinct().count(),
        'assigned_tasks_count': Task.objects.filter(assigned_to=user).exclude(status='DONE').count(),
        'unread_notification_count': Notification.objects.filter(recipient=user, is_read=False).count(),
        'recent_tasks': TaskListSerializer(recent_tasks, many=True, context={'request': request}).data,
        'user_teams': TeamListSerializer(user_teams, many=True, context={'request': request}).data,
    }
    return Response(data)


# =============================================================================
# Teams
# =============================================================================

@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def team_list_create_view(request):
    """List user's teams or create a new team."""
    if request.method == 'GET':
        teams = get_objects_for_user(request.user, 'teams.view_team', klass=Team)
        serializer = TeamListSerializer(teams, many=True, context={'request': request})
        return Response(serializer.data)

    # POST — create
    serializer = TeamCreateUpdateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    team = serializer.save(created_by=request.user)
    return Response(
        TeamDetailSerializer(team, context={'request': request}).data,
        status=status.HTTP_201_CREATED
    )


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def team_detail_view(request, pk):
    """Retrieve, update, or delete a team."""
    team = get_object_or_404(Team, pk=pk)

    if request.method == 'GET':
        if not request.user.has_perm('teams.view_team', team):
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = TeamDetailSerializer(team, context={'request': request})
        return Response(serializer.data)

    if request.method == 'PUT':
        if not request.user.has_perm('teams.change_team', team):
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = TeamCreateUpdateSerializer(team, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(TeamDetailSerializer(team, context={'request': request}).data)

    # DELETE
    if not request.user.has_perm('teams.delete_team', team):
        return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
    team.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def team_add_member_view(request, pk):
    """Add a member to a team."""
    team = get_object_or_404(Team, pk=pk)

    if not request.user.has_perm('teams.manage_members', team):
        return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

    serializer = AddMemberSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = serializer.validated_data['username']  # Returns User object
    role = serializer.validated_data['role']

    # Check if already a member
    if TeamMembership.objects.filter(team=team, user=user).exists():
        return Response(
            {'detail': f"User '{user.username}' is already a member of this team."},
            status=status.HTTP_400_BAD_REQUEST
        )

    membership = TeamMembership(team=team, user=user, role=role)
    membership._adder = request.user
    membership.save()

    return Response(
        TeamMembershipSerializer(membership).data,
        status=status.HTTP_201_CREATED
    )


@api_view(['PATCH', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def team_member_view(request, pk, user_id):
    """Change role or remove a team member."""
    team = get_object_or_404(Team, pk=pk)

    if not request.user.has_perm('teams.manage_members', team):
        return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

    membership = get_object_or_404(TeamMembership, team=team, user_id=user_id)

    if request.method == 'DELETE':
        # Prevent removing the last owner
        if membership.role == TeamMembership.OWNER:
            owner_count = TeamMembership.objects.filter(team=team, role=TeamMembership.OWNER).count()
            if owner_count <= 1:
                return Response(
                    {'detail': 'Cannot remove the last owner.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        user = membership.user
        remove_perm('teams.view_team', user, team)
        remove_perm('teams.change_team', user, team)
        remove_perm('teams.delete_team', user, team)
        remove_perm('teams.manage_members', user, team)
        membership.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # PATCH — change role
    serializer = ChangeRoleSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    new_role = serializer.validated_data['role']
    old_role = membership.role

    if old_role == TeamMembership.OWNER and new_role == TeamMembership.MEMBER:
        owner_count = TeamMembership.objects.filter(team=team, role=TeamMembership.OWNER).count()
        if owner_count <= 1:
            return Response(
                {'detail': 'Cannot change the role of the last owner.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    membership.role = new_role
    membership.save()

    if new_role == TeamMembership.OWNER:
        assign_perm('teams.change_team', membership.user, team)
        assign_perm('teams.delete_team', membership.user, team)
        assign_perm('teams.manage_members', membership.user, team)
    else:
        remove_perm('teams.change_team', membership.user, team)
        remove_perm('teams.delete_team', membership.user, team)
        remove_perm('teams.manage_members', membership.user, team)

    return Response(TeamMembershipSerializer(membership).data)


# =============================================================================
# Tasks
# =============================================================================

class TaskPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def task_list_create_view(request):
    """List tasks with filters or create a new task."""
    if request.method == 'GET':
        user_teams = Team.objects.filter(memberships__user=request.user)
        tasks_qs = Task.objects.filter(
            team__in=user_teams
        ).select_related('team', 'created_by', 'assigned_to').order_by('-created_at')

        # Filters
        team_id = request.query_params.get('team')
        status_filter = request.query_params.get('status')
        if team_id:
            tasks_qs = tasks_qs.filter(team_id=team_id)
        if status_filter:
            tasks_qs = tasks_qs.filter(status=status_filter)

        paginator = TaskPagination()
        page = paginator.paginate_queryset(tasks_qs, request)
        serializer = TaskListSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)

    # POST — create
    serializer = TaskCreateUpdateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    # Verify user is a member of the team
    team = serializer.validated_data['team']
    if not TeamMembership.objects.filter(team=team, user=request.user).exists():
        return Response(
            {'detail': 'You must be a member of the team to create tasks.'},
            status=status.HTTP_403_FORBIDDEN
        )

    task = serializer.save(created_by=request.user)
    return Response(
        TaskDetailSerializer(task, context={'request': request}).data,
        status=status.HTTP_201_CREATED
    )


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def task_detail_view(request, pk):
    """Retrieve, update, or delete a task."""
    task = get_object_or_404(
        Task.objects.select_related('team', 'created_by', 'assigned_to'),
        pk=pk
    )

    # Must be team member
    if not TeamMembership.objects.filter(team=task.team, user=request.user).exists():
        return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        serializer = TaskDetailSerializer(task, context={'request': request})
        return Response(serializer.data)

    # Check edit/delete permissions
    is_owner = TeamMembership.objects.filter(
        team=task.team, user=request.user, role=TeamMembership.OWNER
    ).exists()
    can_modify = is_owner or task.created_by == request.user

    if not can_modify:
        return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'PUT':
        serializer = TaskCreateUpdateSerializer(task, data=request.data)
        serializer.is_valid(raise_exception=True)
        task = serializer.save()
        task._updating_user = request.user
        task.save()
        return Response(TaskDetailSerializer(task, context={'request': request}).data)

    # DELETE
    task.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def team_members_view(request, team_id):
    """Get members of a team (for assignee dropdown)."""
    team = get_object_or_404(Team, pk=team_id)
    if not TeamMembership.objects.filter(team=team, user=request.user).exists():
        return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

    members = TeamMembership.objects.filter(team=team).select_related('user')
    data = [
        {
            'id': m.user.id,
            'username': m.user.username,
            'full_name': m.user.get_full_name() or m.user.username,
            'role': m.role,
        }
        for m in members
    ]
    return Response({'members': data})


# =============================================================================
# Comments
# =============================================================================

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def comment_create_view(request, task_pk):
    """Create a comment on a task."""
    task = get_object_or_404(Task, pk=task_pk)

    if not TeamMembership.objects.filter(team=task.team, user=request.user).exists():
        return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

    serializer = CommentCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    comment = Comment.objects.create(
        task=task,
        author=request.user,
        content=serializer.validated_data['content']
    )
    return Response(
        CommentSerializer(comment, context={'request': request}).data,
        status=status.HTTP_201_CREATED
    )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def comment_reply_view(request, comment_pk):
    """Reply to a comment."""
    parent = get_object_or_404(Comment, pk=comment_pk)
    task = parent.task

    if not TeamMembership.objects.filter(team=task.team, user=request.user).exists():
        return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

    serializer = CommentCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    reply = Comment.objects.create(
        task=task,
        author=request.user,
        content=serializer.validated_data['content'],
        parent=parent
    )
    return Response(
        CommentSerializer(reply, context={'request': request}).data,
        status=status.HTTP_201_CREATED
    )


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def comment_delete_view(request, comment_pk):
    """Delete a comment."""
    comment = get_object_or_404(Comment, pk=comment_pk)
    task = comment.task

    can_delete = (
        comment.author == request.user or
        TeamMembership.objects.filter(
            team=task.team, user=request.user, role=TeamMembership.OWNER
        ).exists()
    )

    if not can_delete:
        return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

    comment.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# =============================================================================
# Files
# =============================================================================

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def file_upload_task_view(request, task_pk):
    """Upload a file to a task."""
    task = get_object_or_404(Task, pk=task_pk)

    if not TeamMembership.objects.filter(team=task.team, user=request.user).exists():
        return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

    file = request.FILES.get('file')
    if not file:
        return Response({'detail': 'No file provided.'}, status=status.HTTP_400_BAD_REQUEST)

    # Check file size (10MB max)
    if file.size > 10 * 1024 * 1024:
        return Response(
            {'detail': f'File size must not exceed 10MB. Current: {file.size / (1024*1024):.2f}MB'},
            status=status.HTTP_400_BAD_REQUEST
        )

    file_upload = FileUpload(
        file=file,
        uploaded_by=request.user,
        content_object=task
    )
    file_upload.save()
    return Response(
        FileUploadSerializer(file_upload, context={'request': request}).data,
        status=status.HTTP_201_CREATED
    )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def file_download_view(request, file_pk):
    """Download a file."""
    file_upload = get_object_or_404(FileUpload, pk=file_pk)
    content_object = file_upload.content_object

    if isinstance(content_object, Task):
        task = content_object
    elif isinstance(content_object, Comment):
        task = content_object.task
    else:
        raise Http404("Invalid file association")

    if not TeamMembership.objects.filter(team=task.team, user=request.user).exists():
        return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

    try:
        response = FileResponse(file_upload.file.open('rb'))
        response['Content-Disposition'] = f'attachment; filename="{file_upload.filename}"'
        return response
    except FileNotFoundError:
        raise Http404("File not found")


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def file_delete_view(request, file_pk):
    """Delete a file."""
    file_upload = get_object_or_404(FileUpload, pk=file_pk)
    content_object = file_upload.content_object

    if isinstance(content_object, Task):
        task = content_object
    elif isinstance(content_object, Comment):
        task = content_object.task
    else:
        return Response({'detail': 'Invalid file.'}, status=status.HTTP_400_BAD_REQUEST)

    can_delete = (
        file_upload.uploaded_by == request.user or
        TeamMembership.objects.filter(
            team=task.team, user=request.user, role=TeamMembership.OWNER
        ).exists()
    )

    if not can_delete:
        return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

    file_upload.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# =============================================================================
# Notifications
# =============================================================================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def notification_list_view(request):
    """List notifications for the current user."""
    notifications = Notification.objects.filter(
        recipient=request.user
    ).select_related('sender', 'content_type')[:50]

    serializer = NotificationSerializer(notifications, many=True, context={'request': request})
    return Response({
        'notifications': serializer.data,
        'unread_count': NotificationService.get_unread_count(request.user),
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def notification_mark_read_view(request, notification_id):
    """Mark a notification as read."""
    notification = NotificationService.mark_as_read(notification_id, request.user)
    if notification:
        return Response({'success': True})
    return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def notification_mark_all_read_view(request):
    """Mark all notifications as read."""
    count = NotificationService.mark_all_as_read(request.user)
    return Response({'success': True, 'count': count})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def notification_unread_count_view(request):
    """Get unread notification count."""
    count = NotificationService.get_unread_count(request.user)
    return Response({'count': count})


# =============================================================================
# User Teams (for task form dropdowns)
# =============================================================================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_teams_view(request):
    """Get teams the current user is a member of (for form dropdowns)."""
    teams = Team.objects.filter(memberships__user=request.user).distinct()
    serializer = TeamListSerializer(teams, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def task_status_choices_view(request):
    """Get available task status choices."""
    return Response([
        {'value': choice[0], 'label': choice[1]}
        for choice in Task.STATUS_CHOICES
    ])
