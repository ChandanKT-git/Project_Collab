"""Property-based tests for permission system using Hypothesis."""
import pytest
from hypothesis import given, settings, strategies as st, HealthCheck
from django.contrib.auth.models import User
from guardian.shortcuts import assign_perm, remove_perm, get_perms
from apps.teams.models import Team, TeamMembership
from apps.tasks.models import Task
import uuid


# Feature: project-collaboration-portal, Property 22: Permission checks enforce access control
@pytest.mark.django_db(transaction=True)
@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=100, deadline=None)
@given(
    team_name=st.text(min_size=1, max_size=200),
    task_title=st.text(min_size=1, max_size=200)
)
def test_permission_checks_enforce_access_control(team_name, task_title):
    """
    Property 22: Permission checks enforce access control
    For any User attempting to access a Team resource, the system should verify 
    Object-Level Permissions using django-guardian before granting access.
    Validates: Requirements 6.1
    """
    # Create users with unique usernames
    owner_username = f"owner_{uuid.uuid4().hex[:10]}"
    member_username = f"member_{uuid.uuid4().hex[:10]}"
    outsider_username = f"outsider_{uuid.uuid4().hex[:10]}"
    
    owner = User.objects.create_user(username=owner_username, email=f"{owner_username}@test.com", password='testpass123')
    member = User.objects.create_user(username=member_username, email=f"{member_username}@test.com", password='testpass123')
    outsider = User.objects.create_user(username=outsider_username, email=f"{outsider_username}@test.com", password='testpass123')
    
    # Create a team
    team = Team.objects.create(
        name=team_name,
        description="Test team",
        created_by=owner
    )
    
    # Add member to team
    TeamMembership.objects.create(
        team=team,
        user=member,
        role=TeamMembership.MEMBER
    )
    
    # Create a task
    task = Task.objects.create(
        title=task_title,
        description="Test task",
        team=team,
        created_by=owner,
        status=Task.TODO
    )
    
    # Assign permissions to team members for the task
    assign_perm('tasks.view_task', owner, task)
    assign_perm('tasks.change_task', owner, task)
    assign_perm('tasks.delete_task', owner, task)
    assign_perm('tasks.view_task', member, task)
    
    # Verify owner has all permissions on team
    assert owner.has_perm('teams.view_team', team), "Owner should have view permission on team"
    assert owner.has_perm('teams.change_team', team), "Owner should have change permission on team"
    assert owner.has_perm('teams.delete_team', team), "Owner should have delete permission on team"
    
    # Verify member has view permission on team
    assert member.has_perm('teams.view_team', team), "Member should have view permission on team"
    assert not member.has_perm('teams.change_team', team), "Member should not have change permission on team"
    assert not member.has_perm('teams.delete_team', team), "Member should not have delete permission on team"
    
    # Verify outsider has no permissions on team
    assert not outsider.has_perm('teams.view_team', team), "Outsider should not have view permission on team"
    assert not outsider.has_perm('teams.change_team', team), "Outsider should not have change permission on team"
    assert not outsider.has_perm('teams.delete_team', team), "Outsider should not have delete permission on team"
    
    # Verify owner has all permissions on task
    assert owner.has_perm('tasks.view_task', task), "Owner should have view permission on task"
    assert owner.has_perm('tasks.change_task', task), "Owner should have change permission on task"
    assert owner.has_perm('tasks.delete_task', task), "Owner should have delete permission on task"
    
    # Verify member has view permission on task
    assert member.has_perm('tasks.view_task', task), "Member should have view permission on task"
    assert not member.has_perm('tasks.change_task', task), "Member should not have change permission on task"
    assert not member.has_perm('tasks.delete_task', task), "Member should not have delete permission on task"
    
    # Verify outsider has no permissions on task
    assert not outsider.has_perm('tasks.view_task', task), "Outsider should not have view permission on task"
    assert not outsider.has_perm('tasks.change_task', task), "Outsider should not have change permission on task"
    assert not outsider.has_perm('tasks.delete_task', task), "Outsider should not have delete permission on task"


