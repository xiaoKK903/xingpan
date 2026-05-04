import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

print("开始测试导入...")

try:
    from app.models import (
        DailyCPMatch, DailyCPMatchStatus, 
        DailyMatchLimit, TimeLimitedSession, MatchPreference,
        ProfileUnlock, UserVIP, UserPrivateChat
    )
    print("✅ 数据模型导入成功")
except Exception as e:
    print(f"❌ 数据模型导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    from app.services.daily_cp_match_service import (
        check_and_close_expired_sessions,
        get_user_latest_chart,
        match_users_by_compatibility,
        create_daily_match_record,
        create_daily_match_record_internal,
        generate_batch_id,
        get_today_date_str,
        accept_match,
        reject_match,
        unlock_profile,
        extend_session,
        perform_manual_match,
        check_match_availability_with_lock,
        check_match_availability,
        get_match_detail,
        get_session_detail
    )
    print("✅ daily_cp_match_service 导入成功")
except Exception as e:
    print(f"❌ daily_cp_match_service 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    from app.services.task_executor import (
        task_executor,
        TaskExecutor,
        get_task_executor
    )
    print("✅ task_executor 导入成功")
except Exception as e:
    print(f"❌ task_executor 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    from app.main import app
    print("✅ FastAPI app 导入成功")
except Exception as e:
    print(f"❌ FastAPI app 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n🎉 所有导入测试通过！")
