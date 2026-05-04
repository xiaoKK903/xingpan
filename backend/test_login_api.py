"""测试登录 API"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import requests
import json

BASE_URL = "http://localhost:8001/api"

def test_health():
    """测试健康检查"""
    try:
        response = requests.get(f"{BASE_URL[:-4]}/health")
        print(f"健康检查 - 状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        return True
    except Exception as e:
        print(f"健康检查失败: {e}")
        return False

def test_login(username, password):
    """测试登录"""
    try:
        form_data = {
            'username': username,
            'password': password
        }
        response = requests.post(f"{BASE_URL}/users/login", data=form_data)
        print(f"\n登录测试 - 状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        try:
            data = response.json()
            print(f"响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
            return data
        except:
            print(f"响应文本: {response.text}")
            return None
    except Exception as e:
        print(f"登录请求失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_root():
    """测试根路径"""
    try:
        response = requests.get(f"{BASE_URL[:-4]}/")
        print(f"\n根路径测试 - 状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"根路径测试失败: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("后端 API 测试")
    print("=" * 60)
    
    test_root()
    test_health()
    
    print("\n" + "=" * 60)
    print("测试登录 (使用 test 用户)")
    print("=" * 60)
    
    result = test_login("test", "test123")
    
    if result and result.get('code') == 200:
        print("\n✓ 登录成功!")
        token = result.get('data', {}).get('access_token')
        if token:
            print(f"Token: {token[:50]}...")
    else:
        print("\n✗ 登录失败或返回错误")
        if result:
            print(f"错误码: {result.get('code')}")
            print(f"错误消息: {result.get('message')}")
