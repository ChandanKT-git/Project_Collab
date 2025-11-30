from django.contrib import admin
from django.db.models import Count
from .models import Team, TeamMembership


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'member_count', 'task_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description', 'created_by__username')
    readonly_fields = ('created_at',)
    actions = ['delete_with_cascade']
    
    def get_queryset(self, request):
        """Optimize queryset with annotations."""
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            _member_count=Count('memberships', distinct=True),
            _task_count=Count('tasks', distinct=True)
        )
        return queryset
    
    def member_count(self, obj):
        """Display the number of members in the team."""
        return obj._member_count
    member_count.short_description = 'Members'
    member_count.admin_order_field = '_member_count'
    
    def task_count(self, obj):
        """Display the number of tasks in the team."""
        return obj._task_count
    task_count.short_description = 'Tasks'
    task_count.admin_order_field = '_task_count'
    
    def delete_with_cascade(self, request, queryset):
        """Custom action to delete teams with cascade deletion."""
        count = queryset.count()
        # Django's CASCADE will handle related objects automatically
        queryset.delete()
        self.message_user(request, f'Successfully deleted {count} team(s) and all related data.')
    delete_with_cascade.short_description = 'Delete selected teams (cascade)'
    
    def delete_model(self, request, obj):
        """Override delete to ensure cascade deletion."""
        # Django's CASCADE on ForeignKey will handle this automatically
        obj.delete()
    
    def delete_queryset(self, request, queryset):
        """Override bulk delete to ensure cascade deletion."""
        queryset.delete()


@admin.register(TeamMembership)
class TeamMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'team', 'role', 'joined_at')
    list_filter = ('role', 'joined_at')
    search_fields = ('user__username', 'team__name')
    readonly_fields = ('joined_at',)
    actions = ['promote_to_owner', 'demote_to_member']
    
    def promote_to_owner(self, request, queryset):
        """Bulk action to promote members to owners."""
        updated = queryset.update(role=TeamMembership.OWNER)
        self.message_user(request, f'Successfully promoted {updated} member(s) to owner.')
    promote_to_owner.short_description = 'Promote to owner'
    
    def demote_to_member(self, request, queryset):
        """Bulk action to demote owners to members."""
        updated = queryset.update(role=TeamMembership.MEMBER)
        self.message_user(request, f'Successfully demoted {updated} owner(s) to member.')
    demote_to_member.short_description = 'Demote to member'
