"""
调试竞猜系统接口
"""

import requests
import json

BASE_URL = "http://localhost:8001/api"


def login(username, password):
    url = f"{BASE_URL}/users/login"
    files = {
        "username": (None, username),
        "password": (None, password)
    }
    
    try:
        response = requests.post(url, files=files, timeout=10)
        result = response.json()
        
        if result.get("code") == 200:
            token = result["data"].get("access_token") or result["data"].get("token")
            return token
        return None
    except:
        return None


def test_list_sessions(token):
    print("\n" + "="*60)
    print("  测试 list-optimized 接口")
    print("="*60)
    
    url = f"{BASE_URL}/prediction/list-optimized"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        return response.json()
    except Exception as e:
        print(f"错误: {e}")
        return None


def test_system_status(token):
    print("\n" + "="*60)
    print("  测试 prediction/system-status 接口")
    print("="*60)
    
    url = f"{BASE_URL}/prediction/system-status"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        return response.json()
    except Exception as e:
        print(f"错误: {e}")
        return None


def test_my_tickets(token):
    print("\n" + "="*60)
    print("  测试 my-tickets 接口")
    print("="*60)
    
    url = f"{BASE_URL}/star-resonance/my-tickets"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        return response.json()
    except Exception as e:
        print(f"错误: {e}")
        return None


def check_routes():
    print("\n" + "="*60)
    print("  检查可用路由")
    print("="*60)
    
    import sys
    sys.path.insert(0, "d:\\星盘查询\\backend")
    
    try:
        from app.main import app
        print("\n已注册的路由（包含 prediction 的）:")
        for route in app.routes:
            if "prediction" in route.path or "star-resonance" in route.path:
                print(f"  {route.methods} {route.path}")
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()


def main():
    print("="*60)
    print("  调试竞猜系统接口")
    print("="*60)
    
    check_routes()
    
    token = login("testuser", "test123")
    if not token:
        print("\n登录失败")
        return
    
    print(f"\nToken: {token[:50]}...")
    
    test_my_tickets(token)
    test_system_status(token)
    test_list_sessions(token)


if __name__ == "__main__":
    main()
