from django.urls import path
from . import views

urlpatterns = [
    path('', views.task_list, name='task_list'),
    path('create/', views.task_create, name='task_create'),
    path('<int:pk>/', views.task_detail, name='task_detail'),
    path('<int:pk>/update/', views.task_update, name='task_update'),
    path('<int:pk>/delete/', views.task_delete, name='task_delete'),
    path('<int:task_pk>/comment/', views.comment_create, name='comment_create'),
    path('comment/<int:comment_pk>/reply/', views.comment_reply, name='comment_reply'),
    path('comment/<int:comment_pk>/delete/', views.comment_delete, name='comment_delete'),
    path('<int:task_pk>/upload/', views.file_upload_task, name='file_upload_task'),
    path('comment/<int:comment_pk>/upload/', views.file_upload_comment, name='file_upload_comment'),
    path('file/<int:file_pk>/download/', views.file_download, name='file_download'),
    path('file/<int:file_pk>/delete/', views.file_delete, name='file_delete'),
]
