# web项目托管平台 - IP地址实时显示教程

## 1. IP地址抓取机制

web项目托管平台的权限日志功能会实时抓取用户的IP地址，用于审计和安全监控。

### 1.1 抓取原理

- **本地开发环境**：显示 `127.0.0.1`（本地回环地址）
- **生产环境**：显示真实的客户端IP地址

### 1.2 技术实现

IP地址抓取使用以下代码：

```python
# 在权限日志记录中
ip_address = request.META.get('REMOTE_ADDR', '')
```

## 2. 生产环境部署配置

### 2.1 直接部署（无代理）

如果直接部署Django应用，系统会自动通过 `REMOTE_ADDR` 获取客户端的真实IP地址，无需额外配置。

### 2.2 使用反向代理（如Nginx、Apache）

当使用反向代理时，需要配置代理服务器将真实IP传递给Django。

#### 2.2.1 Nginx配置示例

```nginx
server {
    listen 80;
    server_name example.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### 2.2.2 Django配置

在 `settings.py` 中添加：

```python
# 允许使用代理头
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# 可选：使用 django-ipware 库获取真实IP
# 安装：pip install django-ipware
```

### 2.3 云服务或负载均衡

大多数云服务（如AWS、阿里云）会在请求头中添加真实IP信息，Django默认会处理这些情况。

## 3. 权限日志中的IP地址显示

权限日志页面会显示以下信息：
- 操作人：执行权限变更的用户
- 目标用户：权限变更的对象
- 操作类型：创建、更新或删除
- 权限级别：变更后的权限级别
- 权限变更：具体权限的变更情况
- IP地址：执行操作时的客户端IP地址
- 操作时间：权限变更的时间

## 4. 故障排查

### 4.1 IP地址显示不正确

- **检查代理配置**：确保反向代理正确设置了 `X-Real-IP` 和 `X-Forwarded-For` 头
- **检查Django配置**：确保 `USE_X_FORWARDED_HOST` 已设置
- **检查网络环境**：确保网络连接正常，没有额外的网络层干扰

### 4.2 权限日志不显示

- 确保已运行数据库迁移：`python manage.py migrate`
- 确保用户有查看权限日志的权限（管理员或超级管理员）
- 检查服务器日志是否有错误信息

## 5. 最佳实践

- 在生产环境中始终使用HTTPS，保护数据传输
- 定期查看权限日志，监控异常的权限变更
- 配置适当的日志保留策略，平衡安全审计和存储成本
- 结合其他安全措施，如防火墙和入侵检测系统

---

**web项目托管平台** © 2026