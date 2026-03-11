import ctypes
import sys
import os

# 添加当前目录到Python导入路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def set_process_title(title):
    try:
        ctypes.windll.kernel32.SetConsoleTitleW(title)
    except:
        pass

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webHosting.settings')
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    set_process_title("WebHostingService - Django开发服务器")
    
    print("=" * 50)
    print("WebHosting 守护进程")
    print("Django开发服务器")
    print("=" * 50)
    print("")
    print("服务器正在启动...")
    print("访问地址: http://127.0.0.1:8000/")
    print("管理后台: http://127.0.0.1:8000/admin/")
    print("用户名: admin")
    print("密码: admin123")
    print("")
    print("=" * 50)
    print("在任务管理器中查找 'WebHostingService' 进程")
    print("=" * 50)
    print("")
    
    execute_from_command_line(['manage.py', 'runserver'])
