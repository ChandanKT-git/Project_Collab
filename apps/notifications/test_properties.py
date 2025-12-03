"""Property-based tests for notifications app."""
import pytest
import uuid
from hypothesis import given, strategies as st, assume, settings
from hypothesis.extra.django import from_model
from django.contrib.auth.models import User
from apps.teams.models import Team, TeamMembership
from apps.tasks.models import Task, Comment
from apps.notifications.models import Notification
from apps.notifications.services import MentionParser, NotificationService


# Feature: project-collaboration-portal, Property 26: Mention parsing identifies users
@pytest.mark.django_db
@given(
    username=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_')),
    text_before=st.text(max_size=50),
    text_after=st.text(max_size=50, alphabet=st.characters(blacklist_categories=('Nd', 'Lu', 'Ll'), blacklist_characters='_'))
)
def test_mention_parsing_identifies_users(username, text_before, text_after):
    """
    Property 26: Mention parsing identifies users
    
    For any text containing @username, the MentionParser should correctly
    identify and extract the username when followed by non-word characters.
    
    Validates: Requirements 7.1
    """
    # Ensure username is valid (starts with letter or underscore, contains only alphanumeric and underscore)
    assume(len(username) > 0)
    assume(username[0].isalpha() or username[0] == '_')
    assume(all(c.isalnum() or c == '_' for c in username))
    # Ensure text_after doesn't start with a word character (to avoid extending the match)
    assume(len(text_after) == 0 or not (text_after[0].isalnum() or text_after[0] == '_'))
    
    # Create text with mention
    text = f"{text_before}@{username}{text_after}"
    
    # Extract mentions
    mentions = MentionParser.extract_mentions(text)
    
    # Property: The username should be in the extracted mentions
    assert username in mentions, f"Expected {username} to be in {mentions}"


# Feature: project-collaboration-portal, Property 27: Mentions create notifications
@pytest.mark.django_db(transaction=True)
@settings(deadline=None, max_examples=100)  # No deadline, 100 examples as per design
@given(
    comment_text=st.text(min_size=1, max_size=200)
)
def test_mentions_create_notifications(comment_text):
    """
    Property 27: Mentions create notifications
    
    For any comment containing mentions of team members, notifications
    should be created for all mentioned users.
    
    Validates: Requirements 7.2
    """
    # Create test users with unique usernames using UUID
    test_id = str(uuid.uuid4())[:8]
    author = User.objects.create_user(username=f'author_{test_id}', password='testpass123')
    mentioned_user = User.objects.create_user(username=f'mentioned_{test_id}', password='testpass123')
    
    # Create team and add both users
    team = Team.objects.create(name=f'Test Team {test_id}', created_by=author)
    TeamMembership.objects.create(team=team, user=mentioned_user, role=TeamMembership.MEMBER)
    
    # Create task
    task = Task.objects.create(
        title=f'Test Task {test_id}',
        description='Test',
        team=team,
        created_by=author,
        status=Task.TODO
    )
    
    # Create comment with mention
    comment_with_mention = f"{comment_text} @{mentioned_user.username}"
    
    # Get initial notification count
    initial_count = Notification.objects.filter(recipient=mentioned_user).count()
    
    # Create comment (this should trigger notification creation via signal)
    comment = Comment.objects.create(
        task=task,
        author=author,
        content=comment_with_mention
    )
    
    # Property: A notification should be created for the mentioned user
    final_count = Notification.objects.filter(recipient=mentioned_user).count()
    assert final_count > initial_count, "Notification should be created for mentioned user"
    
    # Verify the notification is of type MENTION
    notification = Notification.objects.filter(recipient=mentioned_user).latest('created_at')
    assert notification.notification_type == Notification.MENTION


