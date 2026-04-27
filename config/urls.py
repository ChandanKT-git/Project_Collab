"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from apps.core.views import home
from apps.accounts.views import SignupView
from apps.core.admin import system_statistics_view

urlpatterns = [
    # API endpoints (must be before catch-all)
    path('api/', include('apps.core.api_urls')),

    # Admin
    path('admin/statistics/', system_statistics_view, name='admin_statistics'),
    path('admin/', admin.site.urls),

    # Legacy Django template views (kept during migration)
    path('legacy/', home, name='home'),
    path('legacy/accounts/login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('legacy/accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('legacy/accounts/signup/', SignupView.as_view(), name='signup'),

    # Allauth URLs (includes Google OAuth callbacks)
    path('accounts/', include('allauth.urls')),

    # Legacy template routes (kept as fallback)
    path('legacy/teams/', include('apps.teams.urls')),
    path('legacy/tasks/', include('apps.tasks.urls')),
    path('legacy/notifications/', include('apps.notifications.urls')),
]

# Serve media and static files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += staticfiles_urlpatterns()

# React SPA catch-all — serves index.html for all non-API routes
# This must be LAST so it doesn't override API, admin, or static file routes
urlpatterns += [
    re_path(r'^(?!api/|admin/|accounts/|media/|static/|legacy/).*$',
            TemplateView.as_view(template_name='index.html'),
            name='react_spa'),
]

# Custom error handlers
handler400 = 'apps.core.error_handlers.handler400'
handler403 = 'apps.core.error_handlers.handler403'
handler404 = 'apps.core.error_handlers.handler404'
handler500 = 'apps.core.error_handlers.handler500'

