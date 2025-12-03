from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'sender', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('recipient__username', 'sender__username', 'message')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        """Bulk action to mark notifications as read."""
        updated = queryset.update(is_read=True)
        self.message_user(request, f'Successfully marked {updated} notification(s) as read.')
    mark_as_read.short_description = 'Mark as read'
    
    def mark_as_unread(self, request, queryset):
        """Bulk action to mark notifications as unread."""
        updated = queryset.update(is_read=False)
        self.message_user(request, f'Successfully marked {updated} notification(s) as unread.')
    mark_as_unread.short_description = 'Mark as unread'
