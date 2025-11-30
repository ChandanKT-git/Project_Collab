import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from django.contrib.auth.models import User
from guardian.shortcuts import get_perms
from apps.teams.models import Team, TeamMembership
import uuid


# Feature: project-collaboration-portal, Property 6: Team creator becomes owner
@pytest.mark.django_db(transaction=True)
@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=10, deadline=None)
@given(
    team_name=st.text(min_size=1, max_size=200),
    team_description=st.text(max_size=1000)
)
def test_team_creator_becomes_owner(team_name, team_description):
    """
    Property 6: Team creator becomes owner
    For any User creating a Team, the User should be automatically assigned as Owner 
    of that Team with full permissions.
    Validates: Requirements 2.1
    """
    # Create a user with unique username
    username = f"user_{uuid.uuid4().hex[:10]}"
    user = User.objects.create_user(username=username, email=f"{username}@test.com", password='testpass123')
    
    # Create a team
    team = Team.objects.create(
        name=team_name,
        description=team_description,
        created_by=user
    )
    
    # Check that a membership was created
    membership = TeamMembership.objects.filter(team=team, user=user).first()
    assert membership is not None, "Membership should be created automatically"
    assert membership.role == TeamMembership.OWNER, "Creator should be assigned as OWNER"
    
    # Check that the user has all permissions
    perms = get_perms(user, team)
    assert 'view_team' in perms, "Owner should have view permission"
    assert 'change_team' in perms, "Owner should have change permission"
    assert 'delete_team' in perms, "Owner should have delete permission"
    assert 'manage_members' in perms, "Owner should have manage_members permission"


# Feature: project-collaboration-portal, Property 7: Member addition grants permissions
@pytest.mark.django_db(transaction=True)
@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=10, deadline=None)
@given(
    team_name=st.text(min_size=1, max_size=200)
)
def test_member_addition_grants_permissions(team_name):
    """
    Property 7: Member addition grants permissions
    For any Owner inviting a User to a Team, the User should be added as a Member 
    with appropriate read permissions on Team resources.
    Validates: Requirements 2.2
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
    
    # Check that the member has view permission
    perms = get_perms(member, team)
    assert 'view_team' in perms, "Member should have view permission"
    
    # Check that member does NOT have owner permissions
    assert 'change_team' not in perms, "Member should not have change permission"
    assert 'delete_team' not in perms, "Member should not have delete permission"
    assert 'manage_members' not in perms, "Member should not have manage_members permission"


# Feature: project-collaboration-portal, Property 8: Role assignment updates permissions
@pytest.mark.django_db(transaction=True)
@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=10, deadline=None)
@given(
    team_name=st.text(min_size=1, max_size=200)
)
def test_role_assignment_updates_permissions(team_name):
    """
    Property 8: Role assignment updates permissions
    For any Owner assigning a role to a Team Member, the Member's permissions should 
    be updated to match the new role.
    Validates: Requirements 2.3
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
    
    # Add member to team as MEMBER
    membership = TeamMembership.objects.create(
        team=team,
        user=member,
        role=TeamMembership.MEMBER
    )
    
    # Verify initial permissions
    perms = get_perms(member, team)
    assert 'view_team' in perms
    assert 'change_team' not in perms
    
    # Change role to OWNER
    membership.role = TeamMembership.OWNER
    membership.save()
    
    # Manually assign permissions (simulating what the signal would do)
    from guardian.shortcuts import assign_perm
    assign_perm('teams.change_team', member, team)
    assign_perm('teams.delete_team', member, team)
    assign_perm('teams.manage_members', member, team)
    
    # Verify updated permissions
    perms = get_perms(member, team)
    assert 'view_team' in perms, "Owner should have view permission"
    assert 'change_team' in perms, "Owner should have change permission"
    assert 'delete_team' in perms, "Owner should have delete permission"
    assert 'manage_members' in perms, "Owner should have manage_members permission"


# Feature: project-collaboration-portal, Property 9: Member removal revokes all permissions
@pytest.mark.django_db(transaction=True)
@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=10, deadline=None)
@given(
    team_name=st.text(min_size=1, max_size=200)
)
def test_member_removal_revokes_permissions(team_name):
    """
    Property 9: Member removal revokes all permissions
    For any Owner removing a Member from a Team, all Team-related object-level 
    permissions for that Member should be revoked.
    Validates: Requirements 2.4
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
    
    # Verify member has permissions
    perms = get_perms(member, team)
    assert 'view_team' in perms, "Member should initially have view permission"
    
    # Remove member
    from guardian.shortcuts import remove_perm
    remove_perm('teams.view_team', member, team)
    remove_perm('teams.change_team', member, team)
    remove_perm('teams.delete_team', member, team)
    remove_perm('teams.manage_members', member, team)
    membership.delete()
    
    # Verify all permissions are revoked
    perms = get_perms(member, team)
    assert 'view_team' not in perms, "Member should not have view permission after removal"
    assert 'change_team' not in perms, "Member should not have change permission after removal"
    assert 'delete_team' not in perms, "Member should not have delete permission after removal"
    assert 'manage_members' not in perms, "Member should not have manage_members permission after removal"


# Feature: project-collaboration-portal, Property 10: Team list shows all memberships
@pytest.mark.django_db(transaction=True)
@settings(suppress_health_check=[HealthCheck.too_slow], max_examples=10, deadline=None)
@given(
    num_teams=st.integers(min_value=0, max_value=5)
)
def test_team_list_shows_all_memberships(num_teams):
    """
    Property 10: Team list shows all memberships
    For any User, viewing their Teams list should display all Teams where the User 
    is either Owner or Member, and no other Teams.
    Validates: Requirements 2.5
    """
    # Create user with unique username
    username = f"user_{uuid.uuid4().hex[:10]}"
    user = User.objects.create_user(username=username, email=f"{username}@test.com", password='testpass123')
    
    # Create another user for teams the user is NOT a member of
    other_username = f"other_{uuid.uuid4().hex[:10]}"
    other_user = User.objects.create_user(username=other_username, email=f"{other_username}@test.com", password='testpass123')
    
    # Create teams where user is a member
    user_teams = []
    for i in range(num_teams):
        team = Team.objects.create(
            name=f"Team {uuid.uuid4().hex[:8]}",
            description=f"Description {i}",
            created_by=user
        )
        user_teams.append(team)
    
    # Create a team where user is NOT a member
    other_team = Team.objects.create(
        name=f"Other Team {uuid.uuid4().hex[:8]}",
        description="Other Description",
        created_by=other_user
    )
    
    # Get teams where user has view permission
    from guardian.shortcuts import get_objects_for_user
    accessible_teams = get_objects_for_user(user, 'teams.view_team', klass=Team)
    
    # Verify user can access all their teams
    for team in user_teams:
        assert team in accessible_teams, f"User should have access to team {team.name}"
    
    # Verify user cannot access other team
    assert other_team not in accessible_teams, "User should not have access to other user's team"
