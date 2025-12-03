# User Guide

## Welcome to Project Collaboration Portal

This guide will help you get started with the Project Collaboration Portal and make the most of its features for team collaboration and project management.

## Table of Contents

- [Getting Started](#getting-started)
- [User Roles](#user-roles)
- [Teams](#teams)
- [Tasks](#tasks)
- [Comments and Discussions](#comments-and-discussions)
- [File Management](#file-management)
- [Notifications](#notifications)
- [Activity Tracking](#activity-tracking)
- [Best Practices](#best-practices)
- [Keyboard Shortcuts](#keyboard-shortcuts)
- [FAQ](#faq)

## Getting Started

### Creating an Account

1. Navigate to the signup page at `/accounts/signup/`
2. Fill in the registration form:
   - **Username**: Choose a unique username (letters, numbers, and underscores only)
   - **Email**: Enter a valid email address
   - **Password**: Create a strong password (minimum 8 characters)
   - **Confirm Password**: Re-enter your password
3. Click "Sign Up"
4. You'll be automatically logged in and redirected to the home page

### Logging In

1. Navigate to the login page at `/accounts/login/`
2. Enter your username and password
3. Click "Log In"
4. You'll be redirected to your dashboard

### Your Dashboard

After logging in, you'll see your dashboard with:
- **Teams**: List of teams you're a member of
- **Recent Tasks**: Your recently created or assigned tasks
- **Notifications**: Unread notifications (bell icon in navbar)
- **Quick Actions**: Buttons to create teams and tasks

## User Roles

### Team Owner

Team Owners have full administrative control over their teams:

**Permissions**:
- Create, edit, and delete the team
- Add and remove team members
- Assign roles to members
- Create, edit, and delete all team tasks
- Manage team settings

**Responsibilities**:
- Maintain team organization
- Manage member access
- Ensure proper task assignment
- Monitor team activity

### Team Member

Team Members have standard access to team resources:

**Permissions**:
- View team details and member list
- Create tasks within the team
- View and comment on tasks
- Upload files to tasks
- Receive notifications

**Responsibilities**:
- Complete assigned tasks
- Participate in discussions
- Keep tasks updated
- Collaborate with team members

## Teams

### Creating a Team

1. Click "Teams" in the navigation bar
2. Click the "Create Team" button
3. Fill in the team details:
   - **Name**: Choose a descriptive team name
   - **Description**: Explain the team's purpose (optional)
4. Click "Create Team"
5. You are automatically assigned as the team owner

**Tips**:
- Use clear, descriptive names (e.g., "Marketing Team", "Product Development")
- Add a detailed description to help members understand the team's purpose
- Consider creating separate teams for different projects or departments

### Viewing Teams

1. Click "Teams" in the navigation bar
2. You'll see a list of all teams you're a member of
3. Click on a team name to view its details

**Team Detail Page Shows**:
- Team name and description
- List of team members with their roles
- Recent tasks
- Team statistics
- Management options (if you're an owner)

### Managing Team Members

#### Adding Members

1. Navigate to your team's detail page
2. Click "Add Member"
3. Enter the username of the person you want to invite
4. Select their role:
   - **Member**: Standard access
   - **Owner**: Full administrative access
5. Click "Add Member"

**Note**: The user must already have an account on the platform.

#### Changing Member Roles

1. Navigate to your team's detail page
2. Find the member in the member list
3. Click "Change Role" next to their name
4. Select the new role
5. Click "Update Role"

#### Removing Members

1. Navigate to your team's detail page
2. Find the member in the member list
3. Click "Remove" next to their name
4. Confirm the removal
5. The member will lose all access to team resources

**Warning**: Removing a member revokes all their permissions immediately.

### Editing Team Details

1. Navigate to your team's detail page
2. Click "Edit Team"
3. Update the name or description
4. Click "Save Changes"

### Deleting a Team

1. Navigate to your team's detail page
2. Click "Delete Team"
3. Confirm the deletion
4. All team tasks, comments, and files will be permanently deleted

**Warning**: This action cannot be undone!

## Tasks

### Creating a Task

1. Navigate to a team's detail page
2. Click "Create Task"
3. Fill in the task details:
   - **Title**: Brief, descriptive title (required)
   - **Description**: Detailed task description
   - **Assigned To**: Select a team member (optional)
   - **Status**: Choose initial status (default: To Do)
   - **Deadline**: Set a due date (optional)
4. Click "Create Task"

**Task Statuses**:
- **To Do**: Task not yet started
- **In Progress**: Task is being worked on
- **Review**: Task is complete and awaiting review
- **Done**: Task is completed

**Tips**:
- Write clear, actionable titles (e.g., "Design homepage mockup")
- Include all necessary details in the description
- Set realistic deadlines
- Assign tasks to specific team members for accountability

### Viewing Tasks

#### Task List

1. Click "Tasks" in the navigation bar
2. View all tasks you have access to
3. Use filters to narrow down the list:
   - Filter by team
   - Filter by status
   - Filter by assigned user

#### Task Detail

1. Click on a task title to view its details
2. The task detail page shows:
   - Title and description
   - Status and deadline
   - Creator and assignee
   - Creation and update timestamps
   - Comments and discussions
   - Attached files
   - Activity log

### Updating a Task

1. Navigate to the task detail page
2. Click "Edit Task"
3. Update any fields:
   - Title
   - Description
   - Status
   - Assigned user
   - Deadline
4. Click "Save Changes"

**Note**: The task's "Updated At" timestamp will be automatically updated.

### Deleting a Task

1. Navigate to the task detail page
2. Click "Delete Task"
3. Confirm the deletion
4. The task and all associated comments and files will be permanently deleted

**Warning**: This action cannot be undone!

### Task Status Workflow

Recommended workflow for task statuses:

1. **To Do** → Task is created and ready to be started
2. **In Progress** → Someone begins working on the task
3. **Review** → Work is complete and needs review
4. **Done** → Task is reviewed and completed

**Tips**:
- Update status regularly to keep team informed
- Move to "Review" when you need feedback
- Only mark as "Done" when truly complete

## Comments and Discussions

### Adding a Comment

1. Navigate to a task detail page
2. Scroll to the comments section
3. Type your comment in the text box
4. Click "Add Comment"

**Comment Features**:
- Markdown formatting support
- @mention other team members
- Attach files to comments
- Reply to existing comments

### Replying to Comments

1. Find the comment you want to reply to
2. Click "Reply" below the comment
3. Type your reply
4. Click "Submit Reply"

**Note**: Replies are indented to show the conversation thread.

### Mentioning Team Members

Use the `@username` syntax to mention team members:

1. Type `@` followed by the username (e.g., `@john`)
2. The mentioned user will receive a notification
3. Mentions are highlighted in the comment

**Example**:
```
@john can you review this design?
@jane please update the documentation
```

**Tips**:
- Only mention users who are team members
- Use mentions to direct attention to specific people
- Don't overuse mentions to avoid notification fatigue

### Threaded Discussions

Comments support nested replies for organized discussions:

- **Top-level comments**: Direct responses to the task
- **Replies**: Responses to specific comments
- **Threads**: Chains of related replies

**Best Practices**:
- Reply to specific comments to keep discussions organized
- Start new top-level comments for new topics
- Keep threads focused on one subject

### Deleting Comments

1. Find your comment
2. Click "Delete" (only visible on your own comments)
3. Confirm the deletion
4. All replies to that comment will also be deleted

**Warning**: This action cannot be undone!

## File Management

### Uploading Files to Tasks

1. Navigate to a task detail page
2. Click "Upload File"
3. Select a file from your computer
4. Click "Upload"
5. The file will appear in the task's file list

**Supported File Types**:
- Documents (PDF, DOC, DOCX, TXT)
- Images (JPG, PNG, GIF)
- Spreadsheets (XLS, XLSX, CSV)
- Archives (ZIP, RAR)
- And more...

**File Size Limits**:
- Maximum file size: 10 MB per file
- Contact your administrator for larger files

### Uploading Files to Comments

1. Create or reply to a comment
2. Click "Attach File"
3. Select a file from your computer
4. The file will be attached to your comment

### Downloading Files

1. Find the file in the task or comment
2. Click the file name or download link
3. The file will download to your computer

### File Organization

**Tips**:
- Use descriptive file names
- Include version numbers (e.g., "design_v2.pdf")
- Add a comment explaining what the file contains
- Keep files organized by task

### Deleting Files

Files are automatically deleted when:
- The parent task is deleted
- The parent comment is deleted

**Note**: Individual file deletion is not currently supported. Delete the parent task or comment to remove files.

## Notifications

### Viewing Notifications

1. Click the bell icon in the navigation bar
2. View your list of notifications
3. Click on a notification to view the related task or comment

**Notification Badge**:
- Shows the count of unread notifications
- Updates in real-time
- Disappears when all notifications are read

### Types of Notifications

#### Mention Notifications

You receive a notification when someone mentions you in a comment:
- Shows who mentioned you
- Displays a preview of the comment
- Links to the task and comment

#### Assignment Notifications

You receive a notification when a task is assigned to you:
- Shows the task title
- Displays the task description
- Links to the task detail page

#### Reply Notifications

You receive a notification when someone replies to your comment:
- Shows who replied
- Displays a preview of the reply
- Links to the comment thread

### Email Notifications

In addition to in-app notifications, you'll receive emails for:
- Mentions in comments
- Task assignments
- Replies to your comments

**Email Features**:
- Includes relevant context (task title, comment excerpt)
- Contains direct links to the task
- Batched notifications (multiple notifications in one email)

**Email Settings**:
- Check your spam folder if you don't receive emails
- Contact your administrator to update email preferences

### Managing Notifications

#### Marking as Read

- Click on a notification to mark it as read
- Read notifications are removed from the unread count
- View all notifications (read and unread) in the notification list

#### Notification Batching

Multiple notifications within a 5-minute window are batched into a single email to reduce inbox clutter.

## Activity Tracking

### Activity Log

Every task has an activity log that tracks:
- Task creation
- Status changes
- Field updates (title, description, deadline, assignee)
- Comments added
- Files uploaded
- Member actions

### Viewing Activity

1. Navigate to a task detail page
2. Scroll to the "Activity Log" section
3. View chronological list of all actions

**Activity Log Shows**:
- Action type (created, updated, commented, etc.)
- User who performed the action
- Timestamp
- Details of what changed

**Example Entries**:
- "John created this task" - 2 hours ago
- "Jane changed status from To Do to In Progress" - 1 hour ago
- "Mike added a comment" - 30 minutes ago
- "Sarah uploaded a file" - 10 minutes ago

### Using Activity Logs

**Benefits**:
- Track task progress over time
- See who made specific changes
- Understand task history
- Identify bottlenecks
- Audit team activity

**Tips**:
- Review activity logs before meetings
- Use logs to understand task delays
- Reference logs when providing updates

## Best Practices

### Team Organization

1. **Create focused teams**: One team per project or department
2. **Assign clear roles**: Make sure everyone knows their responsibilities
3. **Regular updates**: Keep team information current
4. **Member management**: Remove inactive members promptly

### Task Management

1. **Clear titles**: Use descriptive, actionable titles
2. **Detailed descriptions**: Include all necessary information
3. **Realistic deadlines**: Set achievable due dates
4. **Regular updates**: Update status as work progresses
5. **Proper assignment**: Assign tasks to specific people
6. **Break down large tasks**: Create multiple smaller tasks for complex work

### Communication

1. **Use comments**: Keep all discussion in task comments
2. **@mention appropriately**: Only mention when necessary
3. **Be specific**: Provide clear, actionable feedback
4. **Stay on topic**: Keep comments relevant to the task
5. **Be respectful**: Maintain professional communication

### File Management

1. **Descriptive names**: Use clear file names
2. **Version control**: Include version numbers
3. **Organize by task**: Keep related files together
4. **Explain uploads**: Add a comment when uploading files
5. **Clean up**: Delete obsolete tasks and files

### Notification Management

1. **Check regularly**: Review notifications daily
2. **Respond promptly**: Address mentions and assignments quickly
3. **Mark as read**: Keep your notification list clean
4. **Use email**: Enable email notifications for important updates

## Keyboard Shortcuts

Currently, the application uses standard browser shortcuts. Future versions may include custom keyboard shortcuts for common actions.

**Browser Shortcuts**:
- `Ctrl/Cmd + F`: Search on page
- `Ctrl/Cmd + Click`: Open link in new tab
- `Tab`: Navigate between form fields
- `Enter`: Submit forms

## FAQ

### General Questions

**Q: How do I reset my password?**
A: Contact your administrator to reset your password. A password reset feature will be added in a future update.

**Q: Can I be a member of multiple teams?**
A: Yes! You can be a member of as many teams as you need.

**Q: Can I create multiple teams?**
A: Yes, there's no limit to the number of teams you can create.

**Q: How do I leave a team?**
A: Contact a team owner to be removed from the team.

### Task Questions

**Q: Can I assign a task to multiple people?**
A: Currently, tasks can only be assigned to one person. Create separate tasks for multiple assignees.

**Q: Can I set recurring tasks?**
A: Recurring tasks are not currently supported. Create new tasks as needed.

**Q: What happens to tasks when a team is deleted?**
A: All tasks, comments, and files are permanently deleted with the team.

**Q: Can I move a task to a different team?**
A: Task moving is not currently supported. Create a new task in the target team.

### Comment Questions

**Q: Can I edit my comments?**
A: Comment editing is not currently supported. Delete and recreate if needed.

**Q: Can I format my comments?**
A: Basic text formatting is supported. Markdown support may be added in future updates.

**Q: What happens when I delete a comment with replies?**
A: All replies to that comment are also deleted.

### File Questions

**Q: What's the maximum file size?**
A: The default limit is 10 MB per file. Contact your administrator for larger files.

**Q: Can I upload multiple files at once?**
A: Currently, files must be uploaded one at a time.

**Q: Where are my files stored?**
A: Files are stored securely on the server. Contact your administrator for details.

**Q: Can I delete individual files?**
A: Files are deleted when their parent task or comment is deleted.

### Notification Questions

**Q: Why am I not receiving email notifications?**
A: Check your spam folder and verify your email address. Contact your administrator if issues persist.

**Q: Can I disable email notifications?**
A: Email notification preferences will be added in a future update.

**Q: How long are notifications kept?**
A: Notifications are kept indefinitely. You can mark them as read to clear them from your unread list.

### Permission Questions

**Q: Why can't I edit a task?**
A: You need appropriate permissions. Contact a team owner to adjust your role.

**Q: Can I make another user a team owner?**
A: Yes, if you're a team owner, you can promote members to owner status.

**Q: What's the difference between Owner and Member roles?**
A: Owners have full administrative control. Members have standard access. See [User Roles](#user-roles) for details.

## Getting Help

### Support Resources

- **Documentation**: Review this user guide and other documentation
- **Admin Dashboard**: Contact your system administrator
- **Team Owners**: Ask your team owner for help with team-specific issues
- **Technical Support**: Contact your IT department for technical issues

### Reporting Issues

If you encounter a bug or issue:

1. Note the exact steps to reproduce the issue
2. Take a screenshot if applicable
3. Note any error messages
4. Contact your system administrator with details

### Feature Requests

Have an idea for a new feature?

1. Discuss with your team
2. Submit a request to your administrator
3. Provide detailed description of the desired feature
4. Explain how it would benefit your workflow

---

**Version**: 1.0.0  
**Last Updated**: November 2025

Thank you for using Project Collaboration Portal!
