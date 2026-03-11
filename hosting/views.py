from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import Http404, FileResponse, HttpResponseForbidden
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
import os
import mimetypes
from .models import Website, UserProfile, Message, PermissionLog
from .forms import WebsiteUploadForm, UserRegistrationForm, UserLoginForm, WebsiteEditForm
from .utils import extract_archive


def home(request):
    websites = Website.objects.filter(status='published')
    return render(request, 'hosting/home.html', {'websites': websites})


def upload_website(request):
    # 检查用户权限
    if not request.user.is_authenticated:
        return redirect('login')
    
    # 超级用户直接跳过权限检查
    if not request.user.is_superuser:
        try:
            user_profile = request.user.profile
            if not user_profile.can_upload:
                return HttpResponseForbidden('权限不足：您没有上传项目的权限')
        except UserProfile.DoesNotExist:
            return HttpResponseForbidden('权限不足：您的用户配置文件不存在')
    
    if request.method == 'POST':
        form = WebsiteUploadForm(request.POST, request.FILES)
        if form.is_valid():
            website = form.save(commit=False)
            # 设置作者为当前登录用户
            website.author = request.user
            
            # 如果用户没有填写slug，则从上传的文件名生成
            if not website.slug and 'upload_file' in request.FILES:
                # 获取上传文件的文件名（不含路径）
                filename = os.path.basename(request.FILES['upload_file'].name)
                # 移除文件扩展名
                slug_name = os.path.splitext(filename)[0]
                # 替换空格为连字符，移除特殊字符，确保符合URL格式
                import re
                slug_name = re.sub(r'[^a-zA-Z0-9]+', '-', slug_name)
                slug_name = slug_name.strip('-')
                
                # 确保slug唯一
                original_slug = slug_name
                counter = 1
                while Website.objects.filter(slug=slug_name).exists():
                    slug_name = f"{original_slug}-{counter}"
                    counter += 1
                
                website.slug = slug_name
            
            # 保存网站信息
            website.save()
            
            target_dir = os.path.join(settings.MEDIA_ROOT, 'sites', website.slug)
            file_path = website.upload_file.path
            
            try:
                extract_archive(file_path, target_dir)
                website.site_path = os.path.join('media', 'sites', website.slug)
                website.status = 'published'
                website.save()
                messages.success(request, '网站上传成功！')
                return redirect('website_detail', slug=website.slug)
            except Exception as e:
                messages.error(request, f'解压失败: {str(e)}')
                website.delete()
    else:
        form = WebsiteUploadForm()
    
    return render(request, 'hosting/upload.html', {'form': form})


def website_detail(request, slug):
    website = get_object_or_404(Website, slug=slug)
    # 更新访问次数
    website.visit_count += 1
    website.save()
    return render(request, 'hosting/detail.html', {'website': website})


