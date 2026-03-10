from django.contrib.auth import login
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.request import Request


class TokenAuthenticationMiddleware:
    """Token认证中间件"""
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # 检查是否有Authorization头
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if auth_header and auth_header.startswith('Bearer '):
            try:
                # 创建一个DRF请求对象
                drf_request = Request(request)
                # 使用JWT认证
                jwt_auth = JWTAuthentication()
                user, token = jwt_auth.authenticate(drf_request)
                
                if user:
                    # 登录用户
                    login(request, user)
            except Exception:
                # Token无效，继续使用当前用户
                pass
        
        return self.get_response(request)