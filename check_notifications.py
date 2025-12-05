#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.notifications.models import Notification

print(f"\nTotal notifications: {Notification.objects.count()}")
print("\nRecent notifications:")
for n in Notification.objects.all().order_by('-created_at')[:10]:
    print(f"  [{n.notification_type}] {n.recipient.username}: {n.message}")
    print(f"    Read: {n.is_read}, Created: {n.created_at}")
