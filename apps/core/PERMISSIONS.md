# Permission System Documentation

This document describes the comprehensive permission system implemented for the Project Collaboration Portal.

## Overview

The permission system uses django-guardian for object-level permissions, providing fine-grained access control for teams, tasks, and other resources.

## Components

### 1. Permission Utilities (`apps/core/permissions.py`)

#### Mixins for Class-Based Views

**ObjectPermissionMixin**
- Requires object-level permissions for class-based views
- Usage:
```python
from apps.core.permissions import ObjectPermissionMixin

class MyView(ObjectPermissionMixin, DetailView):
    model = Team
    permission_required = 'teams.view_team'
    permission_denied_message = 'You do not have permission to view this team.'
```

**TeamMemberRequiredMixin**
- Requires the user to be a member of the team
- Usage:
```python
from apps.core.permissions import TeamMemberRequiredMixin

class TaskDetailView(TeamMemberRequiredMixin, DetailView):
    model = Task
    team_field = 'team'  # Field that references the team
```

#### Decorators for Function-Based Views

**require_object_permission**
```python
from apps.core.permissions import require_object_permission

@require_object_permission('teams.view_team', lambda request, pk: Team.objects.get(pk=pk))
def my_view(request, pk):
    # View logic
    pass
```

**require_team_membership**
```python
from apps.core.permissions import require_team_membership

@require_team_membership(lambda request, pk: Task.objects.get(pk=pk).team)
def my_view(request, pk):
    # View logic
    pass
```

#### Utility Functions

- `check_object_permission(user, permission, obj)` - Check if user has permission on object
- `check_team_membership(user, team)` - Check if user is a team member
- `check_team_owner(user, team)` - Check if user is a team owner
- `get_user_teams(user)` - Get all teams the user can access
- `get_user_tasks(user)` - Get all tasks the user can access

### 2. Template Tags (`apps/core/templatetags/permission_tags.py`)

Load the template tags in your template:
```django
{% load permission_tags %}
```

#### Simple Tags

**check_perm** - Check object-level permission
```django
{% check_perm user "teams.view_team" team as can_view %}
{% if can_view %}
    <a href="{% url 'team_detail' team.pk %}">View Team</a>
{% endif %}
```

**is_team_member** - Check team membership
```django
{% is_team_member user team as is_member %}
{% if is_member %}
    <p>You are a member of this team</p>
{% endif %}
```

**is_team_owner** - Check team ownership
```django
{% is_team_owner user team as is_owner %}
{% if is_owner %}
    <a href="{% url 'team_update' team.pk %}">Edit Team</a>
{% endif %}
```

#### Filters

**can_view** - Check if user can view object
```django
{% if user|can_view:team %}
    <a href="{% url 'team_detail' team.pk %}">View</a>
{% endif %}
```

**can_edit** - Check if user can edit object
```django
{% if user|can_edit:task %}
    <a href="{% url 'task_update' task.pk %}">Edit</a>
{% endif %}
```

**can_delete** - Check if user can delete object
```django
{% if user|can_delete:team %}
    <a href="{% url 'team_delete' team.pk %}">Delete</a>
{% endif %}
```

**can_manage_members** - Check if user can manage team members
```django
{% if user|can_manage_members:team %}
    <a href="{% url 'add_member' team.pk %}">Add Member</a>
{% endif %}
```

#### Inclusion Tag

**permission_buttons** - Render permission-based action buttons
```django
{% permission_buttons user team %}
```

### 3. Automatic Permission Assignment

Permissions are automatically assigned via Django signals:

#### Team Creation
When a team is created:
- Creator becomes owner with full permissions (view, change, delete, manage_members)

#### Team Membership
When a user is added to a team:
- Members get view permission
- Owners get all permissions (view, change, delete, manage_members)

#### Task Creation
When a task is created:
- All team members get view permission
- Team owners and task creator get change and delete permissions

## Permission Types

### Team Permissions
- `teams.view_team` - View team details
- `teams.change_team` - Edit team details
- `teams.delete_team` - Delete team
- `teams.manage_members` - Add/remove members, change roles

### Task Permissions
- `tasks.view_task` - View task details
- `tasks.change_task` - Edit task details
- `tasks.delete_task` - Delete task

## Best Practices

1. **Always check permissions** before allowing access to resources
2. **Use mixins for class-based views** for consistent permission checking
3. **Use decorators for function-based views** to keep code DRY
4. **Use template tags** to conditionally show/hide UI elements based on permissions
5. **Test permissions thoroughly** using property-based tests

## Testing

Property-based tests are located in `apps/core/test_permissions.py`:
- Property 22: Permission checks enforce access control
- Property 23: Permission grants apply at object level
- Property 24: Unauthorized actions are denied
- Property 25: Permission revocation takes immediate effect

Run tests with:
```bash
python -m pytest apps/core/test_permissions.py -v
```

## Examples

### Example 1: Protecting a View
```python
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from apps.core.permissions import require_object_permission
from apps.teams.models import Team

@login_required
@require_object_permission('teams.view_team', lambda request, pk: Team.objects.get(pk=pk))
def team_detail(request, pk):
    team = get_object_or_404(Team, pk=pk)
    return render(request, 'teams/team_detail.html', {'team': team})
```

### Example 2: Conditional Template Rendering
```django
{% load permission_tags %}

<div class="team-actions">
    {% if user|can_edit:team %}
        <a href="{% url 'team_update' team.pk %}" class="btn btn-primary">Edit</a>
    {% endif %}
    
    {% if user|can_manage_members:team %}
        <a href="{% url 'add_member' team.pk %}" class="btn btn-secondary">Add Member</a>
    {% endif %}
    
    {% if user|can_delete:team %}
        <a href="{% url 'team_delete' team.pk %}" class="btn btn-danger">Delete</a>
    {% endif %}
</div>
```

### Example 3: Checking Permissions in Python
```python
from apps.core.permissions import check_object_permission, check_team_owner

def my_function(user, team):
    if check_team_owner(user, team):
        # User is an owner, allow full access
        pass
    elif check_object_permission(user, 'teams.view_team', team):
        # User can view but not edit
        pass
    else:
        # User has no access
        pass
```

## Troubleshooting

### Permission Not Working
1. Check that the user is authenticated
2. Verify the permission string is correct (e.g., 'teams.view_team')
3. Ensure permissions were assigned (check via Django admin or shell)
4. Verify the object exists and is the correct type

### Signal Not Firing
1. Ensure the model is saved (signals fire on save)
2. Check that the signal handler is registered (imported in apps.py)
3. Verify no exceptions are raised in the signal handler

### Template Tag Not Found
1. Ensure you've loaded the template tags: `{% load permission_tags %}`
2. Verify the template tag file is in the correct location
3. Restart the development server after adding new template tags
