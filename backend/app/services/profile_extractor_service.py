from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PlanetWeight(Enum):
    CORE = 10
    PERSONAL = 7
    SOCIAL = 4
    OUTER = 2


PLANET_WEIGHT_MAP: Dict[str, PlanetWeight] = {
    "太阳": PlanetWeight.CORE,
    "月亮": PlanetWeight.CORE,
    "上升": PlanetWeight.CORE,
    "水星": PlanetWeight.PERSONAL,
    "金星": PlanetWeight.PERSONAL,
    "火星": PlanetWeight.PERSONAL,
    "木星": PlanetWeight.SOCIAL,
    "土星": PlanetWeight.SOCIAL,
    "天王星": PlanetWeight.OUTER,
    "海王星": PlanetWeight.OUTER,
    "冥王星": PlanetWeight.OUTER,
}


class SourceIdType(Enum):
    SUN = "sun"
    MOON = "moon"
    ASCENDANT = "ascendant"
    MERCURY = "mercury"
    VENUS = "venus"
    MARS = "mars"
    JUPITER = "jupiter"
    SATURN = "saturn"
    URANUS = "uranus"
    NEPTUNE = "neptune"
    PLUTO = "pluto"
    STELLIUM = "stellium"
    PATTERN = "pattern"
    ASPECT = "aspect"
    VOID_MOON = "void_moon"
    ELEMENT = "element"


SOURCE_ID_MAP: Dict[str, str] = {
    "太阳": SourceIdType.SUN.value,
    "月亮": SourceIdType.MOON.value,
    "上升": SourceIdType.ASCENDANT.value,
    "水星": SourceIdType.MERCURY.value,
    "金星": SourceIdType.VENUS.value,
    "火星": SourceIdType.MARS.value,
    "木星": SourceIdType.JUPITER.value,
    "土星": SourceIdType.SATURN.value,
    "天王星": SourceIdType.URANUS.value,
    "海王星": SourceIdType.NEPTUNE.value,
    "冥王星": SourceIdType.PLUTO.value,
}


@dataclass
class PersonalityTag:
    id: str
    name: str
    category: str
    intensity: int
    description: str
    source: str
    source_id: str
    planet_weight: int


@dataclass
class ChartConfiguration:
    stelliums: List[Dict[str, Any]] = field(default_factory=list)
    key_aspects: List[Dict[str, Any]] = field(default_factory=list)
    void_of_course: bool = False
    void_of_course_moon: bool = False
    big_three: Dict[str, Any] = field(default_factory=dict)
    element_distribution: Dict[str, int] = field(default_factory=dict)
    element_weighted_score: Dict[str, float] = field(default_factory=dict)
    quality_distribution: Dict[str, int] = field(default_factory=dict)
    quality_weighted_score: Dict[str, float] = field(default_factory=dict)
    special_patterns: List[Dict[str, Any]] = field(default_factory=list)


PERSONALITY_TAGS = {
    "aries": {
        "traits": ["热情直接", "行动力强", "冲动急躁", "勇敢先锋"],
        "keywords": ["火象", "开创", "勇敢", "直率"],
    },
    "taurus": {
        "traits": ["稳重踏实", "感官敏锐", "固执己见", "追求舒适"],
        "keywords": ["土象", "固定", "务实", "耐心"],
    },
    "gemini": {
        "traits": ["思维敏捷", "善于沟通", "三心二意", "好奇心强"],
        "keywords": ["风象", "变动", "机智", "多变"],
    },
    "cancer": {
        "traits": ["情感细腻", "保护欲强", "情绪波动", "重视家庭"],
        "keywords": ["水象", "开创", "敏感", "关怀"],
    },
    "leo": {
        "traits": ["自信大方", "渴望关注", "慷慨热情", "自尊心强"],
        "keywords": ["火象", "固定", "光芒", "创意"],
    },
    "virgo": {
        "traits": ["注重细节", "分析能力强", "追求完美", "服务意识"],
        "keywords": ["土象", "变动", "细致", "务实"],
    },
    "libra": {
        "traits": ["追求和谐", "犹豫不决", "审美优秀", "重视关系"],
        "keywords": ["风象", "开创", "平衡", "优雅"],
    },
    "scorpio": {
        "traits": ["洞察力强", "神秘深邃", "控制欲强", "转化能力"],
        "keywords": ["水象", "固定", "深刻", "执着"],
    },
    "sagittarius": {
        "traits": ["乐观开朗", "热爱自由", "直言不讳", "追求真理"],
        "keywords": ["火象", "变动", "探险", "哲学"],
    },
    "capricorn": {
        "traits": ["稳重务实", "野心勃勃", "责任感强", "隐忍克制"],
        "keywords": ["土象", "开创", "坚韧", "成就"],
    },
    "aquarius": {
        "traits": ["特立独行", "思维前卫", "人道主义", "疏离感"],
        "keywords": ["风象", "固定", "创新", "独立"],
    },
    "pisces": {
        "traits": ["富有想象", "敏感共情", "逃避现实", "灵性追求"],
        "keywords": ["水象", "变动", "梦幻", "慈悲"],
    },
}

