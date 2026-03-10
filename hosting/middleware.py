from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import User
from .models import UserProfile, Message


class GuestLoginMiddleware(MiddlewareMixin):
    """游客登录中间件"""
    def process_request(self, request):
        if not request.user.is_authenticated:
            # 检查是否有guest用户，如果没有则创建
            try:
                guest_user = User.objects.get(username='guest')
            except User.DoesNotExist:
                guest_user = User.objects.create_user(
                    username='guest',
                    password='guest123'
                )
                # 创建游客用户的配置文件
                UserProfile.objects.create(
                    user=guest_user,
                    permission_level='guest',
                    can_upload=False,
                    can_edit=False,
                    can_access=True,
                    can_delete=False
                )
            # 登录游客用户
            from django.contrib.auth import login
            login(request, guest_user, backend='django.contrib.auth.backends.ModelBackend')


class PermissionMiddleware(MiddlewareMixin):
    """权限中间件"""
    def process_request(self, request):
        if request.user.is_authenticated:
            # 确保用户有配置文件
            try:
                user_profile = request.user.profile
            except UserProfile.DoesNotExist:
                # 创建默认配置文件
                UserProfile.objects.create(
                    user=request.user,
                    permission_level='user',
                    can_upload=True,
                    can_edit=True,
                    can_access=True,
                    can_delete=True
                )


class MessageMiddleware(MiddlewareMixin):
    """消息中间件，为所有请求添加未读消息数量"""
    
    def process_request(self, request):
        """处理请求，添加未读消息数量到请求对象"""
        if hasattr(request, 'user') and request.user.is_authenticated:
            # 计算未读消息数量
            unread_count = Message.objects.filter(
                recipient=request.user,
                status='unread'
            ).count()
            # 将未读消息数量添加到请求对象
            request.unread_count = unread_count
