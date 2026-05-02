from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
import logging
import math
import statistics

from app.services.profile_extractor_service import (
    extract_tag_matrix,
    get_planet_weight,
    PLANET_WEIGHT_MAP
)

logger = logging.getLogger(__name__)


VALID_STAT_NAMES = {
    "health", "max_health", "attack", "defense", 
    "mana", "max_mana", "speed", "critical_rate", 
    "critical_damage", "combat_power"
}


ASPECT_TYPES = {
    "合相": "conjunction",
    "六分相": "sextile",
    "三分相": "trine",
    "四分相": "square",
    "对分相": "opposition",
}


BASE_STATS = {
    "health": 100,
    "attack": 10,
    "defense": 5,
    "mana": 50,
    "speed": 50,
    "critical_rate": 5.0,
    "critical_damage": 150.0,
}


PLANET_STAT_MAPPING = {
    "火星": {"stat": "attack", "base_bonus": 5, "description": "攻击性、爆发力"},
    "木星": {"stat": "health", "base_bonus": 20, "description": "生命力、扩展性"},
    "土星": {"stat": "defense", "base_bonus": 3, "description": "防御力、稳定性"},
    "月亮": {"stat": "mana", "base_bonus": 10, "description": "情感能量、直觉"},
    "水星": {"stat": "speed", "base_bonus": 3, "description": "思维敏捷、反应速度"},
    "太阳": {"stat": "critical_rate", "base_bonus": 1.0, "description": "核心能量、爆发力"},
    "金星": {"stat": "critical_damage", "base_bonus": 5.0, "description": "魅力、美学加成"},
    "天王星": {"stat": "critical_rate", "base_bonus": 2.0, "description": "突发变化、惊喜"},
    "海王星": {"stat": "mana", "base_bonus": 15, "description": "灵感、灵性能量"},
    "冥王星": {"stat": "critical_damage", "base_bonus": 10.0, "description": "深度转化、极致力量"},
}


SIGN_HOUSE_MULTIPLIERS = {
    "庙旺": 1.5,
    "耀升": 1.3,
    "得地": 1.1,
    "中性": 1.0,
    "落陷": 0.7,
}


RULING_PLANETS_MAP = {
    "白羊座": ["火星"],
    "金牛座": ["金星"],
    "双子座": ["水星"],
    "巨蟹座": ["月亮"],
    "狮子座": ["太阳"],
    "处女座": ["水星"],
    "天秤座": ["金星"],
    "天蝎座": ["冥王星", "火星"],
    "射手座": ["木星"],
    "摩羯座": ["土星"],
    "水瓶座": ["天王星", "土星"],
    "双鱼座": ["海王星", "木星"],
}


EXALTATION_PLANETS = {
    "白羊座": "太阳",
    "金牛座": "月亮",
    "双子座": "北交点",
    "巨蟹座": "木星",
    "狮子座": "冥王星",
    "处女座": "水星",
    "天秤座": "土星",
    "天蝎座": "天王星",
    "射手座": "南交点",
    "摩羯座": "火星",
    "水瓶座": "水星",
    "双鱼座": "金星",
}


ELEMENT_PASSIVES = {
    "火": {
        "name": "烈焰之心",
        "description": "火象能量主导，攻击附带灼烧效果，每次攻击额外造成攻击力10%的伤害",
        "effect_type": "attack_burn",
        "effect_value": 0.1,
        "stat_bonus": {
            "attack": {"value": 5, "type": "fixed"},
            "critical_rate": {"value": 2.0, "type": "fixed"}
        },
    },
    "土": {
        "name": "大地守护",
        "description": "土象能量主导，每次受到攻击时，有30%概率减免50%伤害",
        "effect_type": "damage_reduction",
        "effect_value": 0.5,
        "stat_bonus": {
            "defense": {"value": 5, "type": "fixed"},
            "health": {"value": 30, "type": "fixed"}
        },
    },
    "风": {
        "name": "疾风灵思",
        "description": "风象能量主导，每回合开始时有20%概率获得额外行动点",
        "effect_type": "extra_action",
        "effect_value": 0.2,
        "stat_bonus": {
            "speed": {"value": 10, "type": "fixed"},
            "mana": {"value": 15, "type": "fixed"}
        },
    },
    "水": {
        "name": "深海治愈",
        "description": "水象能量主导，每回合恢复最大蓝量的8%和最大血量的5%",
        "effect_type": "healing",
        "effect_value": 0.08,
        "stat_bonus": {
            "mana": {"value": 20, "type": "fixed"},
            "health": {"value": 15, "type": "fixed"}
        },
    },
}


