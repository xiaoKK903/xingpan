"""
测试登录接口
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import httpx
import json

BASE_URL = "http://localhost:8001"

def test_api():
    print("=" * 60)
    print("Testing API endpoints...")
    print("=" * 60)
    
    with httpx.Client(timeout=10) as client:
        print("\n[1] Testing GET /")
        try:
            response = client.get(f"{BASE_URL}/")
            print(f"  Status: {response.status_code}")
            print(f"  Response: {response.text}")
        except Exception as e:
            print(f"  Error: {e}")
        
        print("\n[2] Testing GET /health")
        try:
            response = client.get(f"{BASE_URL}/health")
            print(f"  Status: {response.status_code}")
            print(f"  Response: {response.text}")
        except Exception as e:
            print(f"  Error: {e}")
        
        print("\n[3] Testing GET /api/pk/status (should fail, not authenticated)")
        try:
            response = client.get(f"{BASE_URL}/api/pk/status")
            print(f"  Status: {response.status_code}")
            print(f"  Response: {response.text}")
        except Exception as e:
            print(f"  Error: {e}")
        
        print("\n[4] Testing GET /api/users/me (should fail, not authenticated)")
        try:
            response = client.get(f"{BASE_URL}/api/users/me")
            print(f"  Status: {response.status_code}")
            print(f"  Response: {response.text}")
        except Exception as e:
            print(f"  Error: {e}")
        
        print("\n[5] Testing PK status with force parameter (for debugging)")
        try:
            response = client.get(f"{BASE_URL}/api/pk/status?force_test=1")
            print(f"  Status: {response.status_code}")
            print(f"  Response: {response.text}")
        except Exception as e:
            print(f"  Error: {e}")

    print("\n" + "=" * 60)
    print("Test complete")
    print("=" * 60)

if __name__ == "__main__":
    test_api()
