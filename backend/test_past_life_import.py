"""
测试前世故事功能的导入
"""
import sys
import os
import traceback

sys.path.insert(0, os.path.dirname(__file__))

print("=" * 60)
print("Testing past life feature imports...")
print("=" * 60)

print("\n[1] Testing past_life_service import...")
try:
    from app.services import past_life_service
    print("    ✓ past_life_service imported successfully")
    print(f"    Themes: {list(past_life_service.PAST_LIFE_THEME_CONFIG.keys())}")
    print(f"    Relationships: {list(past_life_service.PAST_LIFE_RELATIONSHIP_CONFIG.keys())}")
except Exception as e:
    print(f"    ✗ FAILED: {e}")
    traceback.print_exc()

print("\n[2] Testing past_life router import...")
try:
    from app.routers import past_life
    print("    ✓ past_life router imported successfully")
except Exception as e:
    print(f"    ✗ FAILED: {e}")
    traceback.print_exc()

print("\n[3] Testing main app import...")
try:
    from app.main import app
    print("    ✓ Main app imported successfully")
    
    past_life_routes = [r for r in app.routes if 'past-life' in getattr(r, 'path', '')]
    print(f"    Found {len(past_life_routes)} past-life routes:")
    for r in past_life_routes:
        methods = getattr(r, 'methods', ['GET'])
        print(f"      [{','.join(sorted(methods))}] {r.path}")
except Exception as e:
    print(f"    ✗ FAILED: {e}")
    traceback.print_exc()

print("\n" + "=" * 60)
print("Test complete")
print("=" * 60)