QUALITY_PASSIVES = {
    "开创": {
        "name": "先锋意志",
        "description": "开创特质主导，战斗开始时首次攻击伤害提升50%",
        "effect_type": "first_strike",
        "effect_value": 1.5,
    },
    "固定": {
        "name": "磐石坚韧",
        "description": "固定特质主导，当生命值低于30%时，防御力提升100%",
        "effect_type": "defense_boost",
        "effect_value": 2.0,
    },
    "变动": {
        "name": "适应之术",
        "description": "变动特质主导，每回合结束时有25%概率清除一个负面状态",
        "effect_type": "status_clear",
        "effect_value": 0.25,
    },
}


APPEARANCE_TEMPLATES = {
    "太阳": {
        "白羊座": "拥有明亮锐利的眼神，步伐坚定有力，散发着自信的光芒",
        "金牛座": "气质沉稳内敛，五官端正精致，给人一种可靠的感觉",
        "双子座": "眼神灵动多变，表情丰富，总是给人一种聪明伶俐的印象",
        "巨蟹座": "眼神温柔慈祥，面相圆润，给人一种亲切温暖的感觉",
        "狮子座": "气场强大，眼神威严，举止间流露出王者般的自信",
        "处女座": "气质清新干净，五官精致，给人一种一丝不苟的感觉",
        "天秤座": "气质优雅迷人，五官协调，举止间散发着和谐之美",
        "天蝎座": "眼神深邃神秘，气质冷峻，给人一种难以捉摸的感觉",
        "射手座": "眼神明亮开朗，气质洒脱，散发着自由奔放的气息",
        "摩羯座": "气质稳重成熟，眼神坚毅，给人一种值得信赖的感觉",
        "水瓶座": "气质独特前卫，眼神中带着智慧，给人一种与众不同的感觉",
        "双鱼座": "眼神梦幻迷离，气质温柔，给人一种诗意浪漫的感觉",
    },
    "月亮": {
        "白羊座": "情绪直接流露，表情变化丰富，眼神中带着孩童般的纯真",
        "金牛座": "表情温和稳重，眼神中带着满足，给人一种安详的感觉",
        "双子座": "表情活泼多变，眼神灵动，总是带着好奇的光芒",
        "巨蟹座": "眼神柔软敏感，表情含蓄，给人一种需要保护的感觉",
        "狮子座": "表情自信张扬，眼神明亮，带着戏剧性的魅力",
        "处女座": "表情细腻内敛，眼神专注，带着分析的光芒",
        "天秤座": "表情优雅得体，眼神柔和，带着社交的智慧",
        "天蝎座": "表情深沉内敛，眼神锐利，带着神秘的洞察力",
        "射手座": "表情开朗乐观，眼神明亮，带着对远方的向往",
        "摩羯座": "表情克制严肃，眼神坚定，带着责任感的光芒",
        "水瓶座": "表情冷静客观，眼神深邃，带着独特的见解",
        "双鱼座": "表情梦幻温柔，眼神朦胧，带着诗意的浪漫",
    },
    "上升": {
        "白羊座": "身材挺拔，动作敏捷，给人一种充满活力的第一印象",
        "金牛座": "身材匀称，气质沉稳，给人一种可靠踏实的感觉",
        "双子座": "身材轻盈，动作灵活，给人一种聪明伶俐的印象",
        "巨蟹座": "身材圆润，气质温柔，给人一种亲切温暖的感觉",
        "狮子座": "身材挺拔，气宇轩昂，给人一种自信威严的第一印象",
        "处女座": "身材苗条，气质清新，给人一种干净利落的感觉",
        "天秤座": "身材匀称，气质优雅，给人一种和谐美好的印象",
        "天蝎座": "身材匀称，气质神秘，给人一种深邃内敛的感觉",
        "射手座": "身材高挑，气质洒脱，给人一种自由奔放的印象",
        "摩羯座": "身材结实，气质稳重，给人一种成熟可靠的感觉",
        "水瓶座": "身材独特，气质前卫，给人一种与众不同的印象",
        "双鱼座": "身材柔和，气质浪漫，给人一种诗意梦幻的感觉",
    },
}


