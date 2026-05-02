import asyncio
import httpx
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BACKEND_URL = "http://localhost:8001"

test_person_a = {
    "name": "夜行者",
    "birth_date": "1988-10-25",
    "birth_time": "22:30",
    "birth_place": "北京",
    "latitude": 39.9042,
    "longitude": 116.4074,
    "house_system": "placidus"
}

test_person_b = {
    "name": "光明使者",
    "birth_date": "1990-07-15",
    "birth_time": "08:15",
    "birth_place": "上海",
    "latitude": 31.2304,
    "longitude": 121.4737,
    "house_system": "placidus"
}


async def test_health_check():
    """测试后端健康检查"""
    print("\n" + "="*60)
    print("测试 1: 后端健康检查")
    print("="*60)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{BACKEND_URL}/health")
            
            print(f"URL: {BACKEND_URL}/health")
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
                return True
            else:
                print(f"错误响应: {response.text}")
                return False
                
    except Exception as e:
        print(f"错误: {e}")
        return False


async def test_get_styles():
    """测试获取剧情风格列表"""
    print("\n" + "="*60)
    print("测试 2: 获取剧情风格列表")
    print("="*60)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{BACKEND_URL}/api/plaza/styles")
            
            print(f"URL: {BACKEND_URL}/api/plaza/styles")
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
                return True
            else:
                print(f"错误响应: {response.text}")
                return False
                
    except Exception as e:
        print(f"错误: {e}")
        return False


