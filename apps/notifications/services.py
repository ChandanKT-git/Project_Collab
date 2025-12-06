"""Services for notification management."""
import re
import logging
from datetime import timedelta
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string
from django.db import transaction
from .models import Notification

logger = logging.getLogger(__name__)


class MentionParser:
    """Utility to extract @username mentions from text."""
    
    MENTION_PATTERN = r'@(\w+)'
    
    @classmethod
    def extract_mentions(cls, text):
        """
        Extract all @username mentions from text.
        
        Args:
            text: String containing potential mentions
            
        Returns:
            List of usernames (without @ symbol)
        """
        if not text:
            return []
        
        matches = re.findall(cls.MENTION_PATTERN, text)
        # Remove duplicates while preserving order
        seen = set()
        unique_mentions = []
        for match in matches:
            if match not in seen:
                seen.add(match)
                unique_mentions.append(match)
        
        return unique_mentions
    
    @classmethod
    def get_mentioned_users(cls, text, team=None):
        """
        Get User objects for all valid mentions in text.
        
        Args:
            text: String containing potential mentions
            team: Optional Team object to filter mentions to team members only
            
        Returns:
            QuerySet of User objects
        """
        usernames = cls.extract_mentions(text)
        if not usernames:
            return User.objects.none()
        
        users = User.objects.filter(username__in=usernames)
        
        # If team is provided, filter to only team members
        if team:
            from apps.teams.models import TeamMembership
            team_member_ids = TeamMembership.objects.filter(
                team=team
            ).values_list('user_id', flat=True)
            users = users.filter(id__in=team_member_ids)
        
        return users
    
    @classmethod
    def highlight_mentions(cls, text):
        """
        Replace @username mentions with HTML highlighted version.
        
        Args:
            text: String containing potential mentions
            
        Returns:
            String with mentions wrapped in HTML
        """
        if not text:
            return text
        
        def replace_mention(match):
            username = match.group(1)
            return f'<span class="mention">@{username}</span>'
        
        return re.sub(cls.MENTION_PATTERN, replace_mention, text)


class NotificationService:
    """Service for creating and managing notifications."""
    
    @classmethod
    def create_notification(cls, recipient, sender, notification_type, message, content_object):
        """
        Create a notification for a user.
        
        Args:
            recipient: User who will receive the notification
            sender: User who triggered the notification
            notification_type: Type of notification (mention, assignment, etc.)
            message: Notification message text
            content_object: The object this notification is about (Task, Comment, etc.)
            
        Returns:
            Created Notification object
        """
        content_type = ContentType.objects.get_for_model(content_object)
        
        notification = Notification.objects.create(
            recipient=recipient,
            sender=sender,
            notification_type=notification_type,
            message=message,
            content_type=content_type,
            object_id=content_object.id
        )
        
        return notification
    
    @classmethod
    def create_mention_notifications(cls, comment):
        """
        Create notifications for all users mentioned in a comment.
        
        Args:
            comment: Comment object containing mentions
            
        Returns:
            List of created Notification objects
        """
        # Get mentioned users who are team members
        mentioned_users = MentionParser.get_mentioned_users(
            comment.content,
            team=comment.task.team
        )
        
        notifications = []
        for user in mentioned_users:
            # Don't notify the author of their own mentions
            if user != comment.author:
                message = f"{comment.author.username} mentioned you in a comment on '{comment.task.title}'"
                notification = cls.create_notification(
                    recipient=user,
                    sender=comment.author,
                    notification_type=Notification.MENTION,
                    message=message,
                    content_object=comment
                )
                notifications.append(notification)
        
        return notifications
    
    @classmethod
    def create_assignment_notification(cls, task):
        """
        Create notification when a task is assigned to a user.
        
        Args:
            task: Task object that was assigned
            
        Returns:
            Created Notification object or None
        """
        if not task.assigned_to:
            return None
        
        # Don't notify if the user assigned the task to themselves
        if task.assigned_to == task.created_by:
            return None
        
        message = f"{task.created_by.username} assigned you to task '{task.title}'"
        return cls.create_notification(
            recipient=task.assigned_to,
            sender=task.created_by,
            notification_type=Notification.ASSIGNMENT,
            message=message,
            content_object=task
        )
    
    @classmethod
    def create_team_addition_notification(cls, team, new_member, adder):
        """
        Create notification when a user is added to a team.
        
        Args:
            team: Team object the user was added to
            new_member: User who was added to the team
            adder: User who added the new member
            
        Returns:
            Created Notification object
        """
        message = f"{adder.username} added you to team '{team.name}'"
        return cls.create_notification(
            recipient=new_member,
            sender=adder,
            notification_type=Notification.TEAM_ADDED,
            message=message,
            content_object=team
        )
    
    @classmethod
    def create_file_upload_notification(cls, file_upload, task, recipient):
        """
        Create notification when a file is uploaded to a task.
        
        Args:
            file_upload: FileUpload object that was created
            task: Task object the file was uploaded to
            recipient: User who should receive the notification
            
        Returns:
            Created Notification object
        """
        message = f"{file_upload.uploaded_by.username} uploaded '{file_upload.filename}' to task '{task.title}'"
        return cls.create_notification(
            recipient=recipient,
            sender=file_upload.uploaded_by,
            notification_type=Notification.FILE_UPLOADED,
            message=message,
            content_object=file_upload
        )
    
    @classmethod
    def mark_as_read(cls, notification_id, user):
        """
        Mark a notification as read.
        
        Args:
            notification_id: ID of the notification
            user: User who owns the notification
            
        Returns:
            Updated Notification object or None
        """
        try:
            notification = Notification.objects.get(id=notification_id, recipient=user)
            notification.is_read = True
            notification.save()
            return notification
        except Notification.DoesNotExist:
            return None
    
    @classmethod
    def mark_all_as_read(cls, user):
        """
        Mark all notifications as read for a user.
        
        Args:
            user: User whose notifications to mark as read
            
        Returns:
            Number of notifications updated
        """
        return Notification.objects.filter(
            recipient=user,
            is_read=False
        ).update(is_read=True)
    
    @classmethod
    def get_unread_count(cls, user):
        """
        Get count of unread notifications for a user.
        
        Args:
            user: User to get count for
            
        Returns:
            Integer count of unread notifications
        """
        return Notification.objects.filter(
            recipient=user,
            is_read=False
        ).count()



