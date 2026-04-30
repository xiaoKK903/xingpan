import sys
import os
import json
import httpx

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

url = "http://localhost:8001/api/life-script/analyze"
data = {
    "birth_date": "1990-01-01",
    "birth_time": "12:00",
    "latitude": 39.9042,
    "longitude": 116.4074,
    "house_system": "placidus",
    "target_year": 2024
}

print("=" * 60)
print("测试 /api/life-script/analyze 接口")
print("=" * 60)
print(f"请求数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
print()

try:
    response = httpx.post(url, json=data, timeout=60.0)
    print(f"状态码: {response.status_code}")
    print()
    
    if response.status_code == 200:
        result = response.json()
        print("响应:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"错误响应: {response.text}")
        
except Exception as e:
    print(f"请求失败: {e}")
    import traceback
    traceback.print_exc()
