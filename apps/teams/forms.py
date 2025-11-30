from django import forms
from .models import Team, TeamMembership
from django.contrib.auth.models import User


class TeamForm(forms.ModelForm):
    """Form for creating and updating teams."""
    
    class Meta:
        model = Team
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Enter team name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Enter team description',
                'rows': 4
            }),
        }
    
    def clean_name(self):
        """Validate team name."""
        name = self.cleaned_data.get('name')
        if name:
            # Strip whitespace
            name = name.strip()
            
            # Check minimum length
            if len(name) < 3:
                raise forms.ValidationError('Team name must be at least 3 characters long.')
            
            # Check maximum length
            if len(name) > 100:
                raise forms.ValidationError('Team name must not exceed 100 characters.')
            
            # Check for empty after stripping
            if not name:
                raise forms.ValidationError('Team name cannot be empty or only whitespace.')
        
        return name
    
    def clean_description(self):
        """Validate team description."""
        description = self.cleaned_data.get('description')
        if description:
            # Strip whitespace
            description = description.strip()
            
            # Check maximum length
            if len(description) > 1000:
                raise forms.ValidationError('Team description must not exceed 1000 characters.')
        
        return description


class AddMemberForm(forms.Form):
    """Form for adding members to a team."""
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Enter username'
        })
    )
    role = forms.ChoiceField(
        choices=TeamMembership.ROLE_CHOICES,
        initial=TeamMembership.MEMBER,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        })
    )
    
    def __init__(self, *args, team=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.team = team
    
    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise forms.ValidationError(f"User '{username}' does not exist.")
        
        # Check if user is already a member
        if self.team and TeamMembership.objects.filter(team=self.team, user=user).exists():
            raise forms.ValidationError(f"User '{username}' is already a member of this team.")
        
        return user


class ChangeMemberRoleForm(forms.ModelForm):
    """Form for changing a member's role."""
    
    class Meta:
        model = TeamMembership
        fields = ['role']
        widgets = {
            'role': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            })
        }
