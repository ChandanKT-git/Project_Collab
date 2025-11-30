"""Property-based tests for task functionality using Hypothesis."""
import pytest
from hypothesis import given, settings, strategies as st
from hypothesis.extra.django import from_model, TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta
from apps.teams.models import Team, TeamMembership
from apps.tasks.models import Task, Comment, FileUpload, ActivityLog


# Custom strategies for generating test data
@st.composite
def user_strategy(draw):
    """Generate a valid user."""
    username = draw(st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    # Ensure username is unique by adding timestamp
    username = f"user_{username}_{draw(st.integers(min_value=1, max_value=999999))}"
    user = User.objects.create_user(
        username=username,
        password='testpass123',
        email=f"{username}@example.com"
    )
    return user


@st.composite
def team_strategy(draw, user=None):
    """Generate a valid team."""
    if user is None:
        user = draw(user_strategy())
    
    name = draw(st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'))))
    description = draw(st.text(max_size=500))
    
    team = Team.objects.create(
        name=name.strip() or "Team",
        description=description,
        created_by=user
    )
    return team


@st.composite
def task_data_strategy(draw):
    """Generate valid task data."""
    title = draw(st.text(min_size=1, max_size=200, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'))))
    description = draw(st.text(min_size=1, max_size=1000))
    status = draw(st.sampled_from([Task.TODO, Task.IN_PROGRESS, Task.REVIEW, Task.DONE]))
    
    # Generate deadline (optional, can be None or a future date)
    has_deadline = draw(st.booleans())
    if has_deadline:
        days_ahead = draw(st.integers(min_value=1, max_value=365))
        deadline = date.today() + timedelta(days=days_ahead)
    else:
        deadline = None
    
    return {
        'title': title.strip() or "Task",
        'description': description.strip() or "Description",
        'status': status,
        'deadline': deadline
    }


class TestTaskProperties(TestCase):
    """Property-based tests for Task model and operations."""
    
    # Feature: project-collaboration-portal, Property 11: Task creation persists with team association
    @settings(max_examples=100, deadline=None)
    @given(task_data=task_data_strategy())
    def test_task_creation_persists_with_team_association(self, task_data):
        """
        Property 11: Task creation persists with team association
        For any Team Member creating a Task with valid data, the Task should be 
        persisted in the database and associated with the correct Team.
        Validates: Requirements 3.1
        """
        # Create a user and team
        user = User.objects.create_user(username=f'testuser_{timezone.now().timestamp()}', password='testpass123')
        team = Team.objects.create(name=f'Test Team {timezone.now().timestamp()}', created_by=user)
        
        # Create a task with the generated data
        task = Task.objects.create(
            title=task_data['title'],
            description=task_data['description'],
            team=team,
            created_by=user,
            status=task_data['status'],
            deadline=task_data['deadline']
        )
        
        # Verify the task is persisted
        assert Task.objects.filter(pk=task.pk).exists()
        
        # Verify the task is associated with the correct team
        retrieved_task = Task.objects.get(pk=task.pk)
        assert retrieved_task.team == team
        assert retrieved_task.team.id == team.id
        
        # Verify all fields are correctly stored
        assert retrieved_task.title == task_data['title']
        assert retrieved_task.description == task_data['description']
        assert retrieved_task.status == task_data['status']
        assert retrieved_task.deadline == task_data['deadline']
        assert retrieved_task.created_by == user
        
        # Verify timestamps are set
        assert retrieved_task.created_at is not None
        assert retrieved_task.updated_at is not None
    
    # Feature: project-collaboration-portal, Property 12: Task update modifies timestamp
    @settings(max_examples=100, deadline=None)
    @given(
        initial_data=task_data_strategy(),
        updated_title=st.text(min_size=1, max_size=200, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs')))
    )
    def test_task_update_modifies_timestamp(self, initial_data, updated_title):
        """
        Property 12: Task update modifies timestamp
        For any Task being updated by a Member with appropriate permissions, 
        the changes should be saved and the updated_at timestamp should be modified.
        Validates: Requirements 3.3
        """
        # Create a user and team
        user = User.objects.create_user(username=f'testuser_{timezone.now().timestamp()}', password='testpass123')
        team = Team.objects.create(name=f'Test Team {timezone.now().timestamp()}', created_by=user)
        
        # Create initial task
        task = Task.objects.create(
            title=initial_data['title'],
            description=initial_data['description'],
            team=team,
            created_by=user,
            status=initial_data['status'],
            deadline=initial_data['deadline']
        )
        
        # Store original timestamps
        original_created_at = task.created_at
        original_updated_at = task.updated_at
        
        # Small delay to ensure timestamp difference
        import time
        time.sleep(0.01)
        
        # Update the task
        task.title = updated_title.strip() or "Updated Task"
        task.save()
        
        # Refresh from database
        task.refresh_from_db()
        
        # Verify the update was saved
        assert task.title == (updated_title.strip() or "Updated Task")
        
        # Verify created_at remains unchanged
        assert task.created_at == original_created_at
        
        # Verify updated_at was modified
        assert task.updated_at > original_updated_at
    
    # Feature: project-collaboration-portal, Property 13: Task deletion cascades to related objects
    @settings(max_examples=100, deadline=None)
    @given(
        task_data=task_data_strategy(),
        num_comments=st.integers(min_value=1, max_value=5)
    )
    def test_task_deletion_cascades_to_related_objects(self, task_data, num_comments):
        """
        Property 13: Task deletion cascades to related objects
        For any Task being deleted by a Member with appropriate permissions, 
        the Task and all associated Comments and File Uploads should be removed 
        from the database and storage.
        Validates: Requirements 3.4
        """
        # Create a user and team
        user = User.objects.create_user(username=f'testuser_{timezone.now().timestamp()}', password='testpass123')
        team = Team.objects.create(name=f'Test Team {timezone.now().timestamp()}', created_by=user)
        
        # Create a task
        task = Task.objects.create(
            title=task_data['title'],
            description=task_data['description'],
            team=team,
            created_by=user,
            status=task_data['status'],
            deadline=task_data['deadline']
        )
        
        task_id = task.id
        
        # Create comments for the task
        comment_ids = []
        for i in range(num_comments):
            comment = Comment.objects.create(
                task=task,
                author=user,
                content=f"Test comment {i}"
            )
            comment_ids.append(comment.id)
        
        # Verify comments exist
        assert Comment.objects.filter(task_id=task_id).count() == num_comments
        
        # Verify activity logs exist (at least one from task creation)
        initial_log_count = ActivityLog.objects.filter(task_id=task_id).count()
        assert initial_log_count > 0
        
        # Delete the task
        task.delete()
        
        # Verify task is deleted
        assert not Task.objects.filter(pk=task_id).exists()
        
        # Verify all comments are deleted (cascade)
        assert Comment.objects.filter(id__in=comment_ids).count() == 0
        assert Comment.objects.filter(task_id=task_id).count() == 0
        
        # Verify all activity logs are deleted (cascade)
        assert ActivityLog.objects.filter(task_id=task_id).count() == 0
    
    # Feature: project-collaboration-portal, Property 14: Task list respects permissions
    @settings(max_examples=100, deadline=None)
    @given(
        num_teams=st.integers(min_value=2, max_value=5),
        tasks_per_team=st.integers(min_value=1, max_value=3)
    )
    def test_task_list_respects_permissions(self, num_teams, tasks_per_team):
        """
        Property 14: Task list respects permissions
        For any Team Member viewing the Task list, only Tasks the Member has 
        permission to access should be displayed.
        Validates: Requirements 3.5
        """
        # Create two users
        user1 = User.objects.create_user(username=f'user1_{timezone.now().timestamp()}', password='testpass123')
        user2 = User.objects.create_user(username=f'user2_{timezone.now().timestamp()}', password='testpass123')
        
        # Create teams - user1 is member of some, user2 is member of others
        user1_teams = []
        user2_teams = []
        
        for i in range(num_teams):
            if i % 2 == 0:
                # user1's team
                team = Team.objects.create(
                    name=f'Team {i} {timezone.now().timestamp()}',
                    created_by=user1
                )
                user1_teams.append(team)
            else:
                # user2's team
                team = Team.objects.create(
                    name=f'Team {i} {timezone.now().timestamp()}',
                    created_by=user2
                )
                user2_teams.append(team)
        
        # Create tasks for each team
        user1_task_ids = []
        user2_task_ids = []
        
        for team in user1_teams:
            for j in range(tasks_per_team):
                task = Task.objects.create(
                    title=f'Task {j} for {team.name}',
                    description='Test description',
                    team=team,
                    created_by=user1,
                    status=Task.TODO
                )
                user1_task_ids.append(task.id)
        
        for team in user2_teams:
            for j in range(tasks_per_team):
                task = Task.objects.create(
                    title=f'Task {j} for {team.name}',
                    description='Test description',
                    team=team,
                    created_by=user2,
                    status=Task.TODO
                )
                user2_task_ids.append(task.id)
        
        # Get tasks accessible to user1 (tasks from teams where user1 is a member)
        user1_accessible_teams = Team.objects.filter(memberships__user=user1)
        user1_accessible_tasks = Task.objects.filter(team__in=user1_accessible_teams)
        
        # Get tasks accessible to user2 (tasks from teams where user2 is a member)
        user2_accessible_teams = Team.objects.filter(memberships__user=user2)
        user2_accessible_tasks = Task.objects.filter(team__in=user2_accessible_teams)
        
        # Verify user1 can only see their own tasks
        user1_accessible_task_ids = list(user1_accessible_tasks.values_list('id', flat=True))
        for task_id in user1_task_ids:
            assert task_id in user1_accessible_task_ids
        for task_id in user2_task_ids:
            assert task_id not in user1_accessible_task_ids
        
        # Verify user2 can only see their own tasks
        user2_accessible_task_ids = list(user2_accessible_tasks.values_list('id', flat=True))
        for task_id in user2_task_ids:
            assert task_id in user2_accessible_task_ids
        for task_id in user1_task_ids:
            assert task_id not in user2_accessible_task_ids



# Feature: project-collaboration-portal, Property 15: Comment creation associates with task
@pytest.mark.django_db
@settings(max_examples=100, deadline=None)
@given(
    comment_content=st.text(min_size=1, max_size=1000, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Po')))
)
def test_comment_creation_associates_with_task(comment_content):
    """
    Property 15: Comment creation associates with task
    For any Team Member creating a Comment under a Task, the Comment should be 
    persisted and correctly associated with the Task.
    Validates: Requirements 4.1
    """
    # Create a user and team
    user = User.objects.create_user(username=f'testuser_{timezone.now().timestamp()}', password='testpass123')
    team = Team.objects.create(name=f'Test Team {timezone.now().timestamp()}', created_by=user)
    
    # Create a task
    task = Task.objects.create(
        title='Test Task',
        description='Test description',
        team=team,
        created_by=user,
        status=Task.TODO
    )
    
    # Create a comment with the generated content
    comment = Comment.objects.create(
        task=task,
        author=user,
        content=comment_content.strip() or "Comment"
    )
    
    # Verify the comment is persisted
    assert Comment.objects.filter(pk=comment.pk).exists()
    
    # Verify the comment is associated with the correct task
    retrieved_comment = Comment.objects.get(pk=comment.pk)
    assert retrieved_comment.task == task
    assert retrieved_comment.task.id == task.id
    
    # Verify all fields are correctly stored
    assert retrieved_comment.content == (comment_content.strip() or "Comment")
    assert retrieved_comment.author == user
    assert retrieved_comment.parent is None
    
    # Verify timestamp is set
    assert retrieved_comment.created_at is not None
    
    # Verify the comment appears in the task's comments
    assert comment in task.comments.all()


# Feature: project-collaboration-portal, Property 16: Reply establishes parent-child relationship
@pytest.mark.django_db
@settings(max_examples=100, deadline=None)
@given(
    parent_content=st.text(min_size=1, max_size=500, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'))),
    reply_content=st.text(min_size=1, max_size=500, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs')))
)
def test_reply_establishes_parent_child_relationship(parent_content, reply_content):
    """
    Property 16: Reply establishes parent-child relationship
    For any Team Member creating a reply to an existing Comment, the reply should be 
    persisted with a correct parent-child relationship.
    Validates: Requirements 4.2
    """
    # Create a user and team
    user = User.objects.create_user(username=f'testuser_{timezone.now().timestamp()}', password='testpass123')
    team = Team.objects.create(name=f'Test Team {timezone.now().timestamp()}', created_by=user)
    
    # Create a task
    task = Task.objects.create(
        title='Test Task',
        description='Test description',
        team=team,
        created_by=user,
        status=Task.TODO
    )
    
    # Create a parent comment
    parent_comment = Comment.objects.create(
        task=task,
        author=user,
        content=parent_content.strip() or "Parent comment"
    )
    
    # Create a reply to the parent comment
    reply = Comment.objects.create(
        task=task,
        author=user,
        content=reply_content.strip() or "Reply",
        parent=parent_comment
    )
    
    # Verify the reply is persisted
    assert Comment.objects.filter(pk=reply.pk).exists()
    
    # Verify the parent-child relationship is established
    retrieved_reply = Comment.objects.get(pk=reply.pk)
    assert retrieved_reply.parent == parent_comment
    assert retrieved_reply.parent.id == parent_comment.id
    
    # Verify the reply is associated with the same task
    assert retrieved_reply.task == task
    
    # Verify the reply appears in the parent's replies
    assert reply in parent_comment.get_replies()
    assert reply in parent_comment.replies.all()
    
    # Verify all fields are correctly stored
    assert retrieved_reply.content == (reply_content.strip() or "Reply")
    assert retrieved_reply.author == user


# Feature: project-collaboration-portal, Property 17: Comments display in threaded hierarchy
@pytest.mark.django_db
@settings(max_examples=100, deadline=None)
@given(
    num_top_level=st.integers(min_value=1, max_value=5),
    replies_per_comment=st.integers(min_value=0, max_value=3)
)
def test_comments_display_in_threaded_hierarchy(num_top_level, replies_per_comment):
    """
    Property 17: Comments display in threaded hierarchy
    For any Task with Comments, viewing the Task should display all Comments in the 
    correct threaded hierarchy with author, timestamp, and content.
    Validates: Requirements 4.3, 4.5
    """
    # Create a user and team
    user = User.objects.create_user(username=f'testuser_{timezone.now().timestamp()}', password='testpass123')
    team = Team.objects.create(name=f'Test Team {timezone.now().timestamp()}', created_by=user)
    
    # Create a task
    task = Task.objects.create(
        title='Test Task',
        description='Test description',
        team=team,
        created_by=user,
        status=Task.TODO
    )
    
    # Create top-level comments
    top_level_comments = []
    for i in range(num_top_level):
        comment = Comment.objects.create(
            task=task,
            author=user,
            content=f"Top-level comment {i}"
        )
        top_level_comments.append(comment)
        
        # Create replies for each top-level comment
        for j in range(replies_per_comment):
            reply = Comment.objects.create(
                task=task,
                author=user,
                content=f"Reply {j} to comment {i}",
                parent=comment
            )
    
    # Retrieve top-level comments (those without a parent)
    retrieved_top_level = task.comments.filter(parent__isnull=True)
    
    # Verify all top-level comments are retrieved
    assert retrieved_top_level.count() == num_top_level
    
    # Verify each top-level comment has the correct number of replies
    for comment in retrieved_top_level:
        assert comment.replies.count() == replies_per_comment
        
        # Verify each comment has author, timestamp, and content
        assert comment.author is not None
        assert comment.created_at is not None
        assert comment.content is not None
        
        # Verify each reply has author, timestamp, and content
        for reply in comment.replies.all():
            assert reply.author is not None
            assert reply.created_at is not None
            assert reply.content is not None
            assert reply.parent == comment
    
    # Verify total comment count
    total_expected = num_top_level + (num_top_level * replies_per_comment)
    assert Comment.objects.filter(task=task).count() == total_expected


# Feature: project-collaboration-portal, Property 18: Comment deletion cascades to children
@pytest.mark.django_db
@settings(max_examples=100, deadline=None)
@given(
    num_replies=st.integers(min_value=1, max_value=10)
)
def test_comment_deletion_cascades_to_children(num_replies):
    """
    Property 18: Comment deletion cascades to children
    For any Comment being deleted by a Member with appropriate permissions, 
    the Comment and all child Comments in the thread should be removed.
    Validates: Requirements 4.4
    """
    # Create a user and team
    user = User.objects.create_user(username=f'testuser_{timezone.now().timestamp()}', password='testpass123')
    team = Team.objects.create(name=f'Test Team {timezone.now().timestamp()}', created_by=user)
    
    # Create a task
    task = Task.objects.create(
        title='Test Task',
        description='Test description',
        team=team,
        created_by=user,
        status=Task.TODO
    )
    
    # Create a parent comment
    parent_comment = Comment.objects.create(
        task=task,
        author=user,
        content="Parent comment"
    )
    
    parent_id = parent_comment.id
    
    # Create replies to the parent comment
    reply_ids = []
    for i in range(num_replies):
        reply = Comment.objects.create(
            task=task,
            author=user,
            content=f"Reply {i}",
            parent=parent_comment
        )
        reply_ids.append(reply.id)
    
    # Verify replies exist
    assert Comment.objects.filter(parent=parent_comment).count() == num_replies
    
    # Delete the parent comment
    parent_comment.delete()
    
    # Verify parent comment is deleted
    assert not Comment.objects.filter(pk=parent_id).exists()
    
    # Verify all replies are deleted (cascade)
    for reply_id in reply_ids:
        assert not Comment.objects.filter(pk=reply_id).exists()
    
    # Verify no orphaned comments remain
    assert Comment.objects.filter(id__in=reply_ids).count() == 0
    assert Comment.objects.filter(parent_id=parent_id).count() == 0



# Feature: project-collaboration-portal, Property 19: File upload stores and associates correctly
@pytest.mark.django_db
@settings(max_examples=100, deadline=None)
@given(
    filename=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
    file_content=st.binary(min_size=1, max_size=1024)  # Small files for testing
)
def test_file_upload_stores_and_associates_correctly(filename, file_content):
    """
    Property 19: File upload stores and associates correctly
    For any Team Member uploading a file to a Task or Comment, the file should be 
    stored and correctly associated with the parent object via GenericForeignKey.
    Validates: Requirements 5.1, 5.2
    """
    from django.core.files.uploadedfile import SimpleUploadedFile
    from django.contrib.contenttypes.models import ContentType
    
    # Create a user and team
    user = User.objects.create_user(username=f'testuser_{timezone.now().timestamp()}', password='testpass123')
    team = Team.objects.create(name=f'Test Team {timezone.now().timestamp()}', created_by=user)
    
    # Create a task
    task = Task.objects.create(
        title='Test Task',
        description='Test description',
        team=team,
        created_by=user,
        status=Task.TODO
    )
    
    # Create a comment
    comment = Comment.objects.create(
        task=task,
        author=user,
        content='Test comment'
    )
    
    # Test file upload to task
    safe_filename = (filename.strip() or "test") + ".txt"
    uploaded_file = SimpleUploadedFile(safe_filename, file_content, content_type='text/plain')
    
    file_upload_task = FileUpload.objects.create(
        file=uploaded_file,
        uploaded_by=user,
        content_object=task
    )
    
    # Verify the file upload is persisted
    assert FileUpload.objects.filter(pk=file_upload_task.pk).exists()
    
    # Verify the file is associated with the task via GenericForeignKey
    retrieved_file = FileUpload.objects.get(pk=file_upload_task.pk)
    assert retrieved_file.content_object == task
    assert retrieved_file.content_type == ContentType.objects.get_for_model(Task)
    assert retrieved_file.object_id == task.id
    
    # Verify the file is stored
    assert retrieved_file.file is not None
    assert retrieved_file.file.name is not None
    
    # Verify uploader is correct
    assert retrieved_file.uploaded_by == user
    
    # Test file upload to comment
    uploaded_file_comment = SimpleUploadedFile(safe_filename, file_content, content_type='text/plain')
    
    file_upload_comment = FileUpload.objects.create(
        file=uploaded_file_comment,
        uploaded_by=user,
        content_object=comment
    )
    
    # Verify the file upload is persisted
    assert FileUpload.objects.filter(pk=file_upload_comment.pk).exists()
    
    # Verify the file is associated with the comment via GenericForeignKey
    retrieved_file_comment = FileUpload.objects.get(pk=file_upload_comment.pk)
    assert retrieved_file_comment.content_object == comment
    assert retrieved_file_comment.content_type == ContentType.objects.get_for_model(Comment)
    assert retrieved_file_comment.object_id == comment.id
    
    # Verify the file is stored
    assert retrieved_file_comment.file is not None
    assert retrieved_file_comment.file.name is not None
    
    # Clean up files
    file_upload_task.file.delete()
    file_upload_comment.file.delete()


# Feature: project-collaboration-portal, Property 20: File uploads display download links
@pytest.mark.django_db
@settings(max_examples=100, deadline=None)
@given(
    num_files=st.integers(min_value=1, max_value=5)
)
def test_file_uploads_display_download_links(num_files):
    """
    Property 20: File uploads display download links
    For any Task or Comment with File Uploads, viewing the object should display 
    download links for all associated files.
    Validates: Requirements 5.3
    """
    from django.core.files.uploadedfile import SimpleUploadedFile
    from django.contrib.contenttypes.models import ContentType
    
    # Create a user and team
    user = User.objects.create_user(username=f'testuser_{timezone.now().timestamp()}', password='testpass123')
    team = Team.objects.create(name=f'Test Team {timezone.now().timestamp()}', created_by=user)
    
    # Create a task
    task = Task.objects.create(
        title='Test Task',
        description='Test description',
        team=team,
        created_by=user,
        status=Task.TODO
    )
    
    # Upload multiple files to the task
    file_ids = []
    for i in range(num_files):
        uploaded_file = SimpleUploadedFile(
            f'test_file_{i}.txt',
            b'Test content',
            content_type='text/plain'
        )
        
        file_upload = FileUpload.objects.create(
            file=uploaded_file,
            uploaded_by=user,
            content_object=task
        )
        file_ids.append(file_upload.id)
    
    # Retrieve all files associated with the task
    task_content_type = ContentType.objects.get_for_model(Task)
    task_files = FileUpload.objects.filter(
        content_type=task_content_type,
        object_id=task.id
    )
    
    # Verify all files are retrieved
    assert task_files.count() == num_files
    
    # Verify each file has the necessary information for download links
    for file_upload in task_files:
        assert file_upload.id in file_ids
        assert file_upload.file is not None
        assert file_upload.file.name is not None
        assert file_upload.filename is not None  # Property method
        assert file_upload.uploaded_by is not None
        assert file_upload.uploaded_at is not None
    
    # Clean up files
    for file_upload in task_files:
        file_upload.file.delete()


# Feature: project-collaboration-portal, Property 21: Object deletion removes associated files
@pytest.mark.django_db
@settings(max_examples=100, deadline=None)
@given(
    num_task_files=st.integers(min_value=1, max_value=3),
    num_comment_files=st.integers(min_value=1, max_value=3)
)
def test_object_deletion_removes_associated_files(num_task_files, num_comment_files):
    """
    Property 21: Object deletion removes associated files
    For any Task or Comment with File Uploads being deleted, all associated files 
    should be removed from storage.
    Validates: Requirements 5.4
    """
    from django.core.files.uploadedfile import SimpleUploadedFile
    from django.contrib.contenttypes.models import ContentType
    import os
    from django.conf import settings
    
    # Create a user and team
    user = User.objects.create_user(username=f'testuser_{timezone.now().timestamp()}', password='testpass123')
    team = Team.objects.create(name=f'Test Team {timezone.now().timestamp()}', created_by=user)
    
    # Create a task
    task = Task.objects.create(
        title='Test Task',
        description='Test description',
        team=team,
        created_by=user,
        status=Task.TODO
    )
    
    task_id = task.id
    
    # Upload files to the task
    task_file_ids = []
    task_file_paths = []
    for i in range(num_task_files):
        uploaded_file = SimpleUploadedFile(
            f'task_file_{i}.txt',
            b'Test content for task',
            content_type='text/plain'
        )
        
        file_upload = FileUpload.objects.create(
            file=uploaded_file,
            uploaded_by=user,
            content_object=task
        )
        task_file_ids.append(file_upload.id)
        task_file_paths.append(file_upload.file.path)
    
    # Create a comment
    comment = Comment.objects.create(
        task=task,
        author=user,
        content='Test comment'
    )
    
    comment_id = comment.id
    
    # Upload files to the comment
    comment_file_ids = []
    comment_file_paths = []
    for i in range(num_comment_files):
        uploaded_file = SimpleUploadedFile(
            f'comment_file_{i}.txt',
            b'Test content for comment',
            content_type='text/plain'
        )
        
        file_upload = FileUpload.objects.create(
            file=uploaded_file,
            uploaded_by=user,
            content_object=comment
        )
        comment_file_ids.append(file_upload.id)
        comment_file_paths.append(file_upload.file.path)
    
    # Verify files exist in database
    assert FileUpload.objects.filter(id__in=task_file_ids).count() == num_task_files
    assert FileUpload.objects.filter(id__in=comment_file_ids).count() == num_comment_files
    
    # Verify files exist on disk
    for path in task_file_paths:
        assert os.path.exists(path)
    for path in comment_file_paths:
        assert os.path.exists(path)
    
    # Delete the task (should cascade to comments and their files)
    task.delete()
    
    # Verify task is deleted
    assert not Task.objects.filter(pk=task_id).exists()
    
    # Verify comment is deleted (cascade)
    assert not Comment.objects.filter(pk=comment_id).exists()
    
    # Verify all file uploads are deleted from database (cascade)
    assert FileUpload.objects.filter(id__in=task_file_ids).count() == 0
    assert FileUpload.objects.filter(id__in=comment_file_ids).count() == 0
    
    # Verify all files are deleted from disk (signal handler)
    for path in task_file_paths:
        assert not os.path.exists(path), f"File {path} should have been deleted"
    for path in comment_file_paths:
        assert not os.path.exists(path), f"File {path} should have been deleted"



# Feature: project-collaboration-portal, Property 31: Actions create activity log entries
@pytest.mark.django_db
@settings(max_examples=100, deadline=None)
@given(
    task_data=task_data_strategy(),
    comment_content=st.text(min_size=1, max_size=500, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'))),
    num_updates=st.integers(min_value=1, max_value=3)
)
def test_actions_create_activity_log_entries(task_data, comment_content, num_updates):
    """
    Property 31: Actions create activity log entries
    For any Task action (create, update, comment, file upload), an Activity Log entry 
    should be created with the action, User, and timestamp.
    Validates: Requirements 8.1, 8.2, 8.3, 8.4
    """
    from django.core.files.uploadedfile import SimpleUploadedFile
    
    # Create a user and team
    user = User.objects.create_user(username=f'testuser_{timezone.now().timestamp()}', password='testpass123')
    team = Team.objects.create(name=f'Test Team {timezone.now().timestamp()}', created_by=user)
    
    # Test 1: Task creation creates activity log
    task = Task.objects.create(
        title=task_data['title'],
        description=task_data['description'],
        team=team,
        created_by=user,
        status=task_data['status'],
        deadline=task_data['deadline']
    )
    
    # Verify activity log entry for task creation
    creation_logs = ActivityLog.objects.filter(task=task, action='Task created')
    assert creation_logs.exists(), "Task creation should create an activity log entry"
    creation_log = creation_logs.first()
    assert creation_log.user == user
    assert creation_log.timestamp is not None
    assert 'title' in creation_log.details
    
    # Test 2: Task updates create activity logs
    initial_log_count = ActivityLog.objects.filter(task=task).count()
    
    for i in range(num_updates):
        task.status = Task.IN_PROGRESS if i % 2 == 0 else Task.REVIEW
        task.save()
        
        import time
        time.sleep(0.01)  # Small delay to ensure distinct timestamps
    
    # Verify activity log entries for task updates
    update_logs = ActivityLog.objects.filter(task=task, action='Task updated')
    assert update_logs.count() >= num_updates, f"Expected at least {num_updates} update logs"
    
    for log in update_logs:
        assert log.user is not None
        assert log.timestamp is not None
        assert isinstance(log.details, dict)
    
    # Test 3: Comment creation creates activity log
    comment = Comment.objects.create(
        task=task,
        author=user,
        content=comment_content.strip() or "Comment"
    )
    
    # Verify activity log entry for comment creation
    comment_logs = ActivityLog.objects.filter(task=task, action='Comment added')
    assert comment_logs.exists(), "Comment creation should create an activity log entry"
    comment_log = comment_logs.first()
    assert comment_log.user == user
    assert comment_log.timestamp is not None
    assert 'comment_id' in comment_log.details
    assert comment_log.details['comment_id'] == comment.id
    
    # Test 4: File upload creates activity log
    uploaded_file = SimpleUploadedFile(
        'test_file.txt',
        b'Test content',
        content_type='text/plain'
    )
    
    file_upload = FileUpload.objects.create(
        file=uploaded_file,
        uploaded_by=user,
        content_object=task
    )
    
    # Verify activity log entry for file upload
    file_logs = ActivityLog.objects.filter(task=task, action='File uploaded')
    assert file_logs.exists(), "File upload should create an activity log entry"
    file_log = file_logs.first()
    assert file_log.user == user
    assert file_log.timestamp is not None
    assert 'filename' in file_log.details
    assert 'file_id' in file_log.details
    
    # Verify all activity logs have required fields
    all_logs = ActivityLog.objects.filter(task=task)
    for log in all_logs:
        assert log.task == task
        assert log.user is not None
        assert log.action is not None
        assert log.timestamp is not None
        assert isinstance(log.details, dict)
    
    # Clean up
    file_upload.file.delete()


# Feature: project-collaboration-portal, Property 32: Activity log displays chronologically
@pytest.mark.django_db
@settings(max_examples=100, deadline=None)
@given(
    num_actions=st.integers(min_value=3, max_value=10)
)
def test_activity_log_displays_chronologically(num_actions):
    """
    Property 32: Activity log displays chronologically
    For any Task with Activity Log entries, viewing the Task should display 
    the log in chronological order.
    Validates: Requirements 8.5
    """
    import time
    
    # Create a user and team
    user = User.objects.create_user(username=f'testuser_{timezone.now().timestamp()}', password='testpass123')
    team = Team.objects.create(name=f'Test Team {timezone.now().timestamp()}', created_by=user)
    
    # Create a task (this creates the first activity log entry)
    task = Task.objects.create(
        title='Test Task',
        description='Test description',
        team=team,
        created_by=user,
        status=Task.TODO
    )
    
    # Perform multiple actions to create activity log entries
    for i in range(num_actions - 1):  # -1 because task creation already created one
        time.sleep(0.01)  # Small delay to ensure distinct timestamps
        
        if i % 3 == 0:
            # Update task
            task.status = Task.IN_PROGRESS if i % 2 == 0 else Task.REVIEW
            task.save()
        elif i % 3 == 1:
            # Add comment
            Comment.objects.create(
                task=task,
                author=user,
                content=f'Comment {i}'
            )
        else:
            # Upload file
            from django.core.files.uploadedfile import SimpleUploadedFile
            uploaded_file = SimpleUploadedFile(
                f'test_file_{i}.txt',
                b'Test content',
                content_type='text/plain'
            )
            file_upload = FileUpload.objects.create(
                file=uploaded_file,
                uploaded_by=user,
                content_object=task
            )
    
    # Retrieve activity logs (should be in chronological order by default)
    activity_logs = ActivityLog.objects.filter(task=task).order_by('timestamp')
    
    # Verify we have the expected number of logs
    assert activity_logs.count() >= num_actions, f"Expected at least {num_actions} activity log entries"
    
    # Verify chronological ordering
    previous_timestamp = None
    for log in activity_logs:
        assert log.timestamp is not None
        
        if previous_timestamp is not None:
            # Each timestamp should be greater than or equal to the previous
            assert log.timestamp >= previous_timestamp, \
                f"Activity logs should be in chronological order: {log.timestamp} should be >= {previous_timestamp}"
        
        previous_timestamp = log.timestamp
    
    # Verify the first log is the task creation
    first_log = activity_logs.first()
    assert first_log.action == 'Task created', "First activity log should be task creation"
    
    # Verify all logs have required fields
    for log in activity_logs:
        assert log.task == task
        assert log.user is not None
        assert log.action is not None
        assert log.timestamp is not None
        assert isinstance(log.details, dict)
    
    # Clean up files
    from django.contrib.contenttypes.models import ContentType
    task_content_type = ContentType.objects.get_for_model(Task)
    task_files = FileUpload.objects.filter(content_type=task_content_type, object_id=task.id)
    for file_upload in task_files:
        file_upload.file.delete()