def _get_aspect_key(planet1: str, planet2: str, aspect_type: str) -> str:
    """
    统一相位key生成：按字母顺序排序行星，生成标准化字符串key
    """
    sorted_planets = sorted([planet1, planet2])
    return f"{sorted_planets[0]}_{sorted_planets[1]}_{aspect_type}"


ASPECT_APPEARANCE_EFFECTS = {
    _get_aspect_key("太阳", "海王星", "合相"): "眼神朦胧梦幻，气质神秘，给人一种不真实的美感",
    _get_aspect_key("月亮", "海王星", "合相"): "气质温柔诗意，眼神迷离，散发着梦幻般的魅力",
    _get_aspect_key("金星", "海王星", "合相"): "五官精致柔美，气质浪漫，带着艺术的美感",
    _get_aspect_key("火星", "冥王星", "合相"): "眼神锐利深邃，气质强烈，散发着神秘的力量感",
    _get_aspect_key("太阳", "冥王星", "合相"): "气场强大，眼神深邃，给人一种难以忽视的存在感",
    _get_aspect_key("月亮", "冥王星", "合相"): "眼神深邃内敛，气质神秘，情感深沉而强烈",
    _get_aspect_key("太阳", "天王星", "合相"): "气质独特前卫，眼神明亮，带着创新的光芒",
    _get_aspect_key("金星", "天王星", "合相"): "气质与众不同，审美独特，散发着叛逆的魅力",
    _get_aspect_key("太阳", "木星", "合相"): "气质乐观开朗，眼神明亮，散发着自信的光芒",
    _get_aspect_key("金星", "木星", "合相"): "气质优雅大方，五官舒展，散发着社交的魅力",
    _get_aspect_key("太阳", "土星", "合相"): "气质成熟稳重，眼神坚毅，散发着可靠的感觉",
    _get_aspect_key("月亮", "土星", "合相"): "气质内敛克制，眼神深沉，散发着责任感的光芒",
}


@dataclass
class CharacterStats:
    health: int = 100
    max_health: int = 100
    attack: int = 10
    defense: int = 5
    mana: int = 50
    max_mana: int = 50
    speed: int = 50
    critical_rate: float = 5.0
    critical_damage: float = 150.0
    combat_power: int = 0


@dataclass
class CharacterPassive:
    name: str
    description: str
    effect_type: str
    effect_value: float
    stat_bonus: Dict[str, Any] = field(default_factory=dict)
    source: str = ""


@dataclass
class CharacterAppearance:
    overall_description: str = ""
    facial_features: str = ""
    body_type: str = ""
    aura: str = ""
    style_suggestions: List[str] = field(default_factory=list)
    key_details: List[str] = field(default_factory=list)


@dataclass
class GameCharacter:
    name: str = ""
    stats: CharacterStats = field(default_factory=CharacterStats)
    passives: List[CharacterPassive] = field(default_factory=list)
    appearance: CharacterAppearance = field(default_factory=CharacterAppearance)
    astro_source: Dict[str, Any] = field(default_factory=dict)


def validate_stat_name(stat_name: str, context: str = "") -> bool:
    """
    校验属性名称是否在白名单中
    """
    if stat_name not in VALID_STAT_NAMES:
        logger.warning(f"[属性校验警告] 发现非法属性字段: '{stat_name}'，上下文: {context}")
        return False
    return True


