from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging

from app.services.profile_extractor_service import (
    get_planet_weight,
    get_source_id,
    generate_aspect_source_id,
    SourceIdType,
    PLANET_WEIGHT_MAP,
    STELLIUM_THRESHOLD_WEIGHTED,
    ELEMENT_CONFLICT_THRESHOLD,
)

logger = logging.getLogger(__name__)


MIN_CONFLICT_WEIGHT = 10


@dataclass
class ConflictRule:
    id: str
    name: str
    planet1_id: str
    planet2_id: str
    aspect_type: str
    conflict_traits: Tuple[str, str]
    resolution: str
    social_description: str
    min_total_weight: int = MIN_CONFLICT_WEIGHT


def get_aspect_type_id(aspect_type: str) -> str:
    """
    将相位中文名称转换为规范的 ID
    """
    mapping = {
        "合相": "conjunction",
        "六分相": "sextile",
        "三分相": "trine",
        "四分相": "square",
        "对分相": "opposition",
    }
    return mapping.get(aspect_type, aspect_type.lower())


CONFLICT_RULES = [
    ConflictRule(
        id="mars_aries_saturn_conjunction",
        name="火星白羊+土星合火星",
        planet1_id="mars",
        planet2_id="saturn",
        aspect_type="conjunction",
        conflict_traits=("冲动急躁", "克制隐忍"),
        resolution="冲动但克制",
        social_description="表面看似冷静，内心却有强烈的行动欲望，懂得在合适的时机释放能量",
        min_total_weight=11
    ),
    ConflictRule(
        id="mars_aries_saturn_square",
        name="火星白羊+土星四分相",
        planet1_id="mars",
        planet2_id="saturn",
        aspect_type="square",
        conflict_traits=("冲动鲁莽", "谨慎保守"),
        resolution="热情但审慎",
        social_description="有强烈的行动力，但会在行动前反复考量，是深思熟虑后的勇猛",
        min_total_weight=11
    ),
    ConflictRule(
        id="mars_aries_saturn_opposition",
        name="火星白羊+土星对分相",
        planet1_id="mars",
        planet2_id="saturn",
        aspect_type="opposition",
        conflict_traits=("直接冲动", "压抑克制"),
        resolution="外放但有节度",
        social_description="性格中有明显的拉扯感，有时冲动有时克制，但最终能找到平衡点",
        min_total_weight=11
    ),
    ConflictRule(
        id="venus_scorpio_saturn",
        name="金星天蝎+土星相位",
        planet1_id="venus",
        planet2_id="saturn",
        aspect_type="any",
        conflict_traits=("深刻浓烈", "克制疏离"),
        resolution="深情但保留",
        social_description="对感情认真深刻，但不轻易表露，需要时间建立信任",
        min_total_weight=11
    ),
    ConflictRule(
        id="moon_cancer_saturn",
        name="月亮巨蟹+土星相位",
        planet1_id="moon",
        planet2_id="saturn",
        aspect_type="any",
        conflict_traits=("情感敏感", "情感压抑"),
        resolution="温柔但有边界",
        social_description="内心温柔渴望关怀，但因害怕受伤而建立保护壳",
        min_total_weight=14
    ),
    ConflictRule(
        id="sun_leo_saturn",
        name="太阳狮子+土星相位",
        planet1_id="sun",
        planet2_id="saturn",
        aspect_type="any",
        conflict_traits=("渴望展现", "自我限制"),
        resolution="自信但谦逊",
        social_description="有展现自我的欲望，但会以更低调、更负责任的方式表现",
        min_total_weight=14
    ),
    ConflictRule(
        id="mercury_gemini_saturn",
        name="水星双子+土星相位",
        planet1_id="mercury",
        planet2_id="saturn",
        aspect_type="any",
        conflict_traits=("思维跳跃", "思维严谨"),
        resolution="灵活但有条理",
        social_description="思维既敏捷又深刻，能在轻松交流中展现智慧深度",
        min_total_weight=11
    ),
    ConflictRule(
        id="venus_libra_pluto",
        name="金星天秤+冥王星相位",
        planet1_id="venus",
        planet2_id="pluto",
        aspect_type="any",
        conflict_traits=("追求和谐", "渴望深度"),
        resolution="优雅但有力量",
        social_description="表面追求和平，内心却渴望深刻的连接，在关系中既有风度又有原则",
        min_total_weight=9
    ),
    ConflictRule(
        id="moon_capricorn_venus_pisces",
        name="月亮摩羯+金星双鱼",
        planet1_id="moon",
        planet2_id="venus",
        aspect_type="sign_conflict",
        conflict_traits=("克制务实", "浪漫感性"),
        resolution="现实但浪漫",
        social_description="内心既有务实的一面，又有对美好事物的向往，能在现实中保持理想",
        min_total_weight=10
    ),
    ConflictRule(
        id="sun_sagittarius_saturn",
        name="太阳射手+土星相位",
        planet1_id="sun",
        planet2_id="saturn",
        aspect_type="any",
        conflict_traits=("自由奔放", "责任束缚"),
        resolution="自由但负责",
        social_description="渴望自由却不逃避责任，是带着使命感的探险家",
        min_total_weight=14
    ),
    ConflictRule(
        id="sun_aquarius_venus_cancer",
        name="太阳水瓶+金星巨蟹",
        planet1_id="sun",
        planet2_id="venus",
        aspect_type="sign_conflict",
        conflict_traits=("独立疏离", "情感依赖"),
        resolution="独立但温暖",
        social_description="表面追求独立空间，内心却渴望情感连接，在关系中保持距离却不失温度",
        min_total_weight=17
    ),
    ConflictRule(
        id="moon_scorpio_venus_libra",
        name="月亮天蝎+金星天秤",
        planet1_id="moon",
        planet2_id="venus",
        aspect_type="sign_conflict",
        conflict_traits=("深刻私密", "社交开放"),
        resolution="神秘但亲和",
        social_description="内心有深刻的情感世界，但能以优雅开放的方式与人交往",
        min_total_weight=17
    ),
]


