from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_website, name='upload_website'),
    path('website/<slug:slug>/', views.website_detail, name='website_detail'),
    path('site/<slug:slug>/', views.serve_website, name='serve_website'),
    path('site/<slug:slug>/<path:path>', views.serve_website, name='serve_website_with_path'),
    path('website/<slug:slug>/delete/', views.delete_website, name='delete_website'),
    path('website/<slug:slug>/edit/', views.edit_website, name='edit_website'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('user_management/', views.user_management, name='user_management'),
    path('user/<int:user_id>/edit/', views.user_edit, name='user_edit'),
    path('user/<int:user_id>/delete/', views.user_delete, name='user_delete'),
    path('my_projects/', views.my_projects, name='my_projects'),
    path('permission_logs/', views.permission_logs, name='permission_logs'),
    path('messages/', views.messages_view, name='messages'),
    path('messages/<int:message_id>/', views.message_detail, name='message_detail'),
    path('messages/<int:message_id>/delete/', views.delete_message, name='delete_message'),
]

