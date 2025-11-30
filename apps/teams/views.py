from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from guardian.shortcuts import get_objects_for_user, remove_perm
from .models import Team, TeamMembership
from .forms import TeamForm, AddMemberForm, ChangeMemberRoleForm


@login_required
def team_list(request):
    """Display all teams where the user is a member or owner."""
    # Get teams where user has view permission
    teams = get_objects_for_user(request.user, 'teams.view_team', klass=Team)
    
    context = {
        'teams': teams
    }
    return render(request, 'teams/team_list.html', context)


@login_required
def team_create(request):
    """Create a new team."""
    if request.method == 'POST':
        form = TeamForm(request.POST)
        if form.is_valid():
            try:
                team = form.save(commit=False)
                team.created_by = request.user
                team.save()
                messages.success(request, f'Team "{team.name}" created successfully!')
                return redirect('team_detail', pk=team.pk)
            except Exception as e:
                messages.error(request, 'An error occurred while creating the team. Please try again.')
                # Log the error
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Team creation error by user {request.user.username}: {str(e)}', exc_info=True)
        else:
            # Add user-friendly error messages
            if form.errors:
                messages.error(request, 'Please correct the errors in the form.')
    else:
        form = TeamForm()
    
    context = {
        'form': form
    }
    return render(request, 'teams/team_form.html', context)


@login_required
def team_detail(request, pk):
    """Display team details and member list."""
    team = get_object_or_404(Team, pk=pk)
    
    # Check if user has permission to view this team
    if not request.user.has_perm('teams.view_team', team):
        messages.error(request, 'You do not have permission to view this team.')
        return redirect('team_list')
    
    memberships = team.memberships.select_related('user').all()
    can_manage = request.user.has_perm('teams.manage_members', team)
    can_edit = request.user.has_perm('teams.change_team', team)
    
    context = {
        'team': team,
        'memberships': memberships,
        'can_manage': can_manage,
        'can_edit': can_edit
    }
    return render(request, 'teams/team_detail.html', context)


@login_required
def team_update(request, pk):
    """Update team details (owner only)."""
    team = get_object_or_404(Team, pk=pk)
    
    # Check if user has permission to change this team
    if not request.user.has_perm('teams.change_team', team):
        messages.error(request, 'You do not have permission to edit this team.')
        return redirect('team_detail', pk=team.pk)
    
    if request.method == 'POST':
        form = TeamForm(request.POST, instance=team)
        if form.is_valid():
            form.save()
            messages.success(request, f'Team "{team.name}" updated successfully!')
            return redirect('team_detail', pk=team.pk)
    else:
        form = TeamForm(instance=team)
    
    context = {
        'form': form,
        'team': team,
        'is_update': True
    }
    return render(request, 'teams/team_form.html', context)


@login_required
def team_delete(request, pk):
    """Delete a team (owner only)."""
    team = get_object_or_404(Team, pk=pk)
    
    # Check if user has permission to delete this team
    if not request.user.has_perm('teams.delete_team', team):
        messages.error(request, 'You do not have permission to delete this team.')
        return redirect('team_detail', pk=team.pk)
    
    if request.method == 'POST':
        team_name = team.name
        team.delete()
        messages.success(request, f'Team "{team_name}" deleted successfully!')
        return redirect('team_list')
    
    context = {
        'team': team
    }
    return render(request, 'teams/team_confirm_delete.html', context)


@login_required
def add_member(request, pk):
    """Add a member to a team."""
    team = get_object_or_404(Team, pk=pk)
    
    # Check if user has permission to manage members
    if not request.user.has_perm('teams.manage_members', team):
        messages.error(request, 'You do not have permission to manage team members.')
        return redirect('team_detail', pk=team.pk)
    
    if request.method == 'POST':
        form = AddMemberForm(request.POST, team=team)
        if form.is_valid():
            user = form.cleaned_data['username']
            role = form.cleaned_data['role']
            TeamMembership.objects.create(team=team, user=user, role=role)
            messages.success(request, f'User "{user.username}" added to team successfully!')
            return redirect('team_detail', pk=team.pk)
    else:
        form = AddMemberForm(team=team)
    
    context = {
        'form': form,
        'team': team
    }
    return render(request, 'teams/add_member.html', context)


@login_required
def remove_member(request, pk, user_id):
    """Remove a member from a team."""
    team = get_object_or_404(Team, pk=pk)
    
    # Check if user has permission to manage members
    if not request.user.has_perm('teams.manage_members', team):
        messages.error(request, 'You do not have permission to manage team members.')
        return redirect('team_detail', pk=team.pk)
    
    membership = get_object_or_404(TeamMembership, team=team, user_id=user_id)
    
    # Prevent removing the last owner
    if membership.role == TeamMembership.OWNER:
        owner_count = TeamMembership.objects.filter(team=team, role=TeamMembership.OWNER).count()
        if owner_count <= 1:
            messages.error(request, 'Cannot remove the last owner of the team.')
            return redirect('team_detail', pk=team.pk)
    
    if request.method == 'POST':
        username = membership.user.username
        user = membership.user
        
        # Remove all permissions
        remove_perm('teams.view_team', user, team)
        remove_perm('teams.change_team', user, team)
        remove_perm('teams.delete_team', user, team)
        remove_perm('teams.manage_members', user, team)
        
        membership.delete()
        messages.success(request, f'User "{username}" removed from team successfully!')
        return redirect('team_detail', pk=team.pk)
    
    context = {
        'team': team,
        'membership': membership
    }
    return render(request, 'teams/remove_member_confirm.html', context)


@login_required
def change_member_role(request, pk, user_id):
    """Change a member's role."""
    team = get_object_or_404(Team, pk=pk)
    
    # Check if user has permission to manage members
    if not request.user.has_perm('teams.manage_members', team):
        messages.error(request, 'You do not have permission to manage team members.')
        return redirect('team_detail', pk=team.pk)
    
    membership = get_object_or_404(TeamMembership, team=team, user_id=user_id)
    old_role = membership.role
    
    if request.method == 'POST':
        form = ChangeMemberRoleForm(request.POST, instance=membership)
        if form.is_valid():
            new_role = form.cleaned_data['role']
            
            # Prevent changing the last owner to member
            if old_role == TeamMembership.OWNER and new_role == TeamMembership.MEMBER:
                owner_count = TeamMembership.objects.filter(team=team, role=TeamMembership.OWNER).count()
                if owner_count <= 1:
                    messages.error(request, 'Cannot change the role of the last owner.')
                    return redirect('team_detail', pk=team.pk)
            
            membership = form.save()
            
            # Update permissions based on new role
            if new_role == TeamMembership.OWNER:
                from guardian.shortcuts import assign_perm
                assign_perm('teams.change_team', membership.user, team)
                assign_perm('teams.delete_team', membership.user, team)
                assign_perm('teams.manage_members', membership.user, team)
            else:
                # Remove owner permissions
                remove_perm('teams.change_team', membership.user, team)
                remove_perm('teams.delete_team', membership.user, team)
                remove_perm('teams.manage_members', membership.user, team)
            
            messages.success(request, f'Role updated for "{membership.user.username}" successfully!')
            return redirect('team_detail', pk=team.pk)
    else:
        form = ChangeMemberRoleForm(instance=membership)
    
    context = {
        'form': form,
        'team': team,
        'membership': membership
    }
    return render(request, 'teams/change_role.html', context)