# Feature: project-collaboration-portal, Property 28: Mentioned users receive notifications
@pytest.mark.django_db(transaction=True)
@settings(deadline=None, max_examples=100)  # No deadline, 100 examples as per design
@given(
    num_mentions=st.integers(min_value=1, max_value=5)
)
def test_mentioned_users_receive_notifications(num_mentions):
    """
    Property 28: Mentioned users receive notifications
    
    For any set of users mentioned in a comment, each mentioned user
    should receive a notification.
    
    Validates: Requirements 7.3
    """
    # Create author with unique username
    test_id = str(uuid.uuid4())[:8]
    author = User.objects.create_user(username=f'author_{test_id}', password='testpass123')
    
    # Create team
    team = Team.objects.create(name=f'Test Team {test_id}', created_by=author)
    
    # Create mentioned users and add to team
    mentioned_users = []
    for i in range(num_mentions):
        user = User.objects.create_user(username=f'user_{test_id}_{i}', password='testpass123')
        TeamMembership.objects.create(team=team, user=user, role=TeamMembership.MEMBER)
        mentioned_users.append(user)
    
    # Create task
    task = Task.objects.create(
        title=f'Test Task {test_id}',
        description='Test',
        team=team,
        created_by=author,
        status=Task.TODO
    )
    
    # Create comment mentioning all users
    mentions_text = ' '.join([f'@{user.username}' for user in mentioned_users])
    comment = Comment.objects.create(
        task=task,
        author=author,
        content=f"Hello {mentions_text}"
    )
    
    # Property: Each mentioned user should have received a notification
    for user in mentioned_users:
        notifications = Notification.objects.filter(
            recipient=user,
            notification_type=Notification.MENTION
        )
        assert notifications.exists(), f"User {user.username} should have received a notification"


# Feature: project-collaboration-portal, Property 29: Mentions are highlighted in display
@pytest.mark.django_db
@given(
    username=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_')),
    text_content=st.text(max_size=100)
)
def test_mentions_are_highlighted(username, text_content):
    """
    Property 29: Mentions are highlighted in display
    
    For any text containing @username mentions, the highlight_mentions
    function should wrap mentions in HTML span tags.
    
    Validates: Requirements 7.4
    """
    # Ensure username is valid
    assume(len(username) > 0)
    assume(username[0].isalpha() or username[0] == '_')
    assume(all(c.isalnum() or c == '_' for c in username))
    
    # Create text with mention
    text = f"{text_content} @{username}"
    
    # Highlight mentions
    highlighted = MentionParser.highlight_mentions(text)
    
    # Property: The highlighted text should contain HTML span with mention class
    assert '<span class="mention">' in highlighted, "Mentions should be wrapped in span tags"
    assert f'@{username}' in highlighted, "Original mention should be preserved in output"


# Feature: project-collaboration-portal, Property 30: Non-team mentions are ignored
@pytest.mark.django_db(transaction=True)
@settings(deadline=None, max_examples=100)  # No deadline, 100 examples as per design
@given(
    comment_text=st.text(min_size=1, max_size=200)
)
def test_non_team_mentions_ignored(comment_text):
    """
    Property 30: Non-team mentions are ignored
    
    For any comment mentioning a user who is not a team member,
    no notification should be created for that user.
    
    Validates: Requirements 7.5
    """
    # Create test users with unique usernames
    test_id = str(uuid.uuid4())[:8]
    author = User.objects.create_user(username=f'author_{test_id}', password='testpass123')
    non_team_user = User.objects.create_user(username=f'outsider_{test_id}', password='testpass123')
    
    # Create team with only author
    team = Team.objects.create(name=f'Test Team {test_id}', created_by=author)
    
    # Create task
    task = Task.objects.create(
        title=f'Test Task {test_id}',
        description='Test',
        team=team,
        created_by=author,
        status=Task.TODO
    )
    
    # Create comment mentioning non-team user
    comment_with_mention = f"{comment_text} @{non_team_user.username}"
    
    # Get initial notification count for non-team user
    initial_count = Notification.objects.filter(recipient=non_team_user).count()
    
    # Create comment
    comment = Comment.objects.create(
        task=task,
        author=author,
        content=comment_with_mention
    )
    
    # Property: No notification should be created for non-team user
    final_count = Notification.objects.filter(recipient=non_team_user).count()
    assert final_count == initial_count, "Non-team members should not receive notifications"



