import requests
import json

# 测试登录
print("测试登录...")
login_response = requests.post('http://127.0.0.1:8000/api/login/', json={'username': 'admin', 'password': 'admin123'})
print('Status code:', login_response.status_code)
print('Response:', json.dumps(login_response.json(), indent=2))

if login_response.status_code == 200:
    refresh_token = login_response.json()['refresh']
    
    # 测试刷新token
    print("\n测试刷新token...")
    refresh_response = requests.post('http://127.0.0.1:8000/api/refresh/', json={'refresh': refresh_token})
    print('Status code:', refresh_response.status_code)
    print('Response:', json.dumps(refresh_response.json(), indent=2))
    
    # 测试退出
    print("\n测试退出...")
    logout_response = requests.post('http://127.0.0.1:8000/api/logout/', json={'refresh': refresh_token})
    print('Status code:', logout_response.status_code)
    print('Response:', json.dumps(logout_response.json(), indent=2))