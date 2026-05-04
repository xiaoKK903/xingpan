import sys
sys.path.insert(0, '.')

print("=" * 60)
print("验证修复后的代码导入...")
print("=" * 60)

try:
    from app.main import app
    print("✓ main.py 导入成功")
except Exception as e:
    print(f"✗ main.py 导入失败: {e}")
    import traceback
    traceback.print_exc()

try:
    from app.services.growth_task_service import get_growth_task_service, GrowthTaskService, TaskErrorCode
    print("✓ growth_task_service 导入成功")
except Exception as e:
    print(f"✗ growth_task_service 导入失败: {e}")
    import traceback
    traceback.print_exc()

try:
    from app.services.leaderboard_service import get_leaderboard_service
    print("✓ leaderboard_service 导入成功")
except Exception as e:
    print(f"✗ leaderboard_service 导入失败: {e}")
    import traceback
    traceback.print_exc()

try:
    from app.services.ad_free_service import get_ad_free_service
    print("✓ ad_free_service 导入成功")
except Exception as e:
    print(f"✗ ad_free_service 导入失败: {e}")
    import traceback
    traceback.print_exc()

try:
    from app.routers import growth_tasks
    print("✓ growth_tasks router 导入成功")
except Exception as e:
    print(f"✗ growth_tasks router 导入失败: {e}")
    import traceback
    traceback.print_exc()

try:
    from app.routers import leaderboards
    print("✓ leaderboards router 导入成功")
except Exception as e:
    print(f"✗ leaderboards router 导入失败: {e}")
    import traceback
    traceback.print_exc()

try:
    from app.routers import ad_free
    print("✓ ad_free router 导入成功")
except Exception as e:
    print(f"✗ ad_free router 导入失败: {e}")
    import traceback
    traceback.print_exc()

try:
    from app.routers import daily_horoscope
    print("✓ daily_horoscope router 导入成功")
except Exception as e:
    print(f"✗ daily_horoscope router 导入失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("检查关键代码修复...")
print("=" * 60)

import inspect

try:
    service = get_growth_task_service()
    
    source = inspect.getsource(service.check_task_completion)
    if 'with_for_update(skip_locked=True)' in source:
        print("✗ check_task_completion 仍有 skip_locked=True")
    else:
        print("✓ check_task_completion 已移除 skip_locked=True")
    
    if 'old_progress' in source:
        print("✓ check_task_completion 使用 old_progress 保存旧值")
    else:
        print("✗ check_task_completion 没有使用 old_progress")
    
    if 'UserGrowthTaskStatus.CLAIMED.value' in source:
        print("✓ check_task_completion 检查 CLAIMED 状态")
    else:
        print("⚠ check_task_completion 未检查 CLAIMED 状态")
        
except Exception as e:
    print(f"检查 check_task_completion 失败: {e}")

try:
    source = inspect.getsource(service.claim_task_reward)
    if 'with_for_update(skip_locked=True)' in source:
        print("✗ claim_task_reward 仍有 skip_locked=True")
    else:
        print("✓ claim_task_reward 已移除 skip_locked=True")
except Exception as e:
    print(f"检查 claim_task_reward 失败: {e}")

try:
    source = inspect.getsource(service.mark_popup_seen)
    if 'with_for_update(skip_locked=True)' in source:
        print("✗ mark_popup_seen 仍有 skip_locked=True")
    else:
        print("✓ mark_popup_seen 已移除 skip_locked=True")
except Exception as e:
    print(f"检查 mark_popup_seen 失败: {e}")

print("\n" + "=" * 60)
print("所有验证完成")
print("=" * 60)