def serve_website(request, slug, path=''):
    website = get_object_or_404(Website, slug=slug, status='published')

    # 只在访问主页面或根路径时增加访问次数
    if not path or path == 'index.html':
        website.visit_count += 1
        website.save()

    # 确保site_root是正确的路径
    site_root = os.path.join(str(settings.MEDIA_ROOT), 'sites', slug)
    print(f"Site root: {site_root}")
    print(f"Site root exists: {os.path.exists(site_root)}")
    
    # 添加调试信息
    print(f"原始路径: {path}")

    if not path:
        path = 'index.html'

    # 处理 ES6 模块相对路径问题
    # 当路径包含类似 'js/script.js/earth.js' 时，提取真实路径
    original_path = path
    
    # 移除路径中所有数字后缀（如 /1, /2 等）
    # 分割路径并过滤掉数字部分
    parts = path.split('/')
    filtered_parts = []
    for part in parts:
        # 跳过纯数字的部分
        if not part.isdigit():
            filtered_parts.append(part)
    path = '/'.join(filtered_parts)
    
    # 移除路径末尾的斜杠
    path = path.rstrip('/')
    
    # 处理所有文件类型的路径问题，不仅仅是 .js 文件
    # 当路径中包含文件扩展名后又有其他路径时，提取真实路径
    parts = path.split('/')
    
    # 找到最后一个包含文件扩展名的部分
    file_part = None
    for part in reversed(parts):
        if '.' in part:
            file_part = part
            break
    
    if file_part:
        # 找到最后一个文件部分的位置
        file_index = parts.index(file_part)
        # 重建路径，只保留目录部分和最后一个文件部分
        # 例如：js/script.js/earth.js -> js/earth.js
        # 例如：js/earth.js/1 -> js/earth.js
        # 例如：css/style.css/1 -> css/style.css
        dir_parts = parts[:file_index]
        path = '/'.join(dir_parts + [file_part])
        print(f"处理后的路径: {path}")

    # 移除路径末尾的斜杠
    path = path.rstrip('/')
    print(f"最终路径: {path}")

    # 规范化路径，防止路径遍历攻击
    file_path = os.path.join(site_root, path)
    file_path = os.path.normpath(file_path)

    if not file_path.startswith(os.path.normpath(site_root)):
        raise Http404('无效的路径')

    # 如果是目录，尝试查找 index.html
    if os.path.isdir(file_path):
        index_path = os.path.join(file_path, 'index.html')
        if os.path.exists(index_path):
            file_path = index_path
        else:
            raise Http404('目录不存在 index.html')

    if not os.path.exists(file_path):
        raise Http404('文件不存在')

    # 设置正确的 MIME 类型
    content_type, _ = mimetypes.guess_type(file_path)

    # 为不同文件类型设置正确的 MIME 类型
    if content_type is None:
        ext = os.path.splitext(file_path)[1].lower()
        mime_types = {
            '.js': 'application/javascript',
            '.mjs': 'application/javascript',
            '.css': 'text/css',
            '.html': 'text/html',
            '.json': 'application/json',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml',
            '.ico': 'image/x-icon',
            '.woff': 'font/woff',
            '.woff2': 'font/woff2',
            '.ttf': 'font/ttf',
            '.eot': 'application/vnd.ms-fontobject',
        }
        content_type = mime_types.get(ext, 'application/octet-stream')

    # 确保 JavaScript 文件使用正确的 MIME 类型（包括 ES6 模块）
    if file_path.endswith('.js') or file_path.endswith('.mjs'):
        content_type = 'application/javascript'

    # 对于所有 HTML 文件，添加 <base> 标签来帮助浏览器正确解析相对路径
    if file_path.endswith('.html'):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 构建 base URL
            base_url = f'/site/{slug}/'

            # 在 <head> 标签后添加 <base> 标签
            head_end = content.find('</head>')
            if head_end != -1:
                base_tag = f'<base href="{base_url}">'
                content = content[:head_end] + base_tag + content[head_end:]

            # 处理绝对路径的资源引用，将 /assets/ 和 /libs/ 等路径改为相对路径
            import re
            # 替换绝对路径的资源引用
            content = re.sub(r'(src|href)="/(assets|libs|vite\.svg)', r'\1="./\2', content)

            # 返回修改后的内容
            from django.http import HttpResponse
            response = HttpResponse(content, content_type='text/html; charset=utf-8')
        except Exception as e:
            # 如果修改失败，返回原始文件
            response = FileResponse(open(file_path, 'rb'), content_type=content_type)
    else:
        response = FileResponse(open(file_path, 'rb'), content_type=content_type)

    # 添加 CORS 头部，允许跨域请求（如果需要）
    response['Access-Control-Allow-Origin'] = '*'

    return response