def get_planet_strength(planet: Dict[str, Any], chart_data: Dict[str, Any]) -> float:
    """
    计算行星的力量值（0-100）
    考虑因素：
    1. 宫位（第1、10宫较强，第6、12宫较弱）
    2. 庙旺落陷
    3. 相位（与其他行星的关系）
    4. 逆行
    """
    strength = 50.0
    
    house = planet.get("house", 6)
    if not isinstance(house, int) or house < 1 or house > 12:
        house = 6
    
    house_multipliers = {
        1: 1.4, 10: 1.3, 7: 1.2, 4: 1.15,
        2: 1.1, 5: 1.1, 8: 1.05, 9: 1.05,
        3: 1.0, 11: 1.0, 6: 0.85, 12: 0.75
    }
    strength *= house_multipliers.get(house, 1.0)
    
    zodiac_data = planet.get("zodiac", {})
    if not isinstance(zodiac_data, dict):
        zodiac_data = {}
    
    sign = zodiac_data.get("sign", "")
    planet_name = planet.get("name", "")
    
    if sign and planet_name:
        ruling_planets = RULING_PLANETS_MAP.get(sign, [])
        if planet_name in ruling_planets:
            strength *= SIGN_HOUSE_MULTIPLIERS["庙旺"]
        elif EXALTATION_PLANETS.get(sign) == planet_name:
            strength *= SIGN_HOUSE_MULTIPLIERS["耀升"]
    
    aspects = chart_data.get("aspects", [])
    if not isinstance(aspects, list):
        aspects = []
    
    for aspect in aspects:
        if not isinstance(aspect, dict):
            continue
        
        p1 = aspect.get("planet1", "")
        p2 = aspect.get("planet2", "")
        aspect_type = aspect.get("aspect", "")
        
        if not (p1 and p2 and aspect_type):
            continue
        
        if planet_name in [p1, p2]:
            orb = aspect.get("orb", 8)
            if not isinstance(orb, (int, float)):
                orb = 8
            orb = min(max(orb, 0), 8)
            
            if aspect_type in ["三分相", "六分相"]:
                aspect_boost = (8 - orb) / 8 * 10
                strength += aspect_boost
            elif aspect_type in ["四分相", "对分相"]:
                aspect_reduce = (8 - orb) / 8 * 5
                strength -= aspect_reduce
    
    is_retrograde = planet.get("is_retrograde", False)
    if isinstance(is_retrograde, bool) and is_retrograde:
        strength *= 0.9
    
    return min(100.0, max(0.0, strength))


def calculate_base_stats(chart_data: Dict[str, Any]) -> CharacterStats:
    """
    根据星盘计算基础属性
    """
    stats = CharacterStats(**BASE_STATS)
    
    planets = chart_data.get("planets", [])
    if not isinstance(planets, list):
        planets = []
    
    for planet in planets:
        if not isinstance(planet, dict):
            continue
        
        planet_name = planet.get("name", "")
        
        if planet_name in PLANET_STAT_MAPPING:
            stat_info = PLANET_STAT_MAPPING[planet_name]
            strength = get_planet_strength(planet, chart_data)
            
            strength_factor = strength / 50.0
            bonus = stat_info["base_bonus"] * strength_factor
            
            stat_name = stat_info["stat"]
            if not validate_stat_name(stat_name, f"行星{planet_name}属性映射"):
                continue
            
            if not hasattr(stats, stat_name):
                continue
            
            current_value = getattr(stats, stat_name)
            
            if stat_name in ["critical_rate", "critical_damage"]:
                new_value = current_value + float(bonus)
            else:
                new_value = current_value + int(bonus)
            
            setattr(stats, stat_name, new_value)
    
    stats.max_health = stats.health
    stats.max_mana = stats.mana
    
    stats.combat_power = calculate_combat_power(stats)
    
    return stats


def calculate_combat_power(stats: CharacterStats) -> int:
    """
    计算综合战力
    公式：战力 = 生命值×2 + 攻击×5 + 防御×3 + 蓝量×1 + 
              暴击率×10 + (暴击伤害-100)×3 + 速度×2
    """
    power = (
        stats.max_health * 2 +
        stats.attack * 5 +
        stats.defense * 3 +
        stats.max_mana * 1 +
        stats.critical_rate * 10 +
        (stats.critical_damage - 100) * 3 +
        stats.speed * 2
    )
    return int(power)


