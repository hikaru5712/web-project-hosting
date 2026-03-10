from django.urls import path
from . import views

urlpatterns = [
    # JWT认证API
    path('api/login/', views.LoginView.as_view(), name='api_login'),
    path('api/refresh/', views.RefreshTokenView.as_view(), name='api_refresh'),
    path('api/logout/', views.LogoutView.as_view(), name='api_logout'),
]