# Feature: project-collaboration-portal, Property 33: Events trigger email notifications
@pytest.mark.django_db(transaction=True)
@settings(deadline=None, max_examples=100)  # No deadline, 100 examples as per design
@given(
    event_type=st.sampled_from(['mention', 'assignment'])
)
def test_events_trigger_email_notifications(event_type):
    """
    Property 33: Events trigger email notifications
    
    For any notification-worthy event (mention or task assignment),
    an email notification should be sent to the relevant user.
    
    Validates: Requirements 9.1, 9.2, 9.3
    """
    from django.core import mail
    from apps.notifications.services import EmailService
    
    # Create test users with unique usernames
    test_id = str(uuid.uuid4())[:8]
    sender = User.objects.create_user(
        username=f'sender_{test_id}',
        email=f'sender_{test_id}@test.com',
        password='testpass123'
    )
    recipient = User.objects.create_user(
        username=f'recipient_{test_id}',
        email=f'recipient_{test_id}@test.com',
        password='testpass123'
    )
    
    # Create team and add both users
    team = Team.objects.create(name=f'Test Team {test_id}', created_by=sender)
    TeamMembership.objects.create(team=team, user=recipient, role=TeamMembership.MEMBER)
    
    # Clear mail outbox
    mail.outbox = []
    
    if event_type == 'mention':
        # Create task
        task = Task.objects.create(
            title=f'Test Task {test_id}',
            description='Test',
            team=team,
            created_by=sender,
            status=Task.TODO
        )
        
        # Create comment with mention (should trigger email)
        Comment.objects.create(
            task=task,
            author=sender,
            content=f"Hello @{recipient.username}"
        )
    
    elif event_type == 'assignment':
        # Create task with assignment (should trigger email)
        Task.objects.create(
            title=f'Test Task {test_id}',
            description='Test',
            team=team,
            created_by=sender,
            assigned_to=recipient,
            status=Task.TODO
        )
    
    # Property: An email should have been sent
    assert len(mail.outbox) > 0, f"Email should be sent for {event_type} event"
    
    # Verify email was sent to the correct recipient
    email = mail.outbox[0]
    assert recipient.email in email.to, f"Email should be sent to {recipient.email}"


# Feature: project-collaboration-portal, Property 34: Multiple notifications batch within time window
@pytest.mark.django_db(transaction=True)
@settings(deadline=None, max_examples=100)  # No deadline, 100 examples as per design
@given(
    num_notifications=st.integers(min_value=2, max_value=5)
)
def test_multiple_notifications_batch_within_time_window(num_notifications):
    """
    Property 34: Multiple notifications batch within time window
    
    For any user with multiple pending notifications occurring within
    a configurable time window, the notifications should be retrievable
    as a batch for sending in a single email.
    
    Validates: Requirements 9.5
    """
    from apps.notifications.services import EmailService
    
    # Create test users with unique usernames
    test_id = str(uuid.uuid4())[:8]
    sender = User.objects.create_user(
        username=f'sender_{test_id}',
        email=f'sender_{test_id}@test.com',
        password='testpass123'
    )
    recipient = User.objects.create_user(
        username=f'recipient_{test_id}',
        email=f'recipient_{test_id}@test.com',
        password='testpass123'
    )
    
    # Create team
    team = Team.objects.create(name=f'Test Team {test_id}', created_by=sender)
    TeamMembership.objects.create(team=team, user=recipient, role=TeamMembership.MEMBER)
    
    # Create task
    task = Task.objects.create(
        title=f'Test Task {test_id}',
        description='Test',
        team=team,
        created_by=sender,
        status=Task.TODO
    )
    
    # Create multiple notifications within time window
    created_notifications = []
    for i in range(num_notifications):
        notification = NotificationService.create_notification(
            recipient=recipient,
            sender=sender,
            notification_type=Notification.MENTION,
            message=f"Test notification {i}",
            content_object=task
        )
        created_notifications.append(notification)
    
    # Get pending notifications within time window
    pending = EmailService.get_pending_notifications(recipient)
    
    # Property: All created notifications should be in the pending batch
    assert pending.count() >= num_notifications, \
        f"Expected at least {num_notifications} notifications in batch, got {pending.count()}"
    
    # Verify all created notifications are in the batch
    pending_ids = set(pending.values_list('id', flat=True))
    for notification in created_notifications:
        assert notification.id in pending_ids, \
            f"Notification {notification.id} should be in pending batch"