def calculate_element_passives(chart_data: Dict[str, Any], tag_matrix: Dict[str, Any]) -> List[CharacterPassive]:
    """
    根据四元素占比计算天赋被动
    """
    passives = []
    
    if not isinstance(tag_matrix, dict):
        tag_matrix = {}
    
    distribution = tag_matrix.get("distribution", {})
    if not isinstance(distribution, dict):
        distribution = {}
    
    element_scores = distribution.get("element_weighted_score", {})
    if not isinstance(element_scores, dict):
        element_scores = {}
    
    element_percentages = distribution.get("percentage", {})
    if not isinstance(element_percentages, dict):
        element_percentages = {}
    
    total_score = sum(element_scores.values()) if element_scores else 0
    
    if total_score > 0:
        elements = ["火", "土", "风", "水"]
        sorted_elements = sorted(
            elements,
            key=lambda e: element_scores.get(e, 0),
            reverse=True
        )
        
        dominant_element = sorted_elements[0]
        dominant_percentage = element_percentages.get(dominant_element, 25)
        
        if dominant_percentage >= 35:
            passive_info = ELEMENT_PASSIVES.get(dominant_element)
            if passive_info:
                passive = CharacterPassive(
                    name=passive_info["name"],
                    description=passive_info["description"],
                    effect_type=passive_info["effect_type"],
                    effect_value=passive_info["effect_value"],
                    stat_bonus=passive_info.get("stat_bonus", {}),
                    source=f"{dominant_element}象元素主导 ({dominant_percentage}%)"
                )
                passives.append(passive)
        
        for i in range(1, len(sorted_elements)):
            elem = sorted_elements[i]
            elem_percentage = element_percentages.get(elem, 25)
            if elem_percentage >= 30:
                passive_info = ELEMENT_PASSIVES.get(elem)
                if passive_info:
                    scaled_stat_bonus = {}
                    for stat_name, bonus_data in passive_info.get("stat_bonus", {}).items():
                        if isinstance(bonus_data, dict):
                            scaled_stat_bonus[stat_name] = {
                                "value": bonus_data["value"] * 0.6,
                                "type": bonus_data["type"]
                            }
                        else:
                            scaled_stat_bonus[stat_name] = bonus_data * 0.6
                    
                    passive = CharacterPassive(
                        name=passive_info["name"],
                        description=passive_info["description"],
                        effect_type=passive_info["effect_type"],
                        effect_value=passive_info["effect_value"] * 0.6,
                        stat_bonus=scaled_stat_bonus,
                        source=f"{elem}象元素次要 ({elem_percentage}%)"
                    )
                    passives.append(passive)
    
    dominant_quality = distribution.get("dominant_quality", "")
    if dominant_quality and dominant_quality in QUALITY_PASSIVES:
        quality_info = QUALITY_PASSIVES[dominant_quality]
        
        passive = CharacterPassive(
            name=quality_info["name"],
            description=quality_info["description"],
            effect_type=quality_info["effect_type"],
            effect_value=quality_info["effect_value"],
            source=f"{dominant_quality}特质主导"
        )
        passives.append(passive)
    
    return passives


