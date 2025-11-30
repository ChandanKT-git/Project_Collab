from django.urls import path
from . import views

urlpatterns = [
    path('', views.team_list, name='team_list'),
    path('create/', views.team_create, name='team_create'),
    path('<int:pk>/', views.team_detail, name='team_detail'),
    path('<int:pk>/update/', views.team_update, name='team_update'),
    path('<int:pk>/delete/', views.team_delete, name='team_delete'),
    path('<int:pk>/add-member/', views.add_member, name='add_member'),
    path('<int:pk>/remove-member/<int:user_id>/', views.remove_member, name='remove_member'),
    path('<int:pk>/change-role/<int:user_id>/', views.change_member_role, name='change_member_role'),
]
