# web项目托管平台 - 生产环境部署教程

## 1. 环境准备

### 1.1 服务器要求
- **操作系统**：Ubuntu 20.04 LTS 或 CentOS 7+
- **Python**：3.8 或更高版本
- **PostgreSQL**：12 或更高版本
- **Nginx**：1.18 或更高版本
- **内存**：至少 2GB
- **磁盘空间**：至少 20GB

### 1.2 系统更新

#### Ubuntu/Debian
```bash
sudo apt update && sudo apt upgrade -y
```

#### CentOS/RHEL
```bash
sudo yum update -y
```

## 2. PostgreSQL 数据库配置

### 2.1 安装 PostgreSQL

#### Ubuntu/Debian
```bash
sudo apt install postgresql postgresql-contrib -y
```

#### CentOS/RHEL
```bash
sudo yum install postgresql-server postgresql-contrib -y
sudo postgresql-setup --initdb
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 2.2 创建数据库和用户

1. **进入 PostgreSQL 命令行**：
   ```bash
sudo -u postgres psql
   ```

2. **创建数据库**：
   ```sql
   CREATE DATABASE webhosting;
   ```

3. **创建用户**：
   ```sql
   CREATE USER webhostinguser WITH PASSWORD 'your_strong_password';
   ```

4. **授予权限**：
   ```sql
   GRANT ALL PRIVILEGES ON DATABASE webhosting TO webhostinguser;
   ALTER USER webhostinguser WITH SUPERUSER;
   ```

5. **退出 PostgreSQL**：
   ```sql
   \q
   ```

## 3. 项目配置

### 3.1 克隆项目

```bash
cd /var/www
git clone your_repository_url webhosting
cd webhosting
```

### 3.2 创建虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3.3 安装依赖

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
```

### 3.4 修改 settings.py

编辑 `webHosting/settings.py` 文件：

```python
# 基本配置
DEBUG = False
ALLOWED_HOSTS = ['your_domain.com', 'www.your_domain.com']

# 数据库配置
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'webhosting',
        'USER': 'webhostinguser',
        'PASSWORD': 'your_strong_password',
        'HOST': 'localhost',
        'PORT': '',
    }
}

# 静态文件配置
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# 媒体文件配置
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# 安全配置
SECRET_KEY = 'your_secret_key'
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
```

### 3.5 环境变量配置

建议使用环境变量管理敏感信息，创建 `.env` 文件：

```bash
nano .env
```

内容：
```
SECRET_KEY=your_secret_key
DATABASE_URL=postgres://webhostinguser:your_strong_password@localhost:5432/webhosting
```

然后修改 `settings.py` 以使用环境变量：

```python
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')

# 数据库配置
import dj_database_url
db_from_env = dj_database_url.config(default=DATABASE_URL)
DATABASES = {'default': db_from_env}
```

## 4. 数据库迁移

```bash
python manage.py migrate
python manage.py createsuperuser
```

## 5. 静态文件处理

```bash
python manage.py collectstatic
```

## 6. Gunicorn 配置

### 6.1 创建 Gunicorn 配置文件

```bash
nano gunicorn.conf.py
```

内容：
```python
bind = '127.0.0.1:8000'
workers = 3
worker_class = 'sync'
timeout = 30
accesslog = '/var/log/gunicorn/access.log'
errorlog = '/var/log/gunicorn/error.log'
```

### 6.2 创建日志目录

```bash
sudo mkdir -p /var/log/gunicorn
sudo chown -R your_user:your_user /var/log/gunicorn
```

### 6.3 测试 Gunicorn

```bash
gunicorn --config gunicorn.conf.py webHosting.wsgi
```

## 7. Nginx 配置

### 7.1 安装 Nginx

#### Ubuntu/Debian
```bash
sudo apt install nginx -y
```

#### CentOS/RHEL
```bash
sudo yum install nginx -y
sudo systemctl start nginx
sudo systemctl enable nginx
```

### 7.2 创建 Nginx 配置文件

```bash
sudo nano /etc/nginx/sites-available/webhosting
```

内容：
```nginx
server {
    listen 80;
    server_name your_domain.com www.your_domain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name your_domain.com www.your_domain.com;
    
    ssl_certificate /etc/letsencrypt/live/your_domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your_domain.com/privkey.pem;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /var/www/webhosting/static/;
        expires 30d;
    }
    
    location /media/ {
        alias /var/www/webhosting/media/;
        expires 30d;
    }
}
```

### 7.3 启用配置

