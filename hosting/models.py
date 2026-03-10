from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
import os


def website_upload_path(instance, filename):
    return f'uploads/{instance.slug}/{filename}'


class UserProfile(models.Model):
    """用户配置文件模型，添加权限级别字段"""
    PERMISSION_CHOICES = [
        ('guest', '游客'),
        ('user', '普通用户'),
        ('admin', '管理员'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    permission_level = models.CharField(
        max_length=20,
        choices=PERMISSION_CHOICES,
        default='guest',
        verbose_name='权限级别'
    )
    # 具体权限字段
    can_upload = models.BooleanField(default=False, verbose_name='可以上传网站')
    can_edit = models.BooleanField(default=False, verbose_name='可以编辑网站信息')
    can_access = models.BooleanField(default=True, verbose_name='可以访问网站')
    can_delete = models.BooleanField(default=False, verbose_name='可以删除网站')
    
    class Meta:
        verbose_name = '用户配置文件'
        verbose_name_plural = '用户配置文件'
    
    def __str__(self):
        return f'{self.user.username} - {self.permission_level}'


class Website(models.Model):
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('published', '已发布'),
        ('offline', '已下线'),
    ]

    name = models.CharField(max_length=200, verbose_name='网站名称')
    slug = models.SlugField(max_length=200, unique=True, verbose_name='网址标识')
    description = models.TextField(blank=True, verbose_name='网站描述')
    upload_file = models.FileField(upload_to=website_upload_path, verbose_name='上传文件')
    site_path = models.CharField(max_length=500, blank=True, verbose_name='网站路径')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='状态')
    visit_count = models.IntegerField(default=0, verbose_name='访问次数')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='作者', related_name='websites')

    class Meta:
        ordering = ['-created_at']
        verbose_name = '网站'
        verbose_name_plural = '网站'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_site_root(self):
        if self.site_path:
            return self.site_path
        return os.path.join('media', 'sites', self.slug)

    def has_index_html(self):
        site_root = self.get_site_root()
        index_path = os.path.join(site_root, 'index.html')
        return os.path.exists(index_path)


class Message(models.Model):
    """消息模型"""
    STATUS_CHOICES = [
        ('unread', '未读'),
        ('read', '已读'),
    ]
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages', verbose_name='接收者')
    subject = models.CharField(max_length=200, verbose_name='主题')
    content = models.TextField(verbose_name='内容')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unread', verbose_name='状态')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = '消息'
        verbose_name_plural = '消息'
    
    def __str__(self):
        return f"{self.subject} - {self.recipient.username}"


class PermissionLog(models.Model):
    """权限变更日志模型"""
    ACTION_CHOICES = [
        ('create', '创建'),
        ('update', '更新'),
        ('delete', '删除'),
    ]
    
    operator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='操作人')
    target_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='permission_logs', verbose_name='目标用户')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name='操作类型')
    permission_level = models.CharField(max_length=20, blank=True, verbose_name='权限级别')
    can_upload = models.BooleanField(null=True, blank=True, verbose_name='可以上传网站')
    can_edit = models.BooleanField(null=True, blank=True, verbose_name='可以编辑网站信息')
    can_access = models.BooleanField(null=True, blank=True, verbose_name='可以访问网站')
    can_delete = models.BooleanField(null=True, blank=True, verbose_name='可以删除网站')
    ip_address = models.CharField(max_length=50, blank=True, verbose_name='IP地址')
    user_agent = models.CharField(max_length=200, blank=True, verbose_name='用户代理')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='操作时间')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = '权限变更日志'
        verbose_name_plural = '权限变更日志'
    
    def __str__(self):
        return f"{self.operator.username} - {self.action} - {self.target_user.username}"

