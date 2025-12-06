from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save, post_delete, pre_save
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

@receiver(pre_save, sender=Task)
def capture_old_task_state(sender, instance, **kwargs):
    """Capture the old state of the task before saving."""
    if instance.pk:
        try:
            old_instance = Task.objects.get(pk=instance.pk)
            instance._old_assigned_to = old_instance.assigned_to
        except Task.DoesNotExist:
            instance._old_assigned_to = None
    else:
        instance._old_assigned_to = None


@receiver(post_save, sender=Task)
def log_task_creation_or_update(sender, instance, created, **kwargs):
    """Log task creation or update events."""
    # Get the user who made the change (from view or default to creator)
    updating_user = getattr(instance, '_updating_user', instance.created_by)
    
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
        if instance.assigned_to and instance.assigned_to != instance.created_by:
            from apps.notifications.services import NotificationService, EmailService
            from apps.notifications.models import Notification
            # Create notification with proper sender
            message = f"{instance.created_by.username} assigned you to task '{instance.title}'"
            notification = NotificationService.create_notification(
                recipient=instance.assigned_to,
                sender=instance.created_by,
                notification_type=Notification.ASSIGNMENT,
                message=message,
                content_object=instance
            )
            if notification:
                EmailService.send_notification_email(notification)
    else:
        # For updates, we need to track what changed
        # Get old assigned_to from pre_save signal
        old_assigned_to = getattr(instance, '_old_assigned_to', None)
        
        # Log the update
        ActivityLog.objects.create(
            task=instance,
            user=updating_user,
            action='Task updated',
            details={
                'title': instance.title,
                'status': instance.status,
                'assigned_to': instance.assigned_to.username if instance.assigned_to else None,
            }
        )
        
        # Send assignment notification if assignee changed
        if instance.assigned_to and old_assigned_to != instance.assigned_to:
            # Don't notify if user assigned task to themselves
            if instance.assigned_to != updating_user:
                from apps.notifications.services import NotificationService, EmailService
                from apps.notifications.models import Notification
                message = f"{updating_user.username} assigned you to task '{instance.title}'"
                notification = NotificationService.create_notification(
                    recipient=instance.assigned_to,
                    sender=updating_user,
                    notification_type=Notification.ASSIGNMENT,
                    message=message,
                    content_object=instance
                )
                if notification:
                    EmailService.send_notification_email(notification)


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
        from django.db import transaction
        
        notifications = NotificationService.create_mention_notifications(instance)
        
        # Send email for each mention notification after transaction commits
        for notification in notifications:
            transaction.on_commit(
                lambda n=notification: EmailService.send_notification_email(n)
            )


@receiver(post_save, sender=FileUpload)
def log_file_upload(sender, instance, created, **kwargs):
    """Log file upload events and create notifications."""
    if created:
        # Only log if the file is attached to a Task
        if isinstance(instance.content_object, Task):
            task = instance.content_object
            
            ActivityLog.objects.create(
                task=task,
                user=instance.uploaded_by,
                action='File uploaded',
                details={
                    'filename': instance.filename,
                    'file_id': instance.id,
                }
            )
            
            # Identify recipients (task creator and assigned user)
            recipients = set()
            if task.created_by:
                recipients.add(task.created_by)
            if task.assigned_to:
                recipients.add(task.assigned_to)
            
            # Exclude the uploader from recipients
            recipients.discard(instance.uploaded_by)
            
            # Create notifications for each recipient
            from apps.notifications.services import NotificationService, EmailService
            from django.db import transaction
            
            for recipient in recipients:
                notification = NotificationService.create_file_upload_notification(
                    file_upload=instance,
                    task=task,
                    recipient=recipient
                )
                
                # Send email after transaction commits
                if notification:
                    transaction.on_commit(
                        lambda n=notification: EmailService.send_notification_email(n)
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