```bash
sudo ln -s /etc/nginx/sites-available/webhosting /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 8. SSL 证书配置

使用 Let's Encrypt 获取免费 SSL 证书：

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your_domain.com -d www.your_domain.com
```

## 9. 服务管理

### 9.1 创建 systemd 服务文件

```bash
sudo nano /etc/systemd/system/webhosting.service
```

内容：
```ini
[Unit]
Description=Gunicorn instance to serve webhosting
After=network.target

[Service]
User=your_user
Group=www-data
WorkingDirectory=/var/www/webhosting
ExecStart=/var/www/webhosting/venv/bin/gunicorn --config /var/www/webhosting/gunicorn.conf.py webHosting.wsgi
Restart=always

[Install]
WantedBy=multi-user.target
```

### 9.2 启动服务

```bash
sudo systemctl start webhosting
sudo systemctl enable webhosting
sudo systemctl status webhosting
```

## 10. 安全配置

### 10.1 防火墙配置

#### Ubuntu/Debian
```bash
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

#### CentOS/RHEL
```bash
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 10.2 权限设置

```bash
sudo chown -R your_user:www-data /var/www/webhosting
sudo chmod -R 755 /var/www/webhosting
sudo chmod -R 775 /var/www/webhosting/media
```

## 11. 部署流程

1. **更新代码**：
   ```bash
   cd /var/www/webhosting
   git pull
   ```

2. **激活虚拟环境**：
   ```bash
   source venv/bin/activate
   ```

3. **安装新依赖**：
   ```bash
   pip install -r requirements.txt
   ```

4. **运行数据库迁移**：
   ```bash
   python manage.py migrate
   ```

5. **收集静态文件**：
   ```bash
   python manage.py collectstatic --noinput
   ```

6. **重启服务**：
   ```bash
   sudo systemctl restart webhosting
   sudo systemctl restart nginx
   ```

## 12. 监控和维护

### 12.1 日志查看

- **Gunicorn 日志**：
  ```bash
tail -f /var/log/gunicorn/error.log
  ```

- **Nginx 日志**：
  ```bash
tail -f /var/log/nginx/error.log
  ```

### 12.2 定期备份

创建备份脚本：

```bash
nano backup.sh
```

内容：
```bash
#!/bin/bash

BACKUP_DIR="/var/backups/webhosting"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 备份数据库
sudo -u postgres pg_dump webhosting > $BACKUP_DIR/db_$DATE.sql

# 备份项目文件
tar -czf $BACKUP_DIR/files_$DATE.tar.gz /var/www/webhosting

# 删除7天前的备份
find $BACKUP_DIR -type f -mtime +7 -delete

echo "Backup completed: $DATE"
```

设置定时任务：
```bash
crontab -e
```

添加：
```
0 2 * * * /var/www/webhosting/backup.sh
```

## 13. 常见问题排查

### 13.1 502 Bad Gateway 错误
- 检查 Gunicorn 服务是否运行：
  ```bash
  sudo systemctl status webhosting
  ```
- 检查 Gunicorn 日志：
  ```bash
  tail -f /var/log/gunicorn/error.log
  ```

### 13.2 静态文件无法加载
- 检查静态文件目录权限：
  ```bash
  ls -la /var/www/webhosting/static/
  ```
- 检查 Nginx 配置中的静态文件路径是否正确

### 13.3 数据库连接错误
- 检查 PostgreSQL 服务是否运行：
  ```bash
  sudo systemctl status postgresql
  ```
- 检查数据库连接参数是否正确

## 14. 性能优化

1. **启用 Gzip 压缩**：在 Nginx 配置中添加：
   ```nginx
   gzip on;
   gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
   ```

2. **启用浏览器缓存**：在 Nginx 配置中添加：
   ```nginx
   location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
       expires 30d;
       add_header Cache-Control "public, no-transform";
   }
   ```

3. **增加 Gunicorn 工作进程数**：根据服务器 CPU 核心数调整 `gunicorn.conf.py` 中的 `workers` 数量

## 15. 总结

通过以上步骤，您已经成功在生产环境中部署了 web项目托管平台。该部署方案包括：

- 使用 PostgreSQL 作为数据库
- 使用 Gunicorn 作为 WSGI 服务器
- 使用 Nginx 作为反向代理和静态文件服务器
- 配置了 SSL 证书
- 设置了系统服务和防火墙
- 实现了定期备份

这样的部署方案可以确保您的 web项目托管平台在生产环境中稳定运行，同时具备良好的安全性和性能。