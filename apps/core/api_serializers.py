"""
REST API Serializers for CollabHub.

Provides serialization for all models: User, Profile, Team, TeamMembership,
Task, Comment, FileUpload, ActivityLog, and Notification.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from apps.accounts.models import Profile
from apps.teams.models import Team, TeamMembership
from apps.tasks.models import Task, Comment, FileUpload, ActivityLog
from apps.notifications.models import Notification


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name']
        read_only_fields = ['id', 'username', 'email']

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class UserMinimalSerializer(serializers.ModelSerializer):
    """Minimal user serializer for nested representations."""
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'full_name']

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class ProfileSerializer(serializers.ModelSerializer):
    """Serializer for Profile model."""
    class Meta:
        model = Profile
        fields = ['bio']


class SignupSerializer(serializers.Serializer):
    """Serializer for user registration."""
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password1 = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('A user with this username already exists.')
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value

    def validate(self, data):
        if data['password1'] != data['password2']:
            raise serializers.ValidationError({'password2': 'Passwords do not match.'})
        return data

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password1'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


# --- Teams ---

class TeamMembershipSerializer(serializers.ModelSerializer):
    """Serializer for TeamMembership model."""
    user = UserMinimalSerializer(read_only=True)

    class Meta:
        model = TeamMembership
        fields = ['id', 'user', 'role', 'joined_at']
        read_only_fields = ['id', 'joined_at']


class TeamListSerializer(serializers.ModelSerializer):
    """Serializer for Team list view."""
    created_by = UserMinimalSerializer(read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = ['id', 'name', 'description', 'created_at', 'created_by', 'member_count']
        read_only_fields = ['id', 'created_at', 'created_by']

    def get_member_count(self, obj):
        return obj.memberships.count()


class TeamDetailSerializer(serializers.ModelSerializer):
    """Serializer for Team detail view."""
    created_by = UserMinimalSerializer(read_only=True)
    memberships = TeamMembershipSerializer(many=True, read_only=True)
    member_count = serializers.SerializerMethodField()
    can_manage = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = [
            'id', 'name', 'description', 'created_at', 'created_by',
            'memberships', 'member_count', 'can_manage', 'can_edit'
        ]
        read_only_fields = ['id', 'created_at', 'created_by']

    def get_member_count(self, obj):
        return obj.memberships.count()

    def get_can_manage(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.has_perm('teams.manage_members', obj)
        return False

    def get_can_edit(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.has_perm('teams.change_team', obj)
        return False


class TeamCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating teams."""
    class Meta:
        model = Team
        fields = ['name', 'description']

    def validate_name(self, value):
        value = value.strip()
        if len(value) < 3:
            raise serializers.ValidationError('Team name must be at least 3 characters.')
        if len(value) > 100:
            raise serializers.ValidationError('Team name must not exceed 100 characters.')
        return value


class AddMemberSerializer(serializers.Serializer):
    """Serializer for adding a member to a team."""
    username = serializers.CharField()
    role = serializers.ChoiceField(choices=TeamMembership.ROLE_CHOICES, default=TeamMembership.MEMBER)

    def validate_username(self, value):
        try:
            user = User.objects.get(username=value)
        except User.DoesNotExist:
            raise serializers.ValidationError(f"User '{value}' does not exist.")
        return user


class ChangeRoleSerializer(serializers.Serializer):
    """Serializer for changing a member's role."""
    role = serializers.ChoiceField(choices=TeamMembership.ROLE_CHOICES)


# --- Tasks ---

