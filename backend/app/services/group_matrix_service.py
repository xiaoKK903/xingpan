from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
import logging
import math

from app.astro import calculate_chart, parse_birth_datetime, HouseSystem
from app.synastry import (
    calculate_angular_distance, 
    SYNASTRY_ASPECT_TYPES as BASE_ASPECT_TYPES,
    SYNASTRY_PLANET_PRIORITY
)

logger = logging.getLogger(__name__)

ROLE_DEFINITIONS = {
    "glue": {
        "name": "粘合剂",
        "description": "月亮、金星联系多的人，擅长拉近距离、调和矛盾",
        "icon": "🤝",
        "key_planets": ["月亮", "金星"],
        "key_aspects": ["harmonious", "neutral"],
        "color": "#22c55e",
        "line_color": "#22c55e",
        "glow_intensity": 0.8,
        "threejs_color": "#4ade80",
        "threejs_emissive": "#22c55e"
    },
    "firecracker": {
        "name": "火药桶",
        "description": "火星、土星冲突多的人，容易吵架、闹矛盾",
        "icon": "💥",
        "key_planets": ["火星", "土星"],
        "key_aspects": ["challenging"],
        "color": "#ef4444",
        "line_color": "#ef4444",
        "glow_intensity": 1.0,
        "threejs_color": "#f87171",
        "threejs_emissive": "#ef4444"
    },
    "visionary": {
        "name": "愿景导师",
        "description": "木星、海王星厉害的人，会画饼、带方向、有脑洞",
        "icon": "✨",
        "key_planets": ["木星", "海王星"],
        "key_aspects": ["harmonious", "neutral"],
        "color": "#8b5cf6",
        "line_color": "#8b5cf6",
        "glow_intensity": 0.9,
        "threejs_color": "#a78bfa",
        "threejs_emissive": "#8b5cf6"
    }
}

SCENARIO_DEFINITIONS = {
    "meeting": {
        "name": "团队会议",
        "description": "分析团队在开会讨论时的互动模式",
        "key_roles": ["visionary", "glue", "firecracker"],
        "dominant_planets": ["水星", "太阳", "木星"],
        "conflict_planets": ["火星", "土星"],
        "theme_color": "#3b82f6",
        "icon": "📋"
    },
    "travel": {
        "name": "一起旅行",
        "description": "分析团队在旅行中的相处模式",
        "key_roles": ["glue", "firecracker", "visionary"],
        "dominant_planets": ["月亮", "金星", "木星"],
        "conflict_planets": ["火星", "天王星"],
        "theme_color": "#10b981",
        "icon": "✈️"
    },
    "project": {
        "name": "项目合作",
        "description": "分析团队在执行项目时的协作模式",
        "key_roles": ["visionary", "glue", "firecracker"],
        "dominant_planets": ["太阳", "土星", "火星"],
        "conflict_planets": ["土星", "火星"],
        "theme_color": "#f59e0b",
        "icon": "🎯"
    }
}

MAIN_PLANETS = [
    "太阳", "月亮", "水星", "金星", "火星", 
    "木星", "土星", "天王星", "海王星", "冥王星"
]

GROUP_ASPECT_TYPES = [
    {"name": "合相", "symbol": "☌", "angle": 0.0, "orb": 10.0, "nature": "neutral"},
    {"name": "六分相", "symbol": "⚹", "angle": 60.0, "orb": 8.0, "nature": "harmonious"},
    {"name": "四分相", "symbol": "□", "angle": 90.0, "orb": 10.0, "nature": "challenging"},
    {"name": "三分相", "symbol": "△", "angle": 120.0, "orb": 10.0, "nature": "harmonious"},
    {"name": "对分相", "symbol": "☍", "angle": 180.0, "orb": 10.0, "nature": "challenging"},
]

DETRIMENT_SIGNS = {
    "太阳": ["水瓶座"],
    "月亮": ["摩羯座"],
    "水星": ["射手座", "双鱼座"],
    "金星": ["白羊座", "天蝎座"],
    "火星": ["天秤座", "金牛座"],
    "木星": ["双子座", "处女座"],
    "土星": ["巨蟹座", "狮子座"],
    "天王星": ["狮子座", "金牛座"],
    "海王星": ["处女座", "双子座"],
    "冥王星": ["金牛座", "天秤座"]
}

FALL_SIGNS = {
    "太阳": ["天秤座"],
    "月亮": ["天蝎座"],
    "水星": ["狮子座", "双鱼座"],
    "金星": ["天蝎座", "白羊座"],
    "火星": ["巨蟹座", "摩羯座"],
    "木星": ["摩羯座", "双子座"],
    "土星": ["白羊座", "巨蟹座"],
    "天王星": ["金牛座", "狮子座"],
    "海王星": ["双子座", "处女座"],
    "冥王星": ["金牛座", "天秤座"]
}

RULING_SIGNS = {
    "太阳": ["狮子座"],
    "月亮": ["巨蟹座"],
    "水星": ["双子座", "处女座"],
    "金星": ["金牛座", "天秤座"],
    "火星": ["白羊座", "天蝎座"],
    "木星": ["射手座", "双鱼座"],
    "土星": ["摩羯座", "水瓶座"],
    "天王星": ["水瓶座"],
    "海王星": ["双鱼座"],
    "冥王星": ["天蝎座"]
}

EXALTATION_SIGNS = {
    "太阳": ["白羊座"],
    "月亮": ["金牛座"],
    "水星": ["处女座", "水瓶座"],
    "金星": ["双鱼座", "天秤座"],
    "火星": ["摩羯座", "天蝎座"],
    "木星": ["巨蟹座", "射手座"],
    "土星": ["天秤座", "摩羯座"],
    "天王星": ["天蝎座", "水瓶座"],
    "海王星": ["巨蟹座", "双鱼座"],
    "冥王星": ["白羊座", "天蝎座"]
}

HOUSE_STRENGTH = {
    1: 1.5,
    2: 1.0,
    3: 0.8,
    4: 1.2,
    5: 1.3,
    6: 0.7,
    7: 1.3,
    8: 0.8,
    9: 1.2,
    10: 1.5,
    11: 1.0,
    12: 0.6
}

RELATION_TYPE_CONFIG = {
    "harmony": {
        "name": "和谐",
        "line_color": "#22c55e",
        "line_color_hex": 0x22c55e,
        "line_width_base": 1.5,
        "glow_color": "#22c55e",
        "glow_intensity": 0.6,
        "dash_pattern": None,
        "opacity": 0.8
    },
    "conflict": {
        "name": "紧张",
        "line_color": "#ef4444",
        "line_color_hex": 0xef4444,
        "line_width_base": 2.0,
        "glow_color": "#ef4444",
        "glow_intensity": 0.8,
        "dash_pattern": [5, 5],
        "opacity": 0.9
    },
    "neutral": {
        "name": "平淡",
        "line_color": "#64748b",
        "line_color_hex": 0x64748b,
        "line_width_base": 0.8,
        "glow_color": "#64748b",
        "glow_intensity": 0.3,
        "dash_pattern": [2, 2],
        "opacity": 0.5
    }
}

TOPOLOGY_COLORS = [
    "#ff8c32", "#50c8ff", "#22c55e", "#ef4444", "#8b5cf6",
    "#f59e0b", "#06b6d4", "#ec4899", "#6366f1", "#10b981"
]