def generate_appearance(chart_data: Dict[str, Any], tag_matrix: Dict[str, Any]) -> CharacterAppearance:
    """
    根据星盘生成角色外貌描述（优化版：去重、强化逻辑）
    """
    appearance = CharacterAppearance()
    
    if not isinstance(tag_matrix, dict):
        tag_matrix = {}
    
    config = tag_matrix.get("configuration", {})
    if not isinstance(config, dict):
        config = {}
    
    big_three = config.get("big_three", {})
    if not isinstance(big_three, dict):
        big_three = {}
    
    stelliums = config.get("stelliums", [])
    if not isinstance(stelliums, list):
        stelliums = []
    
    special_patterns = config.get("special_patterns", [])
    if not isinstance(special_patterns, list):
        special_patterns = []
    
    distribution = tag_matrix.get("distribution", {})
    if not isinstance(distribution, dict):
        distribution = {}
    
    dominant_element = distribution.get("dominant_element", "")
    
    sun_data = big_three.get("sun", {}) if isinstance(big_three.get("sun"), dict) else {}
    moon_data = big_three.get("moon", {}) if isinstance(big_three.get("moon"), dict) else {}
    asc_data = big_three.get("ascendant", {}) if isinstance(big_three.get("ascendant"), dict) else {}
    
    sun_sign = sun_data.get("sign", "") if isinstance(sun_data, dict) else ""
    moon_sign = moon_data.get("sign", "") if isinstance(moon_data, dict) else ""
    asc_sign = asc_data.get("sign", "") if isinstance(asc_data, dict) else ""
    
    descriptions_set = set()
    descriptions = []
    
    def add_description(desc: str, priority: int = 1):
        if not desc or not isinstance(desc, str):
            return
        desc_stripped = desc.strip()
        if desc_stripped and desc_stripped not in descriptions_set:
            descriptions_set.add(desc_stripped)
            descriptions.append({"text": desc_stripped, "priority": priority})
    
    if sun_sign and sun_sign in APPEARANCE_TEMPLATES["太阳"]:
        add_description(APPEARANCE_TEMPLATES["太阳"][sun_sign], priority=3)
    
    if moon_sign and moon_sign in APPEARANCE_TEMPLATES["月亮"]:
        add_description(APPEARANCE_TEMPLATES["月亮"][moon_sign], priority=2)
    
    if asc_sign and asc_sign in APPEARANCE_TEMPLATES["上升"]:
        add_description(APPEARANCE_TEMPLATES["上升"][asc_sign], priority=3)
    
    aspects = chart_data.get("aspects", []) if isinstance(chart_data.get("aspects"), list) else []
    for aspect in aspects:
        if not isinstance(aspect, dict):
            continue
        
        p1 = aspect.get("planet1", "")
        p2 = aspect.get("planet2", "")
        aspect_type = aspect.get("aspect", "")
        
        if not (p1 and p2 and aspect_type):
            continue
        
        aspect_key = _get_aspect_key(p1, p2, aspect_type)
        
        if aspect_key in ASPECT_APPEARANCE_EFFECTS:
            add_description(ASPECT_APPEARANCE_EFFECTS[aspect_key], priority=4)
    
    descriptions.sort(key=lambda x: x["priority"], reverse=True)
    sorted_descriptions = [d["text"] for d in descriptions]
    
    appearance.overall_description = "。".join(sorted_descriptions) if sorted_descriptions else "独特的气质，让人印象深刻"
    
    facial_parts = []
    if sun_sign:
        facial_parts.append(f"眼神带着{sun_sign}特有的特质")
    if moon_sign:
        facial_parts.append(f"表情流露{moon_sign}的情感特质")
    appearance.facial_features = "，".join(facial_parts) if facial_parts else "五官端正，气质独特"
    
    if asc_sign and asc_sign in APPEARANCE_TEMPLATES["上升"]:
        appearance.body_type = APPEARANCE_TEMPLATES["上升"][asc_sign]
    else:
        appearance.body_type = "身材适中"
    
    aura_descriptions_set = set()
    aura_descriptions = []
    
    def add_aura(desc: str):
        if desc and desc not in aura_descriptions_set:
            aura_descriptions_set.add(desc)
            aura_descriptions.append(desc)
    
    for stellium in stelliums:
        if not isinstance(stellium, dict):
            continue
        sign = stellium.get("sign", "")
        if sign:
            add_aura(f"带有{sign}的能量气息")
    
    if dominant_element:
        element_aura = {
            "火": "散发着炽热的能量",
            "土": "散发着沉稳的气息",
            "风": "散发着灵动的气息",
            "水": "散发着柔和的气息",
        }
        if dominant_element in element_aura:
            add_aura(element_aura[dominant_element])
    
    appearance.aura = "，".join(aura_descriptions) if aura_descriptions else "气质独特，引人注意"
    
    style_suggestions = []
    if sun_sign in ["白羊座", "狮子座", "射手座"]:
        style_suggestions.append("适合明亮、大胆的配色")
    elif sun_sign in ["金牛座", "处女座", "摩羯座"]:
        style_suggestions.append("适合大地色系、质感良好的材质")
    elif sun_sign in ["双子座", "天秤座", "水瓶座"]:
        style_suggestions.append("适合时尚、前卫的款式")
    elif sun_sign in ["巨蟹座", "天蝎座", "双鱼座"]:
        style_suggestions.append("适合柔和、浪漫的风格")
    
    appearance.style_suggestions = style_suggestions
    
    key_details_set = set()
    key_details = []
    
    def add_key_detail(detail: str):
        if detail and detail not in key_details_set:
            key_details_set.add(detail)
            key_details.append(detail)
    
    for stellium in stelliums:
        if not isinstance(stellium, dict):
            continue
        sign = stellium.get("sign", "")
        planets_list = stellium.get("planets", [])
        if sign and planets_list and isinstance(planets_list, list):
            planets_str = "、".join(str(p) for p in planets_list)
            add_key_detail(f"群星{sign}：{planets_str}")
    
    for pattern in special_patterns:
        if not isinstance(pattern, dict):
            continue
        pattern_type = pattern.get("type", "")
        pattern_planets = pattern.get("planets", [])
        if pattern_type and pattern_planets and isinstance(pattern_planets, list):
            planets_str = "、".join(str(p) for p in pattern_planets)
            add_key_detail(f"{pattern_type}格局：{planets_str}")
    
    appearance.key_details = key_details
    
    return appearance


