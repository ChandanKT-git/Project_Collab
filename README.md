# Project Collaboration Portal

A Django-based web application for team collaboration, task management, and project tracking. Built with Django 4.2+, django-guardian for object-level permissions, and TailwindCSS for responsive UI design.

## Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [User Guide](#user-guide)
- [API Documentation](#api-documentation)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Features

### Core Functionality

- **User Authentication**: Secure signup, login, and logout with Django's built-in authentication
- **Team Management**: Create teams, invite members, assign roles (Owner/Member)
- **Task Management**: Create, update, delete, and track tasks with status workflow
- **Threaded Comments**: Add comments to tasks with support for nested replies
- **File Uploads**: Attach files to tasks and comments with automatic cleanup
- **@Mention Notifications**: Mention team members in comments to notify them
- **Activity Logging**: Automatic tracking of all task-related actions
- **Email Notifications**: Receive emails for mentions and task assignments
- **Role-Based Permissions**: Object-level permissions using django-guardian
- **Admin Dashboard**: Comprehensive admin interface for system management

### Security Features

- CSRF protection on all forms
- Password validation and hashing
- Object-level permission checks
- SQL injection protection via Django ORM
- XSS protection with template auto-escaping
- File upload validation

## Technology Stack

- **Backend Framework**: Django 4.2+
- **Database**: SQLite (development), PostgreSQL (production-ready)
- **ORM**: Django ORM
- **Permissions**: django-guardian 2.4+ for object-level permissions
- **Frontend**: TailwindCSS (CDN for development)
- **Testing**: pytest 7.4+, pytest-django 4.5+, Hypothesis 6.82+
- **Email**: Django email backend (console for dev, SMTP for production)
- **File Storage**: Django FileField (local for dev, S3-compatible for production)

## Prerequisites

- **Python**: 3.8 or higher
- **pip**: Python package installer
- **Virtual Environment**: Recommended (venv or virtualenv)
- **Git**: For version control
- **PostgreSQL**: Optional for production (SQLite used by default)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd project-collaboration-portal
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Database

```bash
# Run migrations to create database tables
python manage.py migrate

# Create a superuser account for admin access
python manage.py createsuperuser
```

Follow the prompts to create your admin account.

### 5. Collect Static Files (Production Only)

```bash
python manage.py collectstatic
```

## Configuration

### Environment Variables

For production deployment, configure the following environment variables:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SECRET_KEY` | Django secret key for cryptographic signing | Auto-generated | Yes (Production) |
| `DEBUG` | Enable/disable debug mode | `True` | Yes |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts | `[]` | Yes (Production) |
| `DATABASE_URL` | PostgreSQL connection string | SQLite | No |
| `EMAIL_HOST` | SMTP server hostname | `smtp.gmail.com` | No |
| `EMAIL_PORT` | SMTP server port | `587` | No |
| `EMAIL_HOST_USER` | SMTP username | Empty | No |
| `EMAIL_HOST_PASSWORD` | SMTP password | Empty | No |
| `EMAIL_USE_TLS` | Use TLS for email | `True` | No |
| `DEFAULT_FROM_EMAIL` | Default sender email | `noreply@projectportal.com` | No |
| `MEDIA_ROOT` | Path for uploaded files | `media/` | No |
| `STATIC_ROOT` | Path for collected static files | `staticfiles/` | No |

### Development Settings

The default `config/settings.py` is configured for development:

- **DEBUG**: `True`
- **Database**: SQLite (`db.sqlite3`)
- **Email Backend**: Console (prints emails to terminal)
- **Static Files**: Served by Django development server
- **Secret Key**: Insecure default (change for production)

### Production Settings

For production, create a `.env` file or set environment variables:

```bash
# Example .env file
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

**Important**: Never commit `.env` files or expose secret keys in version control.

## Running the Application

### Development Server

```bash
# Start the Django development server
python manage.py runserver

# Access the application at:
# http://localhost:8000
```

### Admin Dashboard

Access the admin interface at `http://localhost:8000/admin/` using your superuser credentials.

### Creating Test Data

```bash
# Create test users, teams, and tasks via Django shell
python manage.py shell

# Example:
from django.contrib.auth.models import User
from apps.teams.models import Team

user = User.objects.create_user('testuser', 'test@example.com', 'password123')
team = Team.objects.create(name='Test Team', description='A test team', created_by=user)
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest apps/tasks/test_properties.py

# Run specific test function
pytest apps/tasks/test_properties.py::test_task_creation_persists

# Run with coverage report
pytest --cov=apps --cov-report=html

# Run only property-based tests
pytest -k "property" -v
```

### Test Configuration

The project uses `pytest.ini` for test configuration:

```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings
python_files = tests.py test_*.py *_tests.py
addopts = -v --tb=short
```

### Testing Strategy

1. **Unit Tests**: Test individual functions, methods, and components
2. **Property-Based Tests**: Use Hypothesis to test universal properties across random inputs
3. **Integration Tests**: Test complete workflows and interactions between components

### Property-Based Testing

The project uses Hypothesis for property-based testing. Each property test validates a correctness property from the design document:

```python
# Example property test
from hypothesis import given, strategies as st

# Feature: project-collaboration-portal, Property 11: Task creation persists with team association
@given(st.text(min_size=1), st.text())
def test_task_creation_persists(title, description):
    # Test implementation
    pass
```

## Project Structure

```
project_collaboration_portal/
├── apps/                           # Django applications
│   ├── accounts/                   # User authentication
│   │   ├── models.py              # User profile model
│   │   ├── views.py               # Signup, login, logout views
│   │   ├── forms.py               # Authentication forms
│   │   └── tests.py               # Unit tests
│   ├── teams/                      # Team management
│   │   ├── models.py              # Team, TeamMembership models
│   │   ├── views.py               # Team CRUD views
│   │   ├── forms.py               # Team forms
│   │   └── tests.py               # Unit tests
│   ├── tasks/                      # Task and comment management
│   │   ├── models.py              # Task, Comment, FileUpload, ActivityLog
│   │   ├── views.py               # Task CRUD, comment, file upload views
│   │   ├── forms.py               # Task and comment forms
│   │   ├── tests.py               # Unit tests
│   │   └── test_properties.py    # Property-based tests
│   ├── notifications/              # Notification system
│   │   ├── models.py              # Notification model
│   │   ├── services.py            # NotificationService, EmailService
│   │   ├── views.py               # Notification list, mark read
│   │   ├── context_processors.py # Notification count for navbar
│   │   ├── tests.py               # Unit tests
│   │   └── test_properties.py    # Property-based tests
│   └── core/                       # Shared utilities
│       ├── permissions.py         # Permission mixins and utilities
│       ├── views.py               # Base views and home page
│       ├── error_handlers.py      # Custom error handlers
│       └── templatetags/          # Custom template tags
├── config/                         # Django project configuration
│   ├── settings.py                # Django settings
│   ├── urls.py                    # URL routing
│   ├── wsgi.py                    # WSGI configuration
│   └── asgi.py                    # ASGI configuration
├── templates/                      # HTML templates
│   ├── base.html                  # Base template with navbar
│   ├── home.html                  # Dashboard/home page
│   ├── accounts/                  # Authentication templates
│   ├── teams/                     # Team templates
│   ├── tasks/                     # Task templates
│   ├── notifications/             # Notification templates
│   └── *.html                     # Error pages (400, 403, 404, 500)
├── static/                         # Static files (CSS, JS, images)
├── media/                          # User-uploaded files
├── logs/                           # Application logs
├── manage.py                       # Django management script
├── pytest.ini                      # Pytest configuration
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

## User Guide

### Getting Started

1. **Sign Up**: Create an account at `/accounts/signup/`
2. **Log In**: Access your account at `/accounts/login/`
3. **Create a Team**: Navigate to Teams → Create Team
4. **Invite Members**: Add team members by username
5. **Create Tasks**: Within a team, create tasks with descriptions and deadlines
6. **Collaborate**: Add comments, upload files, and mention team members

### User Roles

#### Team Owner
- Full administrative control over the team
- Can add/remove members
- Can assign roles to members
- Can update team details
- Can delete the team
- Has all permissions on team tasks

#### Team Member
- Can view team details and members
- Can create tasks within the team
- Can view and comment on tasks
- Can upload files to tasks
- Permissions depend on role assignment

### Key Features

#### Creating a Team

1. Click "Teams" in the navigation bar
2. Click "Create Team"
3. Enter team name and description
4. Click "Create"
5. You are automatically assigned as the team owner

#### Managing Team Members

1. Navigate to your team's detail page
2. Click "Add Member"
3. Enter the username of the user to invite
4. Select their role (Member or Owner)
5. Click "Add"

To remove a member:
1. Navigate to team detail page
2. Click "Remove" next to the member's name
3. Confirm the removal

#### Creating Tasks

1. Navigate to a team
2. Click "Create Task"
3. Fill in:
   - Title (required)
   - Description
   - Assigned to (optional)
   - Status (TODO, IN_PROGRESS, REVIEW, DONE)
   - Deadline (optional)
4. Click "Create Task"

#### Adding Comments

1. Open a task detail page
2. Scroll to the comments section
3. Type your comment
4. Use `@username` to mention team members
5. Click "Add Comment"

To reply to a comment:
1. Click "Reply" on the comment
2. Type your reply
3. Click "Submit"

#### Uploading Files

1. Open a task or comment
2. Click "Upload File"
3. Select a file from your computer
4. Click "Upload"
5. The file will be attached and available for download

#### Notifications

- View notifications by clicking the bell icon in the navbar
- Notifications are created when:
  - You are mentioned in a comment
  - A task is assigned to you
  - Someone replies to your comment
- Click a notification to view the related task
- Mark notifications as read by clicking them

#### Activity Log

Every task has an activity log showing:
- Task creation
- Status changes
- Comments added
- Files uploaded
- Assignments changed

View the activity log at the bottom of any task detail page.

## API Documentation

### Key Functions and Services

#### NotificationService

Located in `apps/notifications/services.py`

```python
class NotificationService:
    @staticmethod
    def create_notification(recipient, sender, notification_type, content_object, message):
        """
        Create a notification for a user.
        
        Args:
            recipient (User): User receiving the notification
            sender (User): User who triggered the notification
            notification_type (str): Type of notification (mention, assignment, etc.)
            content_object: Related object (Task, Comment, etc.)
            message (str): Notification message
            
        Returns:
            Notification: Created notification instance
        """
        
    @staticmethod
    def parse_mentions(text, team):
        """
        Extract @username mentions from text.
        
        Args:
            text (str): Text containing mentions
            team (Team): Team to validate mentions against
            
        Returns:
            list[User]: List of mentioned users who are team members
        """
```

#### EmailService

Located in `apps/notifications/services.py`

```python
class EmailService:
    @staticmethod
    def send_mention_notification(notification):
        """
        Send email notification for a mention.
        
        Args:
            notification (Notification): Notification instance
        """
        
    @staticmethod
    def send_assignment_notification(task, assigned_user):
        """
        Send email notification for task assignment.
        
        Args:
            task (Task): Task instance
            assigned_user (User): User assigned to the task
        """
```

#### Permission Utilities

Located in `apps/core/permissions.py`

```python
def check_team_permission(user, team, permission):
    """
    Check if user has permission on a team.
    
    Args:
        user (User): User to check
        team (Team): Team instance
        permission (str): Permission string (e.g., 'view_team')
        
    Returns:
        bool: True if user has permission
    """

def assign_team_permissions(user, team, role):
    """
    Assign permissions to user based on role.
    
    Args:
        user (User): User to assign permissions to
        team (Team): Team instance
        role (str): Role (OWNER or MEMBER)
    """
```

### Models

#### Task Model

```python
class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(User, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    deadline = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

#### Comment Model

```python
class Comment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
```

## Deployment

For comprehensive deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

### Quick Deployment Guide

#### Prerequisites
- Python 3.9+
- PostgreSQL database
- SMTP email service
- Domain name (optional)

#### Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your production values
   ```

3. **Run deployment script**:
   ```bash
   # Linux/Mac
   chmod +x deploy.sh
   ./deploy.sh
   
   # Windows
   deploy.bat
   ```

4. **Check deployment readiness**:
   ```bash
   python manage.py check_deployment
   ```

5. **Create superuser**:
   ```bash
   python manage.py createsuperuser
   ```

6. **Start production server**:
   ```bash
   gunicorn config.wsgi:application --bind 0.0.0.0:8000
   ```

### Deployment Platforms

The application is ready to deploy to:
- **Railway**: See `railway.json` configuration
- **PythonAnywhere**: Traditional hosting with WSGI
- **Heroku**: See `Procfile` configuration
- **VPS**: DigitalOcean, AWS, etc. with Nginx + Gunicorn

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DB_NAME=project_portal_db
DB_USER=postgres
DB_PASSWORD=your-password
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Configure `SECRET_KEY` (generate new)
- [ ] Set `ALLOWED_HOSTS`
- [ ] Configure PostgreSQL database
- [ ] Set up SMTP email
- [ ] Run `python manage.py migrate`
- [ ] Run `python manage.py collectstatic`
- [ ] Create superuser
- [ ] Enable HTTPS
- [ ] Run `python manage.py check_deployment`

For detailed deployment instructions, troubleshooting, and platform-specific guides, see [DEPLOYMENT.md](DEPLOYMENT.md).

## Troubleshooting

### Common Issues

#### Database Errors

**Problem**: `django.db.utils.OperationalError: no such table`

**Solution**: Run migrations
```bash
python manage.py migrate
```

#### Static Files Not Loading

**Problem**: CSS/JS files not loading in production

**Solution**: Collect static files
```bash
python manage.py collectstatic --noinput
```

#### Permission Denied Errors

**Problem**: `PermissionDenied` when accessing resources

**Solution**: Check object-level permissions
```python
# In Django shell
from guardian.shortcuts import assign_perm
assign_perm('view_team', user, team)
```

#### Email Not Sending

**Problem**: Emails not being sent

**Solution**: Check email configuration
- Verify `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD`
- For Gmail, use an App Password (not your regular password)
- Check spam folder
- Review logs for email errors

#### File Upload Errors

**Problem**: File uploads failing

**Solution**: 
- Check `MEDIA_ROOT` directory exists and is writable
- Verify file size limits in settings
- Check disk space

### Debug Mode

Enable debug mode for detailed error messages (development only):

```python
# config/settings.py
DEBUG = True
```

### Logging

Check application logs:

```bash
# View error log
cat logs/errors.log

# View Django logs (if using console handler)
python manage.py runserver
```

## Contributing

### Development Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Write tests for new functionality
5. Run tests: `pytest`
6. Commit changes: `git commit -m "Add your feature"`
7. Push to branch: `git push origin feature/your-feature`
8. Create a Pull Request

### Code Style

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions small and focused
- Write tests for new features

### Testing Requirements

- All new features must include unit tests
- Property-based tests for universal properties
- Maintain test coverage above 80%
- All tests must pass before merging

## License

All rights reserved. This project is proprietary software.

## Support

For issues, questions, or contributions, please contact the development team or open an issue in the repository.

---

**Version**: 1.0.0  
**Last Updated**: November 2025  
**Django Version**: 4.2+  
**Python Version**: 3.8+
