import sys
import traceback

print("=" * 60)
print("测试后端模块导入")
print("=" * 60)

test_modules = [
    ("app.config", "配置模块"),
    ("app.database", "数据库模块"),
    ("app.models", "模型模块"),
    ("app.astro", "星盘计算模块"),
    ("app.routers.users", "用户路由"),
    ("app.services.cache_service", "缓存服务"),
    ("app.services.timezone_service", "时区服务"),
    ("app.services.ephemeris_calculator", "星历计算器"),
    ("app.services.energy_scoring", "能量打分"),
    ("app.services.transit_service", "行运服务"),
    ("app.routers.transit", "行运路由"),
    ("app.main", "主应用"),
]

success_count = 0
fail_count = 0

for module_name, description in test_modules:
    print(f"\n测试: {description} ({module_name})")
    try:
        __import__(module_name)
        print(f"  ✓ 导入成功")
        success_count += 1
    except Exception as e:
        print(f"  ✗ 导入失败: {e}")
        print(f"  详细错误:")
        traceback.print_exc()
        fail_count += 1

print("\n" + "=" * 60)
print(f"测试结果: 成功 {success_count}, 失败 {fail_count}")
print("=" * 60)

if fail_count > 0:
    print("\n警告: 部分模块导入失败，请检查错误信息")
    sys.exit(1)
else:
    print("\n所有模块导入成功!")
    sys.exit(0)