def apply_passive_bonuses(stats: CharacterStats, passives: List[CharacterPassive]) -> CharacterStats:
    """
    应用被动技能的属性加成（支持百分比和固定值）
    """
    if not isinstance(passives, list):
        passives = []
    
    for passive in passives:
        if not isinstance(passive, CharacterPassive):
            continue
        
        stat_bonus = passive.stat_bonus
        if not stat_bonus or not isinstance(stat_bonus, dict):
            continue
        
        for stat_name, bonus_data in stat_bonus.items():
            if not validate_stat_name(stat_name, f"被动技能 '{passive.name}' 加成"):
                continue
            
            if not hasattr(stats, stat_name):
                continue
            
            current_value = getattr(stats, stat_name)
            
            if isinstance(bonus_data, dict):
                bonus_value = bonus_data.get("value", 0)
                bonus_type = bonus_data.get("type", "fixed")
                
                if bonus_type == "percentage":
                    new_value = current_value * (1 + bonus_value / 100)
                else:
                    if isinstance(current_value, float):
                        new_value = current_value + float(bonus_value)
                    else:
                        new_value = current_value + int(bonus_value)
            else:
                if isinstance(current_value, float):
                    new_value = current_value + float(bonus_data)
                else:
                    new_value = current_value + int(bonus_data)
            
            setattr(stats, stat_name, new_value)
    
    stats.max_health = stats.health
    stats.max_mana = stats.mana
    stats.combat_power = calculate_combat_power(stats)
    
    return stats


