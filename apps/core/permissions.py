"""Permission utilities and mixins for the Project Collaboration Portal."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from functools import wraps


class ObjectPermissionMixin(LoginRequiredMixin):
    """
    Mixin for class-based views that require object-level permissions.
    
    Usage:
        class MyView(ObjectPermissionMixin, DetailView):
            model = MyModel
            permission_required = 'app.view_mymodel'
            permission_denied_message = 'You do not have permission to view this object.'
    """
    permission_required = None
    permission_denied_message = 'You do not have permission to access this resource.'
    redirect_on_denied = True
    
    def get_permission_required(self):
        """Get the permission required for this view."""
        if self.permission_required is None:
            raise NotImplementedError(
                f'{self.__class__.__name__} is missing the permission_required attribute. '
                'Define {0}.permission_required, or override '
                '{0}.get_permission_required().'.format(self.__class__.__name__)
            )
        return self.permission_required
    
    def get_permission_object(self):
        """Get the object to check permissions against."""
        return self.get_object()
    
    def has_permission(self):
        """Check if the user has the required permission on the object."""
        obj = self.get_permission_object()
        permission = self.get_permission_required()
        return self.request.user.has_perm(permission, obj)
    
    def handle_no_permission(self):
        """Handle the case when the user doesn't have permission."""
        if self.redirect_on_denied:
            messages.error(self.request, self.permission_denied_message)
            return redirect('home')
        else:
            raise PermissionDenied(self.permission_denied_message)
    
    def dispatch(self, request, *args, **kwargs):
        """Check permissions before dispatching the view."""
        if not self.has_permission():
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class TeamMemberRequiredMixin(LoginRequiredMixin):
    """
    Mixin that requires the user to be a member of the team.
    
    Usage:
        class MyView(TeamMemberRequiredMixin, DetailView):
            model = Task
            team_field = 'team'  # Field name that references the team
    """
    team_field = 'team'
    permission_denied_message = 'You must be a member of this team to access this resource.'
    
    def get_team(self):
        """Get the team object from the view's object."""
        obj = self.get_object()
        return getattr(obj, self.team_field)
    
    def is_team_member(self):
        """Check if the user is a member of the team."""
        from apps.teams.models import TeamMembership
        team = self.get_team()
        return TeamMembership.objects.filter(team=team, user=self.request.user).exists()
    
    def dispatch(self, request, *args, **kwargs):
        """Check team membership before dispatching the view."""
        if not self.is_team_member():
            messages.error(self.request, self.permission_denied_message)
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)


def require_object_permission(permission, get_object_func=None, redirect_url='home'):
    """
    Decorator for function-based views that require object-level permissions.
    
    Args:
        permission: The permission string (e.g., 'teams.view_team')
        get_object_func: Function to get the object from request/args/kwargs
        redirect_url: URL to redirect to if permission is denied
    
    Usage:
        @require_object_permission('teams.view_team', lambda request, pk: Team.objects.get(pk=pk))
        def my_view(request, pk):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'You must be logged in to access this resource.')
                return redirect('login')
            
            if get_object_func:
                obj = get_object_func(request, *args, **kwargs)
                if not request.user.has_perm(permission, obj):
                    messages.error(request, 'You do not have permission to access this resource.')
                    return redirect(redirect_url)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_team_membership(get_team_func, redirect_url='home'):
    """
    Decorator for function-based views that require team membership.
    
    Args:
        get_team_func: Function to get the team from request/args/kwargs
        redirect_url: URL to redirect to if not a team member
    
    Usage:
        @require_team_membership(lambda request, pk: Task.objects.get(pk=pk).team)
        def my_view(request, pk):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'You must be logged in to access this resource.')
                return redirect('login')
            
            from apps.teams.models import TeamMembership
            team = get_team_func(request, *args, **kwargs)
            
            if not TeamMembership.objects.filter(team=team, user=request.user).exists():
                messages.error(request, 'You must be a member of this team to access this resource.')
                return redirect(redirect_url)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def check_object_permission(user, permission, obj):
    """
    Utility function to check if a user has a specific permission on an object.
    
    Args:
        user: The user to check permissions for
        permission: The permission string (e.g., 'teams.view_team')
        obj: The object to check permissions against
    
    Returns:
        bool: True if the user has the permission, False otherwise
    """
    if not user.is_authenticated:
        return False
    return user.has_perm(permission, obj)


def check_team_membership(user, team):
    """
    Utility function to check if a user is a member of a team.
    
    Args:
        user: The user to check
        team: The team to check membership for
    
    Returns:
        bool: True if the user is a member, False otherwise
    """
    if not user.is_authenticated:
        return False
    
    from apps.teams.models import TeamMembership
    return TeamMembership.objects.filter(team=team, user=user).exists()


def check_team_owner(user, team):
    """
    Utility function to check if a user is an owner of a team.
    
    Args:
        user: The user to check
        team: The team to check ownership for
    
    Returns:
        bool: True if the user is an owner, False otherwise
    """
    if not user.is_authenticated:
        return False
    
    from apps.teams.models import TeamMembership
    return TeamMembership.objects.filter(
        team=team, 
        user=user, 
        role=TeamMembership.OWNER
    ).exists()


def get_user_teams(user):
    """
    Get all teams where the user is a member.
    
    Args:
        user: The user to get teams for
    
    Returns:
        QuerySet: Teams where the user is a member
    """
    if not user.is_authenticated:
        from apps.teams.models import Team
        return Team.objects.none()
    
    from guardian.shortcuts import get_objects_for_user
    from apps.teams.models import Team
    return get_objects_for_user(user, 'teams.view_team', klass=Team)


def get_user_tasks(user):
    """
    Get all tasks the user has access to.
    
    Args:
        user: The user to get tasks for
    
    Returns:
        QuerySet: Tasks the user can access
    """
    if not user.is_authenticated:
        from apps.tasks.models import Task
        return Task.objects.none()
    
    from apps.teams.models import Team
    from apps.tasks.models import Task
    
    # Get all teams where user is a member
    user_teams = Team.objects.filter(memberships__user=user)
    
    # Get all tasks from those teams
    return Task.objects.filter(team__in=user_teams)
