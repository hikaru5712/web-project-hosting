# JWT认证系统使用说明

## 1. 系统概述

本网站托管平台采用基于JWT（JSON Web Token）的认证系统，支持多用户同时登录和切换，提高了系统的灵活性和安全性。

## 2. 主要功能

### 2.1 多用户同时登录
- 支持在同一浏览器中同时登录多个用户
- 使用localStorage存储多个用户的token信息
- 提供用户切换功能，方便在不同用户间快速切换

### 2.2 自动登录与退出
- 用户关闭浏览器后，登录状态会自动清除
- 支持手动退出登录，清除用户token
- token有效期为2小时，过期后需要重新登录

### 2.3 权限管理
- 基于Token的权限验证
- 支持细粒度的权限控制（上传、编辑、访问、删除）
- 与现有的权限系统无缝集成

## 3. 使用方法

### 3.1 登录
1. 访问登录页面：`http://127.0.0.1:8000/login/`
2. 输入用户名和密码
3. 点击登录按钮
4. 系统会自动存储token并跳转到首页

### 3.2 切换用户
1. 登录多个用户后，在导航栏的用户下拉菜单中会显示"切换用户"选项
2. 点击要切换的用户名
3. 系统会自动切换到该用户的登录状态

### 3.3 退出登录
1. 在导航栏的用户下拉菜单中点击"退出"选项
2. 系统会清除当前用户的token并跳转到登录页面

## 4. API接口

### 4.1 登录接口
- URL: `/api/login/`
- 方法: POST
- 请求参数:
  ```json
  {
    "username": "admin",
    "password": "admin123"
  }
  ```
- 响应:
  ```json
  {
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user_id": 1,
    "username": "admin",
    "permission_level": "admin"
  }
  ```

### 4.2 刷新token接口
- URL: `/api/refresh/`
- 方法: POST
- 请求参数:
  ```json
  {
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
  ```
- 响应:
  ```json
  {
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
  ```

### 4.3 退出接口
- URL: `/api/logout/`
- 方法: POST
- 请求参数:
  ```json
  {
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
  ```
- 响应:
  ```json
  {
    "message": "退出成功"
  }
  ```

## 5. 技术实现

### 5.1 后端
- 使用Django REST Framework和Simple JWT库
- 实现了基于Token的认证中间件
- 支持token的生成、刷新和黑名单管理

### 5.2 前端
- 使用localStorage存储用户token
- 实现了用户切换功能
- 与后端API接口集成

## 6. 注意事项

1. 请妥善保管您的登录凭证，不要与他人共享
2. 长时间不使用系统时，建议手动退出登录
3. 如果遇到登录问题，请检查用户名和密码是否正确
4. 如token过期，请重新登录获取新的token

## 7. 故障排除

### 7.1 登录失败
- 检查用户名和密码是否正确
- 确保用户账号存在且未被禁用

### 7.2 token过期
- 重新登录获取新的token
- 检查token的有效期设置

### 7.3 用户切换失败
- 确保已登录多个用户
- 检查localStorage是否正常工作

## 8. 版本信息

- 版本: 1.2.0
- 发布日期: 2026-03-04
- 主要功能: 多用户同时登录、Token认证、用户切换
