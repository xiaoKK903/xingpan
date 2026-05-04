"""
前世故事 - 分析服务（主题判断、关系判断）
"""
import logging
from typing import Dict, Any, List, Tuple

from .config import (
    PAST_LIFE_THEME_CONFIG,
    PAST_LIFE_RELATIONSHIP_CONFIG,
    ELEMENT_SIGN_MAPPING,
    QUALITY_SIGN_MAPPING
)

logger = logging.getLogger(__name__)


def safe_get(data: Dict, keys: List[str], default: Any = "") -> Any:
    """安全获取嵌套字典值"""
    result = data
    for key in keys:
        if isinstance(result, dict):
            result = result.get(key)
        else:
            return default
        if result is None:
            return default
    return result


def extract_core_planets(chart_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    从星盘数据中提取核心行星信息
    
    返回: 包含核心行星列表，每个行星包含 name, sign, house, zodiac
    """
    planets = safe_get(chart_data, ["planets"], [])
    
    main_planet_names = ["太阳", "月亮", "水星", "金星", "火星", "木星", "土星", "天王星", "海王星", "冥王星"]
    
    core_planets = []
    for p in planets:
        planet_name = safe_get(p, ["name"])
        if planet_name in main_planet_names:
            zodiac = safe_get(p, ["zodiac"], {})
            core_planets.append({
                "name": planet_name,
                "sign": safe_get(zodiac, ["sign"]),
                "house": safe_get(p, ["house"]),
                "degree": safe_get(zodiac, ["degree"], 0),
                "element": _get_element_by_sign(safe_get(zodiac, ["sign"])),
                "quality": _get_quality_by_sign(safe_get(zodiac, ["sign"]))
            })
    
    return core_planets


def _get_element_by_sign(sign: str) -> str:
    """根据星座获取元素属性"""
    for element, signs in ELEMENT_SIGN_MAPPING.items():
        if sign in signs:
            return element
    return "未知"


def _get_quality_by_sign(sign: str) -> str:
    """根据星座获取模式属性"""
    for quality, signs in QUALITY_SIGN_MAPPING.items():
        if sign in signs:
            return quality
    return "未知"


def determine_past_life_theme(
    planets: List[Dict[str, Any]], 
    chart_data: Dict[str, Any]
) -> Tuple[str, Dict[str, Any]]:
    """
    根据星盘数据确定前世主题
    
    算法:
    1. 分析太阳、月亮、上升星座的元素和模式
    2. 根据行星位置匹配8种前世主题
    3. 选择得分最高的主题
    
    返回: (主题类型, 主题详情)
    """
    theme_scores = {key: 0 for key in PAST_LIFE_THEME_CONFIG.keys()}
    matched_planets_by_theme = {key: [] for key in PAST_LIFE_THEME_CONFIG.keys()}
    
    sun_sign = safe_get(chart_data, ["sun_sign", "sign"], "未知")
    moon_sign = safe_get(chart_data, ["moon_sign", "sign"], "未知")
    ascendant = safe_get(chart_data, ["ascendant", "sign"], "未知")
    
    sun_element = _get_element_by_sign(sun_sign)
    moon_element = _get_element_by_sign(moon_sign)
    
    for planet in planets:
        planet_name = planet.get("name", "")
        sign = planet.get("sign", "")
        house = planet.get("house", 0)
        
        for theme_key, theme_config in PAST_LIFE_THEME_CONFIG.items():
            core_planets = theme_config.get("core_planets", [])
            
            if planet_name in core_planets:
                score = 0
                match_reason = []
                
                if planet_name == "太阳":
                    score += 3
                    match_reason.append(f"{planet_name}是核心身份象征")
                elif planet_name == "月亮":
                    score += 2
                    match_reason.append(f"{planet_name}代表内在情感")
                elif planet_name == "水星":
                    score += 2
                    match_reason.append(f"{planet_name}代表思维表达")
                elif planet_name == "金星":
                    score += 2
                    match_reason.append(f"{planet_name}代表价值与美感")
                elif planet_name == "火星":
                    score += 3
                    match_reason.append(f"{planet_name}代表行动力与欲望")
                elif planet_name == "木星":
                    score += 2
                    match_reason.append(f"{planet_name}代表扩张与幸运")
                elif planet_name == "土星":
                    score += 2
                    match_reason.append(f"{planet_name}代表责任与结构")
                elif planet_name in ["天王星", "海王星", "冥王星"]:
                    score += 2
                    match_reason.append(f"{planet_name}代表深层转化力量")
                
                if house and 1 <= house <= 12:
                    if house == 1:
                        score += 1
                    elif house == 10:
                        score += 1
                    elif house == 7:
                        score += 1
                
                theme_scores[theme_key] += score
                matched_planets_by_theme[theme_key].append({
                    "planet": planet_name,
                    "sign": sign,
                    "house": house,
                    "reasons": match_reason
                })
    
    dominant_element = None
    element_counts = {"火象": 0, "土象": 0, "风象": 0, "水象": 0}
    for planet in planets:
        element = planet.get("element")
        if element in element_counts:
            element_counts[element] += 1
    
    if element_counts:
        dominant_element = max(element_counts, key=element_counts.get)
    
    if dominant_element == "火象":
        theme_scores["warrior"] += 2
        theme_scores["adventurer"] += 1
    elif dominant_element == "土象":
        theme_scores["merchant"] += 2
        theme_scores["royal"] += 1
    elif dominant_element == "风象":
        theme_scores["scholar"] += 2
        theme_scores["artist"] += 1
    elif dominant_element == "水象":
        theme_scores["healer"] += 2
        theme_scores["monk"] += 1
        theme_scores["artist"] += 1
    
    best_theme = max(theme_scores, key=lambda k: theme_scores[k])
    max_score = theme_scores[best_theme]
    
    if max_score == 0:
        best_theme = "adventurer"
    
    theme_config = PAST_LIFE_THEME_CONFIG.get(best_theme, PAST_LIFE_THEME_CONFIG["adventurer"])
    
    return best_theme, {
        "theme": best_theme,
        "theme_name": theme_config["name"],
        "theme_icon": theme_config["icon"],
        "theme_description": theme_config["description"],
        "keywords": theme_config["keywords"],
        "score": max_score,
        "all_scores": theme_scores,
        "matched_planets": matched_planets_by_theme.get(best_theme, []),
        "dominant_element": dominant_element,
        "sun_sign": sun_sign,
        "moon_sign": moon_sign,
        "ascendant": ascendant
    }


def determine_past_life_relationship(
    synastry_highlights: Dict[str, Any]
) -> Tuple[str, Dict[str, Any]]:
    """
    根据合盘相位确定前世关系类型
    
    算法:
    1. 分析合盘中的关键相位
    2. 根据相位类型匹配7种前世关系
    3. 选择得分最高的关系类型
    
    返回: (关系类型, 关系详情)
    """
    rel_scores = {key: 0 for key in PAST_LIFE_RELATIONSHIP_CONFIG.keys()}
    
    highlights = safe_get(synastry_highlights, ["highlights"], [])
    overall_theme = safe_get(synastry_highlights, ["overall_theme"], {})
    
    for rel_key, rel_config in PAST_LIFE_RELATIONSHIP_CONFIG.items():
        key_aspects = rel_config.get("key_aspects", [])
        
        for highlight in highlights:
            aspect_type = safe_get(highlight, ["aspect_type"], "")
            planet_a = safe_get(highlight, ["planet_a"], "")
            planet_b = safe_get(highlight, ["planet_b"], "")
            
            for (core_a, core_b) in key_aspects:
                if (planet_a == core_a and planet_b == core_b) or \
                   (planet_a == core_b and planet_b == core_a):
                    if aspect_type in ["合相", "拱相", "六合"]:
                        rel_scores[rel_key] += 3
                    elif aspect_type in ["刑相", "冲相"]:
                        rel_scores[rel_key] += 1
    
    overall_type = safe_get(overall_theme, ["type"], "")
    if overall_type == "romance":
        rel_scores["lovers"] += 2
    elif overall_type == "friendship":
        rel_scores["soulmate"] += 1
        rel_scores["comrade"] += 1
    elif overall_type == "family":
        rel_scores["family"] += 2
    elif overall_type == "tension":
        rel_scores["rival"] += 2
        rel_scores["lovers"] += 1
    
    best_rel = max(rel_scores, key=lambda k: rel_scores[k])
    max_score = rel_scores[best_rel]
    
    if max_score == 0:
        best_rel = "stranger"
    
    rel_config = PAST_LIFE_RELATIONSHIP_CONFIG.get(best_rel, PAST_LIFE_RELATIONSHIP_CONFIG["stranger"])
    
    return best_rel, {
        "relationship_type": best_rel,
        "relationship_name": rel_config["name"],
        "relationship_icon": rel_config["icon"],
        "relationship_description": rel_config["description"],
        "keywords": rel_config["keywords"],
        "score": max_score,
        "all_scores": rel_scores,
        "overall_theme": overall_theme
    }