# Feature: project-collaboration-portal, Property 23: Permission grants apply at object level
@pytest.mark.django_db(transaction=True)
@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=100, deadline=None)
@given(
    team_name=st.text(min_size=1, max_size=200)
)
def test_permission_grants_apply_at_object_level(team_name):
    """
    Property 23: Permission grants apply at object level
    For any Owner granting permissions to a Member, the permissions should be 
    applied at the object level for specific Team resources.
    Validates: Requirements 6.2
    """
    # Create users with unique usernames
    owner_username = f"owner_{uuid.uuid4().hex[:10]}"
    member_username = f"member_{uuid.uuid4().hex[:10]}"
    
    owner = User.objects.create_user(username=owner_username, email=f"{owner_username}@test.com", password='testpass123')
    member = User.objects.create_user(username=member_username, email=f"{member_username}@test.com", password='testpass123')
    
    # Create two teams
    team1 = Team.objects.create(
        name=f"{team_name}_1",
        description="Test team 1",
        created_by=owner
    )
    
    team2 = Team.objects.create(
        name=f"{team_name}_2",
        description="Test team 2",
        created_by=owner
    )
    
    # Add member to team1 only
    TeamMembership.objects.create(
        team=team1,
        user=member,
        role=TeamMembership.MEMBER
    )
    
    # Verify member has permissions on team1
    assert member.has_perm('teams.view_team', team1), "Member should have view permission on team1"
    
    # Verify member does NOT have permissions on team2 (object-level isolation)
    assert not member.has_perm('teams.view_team', team2), "Member should not have view permission on team2"
    
    # Verify permissions are object-specific, not global
    perms_team1 = get_perms(member, team1)
    perms_team2 = get_perms(member, team2)
    
    assert 'view_team' in perms_team1, "Member should have view_team permission on team1"
    assert 'view_team' not in perms_team2, "Member should not have view_team permission on team2"
    
    # Grant specific permission to member on team2
    assign_perm('teams.view_team', member, team2)
    
    # Verify member now has permission on team2
    assert member.has_perm('teams.view_team', team2), "Member should now have view permission on team2"
    
    # Verify permissions are still object-specific
    assert member.has_perm('teams.view_team', team1), "Member should still have view permission on team1"


# Feature: project-collaboration-portal, Property 24: Unauthorized actions are denied
@pytest.mark.django_db(transaction=True)
@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=100, deadline=None)
@given(
    team_name=st.text(min_size=1, max_size=200),
    task_title=st.text(min_size=1, max_size=200)
)
def test_unauthorized_actions_are_denied(team_name, task_title):
    """
    Property 24: Unauthorized actions are denied
    For any Member attempting to modify or delete a Task without appropriate 
    permissions, the action should be denied with an error message.
    Validates: Requirements 6.3, 6.4
    """
    # Create users with unique usernames
    owner_username = f"owner_{uuid.uuid4().hex[:10]}"
    member_username = f"member_{uuid.uuid4().hex[:10]}"
    
    owner = User.objects.create_user(username=owner_username, email=f"{owner_username}@test.com", password='testpass123')
    member = User.objects.create_user(username=member_username, email=f"{member_username}@test.com", password='testpass123')
    
    # Create a team
    team = Team.objects.create(
        name=team_name,
        description="Test team",
        created_by=owner
    )
    
    # Add member to team
    TeamMembership.objects.create(
        team=team,
        user=member,
        role=TeamMembership.MEMBER
    )
    
    # Create a task
    task = Task.objects.create(
        title=task_title,
        description="Test task",
        team=team,
        created_by=owner,
        status=Task.TODO
    )
    
    # Grant only view permission to member
    assign_perm('tasks.view_task', member, task)
    
    # Verify member can view but not modify or delete
    assert member.has_perm('tasks.view_task', task), "Member should have view permission"
    assert not member.has_perm('tasks.change_task', task), "Member should not have change permission"
    assert not member.has_perm('tasks.delete_task', task), "Member should not have delete permission"
    
    # Verify owner has all permissions
    assert owner.has_perm('tasks.view_task', task), "Owner should have view permission"
    assert owner.has_perm('tasks.change_task', task), "Owner should have change permission"
    assert owner.has_perm('tasks.delete_task', task), "Owner should have delete permission"
    
    # Test team permissions
    assert not member.has_perm('teams.change_team', team), "Member should not have change permission on team"
    assert not member.has_perm('teams.delete_team', team), "Member should not have delete permission on team"
    assert not member.has_perm('teams.manage_members', team), "Member should not have manage_members permission on team"
    
    # Verify owner has all team permissions
    assert owner.has_perm('teams.change_team', team), "Owner should have change permission on team"
    assert owner.has_perm('teams.delete_team', team), "Owner should have delete permission on team"
    assert owner.has_perm('teams.manage_members', team), "Owner should have manage_members permission on team"


