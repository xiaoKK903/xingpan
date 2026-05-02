"""
调试 my-tickets 接口
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
        print(f"登录响应状态码: {response.status_code}")
        print(f"登录响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        
        result = response.json()
        if result.get("code") == 200:
            return result["data"].get("access_token") or result["data"].get("token")
    except Exception as e:
        print(f"登录错误: {e}")
    
    return None


def test_my_tickets(token):
    url = f"{BASE_URL}/star-resonance/my-tickets"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"\nmy-tickets 响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n解析后: {json.dumps(result, ensure_ascii=False, indent=2)}")
            return result
        else:
            print(f"\n请求失败，状态码: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"\n请求错误: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_pool_status(token):
    url = f"{BASE_URL}/star-resonance/status"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"\npool-status 响应状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"\n请求错误: {e}")


def check_directly():
    import sqlite3
    from pathlib import Path
    
    db_path = Path(__file__).parent / "ai_customer_service.db"
    
    print("\n" + "="*60)
    print("  直接查询数据库")
    print("="*60)
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT name FROM sqlite_master WHERE type='table' AND name='prophecy_tickets'
        """)
        if cursor.fetchone():
            print("\n✓ prophecy_tickets 表存在")
            
            cursor.execute("SELECT COUNT(*) FROM prophecy_tickets")
            count = cursor.fetchone()[0]
            print(f"  总记录数: {count}")
            
            cursor.execute("SELECT * FROM prophecy_tickets LIMIT 5")
            columns = [desc[0] for desc in cursor.description]
            print(f"\n  表结构: {columns}")
            
            rows = cursor.fetchall()
            for row in rows:
                print(f"\n  记录: {dict(zip(columns, row))}")
        else:
            print("\n✗ prophecy_tickets 表不存在")
            
    except Exception as e:
        print(f"查询错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


def main():
    print("="*60)
    print("  调试 my-tickets 接口")
    print("="*60)
    
    check_directly()
    
    print("\n" + "="*60)
    print("  测试 API 接口")
    print("="*60)
    
    token = login("testuser", "test123")
    
    if not token:
        print("登录失败，无法继续测试")
        return
    
    test_pool_status(token)
    test_my_tickets(token)


if __name__ == "__main__":
    main()
