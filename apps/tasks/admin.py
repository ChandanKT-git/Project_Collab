from django.contrib import admin
from django.db.models import Count
from .models import Task, Comment, FileUpload, ActivityLog


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'team', 'status', 'assigned_to', 'created_by', 'deadline', 'created_at')
    list_filter = ('status', 'team', 'created_at', 'deadline')
    search_fields = ('title', 'description', 'created_by__username', 'assigned_to__username')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    actions = ['mark_as_done', 'mark_as_in_progress', 'mark_as_todo']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'team')
        }),
        ('Assignment', {
            'fields': ('created_by', 'assigned_to', 'status', 'deadline')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def mark_as_done(self, request, queryset):
        """Bulk action to mark tasks as done."""
        updated = queryset.update(status=Task.DONE)
        self.message_user(request, f'Successfully marked {updated} task(s) as done.')
    mark_as_done.short_description = 'Mark as Done'
    
    def mark_as_in_progress(self, request, queryset):
        """Bulk action to mark tasks as in progress."""
        updated = queryset.update(status=Task.IN_PROGRESS)
        self.message_user(request, f'Successfully marked {updated} task(s) as in progress.')
    mark_as_in_progress.short_description = 'Mark as In Progress'
    
    def mark_as_todo(self, request, queryset):
        """Bulk action to mark tasks as todo."""
        updated = queryset.update(status=Task.TODO)
        self.message_user(request, f'Successfully marked {updated} task(s) as todo.')
    mark_as_todo.short_description = 'Mark as To Do'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('task', 'author', 'content_preview', 'parent', 'created_at')
    list_filter = ('created_at', 'task')
    search_fields = ('content', 'author__username', 'task__title')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)
    actions = ['delete_with_replies']
    
    def content_preview(self, obj):
        """Show a preview of the comment content."""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'
    
    def delete_with_replies(self, request, queryset):
        """Custom action to delete comments with all replies."""
        count = queryset.count()
        # Django's CASCADE will handle child comments automatically
        queryset.delete()
        self.message_user(request, f'Successfully deleted {count} comment(s) and all replies.')
    delete_with_replies.short_description = 'Delete with all replies'


@admin.register(FileUpload)
class FileUploadAdmin(admin.ModelAdmin):
    list_display = ('filename', 'uploaded_by', 'content_type', 'object_id', 'uploaded_at')
    list_filter = ('uploaded_at', 'content_type')
    search_fields = ('file', 'uploaded_by__username')
    date_hierarchy = 'uploaded_at'
    readonly_fields = ('uploaded_at',)


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('task', 'user', 'action', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('task__title', 'user__username', 'action')
    date_hierarchy = 'timestamp'
    readonly_fields = ('timestamp',)
    
    def has_add_permission(self, request):
        """Prevent manual creation of activity logs."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Prevent editing of activity logs."""
        return False