def delete_website(request, slug):
    # 检查用户权限
    if not request.user.is_authenticated:
        return redirect('login')
    
    try:
        user_profile = request.user.profile
        if not user_profile.can_delete and not request.user.is_superuser:
            return HttpResponseForbidden('权限不足：您没有删除项目的权限')
    except UserProfile.DoesNotExist:
        return HttpResponseForbidden('权限不足：您的用户配置文件不存在')
    
    website = get_object_or_404(Website, slug=slug)
    
    # 检查是否是作者或超级管理员
    if website.author != request.user and not request.user.is_superuser:
        return HttpResponseForbidden('权限不足：您只能删除自己上传的项目')
    if request.method == 'POST':
        import shutil
        site_dir = os.path.join(settings.MEDIA_ROOT, 'sites', slug)
        if os.path.exists(site_dir):
            shutil.rmtree(site_dir)
        
        # 检查是否需要删除原始项目包
        if request.POST.get('delete_original') == 'on':
            # 获取原始项目包的路径
            if website.upload_file and os.path.exists(website.upload_file.path):
                os.remove(website.upload_file.path)
                # 尝试删除空的上传目录
                try:
                    upload_dir = os.path.dirname(website.upload_file.path)
                    if os.path.exists(upload_dir) and len(os.listdir(upload_dir)) == 0:
                        os.rmdir(upload_dir)
                except:
                    pass
        
        website.delete()
        messages.success(request, '网站已删除！')
        return redirect('home')
    return render(request, 'hosting/confirm_delete.html', {'website': website})


def edit_website(request, slug):
    # 检查用户权限
    if not request.user.is_authenticated:
        return redirect('login')
    
    try:
        user_profile = request.user.profile
        if not user_profile.can_edit and not request.user.is_superuser:
            return HttpResponseForbidden('权限不足：您没有编辑项目的权限')
    except UserProfile.DoesNotExist:
        return HttpResponseForbidden('权限不足：您的用户配置文件不存在')
    
    website = get_object_or_404(Website, slug=slug)
    
    # 检查是否是作者或超级管理员
    if website.author != request.user and not request.user.is_superuser:
        return HttpResponseForbidden('权限不足：您只能编辑自己上传的项目')
    
    if request.method == 'POST':
        form = WebsiteEditForm(request.POST, instance=website)
        if form.is_valid():
            form.save()
            messages.success(request, '网站信息已更新！')
            return redirect('website_detail', slug=website.slug)
    else:
        form = WebsiteEditForm(instance=website)
    
    return render(request, 'hosting/edit_website.html', {'form': form, 'website': website})


