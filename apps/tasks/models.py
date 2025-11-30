from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apps.teams.models import Team


class Task(models.Model):
    """Represents a work item within a team."""
    TODO = 'TODO'
    IN_PROGRESS = 'IN_PROGRESS'
    REVIEW = 'REVIEW'
    DONE = 'DONE'
    
    STATUS_CHOICES = [
        (TODO, 'To Do'),
        (IN_PROGRESS, 'In Progress'),
        (REVIEW, 'Review'),
        (DONE, 'Done'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='tasks')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=TODO)
    deadline = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['team', 'status']),
            models.Index(fields=['assigned_to']),
        ]
    
    def __str__(self):
        return self.title


class Comment(models.Model):
    """Represents a threaded comment on a task."""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['task', 'parent']),
        ]
    
    def __str__(self):
        return f"Comment by {self.author.username} on {self.task.title}"
    
    def get_replies(self):
        """Get all direct replies to this comment."""
        return self.replies.all()


class FileUpload(models.Model):
    """Represents a file attachment to a Task or Comment using GenericForeignKey."""
    file = models.FileField(upload_to='uploads/%Y/%m/%d/')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_files')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # GenericForeignKey fields for polymorphic association
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.file.name} uploaded by {self.uploaded_by.username}"
    
    @property
    def filename(self):
        """Get the filename without the path."""
        import os
        return os.path.basename(self.file.name)


class ActivityLog(models.Model):
    """Represents an audit trail entry for task changes."""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='activity_logs')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=100)
    details = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['task', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.action} by {self.user.username} on {self.task.title}"


# Signal handlers for automatic activity logging

@receiver(post_save, sender=Task)
def log_task_creation_or_update(sender, instance, created, **kwargs):
    """Log task creation or update events."""
    if created:
        ActivityLog.objects.create(
            task=instance,
            user=instance.created_by,
            action='Task created',
            details={
                'title': instance.title,
                'status': instance.status,
                'assigned_to': instance.assigned_to.username if instance.assigned_to else None,
            }
        )
        
        # Assign permissions to team members when task is created
        from guardian.shortcuts import assign_perm
        from apps.teams.models import TeamMembership
        
        team = instance.team
        team_members = TeamMembership.objects.filter(team=team).select_related('user')
        for membership in team_members:
            assign_perm('tasks.view_task', membership.user, instance)
            # Owners and the creator get change/delete permissions
            if membership.role == TeamMembership.OWNER or membership.user == instance.created_by:
                assign_perm('tasks.change_task', membership.user, instance)
                assign_perm('tasks.delete_task', membership.user, instance)
        
        # Send assignment notification email if task is assigned
        if instance.assigned_to:
            from apps.notifications.services import NotificationService, EmailService
            notification = NotificationService.create_assignment_notification(instance)
            if notification:
                EmailService.send_notification_email(notification)
    else:
        # For updates, we need to track what changed
        # This is a simplified version - in production you might want to track specific field changes
        ActivityLog.objects.create(
            task=instance,
            user=instance.created_by,  # In a real app, you'd track the actual user making the change
            action='Task updated',
            details={
                'title': instance.title,
                'status': instance.status,
                'assigned_to': instance.assigned_to.username if instance.assigned_to else None,
            }
        )


@receiver(post_save, sender=Comment)
def log_comment_creation(sender, instance, created, **kwargs):
    """Log comment creation events."""
    if created:
        ActivityLog.objects.create(
            task=instance.task,
            user=instance.author,
            action='Comment added',
            details={
                'comment_id': instance.id,
                'author': instance.author.username,
                'is_reply': instance.parent is not None,
            }
        )
        
        # Create notifications for mentioned users and send emails
        from apps.notifications.services import NotificationService, EmailService
        notifications = NotificationService.create_mention_notifications(instance)
        
        # Send email for each mention notification
        for notification in notifications:
            EmailService.send_notification_email(notification)


@receiver(post_save, sender=FileUpload)
def log_file_upload(sender, instance, created, **kwargs):
    """Log file upload events."""
    if created:
        # Only log if the file is attached to a Task
        if isinstance(instance.content_object, Task):
            ActivityLog.objects.create(
                task=instance.content_object,
                user=instance.uploaded_by,
                action='File uploaded',
                details={
                    'filename': instance.filename,
                    'file_id': instance.id,
                }
            )


@receiver(post_delete, sender=FileUpload)
def delete_file_on_model_delete(sender, instance, **kwargs):
    """Delete the actual file from storage when FileUpload is deleted."""
    if instance.file:
        instance.file.delete(save=False)


@receiver(post_delete, sender=Task)
def delete_task_files(sender, instance, **kwargs):
    """Delete all files associated with a task when the task is deleted."""
    content_type = ContentType.objects.get_for_model(Task)
    file_uploads = FileUpload.objects.filter(content_type=content_type, object_id=instance.id)
    for file_upload in file_uploads:
        file_upload.delete()


@receiver(post_delete, sender=Comment)
def delete_comment_files(sender, instance, **kwargs):
    """Delete all files associated with a comment when the comment is deleted."""
    content_type = ContentType.objects.get_for_model(Comment)
    file_uploads = FileUpload.objects.filter(content_type=content_type, object_id=instance.id)
    for file_upload in file_uploads:
        file_upload.delete()
