"""
简单测试脚本 - 测试登录接口
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import uvicorn
import threading
import time
import requests

def start_server():
    try:
        uvicorn.run(
            "app.main:app",
            host="127.0.0.1",
            port=8002,
            reload=False
        )
    except Exception as e:
        print(f"Server error: {e}")

def test_login():
    time.sleep(3)
    
    print("\n=== Testing health check ===")
    try:
        response = requests.get("http://127.0.0.1:8002/")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n=== Testing login ===")
    try:
        response = requests.post(
            "http://127.0.0.1:8002/api/users/login",
            data={"username": "admin", "password": "admin123"}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    test_login()
    
    print("\n=== Test complete ===")
