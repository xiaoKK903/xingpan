"""
调试 vote-secure 接口
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


def test_vote_secure(token, session_id, option_value, asset_type):
    print("\n" + "="*60)
    print("  测试 vote-secure 接口")
    print("="*60)
    
    url = f"{BASE_URL}/prediction/vote-secure"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "session_id": session_id,
        "option_value": option_value,
        "confidence": 80,
        "asset_type": asset_type
    }
    
    print(f"\n请求:")
    print(f"  URL: {url}")
    print(f"  Payload: {json.dumps(payload, ensure_ascii=False)}")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        print(f"\n响应:")
        print(f"  状态码: {response.status_code}")
        print(f"  内容: {response.text}")
        
        try:
            result = response.json()
            print(f"\n  解析后: {json.dumps(result, ensure_ascii=False, indent=2)}")
        except:
            print(f"\n  无法解析 JSON")
        
        return response
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_validate_vote(token, session_id, option_value):
    print("\n" + "="*60)
    print("  测试 validate-vote 接口")
    print("="*60)
    
    url = f"{BASE_URL}/prediction/validate-vote"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "prediction_id": session_id,
        "selected_option": option_value,
        "confidence": 80
    }
    
    print(f"\n请求:")
    print(f"  URL: {url}")
    print(f"  Payload: {json.dumps(payload, ensure_ascii=False)}")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        print(f"\n响应:")
        print(f"  状态码: {response.status_code}")
        print(f"  内容: {response.text}")
        
        return response
    except Exception as e:
        print(f"\n错误: {e}")
        return None


def test_old_vote(token, session_id, option_value, asset_type):
    print("\n" + "="*60)
    print("  测试旧版 vote 接口")
    print("="*60)
    
    url = f"{BASE_URL}/prediction/vote"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "prediction_id": session_id,
        "selected_option": option_value,
        "confidence": 80,
        "vote_asset_type": asset_type
    }
    
    print(f"\n请求:")
    print(f"  URL: {url}")
    print(f"  Payload: {json.dumps(payload, ensure_ascii=False)}")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        print(f"\n响应:")
        print(f"  状态码: {response.status_code}")
        print(f"  内容: {response.text}")
        
        return response
    except Exception as e:
        print(f"\n错误: {e}")
        return None


def main():
    print("="*60)
    print("  调试 vote-secure 接口")
    print("="*60)
    
    token = login("testuser", "test123")
    if not token:
        print("\n登录失败")
        return
    
    print(f"\nToken: {token[:50]}...")
    
    session_id = 2
    option_value = "sunny"
    
    test_validate_vote(token, session_id, option_value)
    test_vote_secure(token, session_id, option_value, "fragment")
    test_old_vote(token, session_id, option_value, "fragment")


if __name__ == "__main__":
    main()
