"""
Tests for form validation and error handling.
"""
import pytest
from django.contrib.auth.models import User
from apps.accounts.forms import SignupForm
from apps.teams.forms import TeamForm, AddMemberForm
from apps.tasks.forms import TaskForm, CommentForm, FileUploadForm
from apps.teams.models import Team, TeamMembership
from django.core.files.uploadedfile import SimpleUploadedFile


@pytest.mark.django_db
class TestAccountsForms:
    """Test accounts form validation."""
    
    def test_signup_form_duplicate_username(self):
        """Test that duplicate username is rejected."""
        # Create a user
        User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        
        # Try to create another user with same username
        form = SignupForm(data={
            'username': 'testuser',
            'email': 'another@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123'
        })
        
        assert not form.is_valid()
        assert 'username' in form.errors
        assert 'already exists' in str(form.errors['username'])
    
    def test_signup_form_duplicate_email(self):
        """Test that duplicate email is rejected."""
        # Create a user
        User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        
        # Try to create another user with same email
        form = SignupForm(data={
            'username': 'anotheruser',
            'email': 'test@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123'
        })
        
        assert not form.is_valid()
        assert 'email' in form.errors
        assert 'already exists' in str(form.errors['email'])


@pytest.mark.django_db
class TestTeamsForms:
    """Test teams form validation."""
    
    def test_team_form_short_name(self):
        """Test that team name must be at least 3 characters."""
        form = TeamForm(data={
            'name': 'ab',
            'description': 'Test description'
        })
        
        assert not form.is_valid()
        assert 'name' in form.errors
        assert 'at least 3 characters' in str(form.errors['name'])
    
    def test_team_form_long_name(self):
        """Test that team name cannot exceed 100 characters."""
        form = TeamForm(data={
            'name': 'a' * 101,
            'description': 'Test description'
        })
        
        assert not form.is_valid()
        assert 'name' in form.errors
        assert 'must not exceed 100 characters' in str(form.errors['name'])
    
    def test_team_form_whitespace_name(self):
        """Test that team name cannot be only whitespace."""
        form = TeamForm(data={
            'name': '   ',
            'description': 'Test description'
        })
        
        assert not form.is_valid()
        assert 'name' in form.errors
    
    def test_add_member_form_nonexistent_user(self):
        """Test that adding nonexistent user is rejected."""
        user = User.objects.create_user(username='owner', password='testpass123')
        team = Team.objects.create(name='Test Team', created_by=user)
        
        form = AddMemberForm(data={
            'username': 'nonexistent',
            'role': TeamMembership.MEMBER
        }, team=team)
        
        assert not form.is_valid()
        assert 'username' in form.errors
        assert 'does not exist' in str(form.errors['username'])
    
    def test_add_member_form_duplicate_member(self):
        """Test that adding existing member is rejected."""
        owner = User.objects.create_user(username='owner', password='testpass123')
        member = User.objects.create_user(username='member', password='testpass123')
        team = Team.objects.create(name='Test Team', created_by=owner)
        TeamMembership.objects.create(team=team, user=member, role=TeamMembership.MEMBER)
        
        form = AddMemberForm(data={
            'username': 'member',
            'role': TeamMembership.MEMBER
        }, team=team)
        
        assert not form.is_valid()
        assert 'username' in form.errors
        assert 'already a member' in str(form.errors['username'])


@pytest.mark.django_db
class TestTasksForms:
    """Test tasks form validation."""
    
    def test_task_form_short_title(self):
        """Test that task title must be at least 3 characters."""
        user = User.objects.create_user(username='testuser', password='testpass123')
        
        form = TaskForm(data={
            'title': 'ab',
            'description': 'Test description',
            'status': 'TODO'
        }, user=user)
        
        assert not form.is_valid()
        assert 'title' in form.errors
        assert 'at least 3 characters' in str(form.errors['title'])
    
    def test_task_form_long_title(self):
        """Test that task title cannot exceed 200 characters."""
        user = User.objects.create_user(username='testuser', password='testpass123')
        
        form = TaskForm(data={
            'title': 'a' * 201,
            'description': 'Test description',
            'status': 'TODO'
        }, user=user)
        
        assert not form.is_valid()
        assert 'title' in form.errors
        # Django's max_length validation or our custom validation
        assert '200 characters' in str(form.errors['title'])
    
    def test_task_form_whitespace_title(self):
        """Test that task title cannot be only whitespace."""
        user = User.objects.create_user(username='testuser', password='testpass123')
        
        form = TaskForm(data={
            'title': '   ',
            'description': 'Test description',
            'status': 'TODO'
        }, user=user)
        
        assert not form.is_valid()
        assert 'title' in form.errors
    
    def test_comment_form_empty_content(self):
        """Test that comment content cannot be empty."""
        form = CommentForm(data={
            'content': ''
        })
        
        assert not form.is_valid()
        assert 'content' in form.errors
    
    def test_comment_form_whitespace_content(self):
        """Test that comment content cannot be only whitespace."""
        form = CommentForm(data={
            'content': '   '
        })
        
        assert not form.is_valid()
        assert 'content' in form.errors
        # Either required field or our custom validation message
        error_msg = str(form.errors['content'])
        assert 'required' in error_msg.lower() or 'cannot be empty' in error_msg.lower()
    
    def test_comment_form_long_content(self):
        """Test that comment content cannot exceed 2000 characters."""
        form = CommentForm(data={
            'content': 'a' * 2001
        })
        
        assert not form.is_valid()
        assert 'content' in form.errors
        assert 'must not exceed 2000 characters' in str(form.errors['content'])
    
    def test_file_upload_form_large_file(self):
        """Test that file size validation works."""
        # Create a file larger than 10MB
        large_file = SimpleUploadedFile(
            "large_file.txt",
            b"x" * (11 * 1024 * 1024),  # 11MB
            content_type="text/plain"
        )
        
        form = FileUploadForm(data={}, files={'file': large_file})
        
        assert not form.is_valid()
        assert 'file' in form.errors
        assert 'must not exceed 10MB' in str(form.errors['file'])


@pytest.mark.django_db
class TestErrorHandlers:
    """Test custom error handlers."""
    
    def test_404_handler(self, client):
        """Test that 404 page is displayed for non-existent pages."""
        response = client.get('/nonexistent-page/')
        assert response.status_code == 404
    
    def test_403_handler(self, client):
        """Test that 403 page is displayed for forbidden access."""
        # Create a user and team
        owner = User.objects.create_user(username='owner', password='testpass123')
        other_user = User.objects.create_user(username='other', password='testpass123')
        team = Team.objects.create(name='Test Team', created_by=owner)
        
        # Login as other user and try to access team
        client.login(username='other', password='testpass123')
        response = client.get(f'/teams/{team.pk}/')
        
        # Should redirect with error message (not 403 in this case, but permission denied)
        assert response.status_code in [302, 403]