# Feature: project-collaboration-portal, Property 25: Permission revocation takes immediate effect
@pytest.mark.django_db(transaction=True)
@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=100, deadline=None)
@given(
    team_name=st.text(min_size=1, max_size=200)
)
def test_permission_revocation_takes_immediate_effect(team_name):
    """
    Property 25: Permission revocation takes immediate effect
    For any Member having permissions revoked, subsequent access attempts should 
    immediately be denied.
    Validates: Requirements 6.5
    """
    # Create users with unique usernames
    owner_username = f"owner_{uuid.uuid4().hex[:10]}"
    member_username = f"member_{uuid.uuid4().hex[:10]}"
    
    owner = User.objects.create_user(username=owner_username, email=f"{owner_username}@test.com", password='testpass123')
    member = User.objects.create_user(username=member_username, email=f"{member_username}@test.com", password='testpass123')
    
    # Create a team
    team = Team.objects.create(
        name=team_name,
        description="Test team",
        created_by=owner
    )
    
    # Add member to team
    membership = TeamMembership.objects.create(
        team=team,
        user=member,
        role=TeamMembership.MEMBER
    )
    
    # Verify member has view permission
    assert member.has_perm('teams.view_team', team), "Member should initially have view permission"
    
    # Grant additional permissions to member
    assign_perm('teams.change_team', member, team)
    assign_perm('teams.delete_team', member, team)
    
    # Verify member has all permissions
    assert member.has_perm('teams.view_team', team), "Member should have view permission"
    assert member.has_perm('teams.change_team', team), "Member should have change permission"
    assert member.has_perm('teams.delete_team', team), "Member should have delete permission"
    
    # Revoke change permission
    remove_perm('teams.change_team', member, team)
    
    # Verify change permission is immediately revoked
    assert member.has_perm('teams.view_team', team), "Member should still have view permission"
    assert not member.has_perm('teams.change_team', team), "Member should no longer have change permission"
    assert member.has_perm('teams.delete_team', team), "Member should still have delete permission"
    
    # Revoke all remaining permissions
    remove_perm('teams.view_team', member, team)
    remove_perm('teams.delete_team', member, team)
    remove_perm('teams.manage_members', member, team)
    
    # Verify all permissions are immediately revoked
    assert not member.has_perm('teams.view_team', team), "Member should no longer have view permission"
    assert not member.has_perm('teams.change_team', team), "Member should no longer have change permission"
    assert not member.has_perm('teams.delete_team', team), "Member should no longer have delete permission"
    assert not member.has_perm('teams.manage_members', team), "Member should no longer have manage_members permission"
    
    # Verify permissions list is empty
    perms = get_perms(member, team)
    assert len(perms) == 0, "Member should have no permissions after revocation"
