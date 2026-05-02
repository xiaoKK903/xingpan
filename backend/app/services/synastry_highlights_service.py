from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging
import json
import random
import hashlib

from app.synastry import SYNASTRY_ASPECT_TYPES
from app.synastry_analysis import generate_aspect_interpretation

logger = logging.getLogger(__name__)

HIGHLIGHT_CATEGORIES = {
    "soulmate_connection": {
        "name": "灵魂共鸣",
        "icon": "💫",
        "key_aspects": [("太阳", "月亮"), ("月亮", "月亮"), ("金星", "冥王星")],
        "description": "存在深层的灵魂连接和情感共鸣"
    },
    "passion_chemistry": {
        "name": "激情火花",
        "icon": "🔥",
        "key_aspects": [("金星", "火星"), ("火星", "太阳"), ("太阳", "火星")],
        "description": "强烈的性吸引力和化学反应"
    },
    "emotional_harmony": {
        "name": "情感和谐",
        "icon": "💕",
        "key_aspects": [("月亮", "金星"), ("太阳", "金星"), ("月亮", "月亮")],
        "description": "情感表达自然流畅，相互理解"
    },
    "communication_synergy": {
        "name": "思维契合",
        "icon": "🧠",
        "key_aspects": [("水星", "水星"), ("水星", "金星"), ("太阳", "水星")],
        "description": "沟通顺畅，思维方式相似"
    },
    "long_term_stability": {
        "name": "长久稳定",
        "icon": "🏔️",
        "key_aspects": [("土星", "太阳"), ("土星", "月亮"), ("土星", "金星")],
        "description": "土星相位带来稳定感和责任感"
    },
    "creative_inspiration": {
        "name": "创作共鸣",
        "icon": "🎨",
        "key_aspects": [("海王星", "太阳"), ("海王星", "金星"), ("木星", "太阳")],
        "description": "艺术和想象力的共鸣"
    },
    "growth_challenge": {
        "name": "成长张力",
        "icon": "🌱",
        "key_aspects": [("冥王星", "金星"), ("冥王星", "太阳"), ("土星", "火星")],
        "description": "挑战相位带来深刻的成长潜力"
    },
    "freedom_vs_commitment": {
        "name": "自由与承诺",
        "icon": "🦅",
        "key_aspects": [("天王星", "金星"), ("天王星", "月亮"), ("天王星", "太阳")],
        "description": "需要在自由和承诺之间寻找平衡"
    }
}

SPECIAL_ASPECT_COMBINATIONS = {
    "golden_trio": {
        "name": "黄金三角",
        "description": "太阳、月亮、金星形成完美和谐相位",
        "aspects_needed": [
            ("太阳", "月亮", "harmonious"),
            ("太阳", "金星", "harmonious"),
            ("月亮", "金星", "harmonious")
        ]
    },
    "passion_storm": {
        "name": "激情风暴",
        "description": "火星与金星、冥王星形成强烈相位",
        "aspects_needed": [
            ("金星", "火星", "any"),
            ("火星", "冥王星", "any")
        ]
    },
    "karmic_link": {
        "name": "业力连接",
        "description": "土星与个人行星形成重要相位",
        "aspects_needed": [
            ("土星", "太阳", "any"),
            ("土星", "月亮", "any")
        ]
    }
}


