from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from apps.teams.models import Team
from apps.tasks.models import Task, Comment, FileUpload, ActivityLog
from datetime import date, timedelta


class TaskModelTest(TestCase):
    """Test the Task model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.team = Team.objects.create(name='Test Team', created_by=self.user)
    
    def test_task_creation(self):
        """Test creating a task."""
        task = Task.objects.create(
            title='Test Task',
            description='Test description',
            team=self.team,
            created_by=self.user,
            status=Task.TODO,
            deadline=date.today() + timedelta(days=7)
        )
        self.assertEqual(task.title, 'Test Task')
        self.assertEqual(task.status, Task.TODO)
        self.assertEqual(task.team, self.team)
        self.assertEqual(task.created_by, self.user)
        self.assertIsNotNone(task.created_at)
        self.assertIsNotNone(task.updated_at)
    
    def test_task_status_choices(self):
        """Test all status choices are valid."""
        statuses = [Task.TODO, Task.IN_PROGRESS, Task.REVIEW, Task.DONE]
        for status in statuses:
            task = Task.objects.create(
                title=f'Task {status}',
                description='Test',
                team=self.team,
                created_by=self.user,
                status=status
            )
            self.assertEqual(task.status, status)
    
    def test_task_assigned_to_optional(self):
        """Test that assigned_to is optional."""
        task = Task.objects.create(
            title='Unassigned Task',
            description='Test',
            team=self.team,
            created_by=self.user,
            status=Task.TODO
        )
        self.assertIsNone(task.assigned_to)
    
    def test_activity_log_created_on_task_creation(self):
        """Test that activity log is automatically created when task is created."""
        task = Task.objects.create(
            title='Test Task',
            description='Test',
            team=self.team,
            created_by=self.user,
            status=Task.TODO
        )
        logs = ActivityLog.objects.filter(task=task)
        self.assertEqual(logs.count(), 1)
        self.assertEqual(logs.first().action, 'Task created')


class CommentModelTest(TestCase):
    """Test the Comment model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.team = Team.objects.create(name='Test Team', created_by=self.user)
        self.task = Task.objects.create(
            title='Test Task',
            description='Test',
            team=self.team,
            created_by=self.user
        )
    
    def test_comment_creation(self):
        """Test creating a comment."""
        comment = Comment.objects.create(
            task=self.task,
            author=self.user,
            content='Test comment'
        )
        self.assertEqual(comment.content, 'Test comment')
        self.assertEqual(comment.task, self.task)
        self.assertEqual(comment.author, self.user)
        self.assertIsNone(comment.parent)
    
    def test_comment_reply(self):
        """Test creating a reply to a comment."""
        parent_comment = Comment.objects.create(
            task=self.task,
            author=self.user,
            content='Parent comment'
        )
        reply = Comment.objects.create(
            task=self.task,
            author=self.user,
            content='Reply comment',
            parent=parent_comment
        )
        self.assertEqual(reply.parent, parent_comment)
        self.assertIn(reply, parent_comment.get_replies())
    
    def test_activity_log_created_on_comment_creation(self):
        """Test that activity log is created when comment is added."""
        # Clear existing logs from task creation
        ActivityLog.objects.filter(task=self.task).delete()
        
        comment = Comment.objects.create(
            task=self.task,
            author=self.user,
            content='Test comment'
        )
        logs = ActivityLog.objects.filter(task=self.task, action='Comment added')
        self.assertEqual(logs.count(), 1)


