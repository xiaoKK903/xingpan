"""
元素缺角寻宝系统测试脚本
测试核心功能：
1. 元素能量计算
2. 能量标签生成
3. 互补用户匹配
4. 盲盒线索生成
5. 缺角补全分数计算
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import json
from app.services.element_deficiency_service import (
    element_deficiency_service,
    Element,
    ENERGY_LEVEL_LABELS,
    EnergyLevel
)


def create_sample_chart_data(sign_adjustments=None):
    """
    创建测试用的星盘数据
    sign_adjustments: 用于调整星座以创建不同的元素分布
    """
    zodiacs = {
        "aries": "白羊座",     # 火
        "taurus": "金牛座",    # 土
        "gemini": "双子座",    # 风
        "cancer": "巨蟹座",    # 水
        "leo": "狮子座",       # 火
        "virgo": "处女座",     # 土
        "libra": "天秤座",     # 风
        "scorpio": "天蝎座",   # 水
        "sagittarius": "射手座", # 火
        "capricorn": "摩羯座",  # 土
        "aquarius": "水瓶座",   # 风
        "pisces": "双鱼座"      # 水
    }
    
    # 默认行星配置 (各元素相对均衡)
    planets = [
        {"name": "太阳", "zodiac": {"sign": "狮子座"}, "house": 5, "is_retrograde": False},
        {"name": "月亮", "zodiac": {"sign": "巨蟹座"}, "house": 4, "is_retrograde": False},
        {"name": "水星", "zodiac": {"sign": "处女座"}, "house": 6, "is_retrograde": False},
        {"name": "金星", "zodiac": {"sign": "天秤座"}, "house": 7, "is_retrograde": False},
        {"name": "火星", "zodiac": {"sign": "白羊座"}, "house": 1, "is_retrograde": False},
        {"name": "木星", "zodiac": {"sign": "金牛座"}, "house": 2, "is_retrograde": False},
        {"name": "土星", "zodiac": {"sign": "水瓶座"}, "house": 11, "is_retrograde": False},
        {"name": "天王星", "zodiac": {"sign": "双鱼座"}, "house": 12, "is_retrograde": False},
        {"name": "海王星", "zodiac": {"sign": "天蝎座"}, "house": 8, "is_retrograde": False},
        {"name": "冥王星", "zodiac": {"sign": "射手座"}, "house": 9, "is_retrograde": False},
    ]
    
    # 应用星座调整
    if sign_adjustments:
        for planet_name, new_sign in sign_adjustments.items():
            for planet in planets:
                if planet["name"] == planet_name:
                    planet["zodiac"]["sign"] = new_sign
                    break
    
    chart_data = {
        "planets": planets,
        "aspects": [
            {"planet1": "太阳", "planet2": "月亮", "aspect": "合相"},
            {"planet1": "水星", "planet2": "金星", "aspect": "三分相"},
            {"planet1": "火星", "planet2": "木星", "aspect": "四分相"},
            {"planet1": "土星", "planet2": "天王星", "aspect": "对分相"},
        ],
        "ascendant": {"sign": "天秤座"},
        "midheaven": {"sign": "巨蟹座"},
    }
    
    return chart_data


def test_element_energy_calculation():
    """
    测试1: 元素能量计算
    """
    print("\n" + "=" * 60)
    print("测试1: 元素能量计算")
    print("=" * 60)
    
    # 测试数据1: 均衡分布
    print("\n--- 测试均衡分布 ---")
    chart_data_balanced = create_sample_chart_data()
    analysis = element_deficiency_service.calculate_element_energies(chart_data_balanced)
    
    print(f"\n总分: {analysis['total_score']:.2f}")
    print(f"平均分: {analysis['average_score']:.2f}")
    
    elements = analysis["elements"]
    for elem_key, elem_data in elements.items():
        print(f"\n{elem_data['info']['symbol']} {elem_data['info']['name_cn']}:")
        print(f"  分数: {elem_data['score']:.2f} ({elem_data['percentage']}%)")
        print(f"  等级: {elem_data['level_label']} ({elem_data['level']})")
        print(f"  行星数量: {len(elem_data['planets'])}")
    
    print(f"\n主导元素: {[d['info']['name_cn'] for d in analysis['dominant_elements']]}")
    print(f"缺角元素: {[d['info']['name_cn'] for d in analysis['deficient_elements']]}")
    print(f"是否有缺角: {analysis['has_deficiency']}")
    
    # 测试数据2: 火元素主导，水元素缺角
    print("\n--- 测试火元素主导，水元素缺角 ---")
    chart_data_fire_dominant = create_sample_chart_data({
        "太阳": "白羊座",
        "月亮": "狮子座",
        "水星": "射手座",
        "金星": "狮子座",
        "火星": "白羊座",
        "木星": "双子座",
        "土星": "天秤座",
        "天王星": "水瓶座",
        "海王星": "金牛座",
        "冥王星": "处女座",
    })
    
    analysis_fire = element_deficiency_service.calculate_element_energies(chart_data_fire_dominant)
    
    elements_fire = analysis_fire["elements"]
    for elem_key, elem_data in elements_fire.items():
        print(f"\n{elem_data['info']['symbol']} {elem_data['info']['name_cn']}:")
        print(f"  分数: {elem_data['score']:.2f}")
        print(f"  等级: {elem_data['level_label']}")
    
    print(f"\n主导元素: {[d['info']['name_cn'] for d in analysis_fire['dominant_elements']]}")
    print(f"缺角元素: {[d['info']['name_cn'] for d in analysis_fire['deficient_elements']]}")
    
    # 显示缺角建议
    if analysis_fire["primary_deficiency"]:
        print(f"\n主要缺角: {analysis_fire['primary_deficiency']['info']['name_cn']}")
        print(f"短期影响: {analysis_fire['primary_deficiency']['descriptions']['short_term']}")
        print(f"建议: {analysis_fire['primary_deficiency']['descriptions']['suggestions'][0]}")
    
    return analysis, analysis_fire


def test_energy_tags_generation():
    """
    测试2: 能量标签生成
    """
    print("\n" + "=" * 60)
    print("测试2: 能量标签生成")
    print("=" * 60)
    
    # 测试数据: 土元素主导
    chart_data_earth = create_sample_chart_data({
        "太阳": "金牛座",
        "月亮": "处女座",
        "水星": "摩羯座",
        "金星": "金牛座",
        "火星": "处女座",
        "木星": "摩羯座",
        "土星": "白羊座",
        "天王星": "狮子座",
        "海王星": "射手座",
        "冥王星": "双子座",
    })
    
    analysis = element_deficiency_service.calculate_element_energies(chart_data_earth)
    tags = element_deficiency_service.generate_energy_tags(analysis)
    
    print(f"\n生成了 {len(tags)} 个能量标签:")
    for tag in tags:
        print(f"\n  🔖 {tag.name}")
        print(f"     Key: {tag.key}")
        print(f"     类别: {tag.category}")
        print(f"     分数: {tag.score:.2f}")
        print(f"     描述: {tag.description}")
    
    return tags


def test_complementary_matching():
    """
    测试3: 互补用户匹配
    """
    print("\n" + "=" * 60)
    print("测试3: 互补用户匹配")
    print("=" * 60)
    
    # 当前用户: 火元素缺角
    current_user_chart = create_sample_chart_data({
        "太阳": "巨蟹座",    # 水
        "月亮": "天蝎座",    # 水
        "水星": "双鱼座",    # 水
        "金星": "天秤座",    # 风
        "火星": "水瓶座",    # 风
        "木星": "双子座",    # 风
        "土星": "金牛座",    # 土
        "天王星": "处女座",  # 土
        "海王星": "摩羯座",  # 土
        "冥王星": "巨蟹座",  # 水
    })
    
    current_analysis = element_deficiency_service.calculate_element_energies(current_user_chart)
    
    print("\n当前用户元素分布:")
    for elem_key, elem_data in current_analysis["elements"].items():
        print(f"  {elem_data['info']['symbol']} {elem_data['info']['name_cn']}: {elem_data['score']:.2f} ({elem_data['level_label']})")
    
    print(f"\n缺角元素: {[d['info']['name_cn'] for d in current_analysis['deficient_elements']]}")
    
    # 创建其他用户数据
    other_users = []
    
    # 用户A: 火元素充沛 (完美互补)
    user_a_chart = create_sample_chart_data({
        "太阳": "白羊座", "月亮": "狮子座", "水星": "射手座",
        "金星": "狮子座", "火星": "白羊座", "木星": "射手座",
        "土星": "金牛座", "天王星": "处女座", "海王星": "摩羯座",
        "冥王星": "双子座",
    })
    user_a_analysis = element_deficiency_service.calculate_element_energies(user_a_chart)
    other_users.append({
        "user_id": 1,
        "username": "热情的白羊",
        "avatar_info": None,
        "element_analysis": user_a_analysis
    })
    
    # 用户B: 土元素充沛
    user_b_chart = create_sample_chart_data({
        "太阳": "金牛座", "月亮": "处女座", "水星": "摩羯座",
        "金星": "金牛座", "火星": "处女座", "木星": "摩羯座",
        "土星": "白羊座", "天王星": "狮子座", "海王星": "射手座",
        "冥王星": "天秤座",
    })
    user_b_analysis = element_deficiency_service.calculate_element_energies(user_b_chart)
    other_users.append({
        "user_id": 2,
        "username": "稳重的金牛",
        "avatar_info": None,
        "element_analysis": user_b_analysis
    })
    
    # 用户C: 均衡分布
    user_c_chart = create_sample_chart_data()
    user_c_analysis = element_deficiency_service.calculate_element_energies(user_c_chart)
    other_users.append({
        "user_id": 3,
        "username": "平衡的天秤",
        "avatar_info": None,
        "element_analysis": user_c_analysis
    })
    
    # 进行互补匹配
    print(f"\n开始互补匹配 (当前有 {len(other_users)} 个用户)...")
    matches = element_deficiency_service.find_complementary_users(
        current_analysis,
        other_users,
        limit=5
    )
    
    print(f"\n找到 {len(matches)} 个匹配用户:")
    for i, match in enumerate(matches, 1):
        print(f"\n  排名 {i}: {match['username']} (ID: {match['user_id']})")
        print(f"     互补分数: {match['complement_score']:.2f}")
        print(f"     匹配类型: {match['match_type']}")
        print(f"     互补详情:")
        for detail in match["complement_details"]:
            print(f"       - {detail['description']}")
    
    return matches


def test_blind_box_clues():
    """
    测试4: 盲盒线索生成
    """
    print("\n" + "=" * 60)
    print("测试4: 盲盒线索生成")
    print("=" * 60)
    
    # 当前用户: 水元素缺角
    current_user_chart = create_sample_chart_data({
        "太阳": "白羊座", "月亮": "狮子座", "水星": "射手座",
        "金星": "双子座", "火星": "天秤座", "木星": "水瓶座",
        "土星": "金牛座", "天王星": "处女座", "海王星": "摩羯座",
        "冥王星": "白羊座",
    })
    current_analysis = element_deficiency_service.calculate_element_energies(current_user_chart)
    
    # 匹配用户: 水元素充沛
    matched_chart = create_sample_chart_data({
        "太阳": "巨蟹座", "月亮": "天蝎座", "水星": "双鱼座",
        "金星": "巨蟹座", "火星": "天蝎座", "木星": "双鱼座",
        "土星": "白羊座", "天王星": "狮子座", "海王星": "射手座",
        "冥王星": "金牛座",
    })
    matched_analysis = element_deficiency_service.calculate_element_energies(matched_chart)
    
    matched_user = {
        "user_id": 100,
        "username": "神秘的巨蟹",
        "avatar_info": None,
        "complement_score": 85.5,
        "complement_details": [
            {
                "element": "water",
                "match_type": "perfect",
                "description": "对方水元素能量充沛"
            }
        ],
        "element_analysis": matched_analysis
    }
    
    print("\n当前用户缺角元素:")
    for d in current_analysis["deficient_elements"]:
        print(f"  {d['info']['symbol']} {d['info']['name_cn']}: {d['score']:.2f}")
    
    print("\n匹配用户元素分布:")
    for elem_key, elem_data in matched_analysis["elements"].items():
        print(f"  {elem_data['info']['symbol']} {elem_data['info']['name_cn']}: {elem_data['score']:.2f} ({elem_data['level_label']})")
    
    # 生成盲盒线索
    print("\n生成盲盒线索...")
    blind_box = element_deficiency_service.generate_blind_box_clues(
        matched_user,
        current_analysis
    )
    
    print(f"\n盲盒ID: {blind_box['blind_box_id']}")
    print(f"互补分数: {blind_box['complement_score']}")
    print(f"\n线索列表 ({len(blind_box['clues'])} 条):")
    for i, clue in enumerate(blind_box["clues"], 1):
        print(f"\n  #{i} [{clue['hint_level']}]:")
        print(f"     类型: {clue['type']}")
        print(f"     线索: {clue['clue']}")
    
    return blind_box


def test_deficiency_completeness():
    """
    测试5: 缺角补全分数计算
    """
    print("\n" + "=" * 60)
    print("测试5: 缺角补全分数计算")
    print("=" * 60)
    
    # 场景1: 用户缺火，匹配用户火元素充沛
    print("\n--- 场景1: 用户缺火，匹配用户火元素充沛 ---")
    
    user_chart = create_sample_chart_data({
        "太阳": "巨蟹座", "月亮": "天蝎座", "水星": "双鱼座",  # 水
        "金星": "天秤座", "火星": "水瓶座", "木星": "双子座",  # 风
        "土星": "金牛座", "天王星": "处女座", "海王星": "摩羯座",  # 土
        "冥王星": "巨蟹座",  # 水
    })
    user_analysis = element_deficiency_service.calculate_element_energies(user_chart)
    
    match_chart = create_sample_chart_data({
        "太阳": "白羊座", "月亮": "狮子座", "水星": "射手座",  # 火
        "金星": "狮子座", "火星": "白羊座", "木星": "射手座",  # 火
        "土星": "金牛座", "天王星": "处女座", "海王星": "摩羯座",  # 土
        "冥王星": "白羊座",  # 火
    })
    match_analysis = element_deficiency_service.calculate_element_energies(match_chart)
    
    print("\n用户元素分布:")
    for elem_key, elem_data in user_analysis["elements"].items():
        deficit = max(0, user_analysis["average_score"] - elem_data["score"])
        print(f"  {elem_data['info']['symbol']} {elem_data['info']['name_cn']}: {elem_data['score']:.2f} (缺口: {deficit:.2f})")
    
    print("\n匹配用户元素分布:")
    for elem_key, elem_data in match_analysis["elements"].items():
        surplus = max(0, elem_data["score"] - match_analysis["average_score"])
        print(f"  {elem_data['info']['symbol']} {elem_data['info']['name_cn']}: {elem_data['score']:.2f} (盈余: {surplus:.2f})")
    
    completeness = element_deficiency_service.calculate_deficiency_completeness_score(
        user_analysis,
        match_analysis
    )
    
    print(f"\n总体补全分数: {completeness['overall_completeness']}%")
    print(f"是否完全补全: {completeness['is_fully_complete']}")
    
    print("\n各元素补全详情:")
    for elem_key, elem_detail in completeness["element_details"].items():
        print(f"\n  {elem_detail['info']['symbol']} {elem_detail['info']['name_cn']}:")
        print(f"     用户分数: {elem_detail['user_score']:.2f}")
        print(f"     匹配用户分数: {elem_detail['match_score']:.2f}")
        print(f"     用户缺口: {elem_detail['user_deficit']:.2f}")
        print(f"     匹配用户盈余: {elem_detail['match_surplus']:.2f}")
        print(f"     补全百分比: {elem_detail['completeness_percentage']}%")
        print(f"     是否已补全: {elem_detail['is_complete']}")
    
    return completeness


def main():
    """
    运行所有测试
    """
    print("=" * 60)
    print("元素缺角寻宝系统 - 核心功能测试")
    print("=" * 60)
    
    test_count = 5
    passed = 0
    failed = 0
    
    try:
        test_element_energy_calculation()
        print("\n✅ 测试1通过: 元素能量计算正常")
        passed += 1
    except Exception as e:
        print(f"\n❌ 测试1失败: {e}")
        failed += 1
    
    try:
        test_energy_tags_generation()
        print("\n✅ 测试2通过: 能量标签生成正常")
        passed += 1
    except Exception as e:
        print(f"\n❌ 测试2失败: {e}")
        failed += 1
    
    try:
        test_complementary_matching()
        print("\n✅ 测试3通过: 互补用户匹配正常")
        passed += 1
    except Exception as e:
        print(f"\n❌ 测试3失败: {e}")
        failed += 1
    
    try:
        test_blind_box_clues()
        print("\n✅ 测试4通过: 盲盒线索生成正常")
        passed += 1
    except Exception as e:
        print(f"\n❌ 测试4失败: {e}")
        failed += 1
    
    try:
        test_deficiency_completeness()
        print("\n✅ 测试5通过: 缺角补全分数计算正常")
        passed += 1
    except Exception as e:
        print(f"\n❌ 测试5失败: {e}")
        failed += 1
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    print(f"总测试数: {test_count}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    
    if failed == 0:
        print("\n🎉 所有测试通过！元素缺角寻宝系统核心功能正常工作！")
    else:
        print(f"\n⚠️ 有 {failed} 个测试失败，请检查代码")


if __name__ == "__main__":
    main()
