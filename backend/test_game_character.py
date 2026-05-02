import asyncio
import logging
import sys
import os
import math
from typing import Dict, List, Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.astro import calculate_chart
from app.services.game_character_service import (
    generate_game_character,
    calculate_stats_stddev,
    check_stat_balance,
    validate_stat_name,
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


TEST_CASES = [
    {
        "name": "火焰战士（火象主导）",
        "description": "太阳白羊、月亮狮子、上升射手 - 纯火象三巨头",
        "category": "基础元素",
        "birth_data": {
            "year": 1990,
            "month": 4,
            "day": 10,
            "hour": 12,
            "minute": 0,
            "latitude": 39.9042,
            "longitude": 116.4074,
        }
    },
    {
        "name": "大地守护者（土象主导）",
        "description": "太阳金牛、月亮处女、上升摩羯 - 纯土象三巨头",
        "category": "基础元素",
        "birth_data": {
            "year": 1990,
            "month": 5,
            "day": 5,
            "hour": 6,
            "minute": 0,
            "latitude": 39.9042,
            "longitude": 116.4074,
        }
    },
    {
        "name": "疾风智者（风象主导）",
        "description": "太阳双子、月亮天秤、上升水瓶 - 纯风象三巨头",
        "category": "基础元素",
        "birth_data": {
            "year": 1990,
            "month": 6,
            "day": 10,
            "hour": 18,
            "minute": 0,
            "latitude": 39.9042,
            "longitude": 116.4074,
        }
    },
    {
        "name": "深海先知（水象主导）",
        "description": "太阳巨蟹、月亮天蝎、上升双鱼 - 纯水象三巨头",
        "category": "基础元素",
        "birth_data": {
            "year": 1990,
            "month": 7,
            "day": 10,
            "hour": 0,
            "minute": 0,
            "latitude": 39.9042,
            "longitude": 116.4074,
        }
    },
    {
        "name": "梦幻诗人（月亮双鱼合海王）",
        "description": "月亮双鱼，海王星强相位 - 测试神秘朦胧人设",
        "category": "特殊相位",
        "birth_data": {
            "year": 1995,
            "month": 3,
            "day": 15,
            "hour": 20,
            "minute": 30,
            "latitude": 39.9042,
            "longitude": 116.4074,
        }
    },
    {
        "name": "深渊战士（火星冥王星配置）",
        "description": "火星与冥王星有强相位 - 测试高强度战力角色",
        "category": "特殊相位",
        "birth_data": {
            "year": 1985,
            "month": 11,
            "day": 20,
            "hour": 8,
            "minute": 0,
            "latitude": 39.9042,
            "longitude": 116.4074,
        }
    },
    {
        "name": "南半球旅者（澳大利亚悉尼）",
        "description": "南半球坐标测试 - 悉尼 (南纬33°)",
        "category": "地理位置",
        "birth_data": {
            "year": 1990,
            "month": 1,
            "day": 15,
            "hour": 10,
            "minute": 0,
            "latitude": -33.8688,
            "longitude": 151.2093,
        }
    },
    {
        "name": "西经探索者（美国纽约）",
        "description": "西经坐标测试 - 纽约 (西经74°)",
        "category": "地理位置",
        "birth_data": {
            "year": 1990,
            "month": 7,
            "day": 4,
            "hour": 14,
            "minute": 30,
            "latitude": 40.7128,
            "longitude": -74.0060,
        }
    },
    {
        "name": "北欧极光守护者（挪威奥斯陆）",
        "description": "高纬度测试 - 奥斯陆 (北纬59°)",
        "category": "地理位置",
        "birth_data": {
            "year": 1990,
            "month": 12,
            "day": 21,
            "hour": 11,
            "minute": 0,
            "latitude": 59.9139,
            "longitude": 10.7522,
        }
    },
    {
        "name": "平庸行者（均衡星盘）",
        "description": "元素分布相对均衡的星盘 - 测试平衡性",
        "category": "均衡测试",
        "birth_data": {
            "year": 1988,
            "month": 8,
            "day": 15,
            "hour": 15,
            "minute": 30,
            "latitude": 39.9042,
            "longitude": 116.4074,
        }
    },
    {
        "name": "边界探索者（凌晨0点）",
        "description": "凌晨零点出生 - 测试宫位边界计算",
        "category": "边界测试",
        "birth_data": {
            "year": 1990,
            "month": 3,
            "day": 20,
            "hour": 0,
            "minute": 1,
            "latitude": 39.9042,
            "longitude": 116.4074,
        }
    },
    {
        "name": "正午之子（中午12点）",
        "description": "中午12点出生 - 太阳可能在天顶附近",
        "category": "边界测试",
        "birth_data": {
            "year": 1990,
            "month": 6,
            "day": 21,
            "hour": 12,
            "minute": 0,
            "latitude": 39.9042,
            "longitude": 116.4074,
        }
    },
]


async def test_single_case(test_case: Dict) -> Dict:
    """
    测试单个案例
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"测试案例: {test_case['name']}")
    logger.info(f"描述: {test_case['description']}")
    logger.info(f"分类: {test_case.get('category', '未分类')}")
    logger.info(f"{'='*60}")
    
    birth_data = test_case["birth_data"]
    
    chart_data = calculate_chart(
        year=birth_data["year"],
        month=birth_data["month"],
        day=birth_data["day"],
        hour=birth_data["hour"],
        minute=birth_data["minute"],
        latitude=birth_data["latitude"],
        longitude=birth_data["longitude"],
        house_system="placidus"
    )
    
    result = await generate_game_character(chart_data, test_case["name"])
    
    if not result["success"]:
        logger.error(f"测试失败: {result.get('error', '未知错误')}")
        return result
    
    character = result["character"]
    stats = character["stats"]
    
    logger.info(f"\n【属性面板】")
    logger.info(f"  生命值: {stats['health']} (最大: {stats['max_health']})")
    logger.info(f"  攻击力: {stats['attack']}")
    logger.info(f"  防御力: {stats['defense']}")
    logger.info(f"  蓝量: {stats['mana']} (最大: {stats['max_mana']})")
    logger.info(f"  速度: {stats['speed']}")
    logger.info(f"  暴击率: {stats['critical_rate']}%")
    logger.info(f"  暴击伤害: {stats['critical_damage']}%")
    logger.info(f"  综合战力: {stats['combat_power']}")
    
    logger.info(f"\n【天赋被动】")
    if character["passives"]:
        for passive in character["passives"]:
            logger.info(f"  ✦ {passive['name']}")
            logger.info(f"    描述: {passive['description']}")
            logger.info(f"    来源: {passive['source']}")
            if passive.get("stat_bonus"):
                logger.info(f"    属性加成: {passive['stat_bonus']}")
    else:
        logger.info(f"  暂无天赋被动")
    
    logger.info(f"\n【外貌描述】")
    appearance = character["appearance"]
    logger.info(f"  整体描述: {appearance['overall_description']}")
    logger.info(f"  面部特征: {appearance['facial_features']}")
    logger.info(f"  体型特征: {appearance['body_type']}")
    logger.info(f"  气场: {appearance['aura']}")
    if appearance.get("style_suggestions"):
        logger.info(f"  风格建议: {', '.join(appearance['style_suggestions'])}")
    if appearance.get("key_details"):
        logger.info(f"  关键细节: {', '.join(appearance['key_details'])}")
    
    logger.info(f"\n【星盘来源】")
    astro_source = character["astro_source"]
    big_three = astro_source.get("big_three", {})
    if big_three.get("sun"):
        sun_sign = big_three["sun"].get("sign", "未知") if isinstance(big_three.get("sun"), dict) else "未知"
        sun_house = big_three["sun"].get("house", 0) if isinstance(big_three.get("sun"), dict) else 0
        logger.info(f"  太阳: {sun_sign} 第{sun_house}宫")
    if big_three.get("moon"):
        moon_sign = big_three["moon"].get("sign", "未知") if isinstance(big_three.get("moon"), dict) else "未知"
        moon_house = big_three["moon"].get("house", 0) if isinstance(big_three.get("moon"), dict) else 0
        logger.info(f"  月亮: {moon_sign} 第{moon_house}宫")
    if big_three.get("ascendant"):
        asc_sign = big_three["ascendant"].get("sign", "未知") if isinstance(big_three.get("ascendant"), dict) else "未知"
        logger.info(f"  上升: {asc_sign}")
    logger.info(f"  主导元素: {astro_source.get('dominant_element', '未知')}")
    logger.info(f"  主导特质: {astro_source.get('dominant_quality', '未知')}")
    element_percent = astro_source.get("element_percentage", {})
    if isinstance(element_percent, dict) and element_percent:
        logger.info(f"  元素占比: 火{element_percent.get('火', 0)}% 土{element_percent.get('土', 0)}% 风{element_percent.get('风', 0)}% 水{element_percent.get('水', 0)}%")
    
    return result


async def test_stat_validation():
    """
    测试属性白名单校验功能
    """
    logger.info(f"\n{'#'*60}")
    logger.info(f"# 测试属性白名单校验")
    logger.info(f"{'#'*60}")
    
    valid_stats = ["health", "attack", "defense", "mana", "speed", "critical_rate", "critical_damage", "combat_power"]
    invalid_stats = ["invalid_stat", "power", "strength", "stamina", "unknown_field"]
    
    logger.info(f"\n【有效属性测试】")
    for stat in valid_stats:
        result = validate_stat_name(stat, "测试上下文")
        status = "✓ 有效" if result else "✗ 无效（异常）"
        logger.info(f"  {stat}: {status}")
    
    logger.info(f"\n【无效属性测试（应输出警告日志）】")
    for stat in invalid_stats:
        result = validate_stat_name(stat, "测试上下文-无效字段")
        status = "✗ 正确识别为无效" if not result else "✓ 异常（应无效）"
        logger.info(f"  {stat}: {status}")
    
    logger.info(f"\n属性白名单校验测试完成")


async def run_all_tests():
    """
    运行所有测试
    """
    logger.info(f"\n{'#'*60}")
    logger.info(f"# 开始游戏角色生成测试")
    logger.info(f"# 测试案例数量: {len(TEST_CASES)}")
    logger.info(f"{'#'*60}")
    
    await test_stat_validation()
    
    results = []
    all_stats_list = []
    category_stats = {}
    
    for test_case in TEST_CASES:
        result = await test_single_case(test_case)
        results.append(result)
        
        if result["success"]:
            stats = result["character"]["stats"]
            all_stats_list.append(stats)
            
            category = test_case.get("category", "未分类")
            if category not in category_stats:
                category_stats[category] = []
            category_stats[category].append(stats)
    
    logger.info(f"\n{'#'*60}")
    logger.info(f"# 测试统计与平衡性分析")
    logger.info(f"{'#'*60}")
    
    if all_stats_list:
        all_stats_list_sorted = sorted(
            [{"name": TEST_CASES[i]["name"], "stats": s, "category": TEST_CASES[i].get("category", "未分类")}
             for i, s in enumerate(all_stats_list)],
            key=lambda x: x["stats"]["combat_power"],
            reverse=True
        )
        
        logger.info(f"\n【战力排名】")
        for i, stat_item in enumerate(all_stats_list_sorted, 1):
            stats = stat_item["stats"]
            logger.info(f"  {i}. {stat_item['name']}")
            logger.info(f"     分类: {stat_item['category']}, 战力: {stats['combat_power']}")
            logger.info(f"     攻{stats['attack']}/防{stats['defense']}/血{stats['max_health']}/蓝{stats['max_mana']}")
        
        logger.info(f"\n【分类统计】")
        for category, stats_list in category_stats.items():
            if stats_list:
                powers = [s["combat_power"] for s in stats_list]
                avg_power = sum(powers) / len(powers)
                logger.info(f"  {category}: {len(stats_list)} 个角色")
                logger.info(f"    平均战力: {avg_power:.1f}, 范围: {min(powers)} - {max(powers)}")
        
        logger.info(f"\n【标准差统计】")
        stddev_result = calculate_stats_stddev(all_stats_list)
        
        for stat_name, data in stddev_result.items():
            logger.info(f"  {stat_name}:")
            logger.info(f"    平均值: {data['mean']}")
            logger.info(f"    标准差: {data['stddev']}")
            logger.info(f"    变异系数(CV): {data['cv']}%")
        
        logger.info(f"\n【平衡性分析】")
        balance_report = check_stat_balance(all_stats_list, cv_threshold=30.0)
        
        if balance_report["is_balanced"]:
            logger.info(f"  ✅ 整体平衡性良好: 所有属性变异系数均在阈值(30%)以内")
        else:
            logger.info(f"  ⚠️ 检测到不平衡属性:")
            for unbalanced in balance_report["unbalanced_stats"]:
                logger.info(f"    - {unbalanced['stat']}: CV={unbalanced['cv']}% > 阈值={unbalanced['threshold']}%")
        
        logger.info(f"\n【单属性均衡校验】")
        stat_ranges = {
            "health": {"min": 80, "max": 200, "name": "生命值"},
            "attack": {"min": 10, "max": 50, "name": "攻击力"},
            "defense": {"min": 3, "max": 30, "name": "防御力"},
            "mana": {"min": 40, "max": 150, "name": "蓝量"},
            "speed": {"min": 40, "max": 80, "name": "速度"},
            "combat_power": {"min": 600, "max": 1200, "name": "综合战力"},
        }
        
        for stat_name, expected_range in stat_ranges.items():
            values = [s[stat_name] for s in all_stats_list]
            min_val = min(values)
            max_val = max(values)
            avg_val = sum(values) / len(values)
            
            in_range = all(expected_range["min"] <= v <= expected_range["max"] for v in values)
            status = "✓ 正常" if in_range else "⚠️ 超出预期范围"
            
            logger.info(f"  {expected_range['name']} ({stat_name}):")
            logger.info(f"    范围: {min_val} - {max_val}, 预期: {expected_range['min']} - {expected_range['max']}")
            logger.info(f"    平均值: {avg_val:.1f}")
            logger.info(f"    状态: {status}")
    
    success_count = sum(1 for r in results if r["success"])
    logger.info(f"\n【测试结果】")
    logger.info(f"  成功: {success_count}/{len(results)}")
    logger.info(f"  失败: {len(results) - success_count}/{len(results)}")
    
    return results


if __name__ == "__main__":
    asyncio.run(run_all_tests())
