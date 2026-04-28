import logging
logging.basicConfig(level=logging.INFO)

from app.astro import calculate_chart

print("=" * 60)
print("测试案例: 1988年5月15日 10:30 北京")
print("=" * 60)

result = calculate_chart(
    year=1988,
    month=5,
    day=15,
    hour=10,
    minute=30,
    latitude=39.9042,
    longitude=116.4074,
    house_system='placidus'
)

print("")
print("【计算结果】")
print(f"儒略日: {result['julday']}")
print("")
print("【时区信息】")
tz = result['timezone_info']
print(f"  本地时间: {tz['input_local']}")
print(f"  时区: {tz['timezone']}")
print(f"  偏移: {tz['offset_hours']} 小时")
print(f"  夏令时: {'是' if tz['is_dst'] else '否'}")
print(f"  UTC时间: {tz['utc_time']}")
print("")
print("【三大主星】")
print(f"  太阳: {result['sun_sign']['sign']} {result['sun_sign']['dms']['formatted']}")
print(f"  月亮: {result['moon_sign']['sign']} {result['moon_sign']['dms']['formatted']}")
print(f"  上升: {result['ascendant']['sign']} {result['ascendant']['dms']['formatted']}")
print("")
print("【天顶】")
print(f"  {result['midheaven']['sign']} {result['midheaven']['dms']['formatted']}")
print("")
print("【行星列表】")
print(f"  {'名称':<6s} {'星座':<6s} {'度数':<12s} {'宫位':<4s} {'逆行'}")
print("  " + "-" * 45)
for p in result['planets']:
    retro = "✓" if p['is_retrograde'] else " "
    print(f"  {p['name']:<6s} {p['zodiac']['sign']:<6s} {p['zodiac']['dms']['formatted']:<12s} 第{p['house']:d}宫   {retro}")

print("")
print(f"【宫位系统】: {result['houses']['system']}")
print("")
print("【宫位列表】")
houses = result['houses']['houses']
for i, h in enumerate(houses):
    print(f"  第{i+1:2d}宫: {h['sign']} {h['dms']['formatted']}")

print("")
print(f"【相位数量】: {len(result['aspects'])}")
print("=" * 60)
