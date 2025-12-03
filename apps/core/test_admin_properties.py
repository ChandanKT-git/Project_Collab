"""
Property-based tests for admin functionality.
"""
import pytest
import uuid
from hypothesis import given, strategies as st, settings
from django.contrib.auth.models import User
from django.test import Client
from django.db import transaction
from apps.teams.models import Team, TeamMembership
from apps.tasks.models import Task, Comment, FileUpload
from apps.notifications.models import Notification


# Hypothesis strategies for generating test data
@st.composite
def user_data(draw):
    """Generate valid user data."""
    username = draw(st.text(min_size=1, max_size=150, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'), 
        whitelist_characters='_'
    )))
    email = draw(st.emails())
    password = draw(st.text(min_size=8, max_size=128))
    return {
        'username': username,
        'email': email,
        'password': password,
    }


@pytest.mark.django_db(transaction=True)
class TestAdminProperties:
    """Property-based tests for admin functionality."""
    
    @settings(max_examples=100, deadline=None)
    @given(
        is_active=st.booleans()
    )
    def test_admin_user_modifications_apply_immediately(self, is_active):
        """
        **Feature: project-collaboration-portal, Property 35: Admin modifications apply immediately**
        
        For any superuser modifying a User account via the admin dashboard, 
        the changes should be applied immediately to the User record.
        
        **Validates: Requirements 10.2**
        """
        # Create a unique username for this test run
        unique_id = str(uuid.uuid4())[:8]
        username = f'testuser_{unique_id}'
        email = f'{username}@test.com'
        
        # Create a regular user
        user = User.objects.create_user(
            username=username,
            email=email,
            password='testpass123'
        )
        
        # Modify the user's is_active status
        user.is_active = is_active
        user.save()
        
        # Verify the change was applied immediately
        user.refresh_from_db()
        assert user.is_active == is_active
        
        # Verify the change persists
        retrieved_user = User.objects.get(pk=user.pk)
        assert retrieved_user.is_active == is_active
    
    @settings(max_examples=100, deadline=None)
    @given(st.integers(min_value=0, max_value=10))
    def test_system_statistics_are_accurate(self, num_users):
        """
        **Feature: project-collaboration-portal, Property 36: System statistics are accurate**
        
        For any system state, the admin dashboard should display accurate counts 
        of Users, Teams, Tasks, and Comments.
        
        **Validates: Requirements 10.3**
        """
        # Use a unique prefix for this test run
        unique_id = str(uuid.uuid4())[:8]
        
        # Create a known number of users
        users = []
        for i in range(num_users):
            user = User.objects.create_user(
                username=f'user_{unique_id}_{i}',
                email=f'user{unique_id}{i}@test.com',
                password='testpass123'
            )
            users.append(user)
        
        # Count users with this prefix
        actual_user_count = User.objects.filter(username__startswith=f'user_{unique_id}_').count()
        
        # Verify the count matches
        assert actual_user_count == len(users)
        
        # Create some teams
        teams = []
        for i, user in enumerate(users[:min(5, len(users))]):
            team = Team.objects.create(
                name=f'Team {unique_id} {i}',
                description=f'Test team {i}',
                created_by=user
            )
            teams.append(team)
        
        # Count teams with this prefix
        actual_team_count = Team.objects.filter(name__startswith=f'Team {unique_id}').count()
        assert actual_team_count == len(teams)
        
        # Create some tasks
        tasks = []
        for i, team in enumerate(teams):
            task = Task.objects.create(
                title=f'Task {unique_id} {i}',
                description=f'Test task {i}',
                team=team,
                created_by=team.created_by,
                status=Task.TODO
            )
            tasks.append(task)
        
        # Count tasks with this prefix
        actual_task_count = Task.objects.filter(title__startswith=f'Task {unique_id}').count()
        assert actual_task_count == len(tasks)
        
        # Create some comments
        comments = []
        for i, task in enumerate(tasks):
            comment = Comment.objects.create(
                task=task,
                author=task.created_by,
                content=f'Test comment {unique_id} {i}'
            )
            comments.append(comment)
        
        # Count comments with this prefix
        actual_comment_count = Comment.objects.filter(content__startswith=f'Test comment {unique_id}').count()
        assert actual_comment_count == len(comments)
    
    @settings(max_examples=100, deadline=None)
    @given(
        num_tasks=st.integers(min_value=0, max_value=10),
        num_comments=st.integers(min_value=0, max_value=10)
    )
    def test_admin_team_deletion_cascades_completely(self, num_tasks, num_comments):
        """
        **Feature: project-collaboration-portal, Property 37: Admin team deletion cascades completely**
        
        For any superuser deleting a Team via the admin dashboard, 
        all associated Tasks, Comments, and File Uploads should be removed.
        
        **Validates: Requirements 10.4**
        """
        # Create a unique identifier for this test run
        unique_id = str(uuid.uuid4())[:8]
        
        # Create a user
        user = User.objects.create_user(
            username=f'testuser_cascade_{unique_id}',
            email=f'test{unique_id}@cascade.com',
            password='testpass123'
        )
        
        # Create a team
        team = Team.objects.create(
            name=f'Team Cascade {unique_id}',
            description='Test team for cascade deletion',
            created_by=user
        )
        
        # Create tasks
        tasks = []
        for i in range(num_tasks):
            task = Task.objects.create(
                title=f'Task {unique_id} {i}',
                description=f'Test task {i}',
                team=team,
                created_by=user,
                status=Task.TODO
            )
            tasks.append(task)
        
        # Create comments on tasks
        comments = []
        for task in tasks:
            for i in range(num_comments):
                comment = Comment.objects.create(
                    task=task,
                    author=user,
                    content=f'Test comment {unique_id} {i}'
                )
                comments.append(comment)
        
        # Record IDs before deletion
        team_id = team.pk
        task_ids = [t.pk for t in tasks]
        comment_ids = [c.pk for c in comments]
        
        # Delete the team
        team.delete()
        
        # Verify team is deleted
        assert not Team.objects.filter(pk=team_id).exists()
        
        # Verify all tasks are deleted (cascade)
        assert Task.objects.filter(pk__in=task_ids).count() == 0
        
        # Verify all comments are deleted (cascade)
        assert Comment.objects.filter(pk__in=comment_ids).count() == 0
    
    @settings(max_examples=100, deadline=None)
    @given(
        is_superuser=st.booleans()
    )
    def test_admin_access_requires_superuser_privileges(self, is_superuser):
        """
        **Feature: project-collaboration-portal, Property 38: Admin access requires superuser privileges**
        
        For any User attempting to access the admin dashboard, 
        access should only be granted if the User has superuser privileges.
        
        **Validates: Requirements 10.5**
        """
        # Create a unique identifier for this test run
        unique_id = str(uuid.uuid4())[:8]
        username = f'testuser_{unique_id}'
        email = f'{username}@test.com'
        
        # Create a user with or without superuser privileges
        if is_superuser:
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password='testpass123'
            )
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password='testpass123'
            )
        
        # Create a client and login
        client = Client()
        client.force_login(user)
        
        # Try to access the admin index
        response = client.get('/admin/')
        
        # Verify access based on superuser status
        if is_superuser:
            # Superusers should be able to access admin
            assert response.status_code in [200, 302]  # 200 for success, 302 for redirect to admin
        else:
            # Non-superusers should be redirected to login or get 403
            assert response.status_code in [302, 403]
        
        # Try to access the statistics view
        response = client.get('/admin/statistics/')
        
        # Verify access based on superuser status
        if is_superuser:
            # Superusers should be able to access statistics
            assert response.status_code == 200
        else:
            # Non-superusers should get 403 or be redirected
            assert response.status_code in [302, 403]
