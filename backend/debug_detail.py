"""
调试 detail-optimized 接口
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
            return result["data"].get("access_token") or result["data"].get("token")
        return None
    except:
        return None


def test_detail_optimized(token, session_id):
    print("\n" + "="*60)
    print(f"  测试 detail-optimized/{session_id} 接口")
    print("="*60)
    
    url = f"{BASE_URL}/prediction/detail-optimized/{session_id}"
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
        import traceback
        traceback.print_exc()
        return None


def test_detail_old(token, session_id):
    print("\n" + "="*60)
    print(f"  测试 detail/{session_id} 接口（旧版）")
    print("="*60)
    
    url = f"{BASE_URL}/prediction/detail/{session_id}"
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


def test_open_sessions(token):
    print("\n" + "="*60)
    print("  测试 open 接口")
    print("="*60)
    
    url = f"{BASE_URL}/prediction/open"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        result = response.json()
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        return result
    except Exception as e:
        print(f"错误: {e}")
        return None


def main():
    print("="*60)
    print("  调试 detail-optimized 接口")
    print("="*60)
    
    token = login("testuser", "test123")
    if not token:
        print("\n登录失败")
        return
    
    print(f"\nToken: {token[:50]}...")
    
    open_result = test_open_sessions(token)
    if open_result and open_result.get("code") == 200:
        sessions = open_result["data"].get("sessions", []) or open_result["data"].get("predictions", [])
        if sessions:
            session_id = sessions[0].get("id")
            test_detail_optimized(token, session_id)
            test_detail_old(token, session_id)


if __name__ == "__main__":
    main()