class TaskListSerializer(serializers.ModelSerializer):
    """Serializer for Task list view."""
    team = TeamListSerializer(read_only=True)
    created_by = UserMinimalSerializer(read_only=True)
    assigned_to = UserMinimalSerializer(read_only=True)
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'status', 'deadline', 'created_at',
            'team', 'created_by', 'assigned_to', 'comment_count'
        ]

    def get_comment_count(self, obj):
        return obj.comments.count()


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for Comment model with nested replies."""
    author = UserMinimalSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'content', 'author', 'parent', 'created_at', 'replies', 'can_delete']
        read_only_fields = ['id', 'author', 'created_at']

    def get_replies(self, obj):
        if obj.parent is not None:
            return []
        replies = obj.replies.select_related('author').all()
        return CommentSerializer(replies, many=True, context=self.context).data

    def get_can_delete(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        if obj.author == request.user:
            return True
        return TeamMembership.objects.filter(
            team=obj.task.team, user=request.user, role=TeamMembership.OWNER
        ).exists()


class FileUploadSerializer(serializers.ModelSerializer):
    """Serializer for FileUpload model."""
    uploaded_by = UserMinimalSerializer(read_only=True)
    filename = serializers.ReadOnlyField()

    class Meta:
        model = FileUpload
        fields = ['id', 'file', 'filename', 'uploaded_by', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_by', 'uploaded_at']


class ActivityLogSerializer(serializers.ModelSerializer):
    """Serializer for ActivityLog model."""
    user = UserMinimalSerializer(read_only=True)

    class Meta:
        model = ActivityLog
        fields = ['id', 'action', 'details', 'timestamp', 'user']


class TaskDetailSerializer(serializers.ModelSerializer):
    """Serializer for Task detail view."""
    team = TeamListSerializer(read_only=True)
    created_by = UserMinimalSerializer(read_only=True)
    assigned_to = UserMinimalSerializer(read_only=True)
    comments = serializers.SerializerMethodField()
    files = serializers.SerializerMethodField()
    activity_logs = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'deadline',
            'created_at', 'updated_at', 'team', 'created_by', 'assigned_to',
            'comments', 'files', 'activity_logs', 'can_edit', 'can_delete'
        ]

    def get_comments(self, obj):
        top_level = obj.comments.filter(parent__isnull=True).select_related('author').prefetch_related('replies__author')
        return CommentSerializer(top_level, many=True, context=self.context).data

    def get_files(self, obj):
        from django.contrib.contenttypes.models import ContentType
        ct = ContentType.objects.get_for_model(Task)
        files = FileUpload.objects.filter(content_type=ct, object_id=obj.pk).select_related('uploaded_by')
        return FileUploadSerializer(files, many=True, context=self.context).data

    def get_activity_logs(self, obj):
        logs = obj.activity_logs.select_related('user')[:20]
        return ActivityLogSerializer(logs, many=True, context=self.context).data

    def get_can_edit(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        is_owner = TeamMembership.objects.filter(
            team=obj.team, user=request.user, role=TeamMembership.OWNER
        ).exists()
        return is_owner or obj.created_by == request.user

    def get_can_delete(self, obj):
        return self.get_can_edit(obj)


class TaskCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating tasks."""
    class Meta:
        model = Task
        fields = ['title', 'description', 'team', 'assigned_to', 'status', 'deadline']

    def validate_title(self, value):
        value = value.strip()
        if len(value) < 3:
            raise serializers.ValidationError('Task title must be at least 3 characters.')
        if len(value) > 200:
            raise serializers.ValidationError('Task title must not exceed 200 characters.')
        return value

    def validate(self, data):
        team = data.get('team')
        assigned_to = data.get('assigned_to')
        if team and assigned_to:
            if not TeamMembership.objects.filter(team=team, user=assigned_to).exists():
                raise serializers.ValidationError(
                    {'assigned_to': 'The assigned user must be a member of the selected team.'}
                )
        deadline = data.get('deadline')
        if deadline and not self.instance:
            from django.utils import timezone
            if deadline < timezone.now().date():
                raise serializers.ValidationError({'deadline': 'Deadline cannot be in the past.'})
        return data


class CommentCreateSerializer(serializers.Serializer):
    """Serializer for creating a comment."""
    content = serializers.CharField(max_length=2000)

    def validate_content(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Comment cannot be empty.')
        return value


# --- Notifications ---

class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model."""
    sender = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'sender', 'notification_type', 'message',
            'is_read', 'created_at'
        ]
        read_only_fields = ['id', 'sender', 'notification_type', 'message', 'created_at']


# --- Dashboard ---

class DashboardSerializer(serializers.Serializer):
    """Serializer for dashboard stats."""
    user_teams_count = serializers.IntegerField()
    user_tasks_count = serializers.IntegerField()
    assigned_tasks_count = serializers.IntegerField()
    unread_notification_count = serializers.IntegerField()
    recent_tasks = TaskListSerializer(many=True)
    user_teams = TeamListSerializer(many=True)
