from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from guardian.shortcuts import assign_perm


class Team(models.Model):
    """Represents a collaboration team."""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_teams')
    
    class Meta:
        ordering = ['-created_at']
        permissions = (
            ('manage_members', 'Can manage team members'),
        )
    
    def __str__(self):
        return self.name


class TeamMembership(models.Model):
    """Links Users to Teams with roles."""
    OWNER = 'owner'
    MEMBER = 'member'
    
    ROLE_CHOICES = [
        (OWNER, 'Owner'),
        (MEMBER, 'Member'),
    ]
    
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='team_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('team', 'user')
        ordering = ['-joined_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.team.name} ({self.role})"


@receiver(post_save, sender=Team)
def create_team_owner_membership(sender, instance, created, **kwargs):
    """Automatically create owner membership when a team is created."""
    if created:
        membership = TeamMembership.objects.create(
            team=instance,
            user=instance.created_by,
            role=TeamMembership.OWNER
        )
        # Assign all permissions to the owner
        assign_perm('teams.view_team', instance.created_by, instance)
        assign_perm('teams.change_team', instance.created_by, instance)
        assign_perm('teams.delete_team', instance.created_by, instance)
        assign_perm('teams.manage_members', instance.created_by, instance)


@receiver(post_save, sender=TeamMembership)
def assign_membership_permissions(sender, instance, created, **kwargs):
    """Assign permissions based on team membership role."""
    if created or instance.pk:
        # Always grant view permission to members
        assign_perm('teams.view_team', instance.user, instance.team)
        
        # Grant additional permissions to owners
        if instance.role == TeamMembership.OWNER:
            assign_perm('teams.change_team', instance.user, instance.team)
            assign_perm('teams.delete_team', instance.user, instance.team)
            assign_perm('teams.manage_members', instance.user, instance.team)
