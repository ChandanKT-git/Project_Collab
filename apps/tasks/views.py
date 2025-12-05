from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import FileResponse, Http404, JsonResponse
from django.contrib.contenttypes.models import ContentType
from guardian.shortcuts import get_objects_for_user, assign_perm, remove_perm
from .models import Task, Comment, FileUpload, ActivityLog
from .forms import TaskForm, CommentForm, FileUploadForm
from apps.teams.models import Team, TeamMembership
import os


@login_required
def task_list(request):
    """Display all tasks the user has permission to access with filtering."""
    # Get all teams where user is a member
    user_teams = Team.objects.filter(memberships__user=request.user)
    
    # Get all tasks from those teams
    tasks = Task.objects.filter(team__in=user_teams).select_related(
        'team', 'created_by', 'assigned_to'
    )
    
    # Apply filters
    team_filter = request.GET.get('team')
    status_filter = request.GET.get('status')
    
    if team_filter:
        tasks = tasks.filter(team_id=team_filter)
    
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    
    context = {
        'tasks': tasks,
        'user_teams': user_teams,
        'status_choices': Task.STATUS_CHOICES,
        'selected_team': team_filter,
        'selected_status': status_filter,
    }
    return render(request, 'tasks/task_list.html', context)


@login_required
def task_create(request):
    """Create a new task."""
    # Check if user is a member of any team
    user_teams = Team.objects.filter(memberships__user=request.user)
    
    if not user_teams.exists():
        messages.warning(request, 'You need to create or join a team before creating tasks.')
        return redirect('team_create')
    
    if request.method == 'POST':
        form = TaskForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                task = form.save(commit=False)
                task.created_by = request.user
                task.save()
                
                # Permissions are automatically assigned via signal handler
                
                messages.success(request, f'Task "{task.title}" created successfully!')
                return redirect('task_detail', pk=task.pk)
            except Exception as e:
                messages.error(request, 'An error occurred while creating the task. Please try again.')
                # Log the error
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Task creation error by user {request.user.username}: {str(e)}', exc_info=True)
        else:
            # Add user-friendly error messages
            if form.errors:
                messages.error(request, 'Please correct the errors in the form.')
    else:
        form = TaskForm(user=request.user)
    
    context = {
        'form': form
    }
    return render(request, 'tasks/task_form.html', context)


@login_required
def task_detail(request, pk):
    """Display task details with comments and activity log."""
    task = get_object_or_404(Task, pk=pk)
    
    # Check if user has permission to view this task
    # User must be a member of the team
    if not TeamMembership.objects.filter(team=task.team, user=request.user).exists():
        messages.error(request, 'You do not have permission to view this task.')
        return redirect('task_list')
    
    # Get comments and activity logs
    comments = task.comments.filter(parent__isnull=True).select_related('author').prefetch_related('replies__author')
    activity_logs = task.activity_logs.select_related('user').all()
    
    # Get file uploads for the task
    task_content_type = ContentType.objects.get_for_model(Task)
    task_files = FileUpload.objects.filter(
        content_type=task_content_type,
        object_id=task.pk
    ).select_related('uploaded_by')
    
    # Check permissions
    can_edit = (
        TeamMembership.objects.filter(team=task.team, user=request.user, role=TeamMembership.OWNER).exists()
        or task.created_by == request.user
    )
    can_delete = can_edit
    
    # Create forms
    comment_form = CommentForm()
    file_upload_form = FileUploadForm()
    
    context = {
        'task': task,
        'comments': comments,
        'activity_logs': activity_logs,
        'task_files': task_files,
        'can_edit': can_edit,
        'can_delete': can_delete,
        'comment_form': comment_form,
        'file_upload_form': file_upload_form,
    }
    return render(request, 'tasks/task_detail.html', context)


@login_required
def task_update(request, pk):
    """Update task details with permission checks."""
    task = get_object_or_404(Task, pk=pk)
    
    # Check if user has permission to change this task
    can_edit = (
        TeamMembership.objects.filter(team=task.team, user=request.user, role=TeamMembership.OWNER).exists()
        or task.created_by == request.user
    )
    
    if not can_edit:
        messages.error(request, 'You do not have permission to edit this task.')
        return redirect('task_detail', pk=task.pk)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, user=request.user)
        if form.is_valid():
            # Store the user who made the update for activity logging
            task = form.save(commit=False)
            # Store the updating user in a temporary attribute for the signal
            task._updating_user = request.user
            task.save()
            
            messages.success(request, f'Task "{task.title}" updated successfully!')
            return redirect('task_detail', pk=task.pk)
    else:
        form = TaskForm(instance=task, user=request.user)
    
    context = {
        'form': form,
        'task': task,
        'is_update': True
    }
    return render(request, 'tasks/task_form.html', context)


