"""
Django management command to populate the database with seed data.
Usage: python manage.py seed_data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from apps.teams.models import Team, TeamMembership
from apps.tasks.models import Task, Comment, ActivityLog
from apps.notifications.models import Notification


class Command(BaseCommand):
    help = 'Populate the database with seed data for demonstration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            self.clear_data()

        self.stdout.write(self.style.SUCCESS('Starting to seed database...'))
        
        # Create users
        users = self.create_users()
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(users)} users'))
        
        # Create teams
        teams = self.create_teams(users)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(teams)} teams'))
        
        # Create tasks
        tasks = self.create_tasks(teams, users)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(tasks)} tasks'))
        
        # Create comments
        comments = self.create_comments(tasks, users)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(comments)} comments'))
        
        # Create notifications
        notifications = self.create_notifications(users, tasks, comments)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(notifications)} notifications'))
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write('\nDemo Users Created:')
        self.stdout.write('  Username: admin | Password: admin123')
        self.stdout.write('  Username: john  | Password: john123')
        self.stdout.write('  Username: sarah | Password: sarah123')
        self.stdout.write('  Username: mike  | Password: mike123')
        self.stdout.write('  Username: emma  | Password: emma123')
        self.stdout.write('\nYou can now login with any of these accounts!')

    def clear_data(self):
        """Clear existing data (except superusers)"""
        User.objects.filter(is_superuser=False).delete()
        Team.objects.all().delete()
        Task.objects.all().delete()
        Comment.objects.all().delete()
        Notification.objects.all().delete()
        ActivityLog.objects.all().delete()

    def create_users(self):
        """Create demo users"""
        users_data = [
            {
                'username': 'admin',
                'email': 'admin@example.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'password': 'admin123',
                'is_staff': True,
            },
            {
                'username': 'john',
                'email': 'john@example.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'password': 'john123',
            },
            {
                'username': 'sarah',
                'email': 'sarah@example.com',
                'first_name': 'Sarah',
                'last_name': 'Johnson',
                'password': 'sarah123',
            },
            {
                'username': 'mike',
                'email': 'mike@example.com',
                'first_name': 'Mike',
                'last_name': 'Wilson',
                'password': 'mike123',
            },
            {
                'username': 'emma',
                'email': 'emma@example.com',
                'first_name': 'Emma',
                'last_name': 'Davis',
                'password': 'emma123',
            },
        ]

        users = []
        for user_data in users_data:
            password = user_data.pop('password')
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults=user_data
            )
            if created:
                user.set_password(password)
                user.save()
            users.append(user)

        return users

    def create_teams(self, users):
        """Create demo teams with members"""
        teams_data = [
            {
                'name': 'Web Development Team',
                'description': 'Building awesome web applications with Django and React',
                'created_by': users[0],  # admin
                'members': [users[1], users[2]],  # john, sarah
            },
            {
                'name': 'Mobile App Team',
                'description': 'Creating cross-platform mobile applications',
                'created_by': users[1],  # john
                'members': [users[2], users[3]],  # sarah, mike
            },
            {
                'name': 'DevOps Team',
                'description': 'Managing infrastructure and deployment pipelines',
                'created_by': users[2],  # sarah
                'members': [users[3], users[4]],  # mike, emma
            },
            {
                'name': 'Design Team',
                'description': 'Crafting beautiful user experiences',
                'created_by': users[3],  # mike
                'members': [users[4], users[0]],  # emma, admin
            },
        ]

        teams = []
        for team_data in teams_data:
            members = team_data.pop('members')
            team, created = Team.objects.get_or_create(
                name=team_data['name'],
                defaults=team_data
            )
            
            if created:
                # Add members to team
                for member in members:
                    TeamMembership.objects.get_or_create(
                        team=team,
                        user=member,
                        defaults={'role': TeamMembership.MEMBER}
                    )
            
            teams.append(team)

        return teams

    def create_tasks(self, teams, users):
        """Create demo tasks"""
        tasks_data = [
            # Web Development Team tasks
            {
                'title': 'Implement User Authentication',
                'description': 'Set up Django authentication system with login, logout, and registration functionality.',
                'team': teams[0],
                'created_by': users[0],
                'assigned_to': users[1],
                'status': Task.DONE,
                'deadline': timezone.now().date() - timedelta(days=5),
            },
            {
                'title': 'Design Database Schema',
                'description': 'Create ERD and implement Django models for the application.',
                'team': teams[0],
                'created_by': users[0],
                'assigned_to': users[2],
                'status': Task.DONE,
                'deadline': timezone.now().date() - timedelta(days=3),
            },
            {
                'title': 'Build REST API Endpoints',
                'description': 'Implement RESTful API using Django REST Framework for all core features.',
                'team': teams[0],
                'created_by': users[1],
                'assigned_to': users[1],
                'status': Task.IN_PROGRESS,
                'deadline': timezone.now().date() + timedelta(days=7),
            },
            {
                'title': 'Create React Frontend',
                'description': 'Build responsive frontend using React and TailwindCSS.',
                'team': teams[0],
                'created_by': users[2],
                'assigned_to': users[2],
                'status': Task.REVIEW,
                'deadline': timezone.now().date() + timedelta(days=10),
            },
            {
                'title': 'Write Unit Tests',
                'description': 'Achieve 80% code coverage with comprehensive unit tests.',
                'team': teams[0],
                'created_by': users[0],
                'assigned_to': users[1],
                'status': Task.TODO,
                'deadline': timezone.now().date() + timedelta(days=14),
            },
            
            # Mobile App Team tasks
            {
                'title': 'Setup React Native Project',
                'description': 'Initialize React Native project with navigation and state management.',
                'team': teams[1],
                'created_by': users[1],
                'assigned_to': users[2],
                'status': Task.DONE,
                'deadline': timezone.now().date() - timedelta(days=7),
            },
            {
                'title': 'Implement Push Notifications',
                'description': 'Integrate Firebase Cloud Messaging for push notifications.',
                'team': teams[1],
                'created_by': users[1],
                'assigned_to': users[3],
                'status': Task.IN_PROGRESS,
                'deadline': timezone.now().date() + timedelta(days=5),
            },
            {
                'title': 'Design App UI/UX',
                'description': 'Create mockups and prototypes for mobile app screens.',
                'team': teams[1],
                'created_by': users[2],
                'assigned_to': users[3],
                'status': Task.REVIEW,
                'deadline': timezone.now().date() + timedelta(days=3),
            },
            
            # DevOps Team tasks
            {
                'title': 'Setup CI/CD Pipeline',
                'description': 'Configure GitHub Actions for automated testing and deployment.',
                'team': teams[2],
                'created_by': users[2],
                'assigned_to': users[3],
                'status': Task.IN_PROGRESS,
                'deadline': timezone.now().date() + timedelta(days=6),
            },
            {
                'title': 'Configure Docker Containers',
                'description': 'Create Dockerfiles and docker-compose for development and production.',
                'team': teams[2],
                'created_by': users[3],
                'assigned_to': users[4],
                'status': Task.TODO,
                'deadline': timezone.now().date() + timedelta(days=12),
            },
            {
                'title': 'Setup Monitoring and Logging',
                'description': 'Implement application monitoring using Prometheus and Grafana.',
                'team': teams[2],
                'created_by': users[2],
                'assigned_to': users[3],
                'status': Task.TODO,
                'deadline': timezone.now().date() + timedelta(days=15),
            },
            
            # Design Team tasks
            {
                'title': 'Create Design System',
                'description': 'Develop comprehensive design system with components and guidelines.',
                'team': teams[3],
                'created_by': users[3],
                'assigned_to': users[4],
                'status': Task.IN_PROGRESS,
                'deadline': timezone.now().date() + timedelta(days=8),
            },
            {
                'title': 'User Research and Testing',
                'description': 'Conduct user interviews and usability testing sessions.',
                'team': teams[3],
                'created_by': users[4],
                'assigned_to': users[0],
                'status': Task.REVIEW,
                'deadline': timezone.now().date() + timedelta(days=4),
            },
        ]

        tasks = []
        for task_data in tasks_data:
            task, created = Task.objects.get_or_create(
                title=task_data['title'],
                team=task_data['team'],
                defaults=task_data
            )
            tasks.append(task)

        return tasks

    def create_comments(self, tasks, users):
        """Create demo comments with threading"""
        comments_data = [
            # Comments on "Implement User Authentication"
            {
                'task': tasks[0],
                'author': users[1],
                'content': 'Started working on this. Planning to use Django built-in auth system.',
                'parent': None,
            },
            {
                'task': tasks[0],
                'author': users[0],
                'content': 'Great! Make sure to add password reset functionality as well.',
                'parent': None,
            },
            {
                'task': tasks[0],
                'author': users[2],
                'content': '@john Don\'t forget to implement email verification!',
                'parent': None,
            },
            
            # Comments on "Build REST API Endpoints"
            {
                'task': tasks[2],
                'author': users[1],
                'content': 'Working on the API endpoints. Should we use viewsets or APIView?',
                'parent': None,
            },
            {
                'task': tasks[2],
                'author': users[0],
                'content': 'Use viewsets for CRUD operations, they\'re more concise.',
                'parent': None,
            },
            {
                'task': tasks[2],
                'author': users[2],
                'content': 'Also, make sure to add proper pagination and filtering.',
                'parent': None,
            },
            
            # Comments on "Create React Frontend"
            {
                'task': tasks[3],
                'author': users[2],
                'content': 'Frontend is looking good! Using React hooks for state management.',
                'parent': None,
            },
            {
                'task': tasks[3],
                'author': users[1],
                'content': 'Nice work @sarah! Can you add loading states for API calls?',
                'parent': None,
            },
            
            # Comments on "Setup React Native Project"
            {
                'task': tasks[5],
                'author': users[2],
                'content': 'Project setup complete. Using React Navigation v6.',
                'parent': None,
            },
            {
                'task': tasks[5],
                'author': users[1],
                'content': 'Excellent! Let\'s move on to implementing the core features.',
                'parent': None,
            },
            
            # Comments on "Setup CI/CD Pipeline"
            {
                'task': tasks[8],
                'author': users[3],
                'content': 'Configured GitHub Actions workflow. Running tests on every PR.',
                'parent': None,
            },
            {
                'task': tasks[8],
                'author': users[2],
                'content': 'Perfect! Can you also add automatic deployment to staging?',
                'parent': None,
            },
            {
                'task': tasks[8],
                'author': users[3],
                'content': 'Sure, I\'ll add that next. Should deploy on merge to main branch.',
                'parent': None,
            },
            
            # Comments on "Create Design System"
            {
                'task': tasks[11],
                'author': users[4],
                'content': 'Started documenting the design system. Using Storybook for components.',
                'parent': None,
            },
            {
                'task': tasks[11],
                'author': users[3],
                'content': 'Great choice! Make sure to include accessibility guidelines.',
                'parent': None,
            },
        ]

        comments = []
        for comment_data in comments_data:
            comment, created = Comment.objects.get_or_create(
                task=comment_data['task'],
                author=comment_data['author'],
                content=comment_data['content'],
                defaults={'parent': comment_data['parent']}
            )
            comments.append(comment)

        # Create some threaded replies
        if len(comments) >= 3:
            reply1, _ = Comment.objects.get_or_create(
                task=comments[0].task,
                author=users[0],
                content='Thanks for the update! Keep me posted on the progress.',
                defaults={'parent': comments[0]}
            )
            comments.append(reply1)
            
            reply2, _ = Comment.objects.get_or_create(
                task=comments[3].task,
                author=users[2],
                content='I agree with using viewsets. Much cleaner code.',
                defaults={'parent': comments[4]}
            )
            comments.append(reply2)

        return comments

    def create_notifications(self, users, tasks, comments):
        """Create demo notifications"""
        from django.contrib.contenttypes.models import ContentType
        
        notifications_data = [
            {
                'recipient': users[1],
                'sender': users[0],
                'notification_type': Notification.ASSIGNMENT,
                'message': 'You have been assigned to task: Implement User Authentication',
                'content_object': tasks[0],
                'is_read': True,
            },
            {
                'recipient': users[1],
                'sender': users[2],
                'notification_type': Notification.MENTION,
                'message': 'sarah mentioned you in a comment',
                'content_object': comments[2] if len(comments) > 2 else tasks[0],
                'is_read': False,
            },
            {
                'recipient': users[2],
                'sender': users[0],
                'notification_type': Notification.ASSIGNMENT,
                'message': 'You have been assigned to task: Design Database Schema',
                'content_object': tasks[1],
                'is_read': True,
            },
            {
                'recipient': users[2],
                'sender': users[1],
                'notification_type': Notification.MENTION,
                'message': 'john mentioned you in a comment',
                'content_object': comments[7] if len(comments) > 7 else tasks[3],
                'is_read': False,
            },
            {
                'recipient': users[3],
                'sender': users[1],
                'notification_type': Notification.ASSIGNMENT,
                'message': 'You have been assigned to task: Implement Push Notifications',
                'content_object': tasks[6],
                'is_read': False,
            },
            {
                'recipient': users[4],
                'sender': users[3],
                'notification_type': Notification.ASSIGNMENT,
                'message': 'You have been assigned to task: Create Design System',
                'content_object': tasks[11],
                'is_read': False,
            },
        ]

        notifications = []
        for notif_data in notifications_data:
            content_object = notif_data.pop('content_object')
            content_type = ContentType.objects.get_for_model(content_object)
            
            notification, created = Notification.objects.get_or_create(
                recipient=notif_data['recipient'],
                sender=notif_data['sender'],
                notification_type=notif_data['notification_type'],
                content_type=content_type,
                object_id=content_object.id,
                defaults={
                    'message': notif_data['message'],
                    'is_read': notif_data['is_read'],
                }
            )
            notifications.append(notification)

        return notifications
