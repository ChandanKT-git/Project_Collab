from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.teams.models import Team, TeamMembership
from apps.tasks.models import Task, FileUpload
from apps.notifications.models import Notification
from apps.notifications.services import NotificationService


class FileUploadNotificationTest(TestCase):
    """Test file upload notification functionality."""
    
    def setUp(self):
        """Set up test data."""
        # Create users
        self.creator = User.objects.create_user(username='creator', email='creator@test.com')
        self.assignee = User.objects.create_user(username='assignee', email='assignee@test.com')
        self.uploader = User.objects.create_user(username='uploader', email='uploader@test.com')
        
        # Create team (automatically creates owner membership for creator)
        self.team = Team.objects.create(name='Test Team', created_by=self.creator)
        # Add other members
        TeamMembership.objects.create(team=self.team, user=self.assignee, role=TeamMembership.MEMBER)
        TeamMembership.objects.create(team=self.team, user=self.uploader, role=TeamMembership.MEMBER)
        
        # Create task
        self.task = Task.objects.create(
            title='Test Task',
            description='Test Description',
            team=self.team,
            created_by=self.creator,
            assigned_to=self.assignee
        )
    
    def test_file_upload_creates_notifications(self):
        """Test that file upload creates notifications for task creator and assignee."""
        # Create a file upload
        test_file = SimpleUploadedFile("test.txt", b"file content")
        file_upload = FileUpload.objects.create(
            file=test_file,
            uploaded_by=self.uploader,
            content_object=self.task
        )
        
        # Check notifications were created
        notifications = Notification.objects.filter(notification_type=Notification.FILE_UPLOADED)
        self.assertEqual(notifications.count(), 2)
        
        # Check creator received notification
        creator_notification = notifications.filter(recipient=self.creator).first()
        self.assertIsNotNone(creator_notification)
        self.assertEqual(creator_notification.sender, self.uploader)
        # Check that the filename (without path) is in the message
        self.assertIn('.txt', creator_notification.message)
        self.assertIn(self.uploader.username, creator_notification.message)
        self.assertIn(self.task.title, creator_notification.message)
        
        # Check assignee received notification
        assignee_notification = notifications.filter(recipient=self.assignee).first()
        self.assertIsNotNone(assignee_notification)
        self.assertEqual(assignee_notification.sender, self.uploader)
    
    def test_file_upload_excludes_uploader(self):
        """Test that uploader doesn't receive notification."""
        # Create a file upload by the creator
        test_file = SimpleUploadedFile("test.txt", b"file content")
        file_upload = FileUpload.objects.create(
            file=test_file,
            uploaded_by=self.creator,
            content_object=self.task
        )
        
        # Check only assignee received notification (not creator who uploaded)
        notifications = Notification.objects.filter(notification_type=Notification.FILE_UPLOADED)
        self.assertEqual(notifications.count(), 1)
        self.assertEqual(notifications.first().recipient, self.assignee)
    
    def test_create_file_upload_notification_method(self):
        """Test the NotificationService.create_file_upload_notification method."""
        test_file = SimpleUploadedFile("test.txt", b"file content")
        file_upload = FileUpload.objects.create(
            file=test_file,
            uploaded_by=self.uploader,
            content_object=self.task
        )
        
        # Manually create notification using service
        notification = NotificationService.create_file_upload_notification(
            file_upload=file_upload,
            task=self.task,
            recipient=self.creator
        )
        
        self.assertIsNotNone(notification)
        self.assertEqual(notification.recipient, self.creator)
        self.assertEqual(notification.sender, self.uploader)
        self.assertEqual(notification.notification_type, Notification.FILE_UPLOADED)
        self.assertIn(file_upload.filename, notification.message)
        self.assertIn(self.task.title, notification.message)