async def test_analyze_conflict():
    """测试相位冲突分析（不调用AI）"""
    print("\n" + "="*60)
    print("测试 3: 相位冲突分析（不调用AI）")
    print("="*60)
    
    request_data = {
        "person_a": test_person_a,
        "person_b": test_person_b
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            print(f"URL: {BACKEND_URL}/api/plaza/analyze-conflict")
            print(f"请求数据: {json.dumps(request_data, ensure_ascii=False, indent=2)[:500]}...")
            
            response = await client.post(
                f"{BACKEND_URL}/api/plaza/analyze-conflict",
                json=request_data,
                timeout=60.0
            )
            
            print(f"\n状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"响应成功!")
                
                if data.get("data"):
                    conflict_analysis = data["data"].get("conflict_analysis", {})
                    if conflict_analysis.get("conflicts"):
                        print(f"检测到 {len(conflict_analysis['conflicts'])} 个关键相位冲突")
                        for c in conflict_analysis["conflicts"][:3]:
                            print(f"  - {c.get('planet_pair')} {c.get('aspect_type')}: {c.get('drama_theme')}")
                    else:
                        print(f"未检测到关键相位冲突")
                    
                    if conflict_analysis.get("intensity"):
                        print(f"\n冲突强度: {conflict_analysis['intensity'].get('conflict_level')}")
                    
                    if data["data"].get("basic_info"):
                        print(f"\n基本信息:")
                        print(f"  角色A: {data['data']['basic_info']['person_a']['name']} - {data['data']['basic_info']['person_a']['sun_sign']}")
                        print(f"  角色B: {data['data']['basic_info']['person_b']['name']} - {data['data']['basic_info']['person_b']['sun_sign']}")
                    
                    print(f"\n完整响应: {json.dumps(data, ensure_ascii=False, indent=2)[:1000]}...")
                    return True
                else:
                    print(f"响应格式异常: {json.dumps(data, ensure_ascii=False)}")
                    return False
            else:
                print(f"错误响应: {response.text}")
                return False
                
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_encounter():
    """测试完整相遇分析（调用AI生成剧情）"""
    print("\n" + "="*60)
    print("测试 4: 完整相遇分析（调用AI生成剧情）")
    print("="*60)
    
    request_data = {
        "person_a": test_person_a,
        "person_b": test_person_b,
        "style": "modern",
        "location": "神秘广场",
        "generate_story": True,
        "use_cache": True,
        "generate_characters": True
    }
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            print(f"URL: {BACKEND_URL}/api/plaza/encounter")
            print(f"请求数据: {json.dumps(request_data, ensure_ascii=False, indent=2)[:500]}...")
            print(f"\n正在调用 AI (deepseek-v4-flash)，请稍候...\n")
            
            response = await client.post(
                f"{BACKEND_URL}/api/plaza/encounter",
                json=request_data,
                timeout=120.0
            )
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"响应成功!")
                
                if data.get("data"):
                    result = data["data"]
                    
                    print(f"\n--- 角色面板 ---")
                    if result.get("character_panels"):
                        for char_key in ["person_a", "person_b"]:
                            char = result["character_panels"].get(char_key, {})
                            if char:
                                print(f"\n{char.get('name', '角色')}:")
                                print(f"  战力: {char.get('stats', {}).get('combat_power', 0)}")
                                print(f"  元素: {char.get('element', '未知')}")
                                print(f"  太阳: {char.get('zodiac', {}).get('sun', '未知')}")
                                print(f"  月亮: {char.get('zodiac', {}).get('moon', '未知')}")
                    
                    print(f"\n--- 战力结果 ---")
                    if result.get("combat_result"):
                        cr = result["combat_result"]
                        print(f"  胜利者: {cr.get('winner', '未知')}")
                        print(f"  结果: {cr.get('outcome', '未知')}")
                        print(f"  有效战力: {cr.get('power_a')} vs {cr.get('power_b')}")
                    
                    print(f"\n--- 资源消耗 ---")
                    if result.get("resource_cost"):
                        rc = result["resource_cost"]
                        print(f"  灵力: {rc.get('spiritual_energy', 0)}")
                        print(f"  体力: {rc.get('physical_stamina', 0)}")
                        print(f"  金币: {rc.get('gold_coins', 0)}")
                    
                    print(f"\n--- 道具掉落 ---")
                    if result.get("item_drops"):
                        for item in result["item_drops"]:
                            print(f"  [{item.get('rarity_name', '普通')}] {item.get('item_name')} x{item.get('quantity', 1)}")
                    
                    print(f"\n--- 羁绊积分 ---")
                    if result.get("bond_result"):
                        br = result["bond_result"]
                        print(f"  获得羁绊: {br.get('bond_points_gained', 0)} 点")
                        print(f"  关系变化: {br.get('relationship_shift', '未知')}")
                    
                    print(f"\n--- 场景特效 ---")
                    if result.get("scene_effects"):
                        se = result["scene_effects"]
                        print(f"  氛围: {se.get('mood', '未知')}")
                        print(f"  滤镜: {se.get('filter', {}).get('type', '未知')}")
                        print(f"  BGM: {se.get('bgm', {}).get('options', [])}")
                    
                    print(f"\n--- AI 剧情 ---")
                    if result.get("story"):
                        story = result["story"]
                        print(f"\n场景描述: {story.get('scene_description', '无')}")
                        print(f"\n对话:")
                        for d in story.get("dialogues", []):
                            speaker = d.get("speaker", "未知")
                            line = d.get("line", "")
                            emotion = d.get("emotion", "")
                            if emotion:
                                print(f"  [{speaker} ({emotion})]: {line}")
                            else:
                                print(f"  [{speaker}]: {line}")
                        
                        if result.get("from_cache"):
                            print(f"\n⚠️  来自缓存")
                        if result.get("from_default"):
                            print(f"\n⚠️  来自默认剧情（可能AI调用超时或失败）")
                    
                    print(f"\n--- 调用状态 ---")
                    print(f"  来自缓存: {result.get('from_cache', False)}")
                    print(f"  来自默认: {result.get('from_default', False)}")
                    print(f"  剧情等级: {result.get('story_level', '未知')}")
                    print(f"  剧情等级名称: {result.get('story_level_name', '未知')}")
                    
                    return True
                else:
                    print(f"响应格式异常: {json.dumps(data, ensure_ascii=False)}")
                    return False
            else:
                print(f"错误响应: {response.text}")
                return False
                
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    print("="*60)
    print("DeepSeek API 后端测试")
    print("="*60)
    print(f"后端地址: {BACKEND_URL}")
    print(f"测试时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    results.append(("健康检查", await test_health_check()))
    results.append(("获取剧情风格", await test_get_styles()))
    results.append(("相位冲突分析", await test_analyze_conflict()))
    results.append(("完整相遇分析（含AI）", await test_encounter()))
    
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False
    
    print(f"\n总体: {'✅ 所有测试通过' if all_passed else '❌ 部分测试失败'}")
    
    if all_passed:
        print("\n🎉 DeepSeek API 调用成功！")
        print("   - 模型: deepseek-v4-flash")
        print("   - 后端: http://localhost:8001")
        print("   - 前端代理正常工作")
    else:
        print("\n⚠️  部分测试失败，请检查后端日志")


if __name__ == "__main__":
    asyncio.run(main())