@login_required
def task_delete(request, pk):
    """Delete a task with cascade deletion logic."""
    task = get_object_or_404(Task, pk=pk)
    
    # Check if user has permission to delete this task
    can_delete = (
        TeamMembership.objects.filter(team=task.team, user=request.user, role=TeamMembership.OWNER).exists()
        or task.created_by == request.user
    )
    
    if not can_delete:
        messages.error(request, 'You do not have permission to delete this task.')
        return redirect('task_detail', pk=task.pk)
    
    if request.method == 'POST':
        task_title = task.title
        team_id = task.team.id
        
        # Django will handle cascade deletion of comments, file uploads, and activity logs
        # due to the CASCADE option in the foreign key relationships
        task.delete()
        
        messages.success(request, f'Task "{task_title}" deleted successfully!')
        return redirect('task_list')
    
    context = {
        'task': task
    }
    return render(request, 'tasks/task_confirm_delete.html', context)



@login_required
def comment_create(request, task_pk):
    """Create a new comment on a task."""
    task = get_object_or_404(Task, pk=task_pk)
    
    # Check if user has permission to comment (must be team member)
    if not TeamMembership.objects.filter(team=task.team, user=request.user).exists():
        messages.error(request, 'You do not have permission to comment on this task.')
        return redirect('task_detail', pk=task.pk)
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.task = task
            comment.author = request.user
            comment.save()
            
            messages.success(request, 'Comment added successfully!')
            return redirect('task_detail', pk=task.pk)
    
    # If GET or form invalid, redirect back to task detail
    return redirect('task_detail', pk=task.pk)


@login_required
def comment_reply(request, comment_pk):
    """Create a reply to an existing comment."""
    parent_comment = get_object_or_404(Comment, pk=comment_pk)
    task = parent_comment.task
    
    # Check if user has permission to comment (must be team member)
    if not TeamMembership.objects.filter(team=task.team, user=request.user).exists():
        messages.error(request, 'You do not have permission to reply to this comment.')
        return redirect('task_detail', pk=task.pk)
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.task = task
            reply.author = request.user
            reply.parent = parent_comment
            reply.save()
            
            messages.success(request, 'Reply added successfully!')
            return redirect('task_detail', pk=task.pk)
    
    # If GET or form invalid, redirect back to task detail
    return redirect('task_detail', pk=task.pk)


@login_required
def comment_delete(request, comment_pk):
    """Delete a comment with cascade to children."""
    comment = get_object_or_404(Comment, pk=comment_pk)
    task = comment.task
    
    # Check if user has permission to delete (must be author or team owner)
    can_delete = (
        comment.author == request.user or
        TeamMembership.objects.filter(team=task.team, user=request.user, role=TeamMembership.OWNER).exists()
    )
    
    if not can_delete:
        messages.error(request, 'You do not have permission to delete this comment.')
        return redirect('task_detail', pk=task.pk)
    
    if request.method == 'POST':
        # Django will handle cascade deletion of child comments
        # due to the CASCADE option in the parent foreign key
        comment.delete()
        
        messages.success(request, 'Comment deleted successfully!')
        return redirect('task_detail', pk=task.pk)
    
    # For GET requests, show confirmation page
    context = {
        'comment': comment,
        'task': task
    }
    return render(request, 'tasks/comment_confirm_delete.html', context)



@login_required
def file_upload_task(request, task_pk):
    """Upload a file to a task."""
    task = get_object_or_404(Task, pk=task_pk)
    
    # Check if user has permission to upload (must be team member)
    if not TeamMembership.objects.filter(team=task.team, user=request.user).exists():
        messages.error(request, 'You do not have permission to upload files to this task.')
        return redirect('task_detail', pk=task.pk)
    
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                file_upload = form.save(commit=False)
                file_upload.uploaded_by = request.user
                file_upload.content_object = task
                file_upload.save()
                
                messages.success(request, f'File "{file_upload.filename}" uploaded successfully!')
            except Exception as e:
                messages.error(request, 'An error occurred while uploading the file. Please try again.')
                # Log the error
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'File upload error by user {request.user.username} for task {task.pk}: {str(e)}', exc_info=True)
        else:
            # Display form errors with user-friendly messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'File upload error: {error}')
    
    return redirect('task_detail', pk=task.pk)


