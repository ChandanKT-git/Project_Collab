from django import forms
from django.contrib.auth.models import User
from .models import Task, Comment, FileUpload
from apps.teams.models import Team, TeamMembership


class TaskForm(forms.ModelForm):
    """Form for creating and updating tasks."""
    
    class Meta:
        model = Task
        fields = ['title', 'description', 'team', 'assigned_to', 'status', 'deadline']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'deadline': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Limit team choices to teams where user is a member
        if user:
            user_teams = Team.objects.filter(memberships__user=user)
            self.fields['team'].queryset = user_teams
            
            # Check if user has any teams
            if not user_teams.exists():
                self.fields['team'].help_text = 'You need to create or join a team first before creating tasks.'
            
            # If editing an existing task, limit assigned_to to team members
            if self.instance and self.instance.pk:
                team_members = User.objects.filter(team_memberships__team=self.instance.team)
                self.fields['assigned_to'].queryset = team_members
            else:
                # For new tasks, start with empty queryset - will be populated via JavaScript
                self.fields['assigned_to'].queryset = User.objects.none()
                self.fields['assigned_to'].help_text = 'Select a team first to see available members'
                self.fields['assigned_to'].required = False
    
    def clean_title(self):
        """Validate task title."""
        title = self.cleaned_data.get('title')
        if title:
            # Strip whitespace
            title = title.strip()
            
            # Check minimum length
            if len(title) < 3:
                raise forms.ValidationError('Task title must be at least 3 characters long.')
            
            # Check maximum length
            if len(title) > 200:
                raise forms.ValidationError('Task title must not exceed 200 characters.')
            
            # Check for empty after stripping
            if not title:
                raise forms.ValidationError('Task title cannot be empty or only whitespace.')
        
        return title
    
    def clean_description(self):
        """Validate task description."""
        description = self.cleaned_data.get('description')
        if description:
            # Strip whitespace
            description = description.strip()
            
            # Check maximum length
            if len(description) > 5000:
                raise forms.ValidationError('Task description must not exceed 5000 characters.')
        
        return description
    
    def clean(self):
        """Cross-field validation."""
        cleaned_data = super().clean()
        team = cleaned_data.get('team')
        assigned_to = cleaned_data.get('assigned_to')
        deadline = cleaned_data.get('deadline')
        
        # Validate that assigned user is a member of the team
        if team and assigned_to:
            from apps.teams.models import TeamMembership
            if not TeamMembership.objects.filter(team=team, user=assigned_to).exists():
                raise forms.ValidationError('The assigned user must be a member of the selected team.')
        
        # Validate deadline is not in the past (for new tasks)
        if deadline and not self.instance.pk:
            from django.utils import timezone
            if deadline < timezone.now().date():
                raise forms.ValidationError('Deadline cannot be in the past.')
        
        return cleaned_data


class CommentForm(forms.ModelForm):
    """Form for creating comments and replies."""
    
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Add a comment...',
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
        }
        labels = {
            'content': ''
        }
    
    def clean_content(self):
        """Validate comment content."""
        content = self.cleaned_data.get('content')
        if content:
            # Strip whitespace
            content = content.strip()
            
            # Check minimum length
            if len(content) < 1:
                raise forms.ValidationError('Comment cannot be empty.')
            
            # Check maximum length
            if len(content) > 2000:
                raise forms.ValidationError('Comment must not exceed 2000 characters.')
            
            # Check for empty after stripping
            if not content:
                raise forms.ValidationError('Comment cannot be empty or only whitespace.')
        
        return content


class FileUploadForm(forms.ModelForm):
    """Form for uploading files to tasks or comments."""
    
    class Meta:
        model = FileUpload
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'
            }),
        }
    
    def clean_file(self):
        """Validate file size (max 10MB)."""
        file = self.cleaned_data.get('file')
        if file:
            # Check file size (10MB = 10 * 1024 * 1024 bytes)
            max_size = 10 * 1024 * 1024
            if file.size > max_size:
                raise forms.ValidationError(f'File size must not exceed 10MB. Current size: {file.size / (1024 * 1024):.2f}MB')
        return file