def extract_synastry_highlights(synastry_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    提取合盘亮点分析
    
    Args:
        synastry_data: 合盘计算结果
        
    Returns:
        包含亮点分析的字典
    """
    aspects = synastry_data.get("synastry", {}).get("aspects", [])
    aspect_summary = synastry_data.get("synastry", {}).get("aspect_summary", {})
    
    highlights = []
    special_indicators = []
    key_phase_pairs = []
    
    person_a = synastry_data.get("person_a", {})
    person_b = synastry_data.get("person_b", {})
    
    chart_a = person_a.get("chart", {})
    chart_b = person_b.get("chart", {})
    
    category_scores = {}
    
    for category_key, category_info in HIGHLIGHT_CATEGORIES.items():
        matched_aspects = []
        score = 0
        
        for aspect in aspects:
            planet_a = aspect.get("planet_a", "")
            planet_b = aspect.get("planet_b", "")
            nature = aspect.get("nature", "neutral")
            
            for key_pair in category_info["key_aspects"]:
                if (planet_a == key_pair[0] and planet_b == key_pair[1]) or \
                   (planet_a == key_pair[1] and planet_b == key_pair[0]):
                    
                    base_score = 0
                    if nature == "harmonious":
                        base_score = 30
                    elif nature == "challenging":
                        base_score = 20
                    else:
                        base_score = 15
                    
                    orb = aspect.get("orb_arcminutes", 0)
                    if orb <= 2:
                        base_score *= 1.5
                    elif orb <= 4:
                        base_score *= 1.3
                    
                    score += base_score
                    
                    interpretation = generate_aspect_interpretation(
                        planet_a, planet_b, aspect.get("aspect", ""), nature
                    )
                    
                    matched_aspects.append({
                        "planet_a": planet_a,
                        "planet_b": planet_b,
                        "aspect": aspect.get("aspect", ""),
                        "aspect_symbol": aspect.get("aspect_symbol", ""),
                        "nature": nature,
                        "orb_arcminutes": orb,
                        "interpretation": interpretation
                    })
                    key_phase_pairs.append((planet_a, planet_b, aspect.get("aspect", ""), nature))
        
        category_scores[category_key] = score
        
        if score >= 25:
            highlights.append({
                "category": category_key,
                "name": category_info["name"],
                "icon": category_info["icon"],
                "description": category_info["description"],
                "score": round(score),
                "strength": get_strength_level(score),
                "matched_aspects": matched_aspects[:3]
            })
    
    highlights.sort(key=lambda x: x["score"], reverse=True)
    
    for combo_key, combo_info in SPECIAL_ASPECT_COMBINATIONS.items():
        matched = check_aspect_combination(key_phase_pairs, combo_info["aspects_needed"])
        if matched:
            special_indicators.append({
                "key": combo_key,
                "name": combo_info["name"],
                "description": combo_info["description"],
                "icon": get_combination_icon(combo_key)
            })
    
    element_analysis = analyze_element_compatibility(chart_a, chart_b)
    
    total_aspects = aspect_summary.get("total", 0)
    harmonious = aspect_summary.get("harmonious", 0)
    challenging = aspect_summary.get("challenging", 0)
    
    harmony_ratio = harmonious / total_aspects if total_aspects > 0 else 0.5
    
    overall_theme = determine_overall_theme(harmony_ratio, highlights, special_indicators)
    
    return {
        "highlights": highlights[:5],
        "special_indicators": special_indicators,
        "element_analysis": element_analysis,
        "overall_theme": overall_theme,
        "aspect_stats": {
            "total": total_aspects,
            "harmonious": harmonious,
            "challenging": challenging,
            "harmony_ratio": round(harmony_ratio * 100)
        },
        "generated_at": datetime.utcnow().isoformat()
    }


def get_strength_level(score: float) -> str:
    if score >= 60:
        return "very_strong"
    elif score >= 40:
        return "strong"
    elif score >= 25:
        return "moderate"
    else:
        return "weak"


def get_combination_icon(combo_key: str) -> str:
    icons = {
        "golden_trio": "👑",
        "passion_storm": "🌊",
        "karmic_link": "⚖️"
    }
    return icons.get(combo_key, "✨")


def check_aspect_combination(
    phase_pairs: List[Tuple],
    required_aspects: List[Tuple]
) -> bool:
    """
    检查是否存在特定的相位组合
    """
    matched_count = 0
    
    for req in required_aspects:
        req_p1, req_p2, req_nature = req
        
        for pair in phase_pairs:
            p1, p2, aspect, nature = pair
            
            planets_match = (p1 == req_p1 and p2 == req_p2) or (p1 == req_p2 and p2 == req_p1)
            
            nature_match = req_nature == "any" or nature == req_nature
            
            if planets_match and nature_match:
                matched_count += 1
                break
    
    return matched_count >= len(required_aspects)


def analyze_element_compatibility(chart_a: Dict, chart_b: Dict) -> Dict[str, Any]:
    """
    分析元素兼容性
    """
    element_map = {
        "白羊座": "fire", "狮子座": "fire", "射手座": "fire",
        "金牛座": "earth", "处女座": "earth", "摩羯座": "earth",
        "双子座": "air", "天秤座": "air", "水瓶座": "air",
        "巨蟹座": "water", "天蝎座": "water", "双鱼座": "water"
    }
    
    element_names = {
        "fire": {"name": "火象", "symbol": "🔥", "trait": "热情、主动、充满活力"},
        "earth": {"name": "土象", "symbol": "🪨", "trait": "稳重、务实、追求稳定"},
        "air": {"name": "风象", "symbol": "💨", "trait": "灵活、善于沟通、追求变化"},
        "water": {"name": "水象", "symbol": "💧", "trait": "敏感、情感丰富、直觉强"}
    }
    
    sun_a = chart_a.get("sun_sign", {}).get("sign", "")
    sun_b = chart_b.get("sun_sign", {}).get("sign", "")
    
    moon_a = chart_a.get("moon_sign", {}).get("sign", "")
    moon_b = chart_b.get("moon_sign", {}).get("sign", "")
    
    elem_a = element_map.get(sun_a, "fire")
    elem_b = element_map.get(sun_b, "fire")
    
    compatibility_matrix = {
        "fire": {"fire": 75, "earth": 55, "air": 90, "water": 45},
        "earth": {"fire": 55, "earth": 80, "air": 50, "water": 85},
        "air": {"fire": 90, "earth": 50, "air": 70, "water": 40},
        "water": {"fire": 45, "earth": 85, "air": 40, "water": 75}
    }
    
    score = compatibility_matrix.get(elem_a, {}).get(elem_b, 50)
    
    element_relationship = determine_element_relationship(elem_a, elem_b)
    
    return {
        "person_a": {
            "sun_sign": sun_a,
            "moon_sign": moon_a,
            "element": elem_a,
            "element_info": element_names.get(elem_a, {})
        },
        "person_b": {
            "sun_sign": sun_b,
            "moon_sign": moon_b,
            "element": elem_b,
            "element_info": element_names.get(elem_b, {})
        },
        "compatibility_score": score,
        "relationship": element_relationship,
        "description": generate_element_description(elem_a, elem_b, element_relationship)
    }


def determine_element_relationship(elem_a: str, elem_b: str) -> str:
    if elem_a == elem_b:
        return "same"
    elif (elem_a == "fire" and elem_b == "air") or (elem_a == "air" and elem_b == "fire"):
        return "compatible"
    elif (elem_a == "earth" and elem_b == "water") or (elem_a == "water" and elem_b == "earth"):
        return "compatible"
    elif (elem_a == "fire" and elem_b == "water") or (elem_a == "water" and elem_b == "fire"):
        return "challenging"
    elif (elem_a == "air" and elem_b == "earth") or (elem_a == "earth" and elem_b == "air"):
        return "challenging"
    else:
        return "neutral"


def generate_element_description(elem_a: str, elem_b: str, relationship: str) -> str:
    descriptions = {
        "same": {
            "fire": "双火象组合：热情四射，能够相互激发能量。但需要注意避免过于急躁和冲动。",
            "earth": "双土象组合：非常稳定可靠，能够建立坚实的关系基础。但可能缺乏变化和激情。",
            "air": "双风象组合：沟通顺畅，思想活跃。但可能缺乏深度和行动力。",
            "water": "双水象组合：情感深度极高，能够深刻理解彼此。但可能过于敏感和情绪化。"
        },
        "compatible": {
            "fire-air": "火与风的最佳组合：风象可以为火象提供想法，火象可以将想法付诸行动。这是充满活力和创造力的组合。",
            "earth-water": "土与水的最佳组合：土象可以给水象安全感，水象可以滋润土象的情感。这是稳定而充满滋养的组合。"
        },
        "challenging": {
            "fire-water": "火与水需要调和：火象的直接可能伤害水象的敏感。需要更多的温柔、理解和耐心。",
            "air-earth": "风与土需要平衡：土象的实际与风象的思维可能产生冲突。需要找到平衡点，尊重彼此的差异。"
        },
        "neutral": "你们的元素组合具有独特的化学反应，需要在相处中慢慢探索和理解。"
    }
    
    if relationship == "same":
        return descriptions["same"].get(elem_a, descriptions["neutral"])
    elif relationship == "compatible":
        key = f"{elem_a}-{elem_b}" if elem_a < elem_b else f"{elem_b}-{elem_a}"
        return descriptions["compatible"].get(key, descriptions["neutral"])
    elif relationship == "challenging":
        key = f"{elem_a}-{elem_b}" if elem_a < elem_b else f"{elem_b}-{elem_a}"
        return descriptions["challenging"].get(key, descriptions["neutral"])
    else:
        return descriptions["neutral"]


def determine_overall_theme(
    harmony_ratio: float,
    highlights: List[Dict],
    special_indicators: List[Dict]
) -> Dict[str, Any]:
    """
    确定整体关系主题
    """
    if harmony_ratio >= 0.7:
        theme_type = "harmonious"
        theme_name = "和谐型关系"
        description = "你们的关系以和谐为主，大多数时候能够顺畅沟通、相互理解。这种和谐让你们感到舒适和放松。"
    elif harmony_ratio >= 0.4:
        theme_type = "balanced"
        theme_name = "平衡型关系"
        description = "你们的关系既有和谐的时刻，也有需要磨合的地方。这种平衡是大多数关系的常态，也是成长的机会。"
    else:
        theme_type = "intense"
        theme_name = "张力型关系"
        description = "你们的关系充满张力和挑战。这些挑战虽然困难，但也是深度成长和转化的催化剂。"
    
    if any(h["category"] == "soulmate_connection" for h in highlights):
        theme_type = "soulmate"
        theme_name = "灵魂共鸣型"
        description = "存在深层的灵魂连接，可能有强烈的宿命感和默契。"
    elif any(h["category"] == "passion_chemistry" for h in highlights):
        theme_type = "passionate"
        theme_name = "激情火花型"
        description = "充满强烈的吸引力和化学反应，关系充满活力。"
    
    return {
        "type": theme_type,
        "name": theme_name,
        "description": description
    }


def generate_synastry_ai_prompt(
    highlights: Dict[str, Any],
    person_a_name: str = "人物A",
    person_b_name: str = "人物B"
) -> str:
    """
    生成用于AI文案的提示词
    """
    highlights_list = highlights.get("highlights", [])
    element_analysis = highlights.get("element_analysis", {})
    overall_theme = highlights.get("overall_theme", {})
    aspect_stats = highlights.get("aspect_stats", {})
    
    prompt_parts = [
        f"请为 {person_a_name} 和 {person_b_name} 的合盘写一段优美的中文文案。",
        "",
        "【合盘分析数据】",
        ""
    ]
    
    if overall_theme:
        prompt_parts.append(f"整体关系类型: {overall_theme.get('name', '')}")
        prompt_parts.append(f"关系描述: {overall_theme.get('description', '')}")
        prompt_parts.append("")
    
    if highlights_list:
        prompt_parts.append("【主要亮点】")
        for h in highlights_list:
            prompt_parts.append(f"- {h.get('icon', '')} {h.get('name', '')}: {h.get('description', '')}")
            
            aspects = h.get("matched_aspects", [])
            for aspect in aspects[:2]:
                prompt_parts.append(f"  - {aspect.get('planet_a', '')} {aspect.get('aspect_symbol', '')} {aspect.get('planet_b', '')}: {aspect.get('interpretation', '')[:100]}...")
        prompt_parts.append("")
    
    if element_analysis:
        elem_a = element_analysis.get("person_a", {})
        elem_b = element_analysis.get("person_b", {})
        prompt_parts.append("【元素分析】")
        prompt_parts.append(f"{person_a_name}: {elem_a.get('sun_sign', '')} ({elem_a.get('element_info', {}).get('name', '')})")
        prompt_parts.append(f"{person_b_name}: {elem_b.get('sun_sign', '')} ({elem_b.get('element_info', {}).get('name', '')})")
        prompt_parts.append(f"元素兼容性: {element_analysis.get('compatibility_score', 0)}%")
        prompt_parts.append(f"元素关系描述: {element_analysis.get('description', '')}")
        prompt_parts.append("")
    
    if aspect_stats:
        prompt_parts.append("【相位统计】")
        prompt_parts.append(f"总相位数: {aspect_stats.get('total', 0)}")
        prompt_parts.append(f"和谐相位: {aspect_stats.get('harmonious', 0)}")
        prompt_parts.append(f"挑战相位: {aspect_stats.get('challenging', 0)}")
        prompt_parts.append(f"和谐度比例: {aspect_stats.get('harmony_ratio', 50)}%")
        prompt_parts.append("")
    
    prompt_parts.extend([
        "【写作要求】",
        "1. 写一段优美的合盘分析文案，字数约300-500字",
        "2. 语气要温暖、积极、富有启发性",
        "3. 结合亮点分析，突出关系的独特之处",
        "4. 避免过于专业的术语，让普通用户能够理解",
        "5. 包含对关系的建议和展望",
        "6. 可以使用一些诗意的比喻，但不要过于玄乎",
        "",
        "请直接输出文案内容，不要添加任何其他说明。"
    ])
    
    return "\n".join(prompt_parts)


def generate_photocard_design(
    highlights: Dict[str, Any],
    person_a_name: str = "人物A",
    person_b_name: str = "人物B",
    card_type: str = "default"
) -> Dict[str, Any]:
    """
    生成限定合影卡牌设计数据
    
    Args:
        highlights: 合盘亮点数据
        person_a_name: 人物A名称
        person_b_name: 人物B名称
        card_type: 卡牌类型: default/soulmate/passionate/limited
    
    Returns:
        卡牌设计数据
    """
    overall_theme = highlights.get("overall_theme", {})
    highlights_list = highlights.get("highlights", [])
    element_analysis = highlights.get("element_analysis", {})
    
    themes = {
        "default": {
            "name": "星空相遇",
            "bg_gradient": "linear-gradient(135deg, #1a1a3e 0%, #2d1b69 50%, #4c1d95 100%)",
            "accent_color": "#8b5cf6",
            "decorations": ["✨", "⭐", "💫", "🌟"],
            "border_style": "cosmic"
        },
        "soulmate": {
            "name": "灵魂共鸣",
            "bg_gradient": "linear-gradient(135deg, #4c1d95 0%, #7c3aed 50%, #a78bfa 100%)",
            "accent_color": "#a78bfa",
            "decorations": ["💜", "💫", "✨", "🔮"],
            "border_style": "purple-glow"
        },
        "passionate": {
            "name": "激情火花",
            "bg_gradient": "linear-gradient(135deg, #7f1d1d 0%, #dc2626 50%, #f97316 100%)",
            "accent_color": "#f97316",
            "decorations": ["🔥", "❤️", "💥", "⚡"],
            "border_style": "fiery"
        },
        "limited": {
            "name": "限定珍藏",
            "bg_gradient": "linear-gradient(135deg, #1e3a5f 0%, #0f172a 50%, #1e1b4b 100%)",
            "accent_color": "#fbbf24",
            "decorations": ["👑", "💎", "🏆", "✨"],
            "border_style": "golden"
        }
    }
    
    theme = overall_theme.get("type", "default")
    if theme in ["soulmate", "harmonious"]:
        card_theme = themes["soulmate"]
    elif theme in ["intense", "passionate"]:
        card_theme = themes["passionate"]
    elif card_type == "limited":
        card_theme = themes["limited"]
    else:
        card_theme = themes["default"]
    
    primary_highlight = highlights_list[0] if highlights_list else None
    
    card_id = generate_card_id(person_a_name, person_b_name)
    
    return {
        "card_id": card_id,
        "card_type": card_type,
        "theme_name": card_theme["name"],
        "design": {
            "background": card_theme["bg_gradient"],
            "accent_color": card_theme["accent_color"],
            "decorations": card_theme["decorations"],
            "border_style": card_theme["border_style"]
        },
        "content": {
            "persons": {
                "person_a": {
                    "name": person_a_name,
                    "sun_sign": element_analysis.get("person_a", {}).get("sun_sign", ""),
                    "element": element_analysis.get("person_a", {}).get("element_info", {}).get("name", "")
                },
                "person_b": {
                    "name": person_b_name,
                    "sun_sign": element_analysis.get("person_b", {}).get("sun_sign", ""),
                    "element": element_analysis.get("person_b", {}).get("element_info", {}).get("name", "")
                }
            },
            "overall_theme": overall_theme.get("name", ""),
            "primary_highlight": {
                "icon": primary_highlight.get("icon", "✨") if primary_highlight else "✨",
                "name": primary_highlight.get("name", "缘分天定") if primary_highlight else "缘分天定",
                "description": primary_highlight.get("description", "") if primary_highlight else ""
            } if primary_highlight else None,
            "compatibility_score": highlights.get("aspect_stats", {}).get("harmony_ratio", 50),
            "generated_at": datetime.utcnow().isoformat()
        },
        "limited_edition": card_type == "limited",
        "rarity": determine_rarity(highlights)
    }


def generate_card_id(name_a: str, name_b: str) -> str:
    """生成唯一卡牌ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    combined = f"{name_a}_{name_b}_{timestamp}"
    hash_obj = hashlib.md5(combined.encode())
    return f"SC_{hash_obj.hexdigest()[:8].upper()}"


def determine_rarity(highlights: Dict[str, Any]) -> str:
    """根据亮点分析确定卡牌稀有度"""
    highlights_list = highlights.get("highlights", [])
    special_indicators = highlights.get("special_indicators", [])
    
    total_score = sum(h.get("score", 0) for h in highlights_list)
    special_count = len(special_indicators)
    
    if special_count >= 2 or total_score >= 200:
        return "legendary"
    elif special_count >= 1 or total_score >= 150:
        return "epic"
    elif total_score >= 100:
        return "rare"
    else:
        return "common"


def generate_emotional_value_analysis(
    synastry_data: Dict[str, Any],
    highlights: Dict[str, Any]
) -> Dict[str, Any]:
    """
    生成情绪价值分析（用于人脉链推荐）
    
    Args:
        synastry_data: 合盘数据
        highlights: 亮点分析
    
    Returns:
        情绪价值分析数据
    """
    aspects = synastry_data.get("synastry", {}).get("aspects", [])
    highlights_list = highlights.get("highlights", [])
    
    emotional_aspects = {
        "understanding": {
            "name": "情感理解",
            "icon": "🤝",
            "key_planets": ["月亮", "金星"],
            "aspects": []
        },
        "support": {
            "name": "情绪支持",
            "icon": "💪",
            "key_planets": ["太阳", "月亮", "土星"],
            "aspects": []
        },
        "communication": {
            "name": "情绪表达",
            "icon": "💬",
            "key_planets": ["水星", "月亮", "金星"],
            "aspects": []
        },
        "stability": {
            "name": "情绪稳定",
            "icon": "🏔️",
            "key_planets": ["土星", "月亮", "太阳"],
            "aspects": []
        },
        "passion": {
            "name": "激情共鸣",
            "icon": "🔥",
            "key_planets": ["火星", "金星", "太阳"],
            "aspects": []
        }
    }
    
    for aspect in aspects:
        planet_a = aspect.get("planet_a", "")
        planet_b = aspect.get("planet_b", "")
        nature = aspect.get("nature", "neutral")
        
        for emo_key, emo_data in emotional_aspects.items():
            key_planets = emo_data["key_planets"]
            if (planet_a in key_planets and planet_b in key_planets) or \
               (planet_a in key_planets) or (planet_b in key_planets):
                
                base_score = 0
                if nature == "harmonious":
                    base_score = 25
                elif nature == "challenging":
                    base_score = 15
                else:
                    base_score = 10
                
                orb = aspect.get("orb_arcminutes", 0)
                if orb <= 2:
                    base_score *= 1.3
                elif orb <= 4:
                    base_score *= 1.1
                
                emo_data["aspects"].append({
                    "score": base_score,
                    "nature": nature,
                    "aspect": aspect
                })
    
    emotional_scores = {}
    for emo_key, emo_data in emotional_aspects.items():
        total_score = sum(a["score"] for a in emo_data["aspects"])
        
        if total_score >= 50:
            level = "high"
        elif total_score >= 30:
            level = "medium"
        else:
            level = "low"
        
        percentage = min(100, max(0, int(total_score * 2)))
        
        emotional_scores[emo_key] = {
            "key": emo_key,
            "name": emo_data["name"],
            "icon": emo_data["icon"],
            "score": total_score,
            "level": level,
            "percentage": percentage,
            "description": generate_emotional_description(emo_key, level, total_score)
        }
    
    overall_emotional_value = sum(s.get("percentage", 50) for s in emotional_scores.values()) / len(emotional_scores)
    
    match_type = determine_match_type(emotional_scores, highlights_list)
    
    return {
        "overall_score": round(overall_emotional_value),
        "match_type": match_type,
        "match_type_label": get_match_type_label(match_type),
        "aspects": list(emotional_scores.values()),
        "compatibility_reasons": generate_compatibility_reasons(emotional_scores, highlights_list)
    }


def generate_emotional_description(key: str, level: str, score: float) -> str:
    descriptions = {
        "understanding": {
            "high": "能够深度理解对方的情绪波动，给予恰到好处的支持和共情",
            "medium": "在情绪理解方面表现中等，需要更多的沟通和观察",
            "low": "在情绪理解方面可能存在困难，需要更多的耐心和努力"
        },
        "support": {
            "high": "在对方低落时能够提供稳定的情感依靠和支持",
            "medium": "能够提供一定程度的情绪支持，但可以做得更多",
            "low": "在情绪支持方面需要更多的关注和学习"
        },
        "communication": {
            "high": "能够用温和的方式表达情感，避免冲突和误解",
            "medium": "情绪表达较为一般，需要更多的练习",
            "low": "情感表达可能存在障碍，需要更多的鼓励和引导"
        },
        "stability": {
            "high": "情绪状态非常稳定，能够成为对方的情绪锚点",
            "medium": "情绪稳定性一般，需要更多的自我觉察",
            "low": "情绪可能容易波动，需要更多的内在调节"
        },
        "passion": {
            "high": "能量充沛，能够点燃对方的激情和活力",
            "medium": "激情共鸣表现中等，需要更多的互动",
            "low": "激情方面可能较为平淡，需要更多的创造"
        }
    }
    
    return descriptions.get(key, {}).get(level, "需要更多的了解和互动")


def determine_match_type(
    emotional_scores: Dict[str, Any],
    highlights: List[Dict]
) -> str:
    highlight_categories = [h.get("category", "") for h in highlights]
    
    if "soulmate_connection" in highlight_categories:
        return "soulmate"
    
    understanding = emotional_scores.get("understanding", {}).get("level", "")
    support = emotional_scores.get("support", {}).get("level", "")
    passion = emotional_scores.get("passion", {}).get("level", "")
    
    if understanding == "high" and support == "high":
        return "harmonious"
    elif passion == "high":
        return "challenging"
    elif understanding == "high" or support == "high":
        return "complementary"
    else:
        return "neutral"


def get_match_type_label(match_type: str) -> str:
    labels = {
        "soulmate": "灵魂共鸣",
        "harmonious": "和谐共鸣",
        "complementary": "能量互补",
        "challenging": "张力吸引",
        "neutral": "普通连接"
    }
    return labels.get(match_type, "能量连接")


def generate_compatibility_reasons(
    emotional_scores: Dict[str, Any],
    highlights: List[Dict]
) -> List[Dict[str, Any]]:
    reasons = []
    
    highlight_icons = {
        "soulmate_connection": "💫",
        "passion_chemistry": "🔥",
        "emotional_harmony": "💕",
        "communication_synergy": "🧠",
        "long_term_stability": "🏔️",
        "creative_inspiration": "🎨",
        "growth_challenge": "🌱",
        "freedom_vs_commitment": "🦅"
    }
    
    for h in highlights[:3]:
        category = h.get("category", "")
        reasons.append({
            "icon": highlight_icons.get(category, "✨"),
            "text": h.get("description", "")
        })
    
    high_aspects = []
    for key, data in emotional_scores.items():
        if data.get("level") == "high":
            high_aspects.append(data)
    
    for aspect in high_aspects[:2]:
        if not any(r["text"] == aspect.get("description", "") for r in reasons):
            reasons.append({
                "icon": aspect.get("icon", "✨"),
                "text": aspect.get("description", "")
            })
    
    return reasons[:4]
