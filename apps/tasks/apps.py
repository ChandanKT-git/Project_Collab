from django.apps import AppConfig


class TasksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.tasks'
    
    def ready(self):
        """Import signal handlers when the app is ready."""
        import apps.tasks.models  # noqa: F401
