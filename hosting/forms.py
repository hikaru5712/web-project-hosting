from django import forms
from django.contrib.auth.models import User
from .models import Website, UserProfile


class WebsiteUploadForm(forms.ModelForm):
    class Meta:
        model = Website
        fields = ['name', 'slug', 'description', 'upload_file']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'upload_file': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean_upload_file(self):
        file = self.cleaned_data['upload_file']
        if not (file.name.endswith('.zip') or file.name.endswith('.7z')):
            raise forms.ValidationError('只支持 .zip 或 .7z 格式的文件')
        return file
    
    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        # 如果用户没有填写slug，暂时返回空值，在视图中处理
        if not slug:
            return slug
        
        # 替换空格为连字符，移除特殊字符，确保符合URL格式
        import re
        slug = re.sub(r'[^a-zA-Z0-9]+', '-', slug)
        slug = slug.strip('-')
        
        # 确保slug唯一
        original_slug = slug
        counter = 1
        while Website.objects.filter(slug=slug).exists():
            slug = f"{original_slug}-{counter}"
            counter += 1
        
        return slug


class WebsiteEditForm(forms.ModelForm):
    class Meta:
        model = Website
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class UserRegistrationForm(forms.ModelForm):
    """用户注册表单"""
    password = forms.CharField(label='密码', widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'off'}))
    confirm_password = forms.CharField(label='确认密码', widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'off'}))
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = False
    
    def clean_confirm_password(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError('两次输入的密码不一致')
        return confirm_password


class UserLoginForm(forms.Form):
    """用户登录表单"""
    username = forms.CharField(label='用户名', widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}))
    password = forms.CharField(label='密码', widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'off'}))
