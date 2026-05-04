"""
测试每日 CP 接口 - 找出 500 错误原因
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import httpx

BASE_URL = "http://localhost:8001"

def test_imports():
    print("=" * 60)
    print("Testing imports...")
    print("=" * 60)
    
    # Test DailyCPMatch import
    try:
        from app.models.match import DailyCPMatch, DailyCPMatchStatus, TimeLimitedSession, SessionExtension, ProfileUnlock, MatchPreference, DailyMatchLimit
        print("✓ app.models.match import OK")
    except Exception as e:
        print(f"✗ app.models.match import FAILED: {e}")
        import traceback
        traceback.print_exc()
    
    # Test __init__.py import
    try:
        from app.models import DailyCPMatch, DailyCPMatchStatus, TimeLimitedSession
        print("✓ app.models import OK")
    except Exception as e:
        print(f"✗ app.models import FAILED: {e}")
        import traceback
        traceback.print_exc()
    
    # Test service import
    try:
        from app.services.daily_cp_match_service import check_match_availability, get_match_detail
        print("✓ daily_cp_match_service import OK")
    except Exception as e:
        print(f"✗ daily_cp_match_service import FAILED: {e}")
        import traceback
        traceback.print_exc()

def test_api():
    print("\n" + "=" * 60)
    print("Testing API...")
    print("=" * 60)
    
    with httpx.Client(timeout=10) as client:
        # First, login
        print("\n[1] Login...")
        try:
            response = client.post(
                f"{BASE_URL}/api/users/login",
                data={
                    "username": "test",
                    "password": "test123"
                }
            )
            print(f"  Status: {response.status_code}")
            print(f"  Response: {response.text[:500]}...")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 200 and data.get('data'):
                    token = data['data'].get('access_token')
                    print(f"  ✓ Login successful!")
                    
                    # Test PK status
                    print("\n[2] Test PK status...")
                    headers = {"Authorization": f"Bearer {token}"}
                    response = client.get(f"{BASE_URL}/api/pk/status", headers=headers)
                    print(f"  Status: {response.status_code}")
                    print(f"  Response: {response.text[:500]}...")
                    
                    # Test Daily CP status
                    print("\n[3] Test Daily CP status...")
                    response = client.get(f"{BASE_URL}/api/daily-cp-match/status", headers=headers)
                    print(f"  Status: {response.status_code}")
                    print(f"  Response: {response.text}")
                    
                    # Test Daily CP my-matches
                    print("\n[4] Test Daily CP my-matches...")
                    response = client.get(f"{BASE_URL}/api/daily-cp-match/my-matches", headers=headers)
                    print(f"  Status: {response.status_code}")
                    print(f"  Response: {response.text}")
                    
                    # Test Daily CP preference
                    print("\n[5] Test Daily CP preference...")
                    response = client.get(f"{BASE_URL}/api/daily-cp-match/preference", headers=headers)
                    print(f"  Status: {response.status_code}")
                    print(f"  Response: {response.text}")
                    
                    # Test Daily CP VIP privileges
                    print("\n[6] Test Daily CP vip-privileges...")
                    response = client.get(f"{BASE_URL}/api/daily-cp-match/vip-privileges", headers=headers)
                    print(f"  Status: {response.status_code}")
                    print(f"  Response: {response.text}")
                    
        except Exception as e:
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_imports()
    test_api()