ASPECT_INTERPRETATIONS = {
    "合相": {"intensity": 5, "type": "融合", "description": "能量混合交织"},
    "六分相": {"intensity": 3, "type": "和谐", "description": "能量流畅配合"},
    "三分相": {"intensity": 4, "type": "和谐", "description": "能量自然顺畅"},
    "四分相": {"intensity": 4, "type": "紧张", "description": "能量冲突摩擦"},
    "对分相": {"intensity": 5, "type": "对立", "description": "能量对立拉锯"},
}

STELLIUM_THRESHOLD_WEIGHTED = 15
ELEMENT_CONFLICT_THRESHOLD = 0.6


def get_planet_weight(planet_name: str) -> int:
    """
    获取行星权重值
    """
    weight_enum = PLANET_WEIGHT_MAP.get(planet_name, PlanetWeight.OUTER)
    return weight_enum.value


def get_source_id(planet_name: str) -> str:
    """
    获取规范的 Source ID
    """
    return SOURCE_ID_MAP.get(planet_name, planet_name.lower())


def generate_aspect_source_id(p1: str, p2: str, aspect_type: str) -> str:
    """
    生成相位的规范 Source ID
    """
    p1_id = get_source_id(p1)
    p2_id = get_source_id(p2)
    sorted_ids = sorted([p1_id, p2_id])
    
    aspect_id_map = {
        "合相": "conjunction",
        "六分相": "sextile",
        "三分相": "trine",
        "四分相": "square",
        "对分相": "opposition",
    }
    aspect_key = aspect_id_map.get(aspect_type, aspect_type)
    
    return f"aspect_{sorted_ids[0]}_{aspect_key}_{sorted_ids[1]}"


