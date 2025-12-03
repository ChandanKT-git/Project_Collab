# API Documentation

## Overview

This document provides detailed API documentation for key functions, services, and utilities in the Project Collaboration Portal.

## Table of Contents

- [Notification Services](#notification-services)
- [Email Services](#email-services)
- [Permission Utilities](#permission-utilities)
- [Model Methods](#model-methods)
- [Template Tags](#template-tags)
- [Context Processors](#context-processors)

## Notification Services

### NotificationService

**Location**: `apps/notifications/services.py`

#### `create_notification(recipient, sender, notification_type, content_object, message)`

Creates a notification for a user.

**Parameters**:
- `recipient` (User): User who will receive the notification
- `sender` (User): User who triggered the notification
- `notification_type` (str): Type of notification ('mention', 'assignment', 'reply', etc.)
- `content_object` (Model): Related Django model instance (Task, Comment, etc.)
- `message` (str): Human-readable notification message

**Returns**: `Notification` instance

**Example**:
```python
from apps.notifications.services import NotificationService
from apps.tasks.models import Task

task = Task.objects.get(id=1)
NotificationService.create_notification(
    recipient=user,
    sender=request.user,
    notification_type='assignment',
    content_object=task,
    message=f'You have been assigned to task: {task.title}'
)
```

#### `parse_mentions(text, team)`

Extracts @username mentions from text and validates them against team membership.

**Parameters**:
- `text` (str): Text content containing @username mentions
- `team` (Team): Team instance to validate mentions against

**Returns**: `list[User]` - List of User instances who are mentioned and are team members

**Example**:
```python
from apps.notifications.services import NotificationService

comment_text = "Hey @john and @jane, please review this task"
mentioned_users = NotificationService.parse_mentions(comment_text, team)
# Returns [<User: john>, <User: jane>] if they are team members
```

**Implementation Details**:
- Uses regex pattern `r'@(\w+)'` to find mentions
- Only returns users who are members of the specified team
- Ignores mentions of users not in the team
- Case-sensitive username matching

#### `create_mention_notifications(comment)`

Creates notifications for all users mentioned in a comment.

**Parameters**:
- `comment` (Comment): Comment instance containing mentions

**Returns**: `list[Notification]` - List of created notification instances

**Example**:
```python
comment = Comment.objects.create(
    task=task,
    author=request.user,
    content="@john please review this"
)
NotificationService.create_mention_notifications(comment)
```

## Email Services

### EmailService

**Location**: `apps/notifications/services.py`

#### `send_mention_notification(notification)`

Sends an email notification when a user is mentioned in a comment.

**Parameters**:
- `notification` (Notification): Notification instance with mention details

**Returns**: `int` - Number of emails sent (0 or 1)

**Example**:
```python
from apps.notifications.services import EmailService

notification = Notification.objects.get(id=1)
EmailService.send_mention_notification(notification)
```

**Email Template**: `templates/notifications/email_mention.html`

**Email Content**:
- Subject: "You were mentioned in a comment"
- Body: Includes task title, comment excerpt, and link to task
- Sender: `DEFAULT_FROM_EMAIL` from settings

#### `send_assignment_notification(task, assigned_user)`

Sends an email notification when a task is assigned to a user.

**Parameters**:
- `task` (Task): Task instance
- `assigned_user` (User): User who was assigned to the task

**Returns**: `int` - Number of emails sent (0 or 1)

**Example**:
```python
from apps.notifications.services import EmailService

task = Task.objects.get(id=1)
EmailService.send_assignment_notification(task, user)
```

**Email Template**: `templates/notifications/email_assignment.html`

**Email Content**:
- Subject: "You have been assigned to a task"
- Body: Includes task title, description, deadline, and link
- Sender: `DEFAULT_FROM_EMAIL` from settings

#### `send_batch_notification(user, notifications)`

Sends a batched email containing multiple notifications.

**Parameters**:
- `user` (User): User receiving the batch
- `notifications` (QuerySet): QuerySet of Notification instances

**Returns**: `int` - Number of emails sent (0 or 1)

**Example**:
```python
from apps.notifications.services import EmailService
from apps.notifications.models import Notification

notifications = Notification.objects.filter(
    recipient=user,
    is_read=False,
    created_at__gte=five_minutes_ago
)
EmailService.send_batch_notification(user, notifications)
```

**Email Template**: `templates/notifications/email_batch.html`

## Permission Utilities

### Permission Functions

**Location**: `apps/core/permissions.py`

#### `check_team_permission(user, team, permission)`

Checks if a user has a specific permission on a team.

**Parameters**:
- `user` (User): User to check
- `team` (Team): Team instance
- `permission` (str): Permission string (e.g., 'view_team', 'change_team', 'delete_team')

**Returns**: `bool` - True if user has permission, False otherwise

**Example**:
```python
from apps.core.permissions import check_team_permission

if check_team_permission(request.user, team, 'change_team'):
    # User can edit the team
    pass
```

#### `assign_team_permissions(user, team, role)`

Assigns permissions to a user based on their role in a team.

**Parameters**:
- `user` (User): User to assign permissions to
- `team` (Team): Team instance
- `role` (str): Role string ('OWNER' or 'MEMBER')

**Returns**: `None`

**Example**:
```python
from apps.core.permissions import assign_team_permissions

# Assign owner permissions
assign_team_permissions(user, team, 'OWNER')

# Assign member permissions
assign_team_permissions(user, team, 'MEMBER')
```

**Permissions Assigned**:

**OWNER**:
- `view_team`
- `change_team`
- `delete_team`
- `add_member`
- `remove_member`
- `change_member_role`

**MEMBER**:
- `view_team`

#### `revoke_team_permissions(user, team)`

Revokes all team-related permissions from a user.

**Parameters**:
- `user` (User): User to revoke permissions from
- `team` (Team): Team instance

**Returns**: `None`

**Example**:
```python
from apps.core.permissions import revoke_team_permissions

# Remove user from team and revoke all permissions
revoke_team_permissions(user, team)
```

#### `check_task_permission(user, task, permission)`

Checks if a user has a specific permission on a task.

**Parameters**:
- `user` (User): User to check
- `task` (Task): Task instance
- `permission` (str): Permission string (e.g., 'view_task', 'change_task', 'delete_task')

**Returns**: `bool` - True if user has permission, False otherwise

**Example**:
```python
from apps.core.permissions import check_task_permission

if check_task_permission(request.user, task, 'change_task'):
    # User can edit the task
    pass
```

### Permission Mixins

#### `TeamPermissionMixin`

**Location**: `apps/core/permissions.py`

Mixin for views that require team-level permissions.

**Methods**:
- `get_team()`: Returns the team instance
- `check_permission(permission)`: Checks if user has permission on team

**Example**:
```python
from apps.core.permissions import TeamPermissionMixin
from django.views.generic import UpdateView

class TeamUpdateView(TeamPermissionMixin, UpdateView):
    model = Team
    required_permission = 'change_team'
    
    def dispatch(self, request, *args, **kwargs):
        if not self.check_permission(self.required_permission):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
```

## Model Methods

### Task Model

**Location**: `apps/tasks/models.py`

#### `get_absolute_url()`

Returns the URL for the task detail page.

**Returns**: `str` - URL path

**Example**:
```python
task = Task.objects.get(id=1)
url = task.get_absolute_url()  # Returns '/tasks/1/'
```

#### `get_status_display()`

Returns the human-readable status label.

**Returns**: `str` - Status display name

**Example**:
```python
task = Task.objects.get(id=1)
status = task.get_status_display()  # Returns 'To Do', 'In Progress', etc.
```

#### `is_overdue()`

Checks if the task is past its deadline.

**Returns**: `bool` - True if task is overdue

**Example**:
```python
task = Task.objects.get(id=1)
if task.is_overdue():
    # Task is past deadline
    pass
```

### Comment Model

**Location**: `apps/tasks/models.py`

#### `get_replies()`

Returns all direct replies to this comment.

**Returns**: `QuerySet[Comment]` - Child comments

**Example**:
```python
comment = Comment.objects.get(id=1)
replies = comment.get_replies()
```

#### `get_thread()`

Returns the entire comment thread starting from this comment.

**Returns**: `QuerySet[Comment]` - All descendants

**Example**:
```python
comment = Comment.objects.get(id=1)
thread = comment.get_thread()
```

### Team Model

**Location**: `apps/teams/models.py`

#### `get_members()`

Returns all users who are members of this team.

**Returns**: `QuerySet[User]` - Team members

**Example**:
```python
team = Team.objects.get(id=1)
members = team.get_members()
```

#### `get_owners()`

Returns all users who are owners of this team.

**Returns**: `QuerySet[User]` - Team owners

**Example**:
```python
team = Team.objects.get(id=1)
owners = team.get_owners()
```

#### `is_member(user)`

Checks if a user is a member of this team.

**Parameters**:
- `user` (User): User to check

**Returns**: `bool` - True if user is a member

**Example**:
```python
team = Team.objects.get(id=1)
if team.is_member(request.user):
    # User is a team member
    pass
```

## Template Tags

### Permission Template Tags

**Location**: `apps/core/templatetags/permission_tags.py`

#### `{% has_team_permission user team permission %}`

Checks if a user has a specific permission on a team.

**Parameters**:
- `user`: User instance
- `team`: Team instance
- `permission`: Permission string

**Returns**: `bool`

**Example**:
```django
{% load permission_tags %}

{% has_team_permission request.user team 'change_team' as can_edit %}
{% if can_edit %}
    <a href="{% url 'team_update' team.id %}">Edit Team</a>
{% endif %}
```

#### `{% has_task_permission user task permission %}`

Checks if a user has a specific permission on a task.

**Parameters**:
- `user`: User instance
- `task`: Task instance
- `permission`: Permission string

**Returns**: `bool`

**Example**:
```django
{% load permission_tags %}

{% has_task_permission request.user task 'delete_task' as can_delete %}
{% if can_delete %}
    <a href="{% url 'task_delete' task.id %}">Delete Task</a>
{% endif %}
```

### Notification Template Tags

**Location**: `apps/notifications/templatetags/notification_tags.py`

#### `{% unread_notification_count user %}`

Returns the count of unread notifications for a user.

**Parameters**:
- `user`: User instance

**Returns**: `int`

**Example**:
```django
{% load notification_tags %}

<span class="badge">{% unread_notification_count request.user %}</span>
```

## Context Processors

### Notification Count

**Location**: `apps/notifications/context_processors.py`

#### `notification_count(request)`

Adds unread notification count to template context.

**Parameters**:
- `request`: HttpRequest instance

**Returns**: `dict` - Context dictionary with `unread_notification_count`

**Usage**: Automatically available in all templates

**Example**:
```django
<!-- In any template -->
<span class="notification-badge">{{ unread_notification_count }}</span>
```

## Signal Handlers

### Task Signals

**Location**: `apps/tasks/models.py`

#### `post_save` - Task Creation

Triggered when a task is created.

**Actions**:
- Creates activity log entry
- Sends assignment notification if task is assigned

#### `post_save` - Task Update

Triggered when a task is updated.

**Actions**:
- Creates activity log entry with changed fields
- Sends assignment notification if assignee changed

### Comment Signals

**Location**: `apps/tasks/models.py`

#### `post_save` - Comment Creation

Triggered when a comment is created.

**Actions**:
- Creates activity log entry
- Parses mentions and creates notifications
- Sends email notifications to mentioned users

## Error Handling

### Custom Exceptions

#### `PermissionDeniedError`

Raised when a user attempts an action without proper permissions.

**Example**:
```python
from django.core.exceptions import PermissionDenied

if not user.has_perm('view_team', team):
    raise PermissionDenied("You don't have permission to view this team")
```

### Error Responses

All views return appropriate HTTP status codes:

- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid form data
- `403 Forbidden`: Permission denied
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

## Testing Utilities

### Test Fixtures

**Location**: `apps/core/test_setup.py`

#### `create_test_user(username, email, password)`

Creates a test user.

**Example**:
```python
from apps.core.test_setup import create_test_user

user = create_test_user('testuser', 'test@example.com', 'password123')
```

#### `create_test_team(name, owner)`

Creates a test team.

**Example**:
```python
from apps.core.test_setup import create_test_team

team = create_test_team('Test Team', owner_user)
```

#### `create_test_task(title, team, creator)`

Creates a test task.

**Example**:
```python
from apps.core.test_setup import create_test_task

task = create_test_task('Test Task', team, user)
```

## Best Practices

### Using Services

Always use service classes for business logic:

```python
# Good
from apps.notifications.services import NotificationService
NotificationService.create_notification(...)

# Bad - Don't put business logic in views
notification = Notification.objects.create(...)
```

### Permission Checks

Always check permissions before allowing actions:

```python
# In views
from apps.core.permissions import check_team_permission

if not check_team_permission(request.user, team, 'change_team'):
    raise PermissionDenied

# In templates
{% has_team_permission request.user team 'change_team' as can_edit %}
```

### Error Handling

Always handle exceptions gracefully:

```python
from django.core.exceptions import ObjectDoesNotExist

try:
    task = Task.objects.get(id=task_id)
except ObjectDoesNotExist:
    messages.error(request, 'Task not found')
    return redirect('task_list')
```

## Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [django-guardian Documentation](https://django-guardian.readthedocs.io/)
- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [pytest-django Documentation](https://pytest-django.readthedocs.io/)