SIGN_CONFLICT_PATTERNS = [
    {
        "signs": ["白羊座", "摩羯座"],
        "sign_ids": ["aries", "capricorn"],
        "conflict_traits": ("冲动直接", "克制隐忍"),
        "resolution": "热情但审慎",
        "description": "既有白羊的行动力，又有摩羯的计划性，是稳中求进的类型",
        "min_weight": 10
    },
    {
        "signs": ["双子座", "处女座"],
        "sign_ids": ["gemini", "virgo"],
        "conflict_traits": ("思维跳跃", "思维严谨"),
        "resolution": "灵活但有条理",
        "description": "能在多变中保持秩序，是信息整合的高手",
        "min_weight": 10
    },
    {
        "signs": ["巨蟹座", "摩羯座"],
        "sign_ids": ["cancer", "capricorn"],
        "conflict_traits": ("情感柔软", "现实坚硬"),
        "resolution": "温柔但坚定",
        "description": "以柔克刚的典范，内心温暖却有原则",
        "min_weight": 10
    },
    {
        "signs": ["狮子座", "水瓶座"],
        "sign_ids": ["leo", "aquarius"],
        "conflict_traits": ("自我展现", "群体疏离"),
        "resolution": "独特但合群",
        "description": "既能展现个性，又能融入群体，是有魅力的领导者",
        "min_weight": 10
    },
    {
        "signs": ["天秤座", "天蝎座"],
        "sign_ids": ["libra", "scorpio"],
        "conflict_traits": ("追求和谐", "渴望真实"),
        "resolution": "优雅但有深度",
        "description": "表面追求和平，内心追求真实，在关系中保持平衡",
        "min_weight": 10
    },
    {
        "signs": ["射手座", "处女座"],
        "sign_ids": ["sagittarius", "virgo"],
        "conflict_traits": ("宏观视野", "微观细节"),
        "resolution": "远见但务实",
        "description": "既能看到大局，又能关注细节，是理想的执行者",
        "min_weight": 10
    },
    {
        "signs": ["双鱼座", "处女座"],
        "sign_ids": ["pisces", "virgo"],
        "conflict_traits": ("梦想模糊", "现实清晰"),
        "resolution": "理想但务实",
        "description": "在现实中保持理想，能用实际行动实现梦想",
        "min_weight": 10
    },
]


def _zodiac_to_id(sign_name: str) -> str:
    """将星座中文名称转换为 ID"""
    mapping = {
        "白羊座": "aries",
        "金牛座": "taurus",
        "双子座": "gemini",
        "巨蟹座": "cancer",
        "狮子座": "leo",
        "处女座": "virgo",
        "天秤座": "libra",
        "天蝎座": "scorpio",
        "射手座": "sagittarius",
        "摩羯座": "capricorn",
        "水瓶座": "aquarius",
        "双鱼座": "pisces",
    }
    return mapping.get(sign_name, sign_name.lower())