class EmailService:
    """Service for sending email notifications."""
    
    @classmethod
    def send_notification_email(cls, notification):
        """
        Send an email for a single notification.
        
        Uses transaction.on_commit() to ensure emails are only sent after
        successful database commits. Includes comprehensive error handling
        and logging.
        
        Args:
            notification: Notification object to send email for
            
        Returns:
            Boolean indicating success
        """
        def _send_email():
            """Inner function to send email after transaction commit."""
            try:
                subject = cls._get_email_subject(notification)
                message = cls._get_email_message(notification)
                html_message = cls._get_email_html(notification)
                
                # Use fail_silently=False to catch exceptions properly
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[notification.recipient.email],
                    html_message=html_message,
                    fail_silently=False,
                )
                
                logger.info(
                    f"Email sent successfully to {notification.recipient.email} "
                    f"for notification {notification.id} (type: {notification.notification_type})"
                )
                return True
                
            except Exception as e:
                logger.error(
                    f"Failed to send email for notification {notification.id} "
                    f"to {notification.recipient.email}: {type(e).__name__}: {str(e)}",
                    exc_info=True
                )
                # Don't re-raise the exception - just log it and continue
                return False
        
        # Check if we're in a transaction
        try:
            if transaction.get_connection().in_atomic_block:
                # Schedule email to be sent after transaction commits
                transaction.on_commit(_send_email)
                return True
            else:
                # No active transaction, send immediately
                return _send_email()
        except Exception as e:
            # Fallback: if we can't determine transaction state, send immediately
            logger.warning(
                f"Could not determine transaction state for notification {notification.id}, "
                f"sending email immediately: {str(e)}"
            )
            return _send_email()
    
    @classmethod
    def send_batched_notifications(cls, user, notifications):
        """
        Send a batched email for multiple notifications.
        
        Uses transaction.on_commit() to ensure emails are only sent after
        successful database commits. Includes comprehensive error handling
        and logging.
        
        Args:
            user: User to send email to
            notifications: List of Notification objects
            
        Returns:
            Boolean indicating success
        """
        if not notifications:
            return False
        
        def _send_email():
            """Inner function to send email after transaction commit."""
            try:
                subject = f"You have {len(notifications)} new notifications"
                
                # Build message content
                message_parts = []
                for notification in notifications:
                    message_parts.append(f"- {notification.message}")
                
                message = "\n".join(message_parts)
                
                # Build HTML message
                html_message = render_to_string('notifications/email_batch.html', {
                    'user': user,
                    'notifications': notifications,
                    'count': len(notifications),
                })
                
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    html_message=html_message,
                    fail_silently=False,
                )
                
                logger.info(
                    f"Batched email sent successfully to {user.email} "
                    f"with {len(notifications)} notifications"
                )
                return True
                
            except Exception as e:
                logger.error(
                    f"Failed to send batched email to {user.email}: "
                    f"{type(e).__name__}: {str(e)}",
                    exc_info=True
                )
                return False
        
        # Check if we're in a transaction
        try:
            if transaction.get_connection().in_atomic_block:
                # Schedule email to be sent after transaction commits
                transaction.on_commit(_send_email)
                return True
            else:
                # No active transaction, send immediately
                return _send_email()
        except Exception as e:
            # Fallback: if we can't determine transaction state, send immediately
            logger.warning(
                f"Could not determine transaction state for batched email to {user.email}, "
                f"sending immediately: {str(e)}"
            )
            return _send_email()
    
    @classmethod
    def get_pending_notifications(cls, user, time_window=None):
        """
        Get notifications that should be batched together.
        
        Args:
            user: User to get notifications for
            time_window: Time window in seconds (defaults to settings.NOTIFICATION_BATCH_WINDOW)
            
        Returns:
            QuerySet of Notification objects
        """
        if time_window is None:
            time_window = getattr(settings, 'NOTIFICATION_BATCH_WINDOW', 300)
        
        cutoff_time = timezone.now() - timedelta(seconds=time_window)
        
        return Notification.objects.filter(
            recipient=user,
            is_read=False,
            created_at__gte=cutoff_time
        ).order_by('created_at')
    
    @classmethod
    def _get_email_subject(cls, notification):
        """Generate email subject based on notification type."""
        if notification.notification_type == Notification.MENTION:
            return f"You were mentioned by {notification.sender.username}"
        elif notification.notification_type == Notification.ASSIGNMENT:
            return f"You were assigned a task by {notification.sender.username}"
        elif notification.notification_type == Notification.TEAM_ADDED:
            return f"You were added to a team by {notification.sender.username}"
        else:
            return "New notification"
    
    @classmethod
    def _get_email_message(cls, notification):
        """Generate plain text email message."""
        return notification.message
    
    @classmethod
    def _get_email_html(cls, notification):
        """Generate HTML email message."""
        try:
            template_name = f'notifications/email_{notification.notification_type}.html'
            return render_to_string(template_name, {
                'notification': notification,
                'recipient': notification.recipient,
                'sender': notification.sender,
            })
        except Exception:
            # Fallback to generic template
            return render_to_string('notifications/email_generic.html', {
                'notification': notification,
            })