def calculate_stats_stddev(all_stats_list: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    计算所有属性的标准差
    """
    if not all_stats_list or len(all_stats_list) < 2:
        return {}
    
    stat_names = ["health", "attack", "defense", "mana", "speed", "critical_rate", "critical_damage", "combat_power"]
    stddev_result = {}
    
    for stat_name in stat_names:
        values = []
        for stats in all_stats_list:
            if isinstance(stats, dict) and stat_name in stats:
                values.append(float(stats[stat_name]))
        
        if len(values) >= 2:
            try:
                mean = sum(values) / len(values)
                variance = sum((x - mean) ** 2 for x in values) / len(values)
                stddev = math.sqrt(variance)
                cv = stddev / mean if mean != 0 else 0
                
                stddev_result[stat_name] = {
                    "mean": round(mean, 2),
                    "stddev": round(stddev, 2),
                    "cv": round(cv * 100, 2),
                }
            except (ZeroDivisionError, ValueError) as e:
                logger.warning(f"计算属性标准差时出错: {stat_name}, 错误: {e}")
    
    return stddev_result


def check_stat_balance(all_stats_list: List[Dict[str, Any]], cv_threshold: float = 30.0) -> Dict[str, Any]:
    """
    检查属性平衡性
    cv_threshold: 变异系数阈值（百分比），超过此值视为不平衡
    """
    stddev_result = calculate_stats_stddev(all_stats_list)
    
    balance_report = {
        "is_balanced": True,
        "unbalanced_stats": [],
        "details": stddev_result
    }
    
    for stat_name, data in stddev_result.items():
        if data.get("cv", 0) > cv_threshold:
            balance_report["is_balanced"] = False
            balance_report["unbalanced_stats"].append({
                "stat": stat_name,
                "cv": data["cv"],
                "threshold": cv_threshold
            })
    
    return balance_report


async def generate_game_character(
    chart_data: Dict[str, Any],
    name: str = "神秘旅人"
) -> Dict[str, Any]:
    """
    主函数：根据星盘生成游戏角色
    """
    logger.info(f"开始为 {name} 生成游戏角色")
    
    if not chart_data or not isinstance(chart_data, dict):
        logger.error("星盘数据为空或格式无效")
        return {
            "success": False,
            "error": "星盘数据为空或格式无效",
            "error_type": "invalid_input",
        }
    
    tag_matrix = extract_tag_matrix(chart_data)
    
    base_stats = calculate_base_stats(chart_data)
    
    passives = calculate_element_passives(chart_data, tag_matrix)
    
    final_stats = apply_passive_bonuses(base_stats, passives)
    
    appearance = generate_appearance(chart_data, tag_matrix)
    
    config = tag_matrix.get("configuration", {}) if isinstance(tag_matrix.get("configuration"), dict) else {}
    big_three = config.get("big_three", {}) if isinstance(config.get("big_three"), dict) else {}
    stelliums = config.get("stelliums", []) if isinstance(config.get("stelliums"), list) else []
    distribution = tag_matrix.get("distribution", {}) if isinstance(tag_matrix.get("distribution"), dict) else {}
    
    character = GameCharacter(
        name=name,
        stats=final_stats,
        passives=passives,
        appearance=appearance,
        astro_source={
            "big_three": big_three,
            "stelliums": stelliums,
            "element_distribution": distribution.get("elements", {}) if isinstance(distribution.get("elements"), dict) else {},
            "element_percentage": distribution.get("percentage", {}) if isinstance(distribution.get("percentage"), dict) else {},
            "dominant_element": distribution.get("dominant_element", ""),
            "dominant_quality": distribution.get("dominant_quality", ""),
        }
    )
    
    result = {
        "success": True,
        "character": {
            "name": character.name,
            "stats": {
                "health": character.stats.health,
                "max_health": character.stats.max_health,
                "attack": character.stats.attack,
                "defense": character.stats.defense,
                "mana": character.stats.mana,
                "max_mana": character.stats.max_mana,
                "speed": character.stats.speed,
                "critical_rate": round(character.stats.critical_rate, 1),
                "critical_damage": round(character.stats.critical_damage, 1),
                "combat_power": character.stats.combat_power,
            },
            "passives": [
                {
                    "name": p.name,
                    "description": p.description,
                    "effect_type": p.effect_type,
                    "effect_value": p.effect_value,
                    "stat_bonus": p.stat_bonus,
                    "source": p.source,
                }
                for p in character.passives
            ],
            "appearance": {
                "overall_description": character.appearance.overall_description,
                "facial_features": character.appearance.facial_features,
                "body_type": character.appearance.body_type,
                "aura": character.appearance.aura,
                "style_suggestions": character.appearance.style_suggestions,
                "key_details": character.appearance.key_details,
            },
            "astro_source": character.astro_source,
        },
    }
    
    logger.info(f"游戏角色生成成功: {name}，战力: {final_stats.combat_power}")
    return result