@login_required
def file_upload_comment(request, comment_pk):
    """Upload a file to a comment."""
    comment = get_object_or_404(Comment, pk=comment_pk)
    task = comment.task
    
    # Check if user has permission to upload (must be team member)
    if not TeamMembership.objects.filter(team=task.team, user=request.user).exists():
        messages.error(request, 'You do not have permission to upload files to this comment.')
        return redirect('task_detail', pk=task.pk)
    
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                file_upload = form.save(commit=False)
                file_upload.uploaded_by = request.user
                file_upload.content_object = comment
                file_upload.save()
                
                messages.success(request, f'File "{file_upload.filename}" uploaded successfully!')
            except Exception as e:
                messages.error(request, 'An error occurred while uploading the file. Please try again.')
                # Log the error
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'File upload error by user {request.user.username} for comment {comment.pk}: {str(e)}', exc_info=True)
        else:
            # Display form errors with user-friendly messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'File upload error: {error}')
    
    return redirect('task_detail', pk=task.pk)


@login_required
def file_download(request, file_pk):
    """Download a file with permission checks."""
    file_upload = get_object_or_404(FileUpload, pk=file_pk)
    
    # Determine the parent object (Task or Comment)
    content_object = file_upload.content_object
    
    # Get the task (either directly or through comment)
    if isinstance(content_object, Task):
        task = content_object
    elif isinstance(content_object, Comment):
        task = content_object.task
    else:
        raise Http404("Invalid file association")
    
    # Check if user has permission to access (must be team member)
    if not TeamMembership.objects.filter(team=task.team, user=request.user).exists():
        messages.error(request, 'You do not have permission to download this file.')
        return redirect('task_list')
    
    # Serve the file
    try:
        response = FileResponse(file_upload.file.open('rb'))
        response['Content-Disposition'] = f'attachment; filename="{file_upload.filename}"'
        return response
    except FileNotFoundError:
        raise Http404("File not found")


@login_required
def file_delete(request, file_pk):
    """Delete a file with permission checks."""
    file_upload = get_object_or_404(FileUpload, pk=file_pk)
    
    # Determine the parent object (Task or Comment)
    content_object = file_upload.content_object
    
    # Get the task (either directly or through comment)
    if isinstance(content_object, Task):
        task = content_object
    elif isinstance(content_object, Comment):
        task = content_object.task
    else:
        messages.error(request, 'Invalid file association.')
        return redirect('task_list')
    
    # Check if user has permission to delete (must be uploader or team owner)
    can_delete = (
        file_upload.uploaded_by == request.user or
        TeamMembership.objects.filter(team=task.team, user=request.user, role=TeamMembership.OWNER).exists()
    )
    
    if not can_delete:
        messages.error(request, 'You do not have permission to delete this file.')
        return redirect('task_detail', pk=task.pk)
    
    if request.method == 'POST':
        filename = file_upload.filename
        # The signal handler will delete the actual file from storage
        file_upload.delete()
        
        messages.success(request, f'File "{filename}" deleted successfully!')
        return redirect('task_detail', pk=task.pk)
    
    # For GET requests, redirect to task detail
    return redirect('task_detail', pk=task.pk)


@login_required
def get_team_members(request, team_id):
    """API endpoint to get team members for a specific team."""
    try:
        team = get_object_or_404(Team, pk=team_id)
        
        # Check if user is a member of this team
        if not TeamMembership.objects.filter(team=team, user=request.user).exists():
            return JsonResponse({'error': 'You do not have permission to view this team'}, status=403)
        
        # Get all team members
        members = TeamMembership.objects.filter(team=team).select_related('user')
        
        # Format response
        members_data = [
            {
                'id': membership.user.id,
                'username': membership.user.username,
                'full_name': membership.user.get_full_name() or membership.user.username,
                'role': membership.role
            }
            for membership in members
        ]
        
        return JsonResponse({'members': members_data})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
