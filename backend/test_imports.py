"""
详细测试脚本 - 检查所有导入
"""
import sys
import os
import traceback

sys.path.insert(0, os.path.dirname(__file__))

print("=" * 60)
print("Checking imports...")
print("=" * 60)

test_modules = [
    ("app.database", "Base, SessionLocal, get_db"),
    ("app.models.user", "User"),
    ("app.models.pk_system", "All PK models"),
    ("app.services.pk_service", "PKService, get_pk_service"),
    ("app.routers.pk_system", "PK router"),
    ("app.services.leaderboard_service", "Leaderboard service"),
]

for module_name, description in test_modules:
    print(f"\n[{module_name}] {description}")
    try:
        __import__(module_name)
        print(f"  ✓ OK")
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
        traceback.print_exc()

print("\n" + "=" * 60)
print("Checking main app...")
print("=" * 60)

try:
    from app.main import app
    print("✓ Main app import OK")
    print(f"  Routes: {len(app.routes)}")
except Exception as e:
    print(f"✗ Main app import FAILED: {e}")
    traceback.print_exc()

print("\n" + "=" * 60)
print("Check complete")
print("=" * 60)
