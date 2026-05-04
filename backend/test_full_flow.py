"""
完整测试流程 - 检查数据库用户，测试登录和 PK 接口
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models import User

import httpx
import json

BASE_URL = "http://localhost:8001"

def check_database():
    print("=" * 60)
    print("Checking database...")
    print("=" * 60)
    
    engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    
    try:
        print("\n[1] Checking users table...")
        users = db.query(User).all()
        print(f"  Total users: {len(users)}")
        
        for user in users:
            print(f"    - ID: {user.id}, Username: {user.username}, Email: {user.email}, Active: {user.is_active}")
        
        print("\n[2] Checking tables...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result]
            print(f"  Total tables: {len(tables)}")
            
            pk_tables = [t for t in tables if 'pk' in t.lower() or 'daily_pk' in t.lower()]
            print(f"  PK tables: {pk_tables}")
            
            for t in pk_tables:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {t}"))
                    count = result.fetchone()[0]
                    print(f"    - {t}: {count} records")
                except Exception as e:
                    print(f"    - {t}: Error - {e}")
    
    finally:
        db.close()
    
    print("\n" + "=" * 60)
    print("Database check complete")
    print("=" * 60)

def test_login_and_pk():
    print("\n" + "=" * 60)
    print("Testing login and PK API...")
    print("=" * 60)
    
    with httpx.Client(timeout=10) as client:
        print("\n[1] Testing login with test user (test/test123)...")
        try:
            response = client.post(
                f"{BASE_URL}/api/users/login",
                data={
                    "username": "test",
                    "password": "test123"
                }
            )
            print(f"  Status: {response.status_code}")
            print(f"  Response: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 200 and data.get('data'):
                    token = data['data'].get('access_token')
                    print(f"  ✓ Login successful!")
                    print(f"  Token: {token[:50]}...")
                    
                    print("\n[2] Testing PK status with token...")
                    headers = {"Authorization": f"Bearer {token}"}
                    response = client.get(f"{BASE_URL}/api/pk/status", headers=headers)
                    print(f"  Status: {response.status_code}")
                    print(f"  Response: {response.text}")
                    
                    print("\n[3] Testing GET /api/users/me with token...")
                    response = client.get(f"{BASE_URL}/api/users/me", headers=headers)
                    print(f"  Status: {response.status_code}")
                    print(f"  Response: {response.text}")
                else:
                    print(f"  ✗ Login failed in response")
            else:
                print(f"  ✗ Login failed with status {response.status_code}")
                
        except Exception as e:
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n[4] Testing login with admin user (admin/admin123)...")
        try:
            response = client.post(
                f"{BASE_URL}/api/users/login",
                data={
                    "username": "admin",
                    "password": "admin123"
                }
            )
            print(f"  Status: {response.status_code}")
            print(f"  Response: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 200 and data.get('data'):
                    token = data['data'].get('access_token')
                    print(f"  ✓ Login successful!")
                    
                    print("\n[5] Testing PK status with admin token...")
                    headers = {"Authorization": f"Bearer {token}"}
                    response = client.get(f"{BASE_URL}/api/pk/status", headers=headers)
                    print(f"  Status: {response.status_code}")
                    print(f"  Response: {response.text}")
                    
        except Exception as e:
            print(f"  Error: {e}")

    print("\n" + "=" * 60)
    print("Test complete")
    print("=" * 60)

if __name__ == "__main__":
    check_database()
    test_login_and_pk()
