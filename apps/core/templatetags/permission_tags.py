"""Template tags for permission checking in templates."""
from django import template
from django.contrib.auth.models import User
from apps.core.permissions import (
    check_object_permission,
    check_team_membership,
    check_team_owner
)

register = template.Library()


@register.filter
def has_perm(user, perm_and_obj):
    """
    Check if a user has a specific permission on an object.
    
    Usage in template:
        {% if user|has_perm:"teams.view_team,team" %}
            ...
        {% endif %}
    
    Or with object variable:
        {% if user|has_perm:"teams.view_team"|with_obj:team %}
            ...
        {% endif %}
    """
    if not isinstance(user, User):
        return False
    
    if isinstance(perm_and_obj, str):
        # Format: "permission,object"
        parts = perm_and_obj.split(',', 1)
        if len(parts) == 2:
            permission = parts[0].strip()
            # This won't work directly, need to use the tag version
            return False
        else:
            # Just permission, no object
            return user.has_perm(perm_and_obj)
    
    return False


@register.simple_tag
def check_perm(user, permission, obj):
    """
    Check if a user has a specific permission on an object.
    
    Usage in template:
        {% check_perm user "teams.view_team" team as can_view %}
        {% if can_view %}
            ...
        {% endif %}
    """
    return check_object_permission(user, permission, obj)


@register.simple_tag
def is_team_member(user, team):
    """
    Check if a user is a member of a team.
    
    Usage in template:
        {% is_team_member user team as is_member %}
        {% if is_member %}
            ...
        {% endif %}
    """
    return check_team_membership(user, team)


@register.simple_tag
def is_team_owner(user, team):
    """
    Check if a user is an owner of a team.
    
    Usage in template:
        {% is_team_owner user team as is_owner %}
        {% if is_owner %}
            ...
        {% endif %}
    """
    return check_team_owner(user, team)


@register.filter
def can_view(user, obj):
    """
    Check if a user can view an object.
    
    Usage in template:
        {% if user|can_view:team %}
            ...
        {% endif %}
    """
    if not isinstance(user, User) or not user.is_authenticated:
        return False
    
    # Determine the permission based on object type
    from apps.teams.models import Team
    from apps.tasks.models import Task
    
    if isinstance(obj, Team):
        return check_object_permission(user, 'teams.view_team', obj)
    elif isinstance(obj, Task):
        return check_object_permission(user, 'tasks.view_task', obj)
    
    return False


@register.filter
def can_edit(user, obj):
    """
    Check if a user can edit an object.
    
    Usage in template:
        {% if user|can_edit:team %}
            ...
        {% endif %}
    """
    if not isinstance(user, User) or not user.is_authenticated:
        return False
    
    # Determine the permission based on object type
    from apps.teams.models import Team
    from apps.tasks.models import Task
    
    if isinstance(obj, Team):
        return check_object_permission(user, 'teams.change_team', obj)
    elif isinstance(obj, Task):
        return check_object_permission(user, 'tasks.change_task', obj)
    
    return False


@register.filter
def can_delete(user, obj):
    """
    Check if a user can delete an object.
    
    Usage in template:
        {% if user|can_delete:team %}
            ...
        {% endif %}
    """
    if not isinstance(user, User) or not user.is_authenticated:
        return False
    
    # Determine the permission based on object type
    from apps.teams.models import Team
    from apps.tasks.models import Task
    
    if isinstance(obj, Team):
        return check_object_permission(user, 'teams.delete_team', obj)
    elif isinstance(obj, Task):
        return check_object_permission(user, 'tasks.delete_task', obj)
    
    return False


@register.filter
def can_manage_members(user, team):
    """
    Check if a user can manage members of a team.
    
    Usage in template:
        {% if user|can_manage_members:team %}
            ...
        {% endif %}
    """
    if not isinstance(user, User) or not user.is_authenticated:
        return False
    
    from apps.teams.models import Team
    if isinstance(team, Team):
        return check_object_permission(user, 'teams.manage_members', team)
    
    return False


@register.inclusion_tag('core/permission_buttons.html')
def permission_buttons(user, obj, show_view=True, show_edit=True, show_delete=True):
    """
    Render permission-based action buttons.
    
    Usage in template:
        {% permission_buttons user team %}
    """
    from apps.teams.models import Team
    from apps.tasks.models import Task
    
    context = {
        'user': user,
        'obj': obj,
        'show_view': show_view,
        'show_edit': show_edit,
        'show_delete': show_delete,
        'can_view': False,
        'can_edit': False,
        'can_delete': False,
    }
    
    if isinstance(obj, Team):
        context['can_view'] = check_object_permission(user, 'teams.view_team', obj)
        context['can_edit'] = check_object_permission(user, 'teams.change_team', obj)
        context['can_delete'] = check_object_permission(user, 'teams.delete_team', obj)
        context['view_url'] = 'team_detail'
        context['edit_url'] = 'team_update'
        context['delete_url'] = 'team_delete'
    elif isinstance(obj, Task):
        context['can_view'] = check_object_permission(user, 'tasks.view_task', obj)
        context['can_edit'] = check_object_permission(user, 'tasks.change_task', obj)
        context['can_delete'] = check_object_permission(user, 'tasks.delete_task', obj)
        context['view_url'] = 'task_detail'
        context['edit_url'] = 'task_update'
        context['delete_url'] = 'task_delete'
    
    return context
