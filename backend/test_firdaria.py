import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.firdaria_service import (
    get_firdaria_calculator,
    is_day_birth,
    get_firdaria_order,
    FIRDAIRA_PLANET_INFO,
    DAY_BIRTH_ORDER,
    NIGHT_BIRTH_ORDER
)

print("=" * 60)
print("法达服务测试")
print("=" * 60)

print("\n1. 测试日生/夜生判断:")
test_cases = [
    (0.0, "白羊座 0° (夜生)"),
    (90.0, "巨蟹座 0° (夜生)"),
    (120.0, "狮子座 0° (日生边界)"),
    (180.0, "天秤座 0° (中午)"),
    (270.0, "摩羯座 0° (傍晚)"),
    (300.0, "水瓶座 0° (夜生边界)"),
    (350.0, "双鱼座 20° (夜生)"),
]

for longitude, desc in test_cases:
    is_day = is_day_birth(longitude)
    order = get_firdaria_order(longitude)
    print(f"   {desc}: {'日生 ☀️' if is_day else '夜生 🌙'}")
    print(f"      顺序: {' → '.join(order[:3])}...")

print("\n2. 测试南交点配置:")
south_node = FIRDAIRA_PLANET_INFO.get("south_node", {})
print(f"   名称: {south_node.get('name')}")
print(f"   符号: {south_node.get('symbol')}")
print(f"   周期: {south_node.get('years')} 年")
print(f"   是交点: {south_node.get('is_node')}")

print("\n3. 测试完整周期计算:")
calculator = get_firdaria_calculator()

birth_date = datetime(1990, 1, 1, 12, 0)
sun_longitude = 180.0  # 日生

print(f"   出生日期: {birth_date}")
print(f"   太阳经度: {sun_longitude}° (日生)")

try:
    periods = calculator.calculate_firdaria_periods(birth_date, sun_longitude)
    print(f"   计算成功！共 {len(periods)} 个周期")
    
    for i, p in enumerate(periods[:5]):
        print(f"\n   周期 {i+1}:")
        print(f"      行星: {p.info.get('name')} ({p.planet})")
        print(f"      年龄: {p.start_age} - {p.end_age} 岁")
        print(f"      日期: {p.start_date.strftime('%Y-%m-%d')} - {p.end_date.strftime('%Y-%m-%d')}")
        print(f"      小运数量: {len(p.minor_periods)}")
        if p.minor_periods:
            print(f"      小运开头: {p.minor_periods[0]['planet_name']}")
        
        if p.planet in ['north_node', 'south_node']:
            print(f"      ⚠️  交点周期，无小运")

except Exception as e:
    print(f"   计算失败: {e}")
    import traceback
    traceback.print_exc()

print("\n4. 测试指定年份分析:")

mock_natal_planets = [
    {"name": "太阳", "longitude": 180.0, "zodiac": {"sign": "天秤座"}, "house": 1},
    {"name": "月亮", "longitude": 45.0, "zodiac": {"sign": "金牛座"}, "house": 2},
    {"name": "水星", "longitude": 200.0, "zodiac": {"sign": "天秤座"}, "house": 1},
    {"name": "金星", "longitude": 160.0, "zodiac": {"sign": "处女座"}, "house": 12},
    {"name": "火星", "longitude": 90.0, "zodiac": {"sign": "巨蟹座"}, "house": 4},
    {"name": "木星", "longitude": 270.0, "zodiac": {"sign": "摩羯座"}, "house": 10},
    {"name": "土星", "longitude": 300.0, "zodiac": {"sign": "水瓶座"}, "house": 11},
    {"name": "北交点", "longitude": 60.0, "zodiac": {"sign": "双子座"}, "house": 3},
    {"name": "南交点", "longitude": 240.0, "zodiac": {"sign": "天蝎座"}, "house": 8},
]

try:
    result = calculator.analyze_firdaria_influence(
        birth_date, 2024, mock_natal_planets
    )
    print(f"   分析成功:")
    print(f"      日生: {result.get('is_day_birth')}")
    print(f"      目标年份: 2024")
    print(f"      有活跃周期: {result.get('has_active_period')}")
    
    major = result.get('major_period', {})
    if major:
        print(f"\n      大运:")
        print(f"         行星: {major.get('planet_name')}")
        print(f"         进度: {major.get('progress_percent')}%")
        print(f"         强度: {major.get('intensity')}/10")
    
    minor = result.get('minor_period')
    if minor:
        print(f"\n      小运:")
        print(f"         行星: {minor.get('planet_name')}")
    
    themes = result.get('themes', [])
    if themes:
        print(f"\n      主题: {', '.join(themes)}")
        
except Exception as e:
    print(f"   分析失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
