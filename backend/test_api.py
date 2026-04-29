import sys
import json
import requests

BASE_URL = "http://localhost:8000/api"

def test_root():
    print("=" * 60)
    print("测试: 根端点")
    print("=" * 60)
    try:
        response = requests.get("http://localhost:8000/")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"错误: {e}")
        return False

def test_transit_calculate():
    print("\n" + "=" * 60)
    print("测试: 行运计算接口")
    print("=" * 60)
    
    payload = {
        "birth_date": "1990-01-01",
        "birth_time": "12:00",
        "latitude": 39.9042,
        "longitude": 116.4074,
        "house_system": "placidus"
    }
    
    print(f"请求参数: {json.dumps(payload, ensure_ascii=False)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/transit/calculate",
            json=payload,
            timeout=60
        )
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ 行运计算成功!")
            print(f"  目标日期: {data.get('data', {}).get('target_date')}")
            print(f"  整体能量: {data.get('data', {}).get('overall', {}).get('overall_score')}分")
            print(f"  星象天气: {data.get('data', {}).get('overall', {}).get('mood_label')}")
            print(f"  相位数量: {data.get('data', {}).get('aspects_count')}")
            return True
        else:
            print(f"✗ 错误响应: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"✗ 请求错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_transit_trend():
    print("\n" + "=" * 60)
    print("测试: 7天趋势接口")
    print("=" * 60)
    
    payload = {
        "birth_date": "1990-01-01",
        "birth_time": "12:00",
        "latitude": 39.9042,
        "longitude": 116.4074,
        "house_system": "placidus"
    }
    
    print(f"请求参数: {json.dumps(payload, ensure_ascii=False)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/transit/trend",
            json=payload,
            timeout=60
        )
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            summary = data.get('data', {}).get('summary', {})
            print(f"\n✓ 7天趋势计算成功!")
            print(f"  最高能量: {summary.get('max_score')}分")
            print(f"  最低能量: {summary.get('min_score')}分")
            print(f"  平均能量: {summary.get('avg_score')}分")
            print(f"  转折点数量: {len(summary.get('turning_points', []))}")
            return True
        else:
            print(f"✗ 错误响应: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"✗ 请求错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_transit_cache_status():
    print("\n" + "=" * 60)
    print("测试: 缓存状态接口")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/transit/cache/status")
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ 缓存状态获取成功!")
            print(f"  使用Redis: {data.get('data', {}).get('using_redis')}")
            print(f"  服务可用: {data.get('data', {}).get('service_available')}")
            return True
        else:
            print(f"✗ 错误响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ 请求错误: {e}")
        return False

def main():
    print("=" * 60)
    print("FastAPI 行运气象站 API 测试")
    print("=" * 60)
    
    results = []
    
    results.append(("根端点", test_root()))
    results.append(("缓存状态", test_transit_cache_status()))
    results.append(("行运计算", test_transit_calculate()))
    results.append(("7天趋势", test_transit_trend()))
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    success_count = 0
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")
        if result:
            success_count += 1
    
    print(f"\n总计: {success_count}/{len(results)} 测试通过")
    
    if success_count == len(results):
        print("\n🎉 所有测试通过!")
        return 0
    else:
        print("\n⚠️ 部分测试失败，请检查错误信息")
        return 1

if __name__ == "__main__":
    sys.exit(main())
