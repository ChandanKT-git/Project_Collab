"""Unit tests for permission utilities."""
import pytest
from django.contrib.auth.models import User
from apps.teams.models import Team, TeamMembership
from apps.tasks.models import Task
from apps.core.permissions import (
    check_object_permission,
    check_team_membership,
    check_team_owner,
    get_user_teams,
    get_user_tasks
)


@pytest.mark.django_db
class TestPermissionUtilities:
    """Test permission utility functions."""
    
    def test_check_object_permission(self):
        """Test check_object_permission utility."""
        user = User.objects.create_user(username='testuser', password='testpass123')
        team = Team.objects.create(name='Test Team', created_by=user)
        
        # User should have permissions on their own team
        assert check_object_permission(user, 'teams.view_team', team)
        assert check_object_permission(user, 'teams.change_team', team)
        assert check_object_permission(user, 'teams.delete_team', team)
        
        # Other user should not have permissions
        other_user = User.objects.create_user(username='otheruser', password='testpass123')
        assert not check_object_permission(other_user, 'teams.view_team', team)
    
    def test_check_team_membership(self):
        """Test check_team_membership utility."""
        owner = User.objects.create_user(username='owner', password='testpass123')
        member = User.objects.create_user(username='member', password='testpass123')
        outsider = User.objects.create_user(username='outsider', password='testpass123')
        
        team = Team.objects.create(name='Test Team', created_by=owner)
        TeamMembership.objects.create(team=team, user=member, role=TeamMembership.MEMBER)
        
        # Owner and member should be team members
        assert check_team_membership(owner, team)
        assert check_team_membership(member, team)
        
        # Outsider should not be a team member
        assert not check_team_membership(outsider, team)
    
    def test_check_team_owner(self):
        """Test check_team_owner utility."""
        owner = User.objects.create_user(username='owner', password='testpass123')
        member = User.objects.create_user(username='member', password='testpass123')
        
        team = Team.objects.create(name='Test Team', created_by=owner)
        TeamMembership.objects.create(team=team, user=member, role=TeamMembership.MEMBER)
        
        # Owner should be identified as owner
        assert check_team_owner(owner, team)
        
        # Member should not be identified as owner
        assert not check_team_owner(member, team)
    
    def test_get_user_teams(self):
        """Test get_user_teams utility."""
        user = User.objects.create_user(username='testuser', password='testpass123')
        other_user = User.objects.create_user(username='otheruser', password='testpass123')
        
        # Create teams
        team1 = Team.objects.create(name='Team 1', created_by=user)
        team2 = Team.objects.create(name='Team 2', created_by=user)
        team3 = Team.objects.create(name='Team 3', created_by=other_user)
        
        # Get user's teams
        user_teams = get_user_teams(user)
        
        # User should have access to their own teams
        assert team1 in user_teams
        assert team2 in user_teams
        
        # User should not have access to other user's team
        assert team3 not in user_teams
    
    def test_get_user_tasks(self):
        """Test get_user_tasks utility."""
        user = User.objects.create_user(username='testuser', password='testpass123')
        other_user = User.objects.create_user(username='otheruser', password='testpass123')
        
        # Create teams
        user_team = Team.objects.create(name='User Team', created_by=user)
        other_team = Team.objects.create(name='Other Team', created_by=other_user)
        
        # Create tasks
        task1 = Task.objects.create(
            title='Task 1',
            description='Description 1',
            team=user_team,
            created_by=user,
            status=Task.TODO
        )
        task2 = Task.objects.create(
            title='Task 2',
            description='Description 2',
            team=user_team,
            created_by=user,
            status=Task.TODO
        )
        task3 = Task.objects.create(
            title='Task 3',
            description='Description 3',
            team=other_team,
            created_by=other_user,
            status=Task.TODO
        )
        
        # Get user's tasks
        user_tasks = get_user_tasks(user)
        
        # User should have access to their team's tasks
        assert task1 in user_tasks
        assert task2 in user_tasks
        
        # User should not have access to other team's tasks
        assert task3 not in user_tasks
    
    def test_unauthenticated_user(self):
        """Test that unauthenticated users have no permissions."""
        from django.contrib.auth.models import AnonymousUser
        
        user = User.objects.create_user(username='testuser', password='testpass123')
        team = Team.objects.create(name='Test Team', created_by=user)
        
        anonymous = AnonymousUser()
        
        # Anonymous user should have no permissions
        assert not check_object_permission(anonymous, 'teams.view_team', team)
        assert not check_team_membership(anonymous, team)
        assert not check_team_owner(anonymous, team)
        
        # Anonymous user should have no teams or tasks
        assert get_user_teams(anonymous).count() == 0
        assert get_user_tasks(anonymous).count() == 0
