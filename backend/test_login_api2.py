"""测试登录 API"""
import requests
import json
import sys

BASE_URL = 'http://localhost:8001/api'

print("=" * 60)
print("测试登录 API")
print("=" * 60)

form_data = {
    'username': 'test',
    'password': 'test123'
}

print(f"\n发送登录请求...")
response = requests.post(f'{BASE_URL}/users/login', data=form_data)
print(f'状态码: {response.status_code}')

try:
    data = response.json()
    print(f'响应:')
    print(json.dumps(data, ensure_ascii=False, indent=2))
    
    if data.get('code') == 200:
        print('\n' + '=' * 60)
        print('✓ 登录成功!')
        token = data.get('data', {}).get('access_token')
        if token:
            print(f'Token: {token[:80]}...')
        print('=' * 60)
        sys.exit(0)
    else:
        print('\n' + '=' * 60)
        print('✗ 登录失败')
        print(f'错误码: {data.get("code")}')
        print(f'错误消息: {data.get("message")}')
        print('=' * 60)
        sys.exit(1)
except Exception as e:
    print(f'错误: {e}')
    print(f'响应文本: {response.text}')
    sys.exit(1)