def register(request):
    """用户注册视图"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # 创建用户
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            # 创建用户配置文件，默认权限级别为普通用户，拥有所有网站操作权限
            UserProfile.objects.create(
                user=user, 
                permission_level='user',
                can_upload=True,
                can_edit=True,
                can_access=True,
                can_delete=True
            )
            
            # 记录权限变更日志
            from .models import PermissionLog
            PermissionLog.objects.create(
                operator=user,  # 新用户自己注册
                target_user=user,
                action='create',
                permission_level='user',
                can_upload=True,
                can_edit=True,
                can_access=True,
                can_delete=True,
                ip_address=request.META.get('REMOTE_ADDR', ''),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:200]
            )
            
            messages.success(request, '注册成功！请登录。')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'hosting/register.html', {'form': form})


def user_login(request):
    """用户登录视图"""
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # 存储用户登录状态到session
                request.session['is_logged_in'] = True
                messages.success(request, '登录成功！')
                return redirect('home')
            else:
                messages.error(request, '用户名或密码错误')
    else:
        form = UserLoginForm()
    return render(request, 'hosting/login.html', {'form': form})


def user_logout(request):
    """用户登出视图"""
    # 获取当前用户
    current_user = request.user
    # 执行标准登出操作
    logout(request)
    # 清除登录状态
    if 'is_logged_in' in request.session:
        del request.session['is_logged_in']
    # 删除当前用户的所有会话记录
    from django.contrib.sessions.models import Session
    from django.utils import timezone
    try:
        # 获取所有活跃会话
        active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
        for session in active_sessions:
            try:
                session_data = session.get_decoded()
                if '_auth_user_id' in session_data:
                    user_id = int(session_data['_auth_user_id'])
                    if user_id == current_user.id:
                        session.delete()
            except:
                pass
    except:
        pass
    messages.success(request, '已成功登出')
    return redirect('home')


@login_required
def user_management(request):
    """用户管理视图"""
    # 检查用户权限，只有管理员和超级管理员可以访问
    try:
        user_profile = request.user.profile
        if user_profile.permission_level != 'admin' and not request.user.is_superuser:
            return HttpResponseForbidden('权限不足：您没有访问用户管理页面的权限')
    except UserProfile.DoesNotExist:
        # 如果没有用户配置文件，但用户是超级管理员，允许访问
        if not request.user.is_superuser:
            return HttpResponseForbidden('权限不足：您没有访问用户管理页面的权限')
    
    # 获取所有用户及其配置文件
    users = User.objects.all()
    user_profiles = UserProfile.objects.all()
    
    # 模拟用户登录状态跟踪（实际项目中需要实现更复杂的会话管理）
    # 这里使用一个简单的内存存储来模拟，实际项目中应该使用缓存或数据库
    from django.contrib.sessions.models import Session
    from django.utils import timezone
    
    # 获取所有活跃的会话
    active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
    
    # 提取活跃用户的ID
    active_user_ids = []
    for session in active_sessions:
        try:
            session_data = session.get_decoded()
            if '_auth_user_id' in session_data:
                active_user_ids.append(int(session_data['_auth_user_id']))
        except:
            pass
    
    context = {
        'users': users,
        'user_profiles': user_profiles,
        'active_user_ids': active_user_ids
    }
    
    return render(request, 'hosting/user_management.html', context)


@login_required
def user_edit(request, user_id):
    """编辑用户视图"""
    # 检查用户权限，只有管理员和超级管理员可以访问
    try:
        user_profile = request.user.profile
        if user_profile.permission_level != 'admin' and not request.user.is_superuser:
            return HttpResponseForbidden('没有权限访问此页面')
    except UserProfile.DoesNotExist:
        # 如果没有用户配置文件，但用户是超级管理员，允许访问
        if not request.user.is_superuser:
            return HttpResponseForbidden('没有权限访问此页面')
    
    user = get_object_or_404(User, id=user_id)
    try:
        user_profile = user.profile
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.create(user=user, permission_level='guest')
    
    if request.method == 'POST':
        # 处理用户信息更新
        user.username = request.POST.get('username')
        email = request.POST.get('email')
        if email:
            user.email = email
        else:
            user.email = ''
        user.save()
        
        # 处理权限级别更新
        permission_level = request.POST.get('permission_level')
        if permission_level:
            user_profile.permission_level = permission_level
        
        # 处理具体权限更新
        user_profile.can_upload = request.POST.get('perm_upload') == 'on'
        user_profile.can_edit = request.POST.get('perm_edit') == 'on'
        user_profile.can_access = request.POST.get('perm_access') == 'on'
        user_profile.can_delete = request.POST.get('perm_delete') == 'on'
        
        user_profile.save()
        
        # 记录权限变更日志
        from .models import PermissionLog
        PermissionLog.objects.create(
            operator=request.user,
            target_user=user,
            action='update',
            permission_level=user_profile.permission_level,
            can_upload=user_profile.can_upload,
            can_edit=user_profile.can_edit,
            can_access=user_profile.can_access,
            can_delete=user_profile.can_delete,
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:200]
        )
        
        messages.success(request, '用户信息已更新')
        return redirect('user_management')
    
    context = {
        'user': user,
        'user_profile': user_profile
    }
    
    return render(request, 'hosting/user_edit.html', context)


@login_required
def user_delete(request, user_id):
    """删除用户视图"""
    # 检查用户权限，只有管理员和超级管理员可以访问
    try:
        user_profile = request.user.profile
        if user_profile.permission_level != 'admin' and not request.user.is_superuser:
            return HttpResponseForbidden('没有权限访问此页面')
    except UserProfile.DoesNotExist:
        # 如果没有用户配置文件，但用户是超级管理员，允许访问
        if not request.user.is_superuser:
            return HttpResponseForbidden('没有权限访问此页面')
    
    user = get_object_or_404(User, id=user_id)
    
    # 防止删除超级用户
    if user.is_superuser:
        messages.error(request, '不能删除超级用户')
        return redirect('user_management')
    
    # 防止删除guest用户
    if user.username == 'guest':
        messages.error(request, '不能删除游客用户')
        return redirect('user_management')
    
    if request.method == 'POST':
        # 删除用户配置文件
        try:
            user.profile.delete()
        except UserProfile.DoesNotExist:
            pass
        # 记录权限变更日志
        user_profile = None
        if hasattr(user, 'profile'):
            user_profile = user.profile
        
        PermissionLog.objects.create(
            operator=request.user,
            target_user=user,
            action='delete',
            permission_level=user_profile.permission_level if user_profile else '',
            can_upload=user_profile.can_upload if user_profile else None,
            can_edit=user_profile.can_edit if user_profile else None,
            can_access=user_profile.can_access if user_profile else None,
            can_delete=user_profile.can_delete if user_profile else None,
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:200]
        )
        
        # 删除用户
        user.delete()
        messages.success(request, '用户已删除')
        return redirect('user_management')
    
    context = {
        'user': user
    }
    
    return render(request, 'hosting/user_delete.html', context)


def my_projects(request):
    """我的项目页面视图"""
    # 检查用户权限，只有登录用户可以访问
    if not request.user.is_authenticated:
        return redirect('login')
    
    try:
        user_profile = request.user.profile
        if user_profile.permission_level == 'guest':
            return HttpResponseForbidden('权限不足：您没有访问我的项目页面的权限')
    except UserProfile.DoesNotExist:
        return HttpResponseForbidden('权限不足：您的用户配置文件不存在')
    
    # 获取当前用户上传的网站项目
    websites = Website.objects.filter(author=request.user, status='published')
    
    return render(request, 'hosting/my_projects.html', {'websites': websites})


@login_required
def permission_logs(request):
    """权限变更日志视图"""
    # 检查用户权限，只有管理员和超级管理员可以访问
    try:
        user_profile = request.user.profile
        if user_profile.permission_level != 'admin' and not request.user.is_superuser:
            return HttpResponseForbidden('没有权限访问此页面')
    except UserProfile.DoesNotExist:
        # 如果没有用户配置文件，但用户是超级管理员，允许访问
        if not request.user.is_superuser:
            return HttpResponseForbidden('没有权限访问此页面')
    
    # 获取权限变更日志
    logs = PermissionLog.objects.all().order_by('-created_at')
    
    context = {
        'logs': logs
    }
    
    return render(request, 'hosting/permission_logs.html', context)


def messages_view(request):
    """消息中心视图"""
    # 检查用户权限，只有登录用户可以访问
    if not request.user.is_authenticated:
        return redirect('login')
    
    try:
        user_profile = request.user.profile
        if user_profile.permission_level == 'guest':
            return HttpResponseForbidden('权限不足：您没有访问消息中心的权限')
    except UserProfile.DoesNotExist:
        return HttpResponseForbidden('权限不足：您的用户配置文件不存在')
    
    # 获取当前用户的消息
    user_messages = Message.objects.filter(recipient=request.user).order_by('-created_at')
    
    return render(request, 'hosting/messages.html', {'user_messages': user_messages})


def message_detail(request, message_id):
    """消息详情视图"""
    # 检查用户权限，只有登录用户可以访问
    if not request.user.is_authenticated:
        return redirect('login')
    
    try:
        user_profile = request.user.profile
        if user_profile.permission_level == 'guest':
            return HttpResponseForbidden('权限不足：您没有访问消息详情的权限')
    except UserProfile.DoesNotExist:
        return HttpResponseForbidden('权限不足：您的用户配置文件不存在')
    
    # 获取消息
    message = get_object_or_404(Message, id=message_id, recipient=request.user)
    
    # 标记消息为已读
    if message.status == 'unread':
        message.status = 'read'
        message.save()
    
    return render(request, 'hosting/message_detail.html', {'message': message})


def delete_message(request, message_id):
    """删除消息视图"""
    # 检查用户权限，只有登录用户可以访问
    if not request.user.is_authenticated:
        return redirect('login')
    
    try:
        user_profile = request.user.profile
        if user_profile.permission_level == 'guest':
            return HttpResponseForbidden('权限不足：您没有删除消息的权限')
    except UserProfile.DoesNotExist:
        return HttpResponseForbidden('权限不足：您的用户配置文件不存在')
    
    # 获取消息
    message = get_object_or_404(Message, id=message_id, recipient=request.user)
    
    if request.method == 'POST':
        message.delete()
        messages.success(request, '消息已删除！')
        return redirect('messages')
    
    return render(request, 'hosting/message_detail.html', {'message': message})