class FileUploadModelTest(TestCase):
    """Test the FileUpload model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.team = Team.objects.create(name='Test Team', created_by=self.user)
        self.task = Task.objects.create(
            title='Test Task',
            description='Test',
            team=self.team,
            created_by=self.user
        )
    
    def test_file_upload_to_task(self):
        """Test uploading a file to a task."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        test_file = SimpleUploadedFile("test.txt", b"file content", content_type="text/plain")
        content_type = ContentType.objects.get_for_model(Task)
        
        file_upload = FileUpload.objects.create(
            file=test_file,
            uploaded_by=self.user,
            content_type=content_type,
            object_id=self.task.id
        )
        
        self.assertEqual(file_upload.content_object, self.task)
        self.assertEqual(file_upload.uploaded_by, self.user)
        self.assertIsNotNone(file_upload.file)
    
    def test_file_upload_to_comment(self):
        """Test uploading a file to a comment."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        comment = Comment.objects.create(
            task=self.task,
            author=self.user,
            content='Test comment'
        )
        
        test_file = SimpleUploadedFile("test.txt", b"file content", content_type="text/plain")
        content_type = ContentType.objects.get_for_model(Comment)
        
        file_upload = FileUpload.objects.create(
            file=test_file,
            uploaded_by=self.user,
            content_type=content_type,
            object_id=comment.id
        )
        
        self.assertEqual(file_upload.content_object, comment)


class ActivityLogModelTest(TestCase):
    """Test the ActivityLog model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.team = Team.objects.create(name='Test Team', created_by=self.user)
        self.task = Task.objects.create(
            title='Test Task',
            description='Test',
            team=self.team,
            created_by=self.user
        )
    
    def test_activity_log_ordering(self):
        """Test that activity logs are ordered chronologically."""
        # Clear existing logs
        ActivityLog.objects.filter(task=self.task).delete()
        
        # Create multiple logs
        log1 = ActivityLog.objects.create(
            task=self.task,
            user=self.user,
            action='Action 1',
            details={'test': 'data1'}
        )
        log2 = ActivityLog.objects.create(
            task=self.task,
            user=self.user,
            action='Action 2',
            details={'test': 'data2'}
        )
        
        logs = list(ActivityLog.objects.filter(task=self.task))
        self.assertEqual(logs[0], log1)
        self.assertEqual(logs[1], log2)
    
    def test_activity_log_details_json(self):
        """Test that details field stores JSON data."""
        log = ActivityLog.objects.create(
            task=self.task,
            user=self.user,
            action='Test action',
            details={'key': 'value', 'number': 42}
        )
        self.assertEqual(log.details['key'], 'value')
        self.assertEqual(log.details['number'], 42)


class CascadeDeletionTest(TestCase):
    """Test cascade deletion behavior."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.team = Team.objects.create(name='Test Team', created_by=self.user)
        self.task = Task.objects.create(
            title='Test Task',
            description='Test',
            team=self.team,
            created_by=self.user
        )
    
    def test_task_deletion_cascades_to_comments(self):
        """Test that deleting a task deletes all associated comments."""
        comment1 = Comment.objects.create(
            task=self.task,
            author=self.user,
            content='Comment 1'
        )
        comment2 = Comment.objects.create(
            task=self.task,
            author=self.user,
            content='Comment 2'
        )
        
        task_id = self.task.id
        self.task.delete()
        
        # Verify comments are deleted
        self.assertEqual(Comment.objects.filter(task_id=task_id).count(), 0)
    
    def test_task_deletion_cascades_to_activity_logs(self):
        """Test that deleting a task deletes all associated activity logs."""
        task_id = self.task.id
        initial_log_count = ActivityLog.objects.filter(task=self.task).count()
        self.assertGreater(initial_log_count, 0)  # Should have at least creation log
        
        self.task.delete()
        
        # Verify activity logs are deleted
        self.assertEqual(ActivityLog.objects.filter(task_id=task_id).count(), 0)
    
    def test_comment_deletion_cascades_to_replies(self):
        """Test that deleting a comment deletes all replies."""
        parent_comment = Comment.objects.create(
            task=self.task,
            author=self.user,
            content='Parent comment'
        )
        reply1 = Comment.objects.create(
            task=self.task,
            author=self.user,
            content='Reply 1',
            parent=parent_comment
        )
        reply2 = Comment.objects.create(
            task=self.task,
            author=self.user,
            content='Reply 2',
            parent=parent_comment
        )
        
        parent_id = parent_comment.id
        parent_comment.delete()
        
        # Verify replies are deleted
        self.assertEqual(Comment.objects.filter(parent_id=parent_id).count(), 0)