def detect_planetary_conflicts(aspects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    检测行星之间的冲突配置（使用规范 Source ID 和加权阈值）
    
    优化点：
    1. 使用规范的 Source ID 而非字符串匹配
    2. 应用行星权重过滤低权重冲突
    3. 仅保留加权总分 >= MIN_CONFLICT_WEIGHT 的冲突
    """
    conflicts = []
    
    for aspect in aspects:
        p1 = aspect.get("planet1", "")
        p2 = aspect.get("planet2", "")
        aspect_type = aspect.get("aspect", "")
        aspect_type_id = get_aspect_type_id(aspect_type)
        
        p1_weight = aspect.get("planet1_weight", get_planet_weight(p1))
        p2_weight = aspect.get("planet2_weight", get_planet_weight(p2))
        total_weight = p1_weight + p2_weight
        
        if total_weight < MIN_CONFLICT_WEIGHT:
            continue
        
        for rule in CONFLICT_RULES:
            if rule.aspect_type == "sign_conflict":
                continue
            
            planets_match = (
                (rule.planet1_id == get_source_id(p1) and rule.planet2_id == get_source_id(p2)) or
                (rule.planet1_id == get_source_id(p2) and rule.planet2_id == get_source_id(p1))
            )
            
            if planets_match:
                aspect_match = (
                    rule.aspect_type == aspect_type_id or 
                    rule.aspect_type == "any"
                )
                
                if aspect_match and total_weight >= rule.min_total_weight:
                    conflicts.append({
                        "rule_id": rule.id,
                        "name": rule.name,
                        "planets": [p1, p2],
                        "planet_ids": [get_source_id(p1), get_source_id(p2)],
                        "planet_weights": [p1_weight, p2_weight],
                        "total_weight": total_weight,
                        "aspect": aspect_type,
                        "aspect_id": aspect_type_id,
                        "aspect_symbol": aspect.get("aspect_symbol", ""),
                        "conflict_traits": list(rule.conflict_traits),
                        "resolution": rule.resolution,
                        "social_description": rule.social_description,
                        "orb": aspect.get("orb", 0),
                        "source_id": aspect.get("source_id", generate_aspect_source_id(p1, p2, aspect_type)),
                    })
    
    logger.info(f"检测到 {len(conflicts)} 个行星冲突配置（权重过滤后）")
    return conflicts


def detect_sign_conflicts(
    planets: List[Dict[str, Any]], 
    big_three: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    检测星座之间的冲突配置（使用加权分数制）
    
    优化点：
    1. 计算每个行星的权重
    2. 仅当加权总分 >= min_weight 时才视为显著冲突
    3. 使用规范的星座 ID 匹配
    """
    conflicts = []
    
    sign_positions = {}
    sign_weighted_scores = {}
    main_planets_names = ["太阳", "月亮", "水星", "金星", "火星", "木星", "土星", "天王星", "海王星", "冥王星"]
    
    for planet in planets:
        name = planet.get("name", "")
        if name in main_planets_names:
            sign = planet.get("zodiac", {}).get("sign", "")
            if sign:
                weight = get_planet_weight(name)
                sign_id = _zodiac_to_id(sign)
                
                if sign not in sign_positions:
                    sign_positions[sign] = []
                    sign_weighted_scores[sign] = 0
                
                sign_positions[sign].append(name)
                sign_weighted_scores[sign] += weight
    
    for pattern in SIGN_CONFLICT_PATTERNS:
        s1_id, s2_id = pattern["sign_ids"]
        s1_name, s2_name = pattern["signs"]
        
        has_s1 = s1_name in sign_positions
        has_s2 = s2_name in sign_positions
        
        if has_s1 and has_s2:
            weight_s1 = sign_weighted_scores.get(s1_name, 0)
            weight_s2 = sign_weighted_scores.get(s2_name, 0)
            total_weight = weight_s1 + weight_s2
            
            min_required = pattern.get("min_weight", 10)
            if total_weight >= min_required:
                planets_s1 = sign_positions.get(s1_name, [])
                planets_s2 = sign_positions.get(s2_name, [])
                
                conflicts.append({
                    "pattern": f"{s1_name} + {s2_name}",
                    "signs": [s1_name, s2_name],
                    "sign_ids": [s1_id, s2_id],
                    "planets_in_sign1": planets_s1,
                    "planets_in_sign2": planets_s2,
                    "weights_in_sign1": [get_planet_weight(p) for p in planets_s1],
                    "weights_in_sign2": [get_planet_weight(p) for p in planets_s2],
                    "total_weight": total_weight,
                    "conflict_traits": list(pattern["conflict_traits"]),
                    "resolution": pattern["resolution"],
                    "social_description": pattern["description"],
                    "source_id": f"sign_conflict_{s1_id}_{s2_id}",
                })
    
    logger.info(f"检测到 {len(conflicts)} 个星座冲突配置（加权过滤后）")
    return conflicts


def detect_element_quality_conflicts(
    element_weighted_scores: Dict[str, float],
    quality_weighted_scores: Dict[str, float]
) -> Dict[str, Any]:
    """
    检测元素和特质分布中的冲突/平衡（使用加权分数制）
    
    优化点：
    1. 使用加权分数而非行星数量
    2. 动态阈值而非硬编码
    3. 更精准地捕捉核心行星带来的内在挣扎
    """
    result = {
        "element_balance": {},
        "quality_balance": {},
        "potential_conflicts": [],
    }
    
    total_element_weight = sum(element_weighted_scores.values()) if element_weighted_scores else 0
    
    if total_element_weight > 0:
        for element, score in element_weighted_scores.items():
            percentage = (score / total_element_weight) * 100
            result["element_balance"][element] = {
                "weighted_score": score,
                "percentage": round(percentage, 1),
            }
    
    fire_score = element_weighted_scores.get("火", 0)
    water_score = element_weighted_scores.get("水", 0)
    air_score = element_weighted_scores.get("风", 0)
    earth_score = element_weighted_scores.get("土", 0)
    
    if total_element_weight > 0:
        fire_ratio = fire_score / total_element_weight
        water_ratio = water_score / total_element_weight
        air_ratio = air_score / total_element_weight
        earth_ratio = earth_score / total_element_weight
        
        if fire_ratio >= ELEMENT_CONFLICT_THRESHOLD and water_ratio >= ELEMENT_CONFLICT_THRESHOLD:
            result["potential_conflicts"].append({
                "type": "火水冲突",
                "type_id": "fire_water_conflict",
                "fire_weighted_score": fire_score,
                "water_weighted_score": water_score,
                "fire_ratio": round(fire_ratio, 2),
                "water_ratio": round(water_ratio, 2),
                "description": "火象的热情与水象的敏感相互交织，情感表达丰富但可能波动",
                "resolution": "热情但敏感"
            })
        
        if air_ratio >= ELEMENT_CONFLICT_THRESHOLD and earth_ratio >= ELEMENT_CONFLICT_THRESHOLD:
            result["potential_conflicts"].append({
                "type": "风土冲突",
                "type_id": "air_earth_conflict",
                "air_weighted_score": air_score,
                "earth_weighted_score": earth_score,
                "air_ratio": round(air_ratio, 2),
                "earth_ratio": round(earth_ratio, 2),
                "description": "风象的思维与土象的务实相互作用，既有远见又能落地",
                "resolution": "理想但务实"
            })
    
    total_quality_weight = sum(quality_weighted_scores.values()) if quality_weighted_scores else 0
    
    if total_quality_weight > 0:
        for quality, score in quality_weighted_scores.items():
            percentage = (score / total_quality_weight) * 100
            result["quality_balance"][quality] = {
                "weighted_score": score,
                "percentage": round(percentage, 1),
            }
    
    return result


def resolve_conflicts_in_tags(
    tags: List[Dict[str, Any]], 
    conflicts: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    基于冲突检测结果，优化性格标签（使用规范 Source ID 匹配）
    
    优化点：
    1. 使用规范的 source_id 进行精确匹配，而非字符串模糊匹配
    2. 防止误删有效性格标签
    3. 保留处理来源的清晰追踪
    """
    resolved_tags = []
    processed_source_ids = set()
    
    for conflict in conflicts:
        resolution = conflict.get("resolution", "")
        source_id = conflict.get("source_id", "")
        
        if resolution:
            planet_ids = conflict.get("planet_ids", [])
            for pid in planet_ids:
                processed_source_ids.add(pid)
            
            sign_ids = conflict.get("sign_ids", [])
            for sid in sign_ids:
                processed_source_ids.add(f"stellium_{sid}")
            
            resolved_tags.append({
                "id": f"resolved_{conflict.get('rule_id', conflict.get('source_id', 'unknown'))}",
                "name": resolution,
                "category": "对冲整合",
                "intensity": 9,
                "description": conflict.get("social_description", ""),
                "source": conflict.get("name", conflict.get("pattern", "")),
                "source_id": f"resolved_{source_id}",
                "planet_weight": conflict.get("total_weight", 10),
                "is_resolved": True,
                "conflict_details": {
                    "conflict_traits": conflict.get("conflict_traits", []),
                    "source_id": source_id,
                    "total_weight": conflict.get("total_weight", 10),
                }
            })
    
    for tag in tags:
        tag_source_id = tag.get("source_id", "")
        
        should_keep = True
        
        if tag_source_id in processed_source_ids:
            should_keep = False
        
        tag_source = tag.get("source", "")
        for processed_id in processed_source_ids:
            if processed_id and tag_source_id.startswith(processed_id):
                should_keep = False
                break
        
        if should_keep:
            resolved_tags.append(tag)
    
    logger.info(f"冲突解决完成，优化后共 {len(resolved_tags)} 个标签（使用规范Source ID匹配）")
    return resolved_tags


def generate_conflict_aware_personality(
    chart_data: Dict[str, Any],
    tag_matrix: Dict[str, Any]
) -> Dict[str, Any]:
    """
    主函数：生成考虑冲突对冲的性格画像（优化版）
    
    优化点：
    1. 行星权重体系 - 过滤低权重冲突
    2. 规范 Source ID 匹配 - 精确匹配，防止误删
    3. 加权分数制 - 动态阈值，更精准
    """
    logger.info("开始进行性格对冲逻辑处理（优化版）")
    
    planets = chart_data.get("planets", [])
    aspects = chart_data.get("aspects", [])
    big_three = tag_matrix.get("configuration", {}).get("big_three", {})
    
    distribution = tag_matrix.get("distribution", {})
    element_weighted_scores = distribution.get("element_weighted_score", {})
    quality_weighted_scores = distribution.get("quality_weighted_score", {})
    
    planetary_conflicts = detect_planetary_conflicts(aspects)
    sign_conflicts = detect_sign_conflicts(planets, big_three)
    element_quality_conflicts = detect_element_quality_conflicts(
        element_weighted_scores, quality_weighted_scores
    )
    
    all_conflicts = planetary_conflicts + sign_conflicts
    
    tags_matrix = tag_matrix.get("tags_matrix", {})
    
    all_tags = []
    for category, tags in tags_matrix.items():
        for tag in tags:
            all_tags.append(tag)
    
    resolved_tags = resolve_conflicts_in_tags(all_tags, all_conflicts)
    
    resolved_tags_matrix = {}
    for tag in resolved_tags:
        category = tag.get("category", "其他")
        if category not in resolved_tags_matrix:
            resolved_tags_matrix[category] = []
        resolved_tags_matrix[category].append(tag)
    
    for category in resolved_tags_matrix:
        resolved_tags_matrix[category].sort(
            key=lambda x: (x.get("planet_weight", 0), x.get("intensity", 0)), 
            reverse=True
        )
    
    result = {
        "conflicts_detected": {
            "planetary": planetary_conflicts,
            "sign": sign_conflicts,
            "element_quality": element_quality_conflicts,
            "total_count": len(all_conflicts),
        },
        "original_tags_matrix": tags_matrix,
        "resolved_tags_matrix": resolved_tags_matrix,
        "has_resolved_conflicts": len(all_conflicts) > 0,
        "resolution_summary": _generate_resolution_summary(all_conflicts),
        "_meta": {
            "min_conflict_weight": MIN_CONFLICT_WEIGHT,
            "element_conflict_threshold": ELEMENT_CONFLICT_THRESHOLD,
        }
    }
    
    logger.info(f"对冲处理完成，检测到 {len(all_conflicts)} 个冲突（优化版）")
    return result


def _generate_resolution_summary(conflicts: List[Dict[str, Any]]) -> str:
    """
    生成对冲解决的摘要描述
    """
    if not conflicts:
        return "性格特质较为一致，没有明显的内在冲突"
    
    resolutions = [c.get("resolution", "") for c in conflicts if c.get("resolution")]
    
    if len(resolutions) == 1:
        return f"性格中有明显的对冲特质，但已整合为：{resolutions[0]}"
    elif len(resolutions) <= 3:
        return f"性格中有多重对冲，整体表现为：{'、'.join(resolutions)}"
    else:
        return f"性格丰富复杂，包含多种对冲特质的整合：{'、'.join(resolutions[:3])} 等"
