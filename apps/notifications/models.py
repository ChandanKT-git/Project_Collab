from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Notification(models.Model):
    """Represents a notification for a user."""
    MENTION = 'mention'
    ASSIGNMENT = 'assignment'
    COMMENT = 'comment'
    
    TYPE_CHOICES = [
        (MENTION, 'Mention'),
        (ASSIGNMENT, 'Task Assignment'),
        (COMMENT, 'Comment'),
    ]
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # GenericForeignKey for linking to any object (Task, Comment, etc.)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.notification_type}"