def generate_topo_positions(
    n: int, 
    radius: float = 200.0,
    center_offset: Tuple[float, float] = (0, 0)
) -> List[Dict[str, float]]:
    positions = []
    cx, cy = center_offset
    
    if n == 1:
        positions.append({"x": cx, "y": cy})
        return positions
    
    for i in range(n):
        angle = 2 * math.pi * i / n - math.pi / 2
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        positions.append({"x": x, "y": y})
    
    return positions


def generate_3d_positions(
    n: int, 
    radius: float = 5.0
) -> List[Dict[str, float]]:
    positions = []
    
    if n == 1:
        positions.append({"x": 0, "y": 0, "z": 0})
        return positions
    
    phi = math.pi * (3 - math.sqrt(5))
    
    for i in range(n):
        y = 1 - (i / float(n - 1)) * 2
        radius_at_y = math.sqrt(1 - y * y)
        
        theta = phi * i
        
        x = math.cos(theta) * radius_at_y * radius
        y_pos = y * radius
        z = math.sin(theta) * radius_at_y * radius
        
        positions.append({"x": x, "y": y_pos, "z": z})
    
    return positions


def find_aspect_type(diff: float, aspect_types: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    for aspect_type in aspect_types:
        angle = aspect_type["angle"]
        orb = aspect_type["orb"]
        
        if abs(diff - angle) <= orb:
            orb_used = abs(diff - angle)
            return {
                "aspect": aspect_type["name"],
                "aspect_symbol": aspect_type["symbol"],
                "angle": angle,
                "actual_angle": round(diff, 6),
                "orb": round(orb_used, 6),
                "orb_arcminutes": round(orb_used * 60, 2),
                "nature": aspect_type["nature"],
                "is_applying": None,
                "orb_ratio": round((orb - orb_used) / orb, 3)
            }
    return None


def get_planet_dignity_score(planet_name: str, sign_name: str) -> float:
    score = 1.0
    
    if planet_name in RULING_SIGNS and sign_name in RULING_SIGNS[planet_name]:
        score += 0.5
    elif planet_name in EXALTATION_SIGNS and sign_name in EXALTATION_SIGNS[planet_name]:
        score += 0.3
    elif planet_name in DETRIMENT_SIGNS and sign_name in DETRIMENT_SIGNS[planet_name]:
        score -= 0.4
    elif planet_name in FALL_SIGNS and sign_name in FALL_SIGNS[planet_name]:
        score -= 0.3
    
    return max(0.3, score)


def get_house_strength_score(house_number: int) -> float:
    return HOUSE_STRENGTH.get(house_number, 1.0)


def get_angular_distance_to_axis(planet_longitude: float, axis_longitude: float) -> float:
    diff = abs(planet_longitude - axis_longitude)
    if diff > 180.0:
        diff = 360.0 - diff
    return diff


def is_planet_conjunct_axis(
    planet_longitude: float, 
    axis_longitude: float, 
    orb: float = 8.0
) -> Tuple[bool, float]:
    diff = get_angular_distance_to_axis(planet_longitude, axis_longitude)
    if diff <= orb:
        return True, diff
    return False, 0.0


def calculate_member_chart(member: Dict[str, Any]) -> Dict[str, Any]:
    try:
        required_keys = ["birth_date", "birth_time", "latitude", "longitude"]
        for key in required_keys:
            if key not in member:
                raise ValueError(f"Missing required key: {key}")
        
        dt = parse_birth_datetime(member["birth_date"], member["birth_time"])
        
        chart = calculate_chart(
            year=dt["year"],
            month=dt["month"],
            day=dt["day"],
            hour=dt["hour"],
            minute=dt["minute"],
            latitude=member["latitude"],
            longitude=member["longitude"],
            house_system=member.get("house_system", HouseSystem.PLACIDUS.value)
        )
        
        return chart
    except Exception as e:
        logger.error(f"计算成员星盘失败: {e}")
        raise


def calculate_pair_aspects(
    planets_a: List[Dict[str, Any]],
    planets_b: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    aspects = []
    
    planets_a_filtered = [p for p in planets_a if p["name"] in MAIN_PLANETS]
    planets_b_filtered = [p for p in planets_b if p["name"] in MAIN_PLANETS]
    
    planets_a_dict = {p["name"]: p for p in planets_a_filtered}
    planets_b_dict = {p["name"]: p for p in planets_b_filtered}
    
    for name_a, p_a in planets_a_dict.items():
        for name_b, p_b in planets_b_dict.items():
            diff = calculate_angular_distance(p_a["longitude"], p_b["longitude"])
            
            aspect = find_aspect_type(diff, GROUP_ASPECT_TYPES)
            if aspect:
                aspects.append({
                    "planet_a": name_a,
                    "planet_a_symbol": p_a.get("symbol", ""),
                    "planet_a_longitude": p_a["longitude"],
                    "planet_b": name_b,
                    "planet_b_symbol": p_b.get("symbol", ""),
                    "planet_b_longitude": p_b["longitude"],
                    **aspect,
                    "priority": (
                        SYNASTRY_PLANET_PRIORITY.get(name_a, 0) + 
                        SYNASTRY_PLANET_PRIORITY.get(name_b, 0)
                    ),
                    "line_config": {
                        "color": "#22c55e" if aspect["nature"] == "harmonious" else 
                                 "#ef4444" if aspect["nature"] == "challenging" else "#64748b",
                        "color_hex": 0x22c55e if aspect["nature"] == "harmonious" else 
                                    0xef4444 if aspect["nature"] == "challenging" else 0x64748b,
                        "width": 1.0 if aspect["nature"] == "neutral" else 1.5,
                        "dashed": aspect["nature"] == "challenging",
                        "opacity": 0.8,
                        "orb_ratio": aspect.get("orb_ratio", 0.5)
                    }
                })
    
    aspects.sort(key=lambda x: (x["orb"], -x["priority"]))
    
    return aspects


def calculate_relationship_matrix(
    members: List[Dict[str, Any]],
    charts: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    matrix = {
        "pairs": [],
        "summary": {
            "total_pairs": 0,
            "total_aspects": 0,
            "harmonious_aspects": 0,
            "challenging_aspects": 0,
            "neutral_aspects": 0
        },
        "member_stats": {},
        "threejs_config": {
            "relation_types": RELATION_TYPE_CONFIG
        }
    }
    
    n = len(members)
    matrix["summary"]["total_pairs"] = n * (n - 1) // 2
    
    member_names = [m["name"] for m in members]
    for name in member_names:
        matrix["member_stats"][name] = {
            "total_aspects": 0,
            "harmonious_aspects": 0,
            "challenging_aspects": 0,
            "neutral_aspects": 0,
            "connections": []
        }
    
    for i in range(n):
        for j in range(i + 1, n):
            member_a = members[i]
            member_b = members[j]
            name_a = member_a["name"]
            name_b = member_b["name"]
            weight_a = member_a.get("weight", 1.0)
            weight_b = member_b.get("weight", 1.0)
            combined_weight = weight_a * weight_b
            
            chart_a = charts.get(name_a)
            chart_b = charts.get(name_b)
            
            if not chart_a or not chart_b:
                continue
            
            planets_a = chart_a.get("planets", [])
            planets_b = chart_b.get("planets", [])
            
            aspects = calculate_pair_aspects(planets_a, planets_b)
            
            harmonious = [a for a in aspects if a["nature"] == "harmonious"]
            challenging = [a for a in aspects if a["nature"] == "challenging"]
            neutral = [a for a in aspects if a["nature"] == "neutral"]
            
            harmony_score = (len(harmonious) * 2 + len(neutral)) * combined_weight
            conflict_score = len(challenging) * combined_weight
            
            if conflict_score > 0 and conflict_score >= harmony_score * 0.5:
                relation_type = "conflict"
            elif harmony_score > 0:
                relation_type = "harmony"
            else:
                relation_type = "neutral"
            
            relation_config = RELATION_TYPE_CONFIG.get(relation_type, RELATION_TYPE_CONFIG["neutral"])
            
            total_aspects = len(aspects)
            line_width = relation_config["line_width_base"]
            
            if total_aspects >= 5:
                line_width *= 1.5
            elif total_aspects >= 3:
                line_width *= 1.2
            
            avg_orb_ratio = 0.5
            if aspects:
                avg_orb_ratio = sum(a.get("orb_ratio", 0.5) for a in aspects) / len(aspects)
                
                intensity_factor = 1.0 + (1.0 - avg_orb_ratio) * 0.4
                line_width *= intensity_factor
            
            pair_data = {
                "pair": [name_a, name_b],
                "aspects": aspects,
                "summary": {
                    "total": len(aspects),
                    "harmonious": len(harmonious),
                    "challenging": len(challenging),
                    "neutral": len(neutral),
                    "harmony_score": harmony_score,
                    "conflict_score": conflict_score,
                    "relation_type": relation_type
                },
                "threejs_config": {
                    "relation_type": relation_type,
                    "line_color": relation_config["line_color"],
                    "line_color_hex": relation_config["line_color_hex"],
                    "line_width": line_width,
                    "glow_color": relation_config["glow_color"],
                    "glow_intensity": relation_config["glow_intensity"],
                    "dash_pattern": relation_config["dash_pattern"],
                    "opacity": relation_config["opacity"],
                    "weight_a": weight_a,
                    "weight_b": weight_b,
                    "combined_weight": combined_weight,
                    "aspect_count": len(aspects),
                    "avg_orb_ratio": avg_orb_ratio,
                    "member_indices": [i, j]
                }
            }
            
            matrix["pairs"].append(pair_data)
            
            matrix["summary"]["total_aspects"] += len(aspects)
            matrix["summary"]["harmonious_aspects"] += len(harmonious)
            matrix["summary"]["challenging_aspects"] += len(challenging)
            matrix["summary"]["neutral_aspects"] += len(neutral)
            
            matrix["member_stats"][name_a]["total_aspects"] += len(aspects)
            matrix["member_stats"][name_b]["total_aspects"] += len(aspects)
            matrix["member_stats"][name_a]["harmonious_aspects"] += len(harmonious)
            matrix["member_stats"][name_b]["harmonious_aspects"] += len(harmonious)
            matrix["member_stats"][name_a]["challenging_aspects"] += len(challenging)
            matrix["member_stats"][name_b]["challenging_aspects"] += len(challenging)
            matrix["member_stats"][name_a]["neutral_aspects"] += len(neutral)
            matrix["member_stats"][name_b]["neutral_aspects"] += len(neutral)
            
            matrix["member_stats"][name_a]["connections"].append({
                "to": name_b,
                "to_index": j,
                "relation_type": relation_type,
                "aspect_count": len(aspects),
                "line_config": pair_data["threejs_config"]
            })
            matrix["member_stats"][name_b]["connections"].append({
                "to": name_a,
                "to_index": i,
                "relation_type": relation_type,
                "aspect_count": len(aspects),
                "line_config": pair_data["threejs_config"]
            })
    
    return matrix


GLUE_PLANET_WEIGHTS = {
    "月亮": 12.0,
    "金星": 10.0,
    "木星": 4.0,
    "水星": 2.0
}

FIRECRACKER_PLANET_WEIGHTS = {
    "火星": 14.0,
    "土星": 12.0,
    "冥王星": 10.0,
    "天王星": 8.0,
    "太阳": 3.0
}

VISIONARY_PLANET_WEIGHTS = {
    "木星": 14.0,
    "海王星": 12.0,
    "天王星": 10.0,
    "太阳": 6.0,
    "水星": 5.0,
    "月亮": 3.0
}

SIGN_ROLE_AFFINITY = {
    "巨蟹座": {"glue": 1.4, "visionary": 1.0, "firecracker": 0.9},
    "天蝎座": {"glue": 1.1, "visionary": 1.2, "firecracker": 1.3},
    "双鱼座": {"glue": 1.3, "visionary": 1.4, "firecracker": 0.8},
    "金牛座": {"glue": 1.2, "visionary": 0.9, "firecracker": 1.1},
    "天秤座": {"glue": 1.3, "visionary": 1.0, "firecracker": 0.9},
    "狮子座": {"glue": 0.9, "visionary": 1.3, "firecracker": 1.2},
    "射手座": {"glue": 0.9, "visionary": 1.5, "firecracker": 1.0},
    "水瓶座": {"glue": 0.8, "visionary": 1.4, "firecracker": 1.1},
    "白羊座": {"glue": 0.8, "visionary": 1.1, "firecracker": 1.4},
    "摩羯座": {"glue": 0.9, "visionary": 1.0, "firecracker": 1.3},
    "双子座": {"glue": 1.0, "visionary": 1.3, "firecracker": 0.95},
    "处女座": {"glue": 1.0, "visionary": 1.0, "firecracker": 1.0}
}

HOUSE_ROLE_AFFINITY = {
    1: {"glue": 1.1, "visionary": 1.1, "firecracker": 1.2},
    2: {"glue": 1.1, "visionary": 0.9, "firecracker": 1.0},
    3: {"glue": 1.0, "visionary": 1.1, "firecracker": 0.95},
    4: {"glue": 1.3, "visionary": 1.0, "firecracker": 1.05},
    5: {"glue": 1.2, "visionary": 1.3, "firecracker": 1.0},
    6: {"glue": 1.0, "visionary": 0.95, "firecracker": 1.05},
    7: {"glue": 1.4, "visionary": 1.0, "firecracker": 1.0},
    8: {"glue": 0.95, "visionary": 1.1, "firecracker": 1.25},
    9: {"glue": 1.0, "visionary": 1.4, "firecracker": 0.95},
    10: {"glue": 1.0, "visionary": 1.3, "firecracker": 1.2},
    11: {"glue": 1.1, "visionary": 1.3, "firecracker": 0.95},
    12: {"glue": 1.0, "visionary": 1.2, "firecracker": 1.1}
}

ELEMENT_ROLE_AFFINITY = {
    "火象星座": {"glue": 0.95, "visionary": 1.1, "firecracker": 1.2},
    "土象星座": {"glue": 1.1, "visionary": 0.95, "firecracker": 1.1},
    "风象星座": {"glue": 1.05, "visionary": 1.2, "firecracker": 0.95},
    "水象星座": {"glue": 1.2, "visionary": 1.1, "firecracker": 0.95}
}

SIGN_ELEMENTS = {
    "白羊座": "火象星座", "狮子座": "火象星座", "射手座": "火象星座",
    "金牛座": "土象星座", "处女座": "土象星座", "摩羯座": "土象星座",
    "双子座": "风象星座", "天秤座": "风象星座", "水瓶座": "风象星座",
    "巨蟹座": "水象星座", "天蝎座": "水象星座", "双鱼座": "水象星座"
}


def calculate_planet_role_score(
    planet_name: str,
    planet_data: Dict[str, Any],
    chart: Dict[str, Any],
    role_key: str
) -> float:
    score = 0.0
    
    if not planet_data:
        return score
    
    zodiac = planet_data.get("zodiac", {})
    sign_name = zodiac.get("sign", "")
    house_number = planet_data.get("house", 0)
    planet_longitude = planet_data.get("longitude", 0.0)
    planet_degree = zodiac.get("degree", 0)
    
    houses_result = chart.get("houses", {})
    ascendant_longitude = houses_result.get("ascendant_longitude", 0.0)
    midheaven_longitude = houses_result.get("midheaven_longitude", 0.0)
    
    weights_map = {
        "glue": GLUE_PLANET_WEIGHTS,
        "firecracker": FIRECRACKER_PLANET_WEIGHTS,
        "visionary": VISIONARY_PLANET_WEIGHTS
    }
    
    weights = weights_map.get(role_key, {})
    base_weight = weights.get(planet_name, 0.0)
    
    if base_weight == 0:
        return 0.0
    
    score += base_weight
    
    dignity_score = get_planet_dignity_score(planet_name, sign_name)
    score *= dignity_score
    
    sign_affinity = SIGN_ROLE_AFFINITY.get(sign_name, {}).get(role_key, 1.0)
    score *= sign_affinity
    
    house_affinity = HOUSE_ROLE_AFFINITY.get(house_number, {}).get(role_key, 1.0)
    score *= house_affinity
    
    sign_element = SIGN_ELEMENTS.get(sign_name, "")
    element_affinity = ELEMENT_ROLE_AFFINITY.get(sign_element, {}).get(role_key, 1.0)
    score *= element_affinity
    
    is_conjunct_asc, diff_asc = is_planet_conjunct_axis(planet_longitude, ascendant_longitude, 8.0)
    if is_conjunct_asc:
        axis_bonus = 4.0 - (diff_asc / 8.0) * 3.0
        score += axis_bonus
    
    is_conjunct_mc, diff_mc = is_planet_conjunct_axis(planet_longitude, midheaven_longitude, 8.0)
    if is_conjunct_mc:
        axis_bonus = 3.0 - (diff_mc / 8.0) * 2.0
        score += axis_bonus
    
    if planet_degree >= 0 and planet_degree <= 3:
        score *= 1.15
    elif planet_degree >= 27:
        score *= 1.1
    
    if house_number in [1, 10]:
        score *= 1.15
    elif house_number in [4, 7]:
        score *= 1.1
    
    if role_key == "glue":
        if house_number in [4, 7, 5, 11]:
            score *= 1.1
    
    elif role_key == "firecracker":
        if house_number in [1, 8, 10, 12]:
            score *= 1.1
        
        if sign_element == "火象星座":
            score *= 1.05
    
    elif role_key == "visionary":
        if house_number in [5, 9, 10, 11]:
            score *= 1.1
        
        if sign_element == "火象星座" or sign_element == "风象星座":
            score *= 1.05
    
    return round(score, 3)


def calculate_member_roles(
    member: Dict[str, Any],
    chart: Dict[str, Any],
    matrix: Dict[str, Any],
    all_members: List[Dict[str, Any]],
    member_index: int = 0
) -> Dict[str, Any]:
    name = member["name"]
    is_core = member.get("is_core", False)
    weight = member.get("weight", 1.0)
    
    member_stats = matrix["member_stats"].get(name, {})
    connections = member_stats.get("connections", [])
    
    role_scores = {
        "glue": 0.0,
        "firecracker": 0.0,
        "visionary": 0.0
    }
    
    planets = chart.get("planets", [])
    planet_dict = {p["name"]: p for p in planets if p["name"] in MAIN_PLANETS}
    
    for planet_name in MAIN_PLANETS:
        planet_data = planet_dict.get(planet_name)
        
        glue_score = calculate_planet_role_score(planet_name, planet_data, chart, "glue")
        role_scores["glue"] += glue_score
        
        firecracker_score = calculate_planet_role_score(planet_name, planet_data, chart, "firecracker")
        role_scores["firecracker"] += firecracker_score
        
        visionary_score = calculate_planet_role_score(planet_name, planet_data, chart, "visionary")
        role_scores["visionary"] += visionary_score
    
    for conn in connections:
        other_name = conn["to"]
        other_member = next((m for m in all_members if m["name"] == other_name), None)
        other_weight = other_member.get("weight", 1.0) if other_member else 1.0
        combined_weight = weight * other_weight
        aspect_count = conn.get("aspect_count", 0)
        
        if conn["relation_type"] == "harmony":
            aspect_bonus = aspect_count * 0.3 * combined_weight
            role_scores["glue"] += aspect_bonus
            role_scores["visionary"] += aspect_bonus * 0.5
        elif conn["relation_type"] == "conflict":
            aspect_bonus = aspect_count * 0.4 * combined_weight
            role_scores["firecracker"] += aspect_bonus
        else:
            aspect_bonus = aspect_count * 0.1 * combined_weight
            role_scores["glue"] += aspect_bonus
            role_scores["visionary"] += aspect_bonus
    
    if is_core:
        for role in role_scores:
            role_scores[role] *= 1.5
    
    total_score = sum(role_scores.values())
    if total_score > 0:
        for role in role_scores:
            role_scores[role] = round(role_scores[role], 3)
    
    scores_list = list(role_scores.values())
    max_score = max(scores_list) if scores_list else 0
    min_score = min(scores_list) if scores_list else 0
    
    score_range = max_score - min_score
    if score_range < 2.0 and max_score > 0:
        for role in role_scores:
            if role_scores[role] == max_score:
                role_scores[role] += 2.0
            else:
                role_scores[role] -= 0.5
    
    max_score = max(role_scores.values()) if role_scores else 0
    if max_score == 0:
        primary_role = "glue"
    else:
        primary_role = max(role_scores, key=role_scores.get)
    
    role_def = ROLE_DEFINITIONS[primary_role]
    
    return {
        "name": name,
        "role": primary_role,
        "role_name": role_def["name"],
        "role_description": role_def["description"],
        "role_icon": role_def["icon"],
        "role_color": role_def["color"],
        "scores": role_scores,
        "score_ratios": {
            "glue": round(role_scores["glue"] / max(1, max_score), 2),
            "firecracker": round(role_scores["firecracker"] / max(1, max_score), 2),
            "visionary": round(role_scores["visionary"] / max(1, max_score), 2)
        },
        "is_core": is_core,
        "weight": weight,
        "member_index": member_index,
        "threejs_config": {
            "role": primary_role,
            "color": role_def["color"],
            "color_hex": int(role_def["color"].lstrip('#'), 16),
            "line_color": role_def["line_color"],
            "glow_color": role_def["color"],
            "glow_intensity": role_def["glow_intensity"],
            "threejs_color": role_def["threejs_color"],
            "threejs_emissive": role_def["threejs_emissive"],
            "is_core": is_core,
            "weight": weight,
            "emissive_intensity": 1.5 if is_core else 1.0,
            "scale": 1.15 if is_core else 1.0,
            "member_index": member_index
        }
    }


def generate_meeting_analysis(
    members: List[Dict[str, Any]],
    roles: List[Dict[str, Any]],
    harmony_pairs: List[Dict[str, Any]],
    conflict_pairs: List[Dict[str, Any]]
) -> Dict[str, Any]:
    suggestions = []
    conflict_points = []
    smooth_pairs = []
    
    visionary_roles = [r for r in roles if r["role"] == "visionary"]
    glue_roles = [r for r in roles if r["role"] == "glue"]
    firecracker_roles = [r for r in roles if r["role"] == "firecracker"]
    
    if visionary_roles:
        top_visionary = visionary_roles[0]
        suggestions.append({
            "type": "positive",
            "title": "会议主导者",
            "text": f"💡 {top_visionary['name']} 是天然的会议发起人，善于提出创意和方向。建议让TA负责开场和头脑风暴环节。",
            "person": top_visionary['name'],
            "action": "负责开场/头脑风暴"
        })
    else:
        suggestions.append({
            "type": "warning",
            "title": "缺乏方向感",
            "text": "⚠️ 团队中缺乏明显的愿景导师角色。建议指定专人负责制定会议议程，否则会议可能缺乏明确方向。",
            "action": "指定会议主持人"
        })
    
    if glue_roles:
        top_glue = glue_roles[0]
        suggestions.append({
            "type": "positive",
            "title": "意见协调者",
            "text": f"🤝 {top_glue['name']} 善于倾听和协调。当会议出现分歧时，TA可能是帮助大家达成共识的关键人物。",
            "person": top_glue['name'],
            "action": "协助调解分歧"
        })
    
    if firecracker_roles:
        top_firecracker = firecracker_roles[0]
        conflict_points.append({
            "type": "meeting",
            "title": "可能的挑战",
            "text": f"⚡ {top_firecracker['name']} 可能在会议中表现得比较直接或强势。建议：\n1. 先让其他人表达观点，再让TA发言\n2. 提醒注意表达方式，避免过于尖锐",
            "person": top_firecracker['name'],
            "risk_level": "medium"
        })
        suggestions.append({
            "type": "warning",
            "title": "沟通注意事项",
            "text": f"⚠️ {top_firecracker['name']} 可能直接表达不同意见。请团队保持开放心态，这其实也是帮助发现问题的机会。",
            "person": top_firecracker['name']
        })
    
    for hp in harmony_pairs[:2]:
        smooth_pairs.append({
            "pair": hp["pair"],
            "reason": f"两人有 {hp['aspect_count']} 个和谐相位，配合默契",
            "suggestion": "可以在会议中多配合，比如一起做汇报"
        })
        suggestions.append({
            "type": "positive",
            "title": "默契配对",
            "text": f"✨ {hp['pair'][0]} 和 {hp['pair'][1]} 配合默契，有 {hp['aspect_count']} 个和谐相位。建议让他们在会议中搭档合作。",
            "pair": hp["pair"]
        })
    
    for cp in conflict_pairs[:1]:
        conflict_points.append({
            "type": "pair",
            "title": "需要注意的组合",
            "text": f"🔥 {cp['pair'][0]} 和 {cp['pair'][1]} 有 {cp['aspect_count']} 个紧张相位。建议：\n1. 避免让他们在会议中直接对立\n2. 由第三方（如粘合剂角色）来协调",
            "pair": cp["pair"],
            "risk_level": "high"
        })
        suggestions.append({
            "type": "warning",
            "title": "潜在分歧点",
            "text": f"⚠️ {cp['pair'][0]} 和 {cp['pair'][1]} 可能在某些议题上有不同看法。建议提前沟通，或由主持人引导讨论节奏。",
            "pair": cp["pair"]
        })
    
    if len(visionary_roles) > 1:
        top2 = visionary_roles[:2]
        is_conflict = False
        for cp in conflict_pairs:
            if set(cp["pair"]) == set([top2[0]["name"], top2[1]["name"]]):
                is_conflict = True
                break
        
        if is_conflict:
            suggestions.append({
                "type": "warning",
                "title": "双重领导风险",
                "text": f"⚡ {top2[0]['name']} 和 {top2[1]['name']} 都有较强的主导倾向且关系紧张。建议明确分工，或让粘合剂角色协调。",
                "pair": [top2[0]['name'], top2[1]['name']]
            })
    
    if len(glue_roles) == 0 and firecracker_roles:
        suggestions.append({
            "type": "warning",
            "title": "缺乏调和者",
            "text": "⚠️ 团队中没有明显的粘合剂角色，但存在火药桶。建议：\n1. 制定明确的会议规则\n2. 每个人发言限时\n3. 主持人要主动调解",
            "action": "加强会议规则"
        })
    
    return {
        "suggestions": suggestions,
        "conflict_points": conflict_points,
        "smooth_pairs": smooth_pairs,
        "best_roles": {
            "leader": visionary_roles[0]["name"] if visionary_roles else None,
            "coordinator": glue_roles[0]["name"] if glue_roles else None,
            "challenger": firecracker_roles[0]["name"] if firecracker_roles else None
        }
    }


def generate_travel_analysis(
    members: List[Dict[str, Any]],
    roles: List[Dict[str, Any]],
    harmony_pairs: List[Dict[str, Any]],
    conflict_pairs: List[Dict[str, Any]]
) -> Dict[str, Any]:
    suggestions = []
    conflict_points = []
    smooth_pairs = []
    
    glue_roles = [r for r in roles if r["role"] == "glue"]
    visionary_roles = [r for r in roles if r["role"] == "visionary"]
    firecracker_roles = [r for r in roles if r["role"] == "firecracker"]
    
    if glue_roles:
        top_glue = glue_roles[0]
        suggestions.append({
            "type": "positive",
            "title": "旅行润滑剂",
            "text": f"🤝 {top_glue['name']} 是团队的粘合剂，善于照顾他人情绪。TA会是大家想家或疲惫时的精神支柱。",
            "person": top_glue['name'],
            "action": "关心团队情绪"
        })
    else:
        suggestions.append({
            "type": "warning",
            "title": "缺乏关怀者",
            "text": "⚠️ 团队中没有明显的粘合剂角色。建议大家多主动关心彼此，尤其是长途旅行中容易产生情绪波动。",
            "action": "互相提醒关心他人"
        })
    
    if visionary_roles:
        top_visionary = visionary_roles[0]
        suggestions.append({
            "type": "positive",
            "title": "行程策划者",
            "text": f"✨ {top_visionary['name']} 善于发现有趣的景点和体验。可以让TA负责探索当地特色活动，给大家带来惊喜。",
            "person": top_visionary['name'],
            "action": "探索特色活动"
        })
    
    if firecracker_roles:
        top_firecracker = firecracker_roles[0]
        conflict_points.append({
            "type": "travel",
            "title": "旅行中需要注意",
            "text": f"⚡ {top_firecracker['name']} 可能在以下情况表现出不耐烦：\n1. 行程延误\n2. 他人决策缓慢\n3. 计划被打乱\n\n建议提前明确行程安排，给TA一些自主权。",
            "person": top_firecracker['name'],
            "risk_level": "medium"
        })
        suggestions.append({
            "type": "warning",
            "title": "行程注意事项",
            "text": f"⚠️ {top_firecracker['name']} 可能对行程变化比较敏感。建议：\n1. 提前确认交通/住宿\n2. 留出自由活动时间\n3. 遇到变化时保持沟通",
            "person": top_firecracker['name']
        })
    
    for hp in harmony_pairs[:2]:
        smooth_pairs.append({
            "pair": hp["pair"],
            "reason": f"两人星盘和谐，旅行中会很合拍",
            "suggestion": "可以安排住一间房或一起活动"
        })
        suggestions.append({
            "type": "positive",
            "title": "最佳旅伴",
            "text": f"🏖️ {hp['pair'][0]} 和 {hp['pair'][1]} 星盘和谐，旅行中会很合拍！建议安排他们一起活动，可以提升整体体验。",
            "pair": hp["pair"]
        })
    
    for cp in conflict_pairs[:1]:
        conflict_points.append({
            "type": "pair",
            "title": "需要注意的组合",
            "text": f"🔥 {cp['pair'][0]} 和 {cp['pair'][1]} 星盘有紧张相位。旅行中可能在以下方面产生分歧：\n1. 消费观念\n2. 行程节奏\n3. 住宿选择\n\n建议让第三方安排这些事项。",
            "pair": cp["pair"],
            "risk_level": "high"
        })
        suggestions.append({
            "type": "warning",
            "title": "住宿建议",
            "text": f"⚠️ {cp['pair'][0]} 和 {cp['pair'][1]} 星盘有紧张相位。建议不要安排他们住同一间房，以免产生不必要的摩擦。",
            "pair": cp["pair"]
        })
    
    if firecracker_roles and len(firecracker_roles) > 1:
        suggestions.append({
            "type": "warning",
            "title": "多位火药桶",
            "text": "⚠️ 团队中有多位火药桶角色。建议：\n1. 行程安排要有弹性\n2. 决策前充分沟通\n3. 预留缓冲时间",
            "action": "增加行程弹性"
        })
    
    if visionary_roles and glue_roles:
        suggestions.append({
            "type": "positive",
            "title": "黄金组合",
            "text": f"🎉 团队同时有愿景导师({visionary_roles[0]['name']})和粘合剂({glue_roles[0]['name']})。前者负责发现好玩的，后者负责照顾大家情绪，这趟旅行会很精彩！",
            "action": "优势互补"
        })
    
    return {
        "suggestions": suggestions,
        "conflict_points": conflict_points,
        "smooth_pairs": smooth_pairs,
        "best_roles": {
            "planner": visionary_roles[0]["name"] if visionary_roles else None,
            "caretaker": glue_roles[0]["name"] if glue_roles else None,
            "needs_space": firecracker_roles[0]["name"] if firecracker_roles else None
        }
    }


def generate_project_analysis(
    members: List[Dict[str, Any]],
    roles: List[Dict[str, Any]],
    harmony_pairs: List[Dict[str, Any]],
    conflict_pairs: List[Dict[str, Any]]
) -> Dict[str, Any]:
    suggestions = []
    conflict_points = []
    smooth_pairs = []
    
    visionary_roles = [r for r in roles if r["role"] == "visionary"]
    firecracker_roles = [r for r in roles if r["role"] == "firecracker"]
    glue_roles = [r for r in roles if r["role"] == "glue"]
    
    if visionary_roles:
        top_visionary = visionary_roles[0]
        suggestions.append({
            "type": "positive",
            "title": "方向制定者",
            "text": f"🎯 {top_visionary['name']} 是项目的愿景导师，善于把握大方向和制定战略。适合担任产品经理/项目负责人角色。",
            "person": top_visionary['name'],
            "suggested_role": "项目负责人/产品经理"
        })
    else:
        suggestions.append({
            "type": "warning",
            "title": "缺乏战略思维",
            "text": "⚠️ 团队中没有明显的愿景导师。建议明确项目目标和方向，避免大家各自为政。",
            "action": "共同制定目标"
        })
    
    if firecracker_roles:
        top_firecracker = firecracker_roles[0]
        conflict_points.append({
            "type": "project",
            "title": "可利用的能量",
            "text": f"⚡ {top_firecracker['name']} 的火药桶特质在项目中可以转化为：\n1. 高执行力\n2. 敢于质疑\n3. 推动进展\n\n建议分配需要动力和决心的任务。",
            "person": top_firecracker['name'],
            "risk_level": "low"
        })
        suggestions.append({
            "type": "positive",
            "title": "执行推动者",
            "text": f"💪 {top_firecracker['name']} 的火星/土星能量可以转化为强大的执行力。适合分配需要推动和决断的任务，TA会是项目前进的引擎。",
            "person": top_firecracker['name'],
            "suggested_role": "执行推进者/质量控制"
        })
    else:
        suggestions.append({
            "type": "warning",
            "title": "缺乏推动力",
            "text": "⚠️ 团队中没有明显的火药桶角色。项目可能缺乏紧迫感，建议设定明确的里程碑和检查点。",
            "action": "加强进度管理"
        })
    
    if glue_roles:
        top_glue = glue_roles[0]
        suggestions.append({
            "type": "positive",
            "title": "团队凝聚者",
            "text": f"🤝 {top_glue['name']} 是团队的粘合剂。当项目遇到困难或士气低落时，TA能帮助团队保持团结。适合做团队协调或客户沟通。",
            "person": top_glue['name'],
            "suggested_role": "团队协调/客户沟通"
        })
    
    for hp in harmony_pairs[:2]:
        smooth_pairs.append({
            "pair": hp["pair"],
            "reason": f"配合默契，有 {hp['aspect_count']} 个和谐相位",
            "suggestion": "可以组成核心开发/设计搭档"
        })
        suggestions.append({
            "type": "positive",
            "title": "黄金搭档",
            "text": f"👥 {hp['pair'][0]} 和 {hp['pair'][1]} 配合默契，有 {hp['aspect_count']} 个和谐相位。强烈建议让他们组成核心搭档，会大幅提升协作效率！",
            "pair": hp["pair"],
            "suggested_action": "组成核心搭档"
        })
    
    for cp in conflict_pairs[:1]:
        conflict_points.append({
            "type": "pair",
            "title": "需要注意的组合",
            "text": f"🔥 {cp['pair'][0]} 和 {cp['pair'][1]} 有 {cp['aspect_count']} 个紧张相位。工作中可能在以下方面产生冲突：\n1. 技术方案选择\n2. 优先级判断\n3. 工作风格\n\n建议：\n1. 明确分工，减少直接协作\n2. 由第三方做决策\n3. 建立清晰的沟通规范",
            "pair": cp["pair"],
            "risk_level": "high"
        })
        suggestions.append({
            "type": "warning",
            "title": "分工建议",
            "text": f"⚠️ {cp['pair'][0]} 和 {cp['pair'][1]} 星盘有紧张相位。建议：\n1. 不要让他们共同负责同一模块\n2. 分开在前端/后端或产品/技术等不同方向\n3. 定期同步但减少日常协作",
            "pair": cp["pair"]
        })
    
    if firecracker_roles and glue_roles:
        suggestions.append({
            "type": "positive",
            "title": "完美互补",
            "text": f"🎯 团队同时有火药桶({firecracker_roles[0]['name']})和粘合剂({glue_roles[0]['name']})。前者推动进度，后者维护关系，这是高效团队的黄金组合！",
            "action": "优势互补"
        })
    
    if visionary_roles and firecracker_roles:
        suggestions.append({
            "type": "positive",
            "title": "战略+执行",
            "text": f"🚀 {visionary_roles[0]['name']} 定方向，{firecracker_roles[0]['name']} 推执行。建议让他们多沟通但分工明确：愿景导师负责「做什么」，火药桶负责「怎么做」。",
            "pair": [visionary_roles[0]['name'], firecracker_roles[0]['name']]
        })
    
    if len(visionary_roles) > 1 and conflict_pairs:
        for v1 in visionary_roles:
            for v2 in visionary_roles:
                if v1["name"] < v2["name"]:
                    for cp in conflict_pairs:
                        if set(cp["pair"]) == set([v1["name"], v2["name"]]):
                            suggestions.append({
                                "type": "warning",
                                "title": "方向冲突风险",
                                "text": f"⚠️ {v1['name']} 和 {v2['name']} 都是愿景导师但关系紧张。可能在项目方向上产生分歧。建议：\n1. 明确最终决策人\n2. 分开负责不同模块\n3. 定期对齐目标",
                                "pair": [v1['name'], v2['name']]
                            })
    
    return {
        "suggestions": suggestions,
        "conflict_points": conflict_points,
        "smooth_pairs": smooth_pairs,
        "best_roles": {
            "strategist": visionary_roles[0]["name"] if visionary_roles else None,
            "executor": firecracker_roles[0]["name"] if firecracker_roles else None,
            "coordinator": glue_roles[0]["name"] if glue_roles else None
        },
        "recommended_structure": {
            "vision": visionary_roles[0]["name"] if visionary_roles else "共同决定",
            "execution": firecracker_roles[0]["name"] if firecracker_roles else "轮流负责",
            "communication": glue_roles[0]["name"] if glue_roles else "集体沟通"
        }
    }


def simulate_scenario(
    scenario_type: str,
    members: List[Dict[str, Any]],
    roles: List[Dict[str, Any]],
    matrix: Dict[str, Any]
) -> Dict[str, Any]:
    scenario = SCENARIO_DEFINITIONS.get(scenario_type, SCENARIO_DEFINITIONS["meeting"])
    
    name_to_role = {r["name"]: r for r in roles}
    name_to_member = {m["name"]: m for m in members}
    
    dominant_persons = []
    cooperative_persons = []
    conflict_persons_list = []
    
    for role in roles:
        name = role["name"]
        member = name_to_member.get(name, {})
        is_core = member.get("is_core", False)
        weight = member.get("weight", 1.0)
        
        role_score = role["scores"].get(role["role"], 0)
        
        if role["role"] == "visionary":
            dominant_persons.append({
                "name": name,
                "role": role["role_name"],
                "role_type": role["role"],
                "reason": f"{role['role_icon']} 作为愿景导师，善于提出方向和创意",
                "influence": 3 if is_core else 2,
                "weight": weight,
                "score": role_score,
                "role_color": role["role_color"],
                "threejs_config": role.get("threejs_config", {})
            })
        elif role["role"] == "glue":
            cooperative_persons.append({
                "name": name,
                "role": role["role_name"],
                "role_type": role["role"],
                "reason": f"{role['role_icon']} 作为粘合剂，善于协调和促进合作",
                "influence": 3 if is_core else 2,
                "weight": weight,
                "score": role_score,
                "role_color": role["role_color"],
                "threejs_config": role.get("threejs_config", {})
            })
        elif role["role"] == "firecracker":
            conflict_persons_list.append({
                "name": name,
                "role": role["role_name"],
                "role_type": role["role"],
                "reason": f"{role['role_icon']} 作为火药桶，可能带来挑战和冲突",
                "influence": 2 if is_core else 1,
                "weight": weight,
                "score": role_score,
                "role_color": role["role_color"],
                "threejs_config": role.get("threejs_config", {})
            })
    
    dominant_persons.sort(key=lambda x: (-x["influence"], -x["score"]))
    cooperative_persons.sort(key=lambda x: (-x["influence"], -x["score"]))
    conflict_persons_list.sort(key=lambda x: (-x["influence"], -x["score"]))
    
    harmony_pairs = []
    conflict_pairs = []
    
    for pair in matrix["pairs"]:
        if pair["summary"]["relation_type"] == "harmony":
            harmony_pairs.append({
                "pair": pair["pair"],
                "aspect_count": pair["summary"]["harmonious"],
                "total_aspects": pair["summary"]["total"],
                "description": "关系和谐，容易达成共识",
                "threejs_config": pair.get("threejs_config", {})
            })
        elif pair["summary"]["relation_type"] == "conflict":
            conflict_pairs.append({
                "pair": pair["pair"],
                "aspect_count": pair["summary"]["challenging"],
                "total_aspects": pair["summary"]["total"],
                "description": "存在张力，需要注意沟通",
                "threejs_config": pair.get("threejs_config", {})
            })
    
    harmony_pairs.sort(key=lambda x: -x["aspect_count"])
    conflict_pairs.sort(key=lambda x: -x["aspect_count"])
    
    overall_vibe = "neutral"
    vibe_score = 50
    
    total_harmony_score = sum(p["summary"]["harmony_score"] for p in matrix["pairs"])
    total_conflict_score = sum(p["summary"]["conflict_score"] for p in matrix["pairs"])
    
    if total_harmony_score + total_conflict_score > 0:
        vibe_ratio = total_harmony_score / (total_harmony_score + total_conflict_score)
        vibe_score = int(vibe_ratio * 100)
        
        if vibe_score >= 70:
            overall_vibe = "harmonious"
        elif vibe_score <= 40:
            overall_vibe = "tense"
        else:
            overall_vibe = "balanced"
    
    scenario_analysis = {}
    
    if scenario_type == "meeting":
        scenario_analysis = generate_meeting_analysis(
            members, roles, harmony_pairs, conflict_pairs
        )
    elif scenario_type == "travel":
        scenario_analysis = generate_travel_analysis(
            members, roles, harmony_pairs, conflict_pairs
        )
    elif scenario_type == "project":
        scenario_analysis = generate_project_analysis(
            members, roles, harmony_pairs, conflict_pairs
        )
    else:
        scenario_analysis = {
            "suggestions": [],
            "conflict_points": [],
            "smooth_pairs": [],
            "best_roles": {}
        }
    
    return {
        "scenario": scenario_type,
        "scenario_name": scenario["name"],
        "scenario_description": scenario["description"],
        "scenario_icon": scenario["icon"],
        "theme_color": scenario["theme_color"],
        "overall_vibe": overall_vibe,
        "vibe_score": vibe_score,
        "dominant_persons": dominant_persons,
        "cooperative_persons": cooperative_persons,
        "conflict_persons": conflict_persons_list,
        "harmony_pairs": harmony_pairs,
        "conflict_pairs": conflict_pairs,
        "suggestions": scenario_analysis.get("suggestions", []),
        "conflict_points": scenario_analysis.get("conflict_points", []),
        "smooth_pairs": scenario_analysis.get("smooth_pairs", []),
        "best_roles": scenario_analysis.get("best_roles", {}),
        "recommended_structure": scenario_analysis.get("recommended_structure", {}),
        "threejs_config": {
            "vibe_type": overall_vibe,
            "vibe_score": vibe_score,
            "dominant_names": [p["name"] for p in dominant_persons],
            "cooperative_names": [p["name"] for p in cooperative_persons],
            "conflict_names": [p["name"] for p in conflict_persons_list],
            "theme_color": scenario["theme_color"],
            "highlight_indices": {
                "dominant": [members.index(m) for m in members if m["name"] in [p["name"] for p in dominant_persons[:1]]],
                "cooperative": [members.index(m) for m in members if m["name"] in [p["name"] for p in cooperative_persons[:1]]],
                "conflict": [members.index(m) for m in members if m["name"] in [p["name"] for p in conflict_persons_list[:1]]]
            }
        }
    }


def generate_topology_data(
    members: List[Dict[str, Any]],
    roles: List[Dict[str, Any]],
    matrix: Dict[str, Any]
) -> Dict[str, Any]:
    n = len(members)
    
    topo_positions = generate_topo_positions(n, radius=180.0)
    threejs_positions = generate_3d_positions(n, radius=5.0)
    
    nodes = []
    for i, member in enumerate(members):
        role = next((r for r in roles if r["name"] == member["name"]), None)
        stats = matrix["member_stats"].get(member["name"], {})
        
        node = {
            "name": member["name"],
            "index": i,
            "is_core": member.get("is_core", False),
            "weight": member.get("weight", 1.0),
            "role": role["role"] if role else None,
            "role_name": role["role_name"] if role else None,
            "role_icon": role["role_icon"] if role else None,
            "role_color": role["role_color"] if role else "#64748b",
            "topo_position": topo_positions[i],
            "threejs_position": threejs_positions[i],
            "stats": {
                "total_aspects": stats.get("total_aspects", 0),
                "harmonious": stats.get("harmonious_aspects", 0),
                "challenging": stats.get("challenging_aspects", 0),
                "neutral": stats.get("neutral_aspects", 0)
            },
            "threejs_config": role.get("threejs_config", {}) if role else {},
            "connections": stats.get("connections", [])
        }
        nodes.append(node)
    
    links = []
    for pair in matrix["pairs"]:
        name_a, name_b = pair["pair"]
        node_a = next((n for n in nodes if n["name"] == name_a), None)
        node_b = next((n for n in nodes if n["name"] == name_b), None)
        
        if node_a and node_b:
            link = {
                "source": node_a["index"],
                "target": node_b["index"],
                "source_name": name_a,
                "target_name": name_b,
                "relation_type": pair["summary"]["relation_type"],
                "aspects": pair["aspects"],
                "summary": pair["summary"],
                "threejs_config": pair.get("threejs_config", {}),
                "is_strong": pair["summary"]["total"] >= 3
            }
            links.append(link)
    
    harmony_count = sum(1 for l in links if l["relation_type"] == "harmony")
    conflict_count = sum(1 for l in links if l["relation_type"] == "conflict")
    neutral_count = sum(1 for l in links if l["relation_type"] == "neutral")
    
    team_energy = {
        "total_connections": len(links),
        "harmony_ratio": round(harmony_count / max(1, len(links)), 2),
        "conflict_ratio": round(conflict_count / max(1, len(links)), 2),
        "neutral_ratio": round(neutral_count / max(1, len(links)), 2),
        "dominant_role": max(roles, key=lambda x: x["scores"][x["role"]])["role"] if roles else None,
        "has_core": any(m.get("is_core", False) for m in members),
        "core_count": sum(1 for m in members if m.get("is_core", False))
    }
    
    if team_energy["conflict_ratio"] > 0.4:
        team_energy["energy_type"] = "turbulent"
        team_energy["energy_label"] = "紧张型团队"
        team_energy["energy_color"] = "#ef4444"
    elif team_energy["harmony_ratio"] > 0.6:
        team_energy["energy_type"] = "harmonious"
        team_energy["energy_label"] = "和谐型团队"
        team_energy["energy_color"] = "#22c55e"
    else:
        team_energy["energy_type"] = "balanced"
        team_energy["energy_label"] = "平衡型团队"
        team_energy["energy_color"] = "#8b5cf6"
    
    return {
        "nodes": nodes,
        "links": links,
        "team_energy": team_energy,
        "config": {
            "topo_radius": 180.0,
            "threejs_radius": 5.0,
            "colors": TOPOLOGY_COLORS,
            "role_definitions": ROLE_DEFINITIONS,
            "relation_types": RELATION_TYPE_CONFIG
        }
    }


def calculate_group_matrix(
    group_name: str,
    members: List[Dict[str, Any]],
    group_type: str = "other",
    description: str = ""
) -> Dict[str, Any]:
    try:
        if len(members) < 2:
            raise ValueError("至少需要2个成员才能计算关系矩阵")
        
        charts = {}
        for member in members:
            name = member.get("name", "")
            if not name:
                raise ValueError("成员必须有姓名")
            
            try:
                chart = calculate_member_chart(member)
                charts[name] = chart
            except Exception as e:
                logger.error(f"计算 {name} 的星盘失败: {e}")
                raise ValueError(f"计算 {name} 的星盘失败: {str(e)}")
        
        matrix = calculate_relationship_matrix(members, charts)
        
        roles = []
        for i, member in enumerate(members):
            name = member.get("name", "")
            chart = charts.get(name)
            if chart:
                try:
                    role = calculate_member_roles(member, chart, matrix, members, i)
                    roles.append(role)
                except Exception as e:
                    logger.error(f"计算 {name} 的角色失败: {e}")
                    raise ValueError(f"计算 {name} 的角色失败: {str(e)}")
        
        scenarios = {}
        for scenario_type in SCENARIO_DEFINITIONS.keys():
            try:
                simulation = simulate_scenario(scenario_type, members, roles, matrix)
                scenarios[scenario_type] = simulation
            except Exception as e:
                logger.error(f"模拟场景 {scenario_type} 失败: {e}")
                scenarios[scenario_type] = {
                    "error": str(e), 
                    "scenario": scenario_type,
                    "scenario_name": SCENARIO_DEFINITIONS.get(scenario_type, {}).get("name", scenario_type),
                    "scenario_description": SCENARIO_DEFINITIONS.get(scenario_type, {}).get("description", ""),
                    "dominant_persons": [],
                    "cooperative_persons": [],
                    "conflict_persons": [],
                    "harmony_pairs": [],
                    "conflict_pairs": [],
                    "suggestions": []
                }
        
        topology = generate_topology_data(members, roles, matrix)
        
        members_with_charts = []
        for member in members:
            name = member.get("name", "")
            chart = charts.get(name)
            role = next((r for r in roles if r.get("name") == name), None)
            
            member_data = {
                **member,
                "chart": chart,
                "role": role
            }
            members_with_charts.append(member_data)
        
        result = {
            "group_name": group_name,
            "group_type": group_type,
            "description": description,
            "calculated_at": datetime.utcnow().isoformat(),
            "members_count": len(members),
            "members": members_with_charts,
            "roles": roles,
            "matrix": matrix,
            "scenarios": scenarios,
            "topology": topology,
            "threejs_global_config": {
                "role_definitions": ROLE_DEFINITIONS,
                "relation_type_config": RELATION_TYPE_CONFIG,
                "main_planets": MAIN_PLANETS,
                "topology_colors": TOPOLOGY_COLORS
            }
        }
        
        logger.info(f"群组矩阵计算成功: {group_name}, 成员数: {len(members)}")
        return result
        
    except ValueError as ve:
        logger.error(f"群组矩阵计算参数错误: {ve}")
        raise
    except Exception as e:
        logger.error(f"群组矩阵计算失败: {e}")
        raise ValueError(f"群组矩阵计算失败: {str(e)}")