def extract_stelliums(planets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    提取群星配置（使用加权分数制）
    
    不再使用硬编码的 >= 3 颗行星，而是：
    - 太阳/月亮权重=10
    - 水/金/火权重=7
    - 木/土权重=4
    - 天王/海王/冥王权重=2
    
    阈值：加权总分 >= 15
    """
    stelliums = []
    
    sign_weighted_counts = {}
    main_planets_names = ["太阳", "月亮", "水星", "金星", "火星", "木星", "土星", "天王星", "海王星", "冥王星"]
    main_planets = [p for p in planets if p.get("name") in main_planets_names]
    
    for planet in main_planets:
        sign = planet.get("zodiac", {}).get("sign", "")
        planet_name = planet.get("name", "")
        
        if sign:
            if sign not in sign_weighted_counts:
                sign_weighted_counts[sign] = {
                    "weighted_score": 0,
                    "planet_count": 0,
                    "planets": [],
                    "element": planet.get("zodiac", {}).get("element", "")
                }
            
            weight = get_planet_weight(planet_name)
            sign_weighted_counts[sign]["weighted_score"] += weight
            sign_weighted_counts[sign]["planet_count"] += 1
            sign_weighted_counts[sign]["planets"].append(planet)
    
    for sign, data in sign_weighted_counts.items():
        weighted_score = data["weighted_score"]
        planet_count = data["planet_count"]
        
        if weighted_score >= STELLIUM_THRESHOLD_WEIGHTED:
            significance = "强"
            if weighted_score >= 25:
                significance = "极强"
            elif weighted_score >= 20:
                significance = "较强"
            
            stelliums.append({
                "sign": sign,
                "count": planet_count,
                "weighted_score": weighted_score,
                "significance": significance,
                "planets": [p["name"] for p in data["planets"]],
                "planet_weights": {p["name"]: get_planet_weight(p["name"]) for p in data["planets"]},
                "element": data["element"],
                "description": f"群星{sign}，{planet_count}颗行星，加权分数{weighted_score}，{significance}能量集中",
            })
    
    logger.info(f"检测到 {len(stelliums)} 个群星配置（加权分数制）")
    return stelliums


def extract_key_aspects(aspects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    提取关键相位（使用行星权重过滤边缘行星）
    
    只有满足以下条件的相位才会被视为关键：
    1. 至少包含一颗个人行星（日月水金火）
    2. 或者两颗社会行星形成紧张/重要相位
    3. 纯外行星相位（天王/海王/冥王之间）仅在权重和 >= 6 且为紧张相位时考虑
    """
    key_aspects = []
    
    personal_planets = ["太阳", "月亮", "水星", "金星", "火星"]
    social_planets = ["木星", "土星"]
    outer_planets = ["天王星", "海王星", "冥王星"]
    
    for aspect in aspects:
        p1 = aspect.get("planet1", "")
        p2 = aspect.get("planet2", "")
        aspect_type = aspect.get("aspect", "")
        aspect_info = ASPECT_INTERPRETATIONS.get(aspect_type, {"intensity": 3, "type": "未知"})
        
        p1_weight = get_planet_weight(p1)
        p2_weight = get_planet_weight(p2)
        total_weight = p1_weight + p2_weight
        
        p1_personal = p1 in personal_planets
        p2_personal = p2 in personal_planets
        p1_social = p1 in social_planets
        p2_social = p2 in social_planets
        p1_outer = p1 in outer_planets
        p2_outer = p2 in outer_planets
        
        include_aspect = False
        significance = "普通"
        
        if p1_personal or p2_personal:
            include_aspect = True
            if p1_personal and p2_personal:
                significance = "重要"
            elif (p1_personal and p1_weight == 10) or (p2_personal and p2_weight == 10):
                significance = "重要"
        
        elif p1_social and p2_social:
            if aspect_type in ["合相", "四分相", "对分相"]:
                include_aspect = True
                significance = "中等"
        
        elif (p1_social or p2_social) and (p1_outer or p2_outer):
            if aspect_type in ["合相", "四分相", "对分相", "三分相"]:
                include_aspect = True
                significance = "中等"
        
        elif p1_outer and p2_outer:
            if total_weight >= 4 and aspect_type in ["合相", "四分相", "对分相"]:
                include_aspect = True
                significance = "较弱"
        
        if include_aspect:
            aspect_with_meta = {
                "planet1": p1,
                "planet1_symbol": aspect.get("planet1_symbol", ""),
                "planet1_weight": p1_weight,
                "planet2": p2,
                "planet2_symbol": aspect.get("planet2_symbol", ""),
                "planet2_weight": p2_weight,
                "total_weight": total_weight,
                "aspect": aspect_type,
                "aspect_symbol": aspect.get("aspect_symbol", ""),
                "type": aspect_info["type"],
                "intensity": aspect_info["intensity"],
                "orb": aspect.get("orb", 0),
                "significance": significance,
                "source_id": generate_aspect_source_id(p1, p2, aspect_type),
                "description": f"{p1} {aspect_type} {p2}，{aspect_info['description']}",
            }
            key_aspects.append(aspect_with_meta)
    
    key_aspects.sort(key=lambda x: (x["total_weight"], x["intensity"]), reverse=True)
    
    logger.info(f"提取到 {len(key_aspects)} 个关键相位（行星权重过滤）")
    return key_aspects[:10]


def check_void_of_course_moon(planets: List[Dict[str, Any]], aspects: List[Dict[str, Any]]) -> bool:
    """
    检查月亮空亡
    """
    moon_aspects = []
    for aspect in aspects:
        p1 = aspect.get("planet1", "")
        p2 = aspect.get("planet2", "")
        
        if p1 == "月亮" or p2 == "月亮":
            other_planet = p2 if p1 == "月亮" else p1
            other_weight = get_planet_weight(other_planet)
            
            if other_weight >= 7:
                moon_aspects.append(aspect)
    
    is_void = len(moon_aspects) == 0
    logger.info(f"月亮空亡检测（仅考虑权重>=7的行星）: {'是' if is_void else '否'}")
    return is_void


def extract_big_three(planets: List[Dict[str, Any]], ascendant: Dict[str, Any]) -> Dict[str, Any]:
    """
    提取三巨头（太阳、月亮、上升）- 权重最高的三个配置
    """
    big_three = {}
    
    for planet in planets:
        name = planet.get("name", "")
        if name == "太阳":
            big_three["sun"] = {
                "sign": planet.get("zodiac", {}).get("sign", ""),
                "sign_symbol": planet.get("zodiac", {}).get("sign_symbol", ""),
                "degree": planet.get("zodiac", {}).get("dms", {}).get("formatted", ""),
                "house": planet.get("house", 0),
                "element": planet.get("zodiac", {}).get("element", ""),
                "retrograde": planet.get("is_retrograde", False),
                "weight": get_planet_weight("太阳"),
                "source_id": SourceIdType.SUN.value,
            }
        elif name == "月亮":
            big_three["moon"] = {
                "sign": planet.get("zodiac", {}).get("sign", ""),
                "sign_symbol": planet.get("zodiac", {}).get("sign_symbol", ""),
                "degree": planet.get("zodiac", {}).get("dms", {}).get("formatted", ""),
                "house": planet.get("house", 0),
                "element": planet.get("zodiac", {}).get("element", ""),
                "retrograde": planet.get("is_retrograde", False),
                "weight": get_planet_weight("月亮"),
                "source_id": SourceIdType.MOON.value,
            }
    
    if ascendant:
        big_three["ascendant"] = {
            "sign": ascendant.get("sign", ""),
            "sign_symbol": ascendant.get("sign_symbol", ""),
            "degree": ascendant.get("dms", {}).get("formatted", ""),
            "element": ascendant.get("element", ""),
            "weight": get_planet_weight("上升"),
            "source_id": SourceIdType.ASCENDANT.value,
        }
    
    logger.info(f"三巨头提取完成（权重10）: 太阳={big_three.get('sun', {}).get('sign')}, 月亮={big_three.get('moon', {}).get('sign')}, 上升={big_three.get('ascendant', {}).get('sign')}")
    return big_three


def extract_element_distribution(planets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    提取元素分布（使用加权分数制）
    
    返回：
    - count: 行星数量
    - weighted_score: 加权分数
    - percentage: 加权百分比
    """
    elements = ["火", "土", "风", "水"]
    result = {
        "count": {"火": 0, "土": 0, "风": 0, "水": 0},
        "weighted_score": {"火": 0.0, "土": 0.0, "风": 0.0, "水": 0.0},
    }
    
    main_planets_names = ["太阳", "月亮", "水星", "金星", "火星", "木星", "土星", "天王星", "海王星", "冥王星"]
    
    for planet in planets:
        planet_name = planet.get("name", "")
        if planet_name in main_planets_names:
            element = planet.get("zodiac", {}).get("element", "")
            if element in elements:
                weight = get_planet_weight(planet_name)
                result["count"][element] += 1
                result["weighted_score"][element] += float(weight)
    
    total_weighted = sum(result["weighted_score"].values())
    if total_weighted > 0:
        result["percentage"] = {
            elem: round((result["weighted_score"][elem] / total_weighted) * 100, 1)
            for elem in elements
        }
    else:
        result["percentage"] = {"火": 25, "土": 25, "风": 25, "水": 25}
    
    logger.info(f"元素分布（加权分数制）: 加权分数={result['weighted_score']}, 百分比={result.get('percentage', {})}")
    return result


def extract_quality_distribution(planets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    提取特质分布（开创、固定、变动）- 使用加权分数制
    """
    qualities = ["开创", "固定", "变动"]
    result = {
        "count": {"开创": 0, "固定": 0, "变动": 0},
        "weighted_score": {"开创": 0.0, "固定": 0.0, "变动": 0.0},
    }
    
    main_planets_names = ["太阳", "月亮", "水星", "金星", "火星", "木星", "土星", "天王星", "海王星", "冥王星"]
    
    for planet in planets:
        planet_name = planet.get("name", "")
        if planet_name in main_planets_names:
            quality = planet.get("zodiac", {}).get("quality", "")
            if quality in qualities:
                weight = get_planet_weight(planet_name)
                result["count"][quality] += 1
                result["weighted_score"][quality] += float(weight)
    
    total_weighted = sum(result["weighted_score"].values())
    if total_weighted > 0:
        result["percentage"] = {
            qual: round((result["weighted_score"][qual] / total_weighted) * 100, 1)
            for qual in qualities
        }
    else:
        result["percentage"] = {"开创": 33.3, "固定": 33.3, "变动": 33.4}
    
    logger.info(f"特质分布（加权分数制）: 加权分数={result['weighted_score']}")
    return result


def detect_special_patterns(planets: List[Dict[str, Any]], aspects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    检测特殊格局（使用行星权重过滤）
    只有包含至少一颗核心/个人行星的格局才会被检测
    """
    patterns = []
    
    main_planets_names = ["太阳", "月亮", "水星", "金星", "火星", "木星", "土星", "天王星", "海王星", "冥王星"]
    significant_planets = ["太阳", "月亮", "水星", "金星", "火星", "木星", "土星"]
    
    main_planets = [p.get("name") for p in planets if p.get("name") in main_planets_names]
    
    square_aspects = {}
    trine_aspects = {}
    opposition_aspects = {}
    
    for aspect in aspects:
        p1 = aspect.get("planet1", "")
        p2 = aspect.get("planet2", "")
        
        if p1 not in main_planets or p2 not in main_planets:
            continue
        
        p1_weight = get_planet_weight(p1)
        p2_weight = get_planet_weight(p2)
        
        if p1_weight < 4 and p2_weight < 4:
            continue
        
        aspect_type = aspect.get("aspect", "")
        
        if aspect_type == "四分相":
            if p1 not in square_aspects:
                square_aspects[p1] = []
            if p2 not in square_aspects:
                square_aspects[p2] = []
            square_aspects[p1].append(p2)
            square_aspects[p2].append(p1)
            
        elif aspect_type == "三分相":
            if p1 not in trine_aspects:
                trine_aspects[p1] = []
            if p2 not in trine_aspects:
                trine_aspects[p2] = []
            trine_aspects[p1].append(p2)
            trine_aspects[p2].append(p1)
            
        elif aspect_type == "对分相":
            if p1 not in opposition_aspects:
                opposition_aspects[p1] = []
            if p2 not in opposition_aspects:
                opposition_aspects[p2] = []
            opposition_aspects[p1].append(p2)
            opposition_aspects[p2].append(p1)
    
    significant_planets_list = [p for p in main_planets if p in significant_planets]
    
    for planet in significant_planets_list:
        squares = square_aspects.get(planet, [])
        if len(squares) >= 2:
            for i in range(len(squares)):
                for j in range(i + 1, len(squares)):
                    p1, p2 = squares[i], squares[j]
                    if p1 in opposition_aspects and p2 in opposition_aspects[p1]:
                        planets_in_pattern = [planet, p1, p2]
                        has_significant = any(p in significant_planets for p in planets_in_pattern)
                        
                        if has_significant:
                            total_weight = sum(get_planet_weight(p) for p in planets_in_pattern)
                            
                            patterns.append({
                                "type": "T三角",
                                "planets": planets_in_pattern,
                                "total_weight": total_weight,
                                "description": f"以{planet}为顶点的T三角格局，带来持续的成长动力",
                                "intensity": min(int(total_weight / 5), 5),
                                "source_id": f"pattern_t_{planet.lower()}_{p1.lower()}_{p2.lower()}",
                            })
    
    for planet in significant_planets_list:
        trines = trine_aspects.get(planet, [])
        if len(trines) >= 2:
            for i in range(len(trines)):
                for j in range(i + 1, len(trines)):
                    p1, p2 = trines[i], trines[j]
                    if p1 in trine_aspects and p2 in trine_aspects[p1]:
                        planets_in_pattern = [planet, p1, p2]
                        has_significant = any(p in significant_planets for p in planets_in_pattern)
                        
                        if has_significant:
                            total_weight = sum(get_planet_weight(p) for p in planets_in_pattern)
                            
                            patterns.append({
                                "type": "大三角",
                                "planets": planets_in_pattern,
                                "total_weight": total_weight,
                                "description": f"{planet}、{p1}、{p2}组成大三角，能量流动顺畅",
                                "intensity": min(int(total_weight / 7), 4),
                                "source_id": f"pattern_trine_{planet.lower()}_{p1.lower()}_{p2.lower()}",
                            })
    
    logger.info(f"检测到 {len(patterns)} 个特殊格局（权重过滤）")
    return patterns


def extract_chart_configuration(chart_data: Dict[str, Any]) -> ChartConfiguration:
    """
    从星盘数据中提取核心配置（使用加权分数制）
    """
    if not chart_data:
        return ChartConfiguration()
    
    planets = chart_data.get("planets", [])
    aspects = chart_data.get("aspects", [])
    ascendant = chart_data.get("ascendant", {})
    
    config = ChartConfiguration()
    config.stelliums = extract_stelliums(planets)
    config.key_aspects = extract_key_aspects(aspects)
    config.void_of_course_moon = check_void_of_course_moon(planets, aspects)
    config.big_three = extract_big_three(planets, ascendant)
    
    element_data = extract_element_distribution(planets)
    config.element_distribution = element_data["count"]
    config.element_weighted_score = element_data["weighted_score"]
    
    quality_data = extract_quality_distribution(planets)
    config.quality_distribution = quality_data["count"]
    config.quality_weighted_score = quality_data["weighted_score"]
    
    config.special_patterns = detect_special_patterns(planets, aspects)
    
    return config


def generate_personality_tags(config: ChartConfiguration) -> List[PersonalityTag]:
    """
    基于星盘配置生成性格标签矩阵（使用规范的 Source ID）
    """
    tags = []
    
    big_three = config.big_three
    
    if big_three.get("sun"):
        sun_sign = big_three["sun"]["sign"]
        sun_source_id = big_three["sun"]["source_id"]
        sun_weight = big_three["sun"]["weight"]
        sign_info = PERSONALITY_TAGS.get(_zodiac_to_key(sun_sign), {})
        
        for i, trait in enumerate(sign_info.get("traits", [])[:2]):
            tags.append(PersonalityTag(
                id=f"{sun_source_id}_{_zodiac_to_key(sun_sign)}_trait_{i}",
                name=trait,
                category="核心性格",
                intensity=min(8 + (i == 0 and 2 or 0), 10),
                description=f"太阳{sun_sign}带来的核心特质",
                source=f"太阳{sun_sign}",
                source_id=sun_source_id,
                planet_weight=sun_weight,
            ))
    
    if big_three.get("moon"):
        moon_sign = big_three["moon"]["sign"]
        moon_source_id = big_three["moon"]["source_id"]
        moon_weight = big_three["moon"]["weight"]
        sign_info = PERSONALITY_TAGS.get(_zodiac_to_key(moon_sign), {})
        
        for i, trait in enumerate(sign_info.get("traits", [])[2:]):
            tags.append(PersonalityTag(
                id=f"{moon_source_id}_{_zodiac_to_key(moon_sign)}_trait_{i}",
                name=trait,
                category="情感需求",
                intensity=7,
                description=f"月亮{moon_sign}带来的内在情感需求",
                source=f"月亮{moon_sign}",
                source_id=moon_source_id,
                planet_weight=moon_weight,
            ))
    
    if big_three.get("ascendant"):
        asc_sign = big_three["ascendant"]["sign"]
        asc_source_id = big_three["ascendant"]["source_id"]
        asc_weight = big_three["ascendant"]["weight"]
        sign_info = PERSONALITY_TAGS.get(_zodiac_to_key(asc_sign), {})
        
        for i, keyword in enumerate(sign_info.get("keywords", [])[:2]):
            tags.append(PersonalityTag(
                id=f"{asc_source_id}_{_zodiac_to_key(asc_sign)}_keyword_{i}",
                name=keyword,
                category="外在表现",
                intensity=6,
                description=f"上升{asc_sign}带来的外在形象和社交面具",
                source=f"上升{asc_sign}",
                source_id=asc_source_id,
                planet_weight=asc_weight,
            ))
    
    for stellium in config.stelliums:
        sign = stellium["sign"]
        weighted_score = stellium["weighted_score"]
        sign_info = PERSONALITY_TAGS.get(_zodiac_to_key(sign), {})
        stellium_source_id = f"{SourceIdType.STELLIUM.value}_{_zodiac_to_key(sign)}"
        
        tags.append(PersonalityTag(
            id=stellium_source_id,
            name=f"群星{sign}",
            category="能量集中",
            intensity=min(int(weighted_score / 3), 10),
            description=f"加权分数{weighted_score}，{stellium['significance']}能量集中",
            source=f"群星{sign}",
            source_id=stellium_source_id,
            planet_weight=weighted_score,
        ))
        
        for trait in sign_info.get("traits", [])[:1]:
            tags.append(PersonalityTag(
                id=f"{stellium_source_id}_trait",
                name=f"强化{sign}特质",
                category="性格强化",
                intensity=9,
                description=f"群星{sign}让{sign}的特质更加明显",
                source=f"群星{sign}",
                source_id=stellium_source_id,
                planet_weight=weighted_score,
            ))
    
    for aspect in config.key_aspects:
        p1 = aspect["planet1"]
        p2 = aspect["planet2"]
        aspect_type = aspect["aspect"]
        aspect_intensity = aspect["intensity"]
        total_weight = aspect["total_weight"]
        source_id = aspect["source_id"]
        
        if aspect["type"] == "紧张" or aspect["type"] == "对立":
            tag_name = _generate_tension_aspect_tag(p1, p2, aspect_type)
            tags.append(PersonalityTag(
                id=source_id,
                name=tag_name,
                category="内在冲突",
                intensity=min(int(aspect_intensity * 2), 10),
                description=f"{p1} {aspect_type} {p2}带来的成长议题",
                source=f"{p1} {aspect_type} {p2}",
                source_id=source_id,
                planet_weight=total_weight,
            ))
        else:
            tag_name = _generate_harmony_aspect_tag(p1, p2, aspect_type)
            tags.append(PersonalityTag(
                id=source_id,
                name=tag_name,
                category="天赋优势",
                intensity=min(int(aspect_intensity * 2), 10),
                description=f"{p1} {aspect_type} {p2}带来的流畅能量",
                source=f"{p1} {aspect_type} {p2}",
                source_id=source_id,
                planet_weight=total_weight,
            ))
    
    if config.void_of_course_moon:
        tags.append(PersonalityTag(
            id=SourceIdType.VOID_MOON.value,
            name="月亮空亡",
            category="特殊配置",
            intensity=7,
            description="月亮空亡带来的情感独立和内省倾向",
            source="月亮空亡",
            source_id=SourceIdType.VOID_MOON.value,
            planet_weight=get_planet_weight("月亮"),
        ))
    
    for pattern in config.special_patterns:
        tags.append(PersonalityTag(
            id=pattern["source_id"],
            name=pattern["type"],
            category="特殊格局",
            intensity=pattern["intensity"] * 2,
            description=pattern["description"],
            source=f"{pattern['type']}: {', '.join(pattern['planets'])}",
            source_id=pattern["source_id"],
            planet_weight=pattern["total_weight"],
        ))
    
    logger.info(f"生成了 {len(tags)} 个性格标签（带规范Source ID）")
    return tags


def _zodiac_to_key(sign_name: str) -> str:
    """将星座中文名称转换为key"""
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
    return mapping.get(sign_name, "aries")


def _generate_tension_aspect_tag(p1: str, p2: str, aspect_type: str) -> str:
    """生成紧张相位的标签"""
    tension_mappings = {
        ("太阳", "土星"): "自律但压抑",
        ("月亮", "土星"): "情感克制",
        ("水星", "土星"): "思维严谨但迟缓",
        ("金星", "火星"): "爱恨交织",
        ("金星", "土星"): "感情谨慎",
        ("金星", "冥王星"): "深刻但控制欲",
        ("火星", "土星"): "冲动但克制",
        ("火星", "冥王星"): "强烈意志力",
        ("月亮", "冥王星"): "深刻情感",
        ("太阳", "天王星"): "自我与自由",
        ("月亮", "天王星"): "情感波动",
    }
    
    key = tuple(sorted([p1, p2]))
    if key in tension_mappings:
        return tension_mappings[key]
    
    generic_tension = {
        "太阳": f"自我表达",
        "月亮": f"情感需求",
        "水星": f"思维沟通",
        "金星": f"价值观",
        "火星": f"行动力",
        "木星": f"信仰",
        "土星": f"责任感",
        "天王星": f"独立精神",
        "海王星": f"理想主义",
        "冥王星": f"深刻转化",
    }
    
    return f"{generic_tension.get(p1, p1)}与{generic_tension.get(p2, p2)}的整合"


def _generate_harmony_aspect_tag(p1: str, p2: str, aspect_type: str) -> str:
    """生成和谐相位的标签"""
    harmony_mappings = {
        ("太阳", "木星"): "乐观自信",
        ("太阳", "金星"): "优雅魅力",
        ("太阳", "火星"): "行动力强",
        ("金星", "木星"): "社交达人",
        ("水星", "木星"): "思维开阔",
        ("月亮", "金星"): "情感丰富",
        ("金星", "海王星"): "浪漫理想",
        ("火星", "木星"): "行动力旺盛",
        ("水星", "金星"): "沟通优雅",
        ("太阳", "海王星"): "直觉敏锐",
    }
    
    key = tuple(sorted([p1, p2]))
    if key in harmony_mappings:
        return harmony_mappings[key]
    
    generic_harmony = {
        "太阳": f"自我",
        "月亮": f"情感",
        "水星": f"思维",
        "金星": f"社交",
        "火星": f"行动",
        "木星": f"机遇",
        "土星": f"稳定",
        "天王星": f"创新",
        "海王星": f"灵感",
        "冥王星": f"深度",
    }
    
    return f"{generic_harmony.get(p1, p1)}与{generic_harmony.get(p2, p2)}的和谐"


def get_dominant_by_weighted(weighted_scores: Dict[str, float]) -> str:
    """
    根据加权分数找出主导元素/特质
    """
    if not weighted_scores:
        return ""
    return max(weighted_scores.items(), key=lambda x: x[1])[0]


def extract_tag_matrix(chart_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    主函数：提取星盘配置并生成标签矩阵
    
    优化点：
    1. 行星权重体系 - 区分日月升与远地行星
    2. 规范的 Source ID 映射
    3. 加权分数制替代硬编码阈值
    """
    logger.info("开始提取星盘配置和生成性格标签（优化版）")
    
    config = extract_chart_configuration(chart_data)
    tags = generate_personality_tags(config)
    
    tags_by_category = {}
    all_tag_source_ids = set()
    
    for tag in tags:
        if tag.category not in tags_by_category:
            tags_by_category[tag.category] = []
        
        tag_dict = {
            "id": tag.id,
            "name": tag.name,
            "intensity": tag.intensity,
            "description": tag.description,
            "source": tag.source,
            "source_id": tag.source_id,
            "planet_weight": tag.planet_weight,
        }
        tags_by_category[tag.category].append(tag_dict)
        all_tag_source_ids.add(tag.source_id)
    
    for category in tags_by_category:
        tags_by_category[category].sort(key=lambda x: (x["planet_weight"], x["intensity"]), reverse=True)
    
    dominant_element = get_dominant_by_weighted(config.element_weighted_score)
    dominant_quality = get_dominant_by_weighted(config.quality_weighted_score)
    
    result = {
        "configuration": {
            "big_three": config.big_three,
            "stelliums": config.stelliums,
            "key_aspects": config.key_aspects,
            "special_patterns": config.special_patterns,
            "void_of_course_moon": config.void_of_course_moon,
        },
        "distribution": {
            "elements": config.element_distribution,
            "element_weighted_score": config.element_weighted_score,
            "qualities": config.quality_distribution,
            "quality_weighted_score": config.quality_weighted_score,
            "dominant_element": dominant_element,
            "dominant_quality": dominant_quality,
        },
        "tags_matrix": tags_by_category,
        "tags_count": len(tags),
        "all_source_ids": list(all_tag_source_ids),
        "_meta": {
            "stellium_threshold_weighted": STELLIUM_THRESHOLD_WEIGHTED,
            "element_conflict_threshold": ELEMENT_CONFLICT_THRESHOLD,
            "planet_weight_system": {
                "core": "日月升 - 权重10",
                "personal": "水金火 - 权重7",
                "social": "木土 - 权重4",
                "outer": "天王海王冥王 - 权重2",
            }
        }
    }
    
    logger.info(f"标签矩阵生成完成（优化版），共 {len(tags)} 个标签")
    return result
