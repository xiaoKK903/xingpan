from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

SYNASTRY_DIMENSION_WEIGHTS = {
    "emotional": 0.25,
    "communication": 0.20,
    "romantic": 0.25,
    "values": 0.15,
    "growth": 0.15
}

KEY_PLANET_PAIRS = [
    ("太阳", "月亮"), ("太阳", "太阳"), ("太阳", "金星"),
    ("月亮", "月亮"), ("月亮", "金星"), ("月亮", "火星"),
    ("金星", "火星"), ("金星", "木星"), ("水星", "水星"),
    ("水星", "金星"), ("木星", "土星"), ("土星", "天王星")
]


ASPECT_SCORE_MAP = {
    "三分相": 15,
    "六分相": 10,
    "合相": 5,
    "对分相": -8,
    "四分相": -12
}

ASPECT_NATURE_SCORE = {
    "harmonious": 12,
    "neutral": 3,
    "challenging": -10
}


def calculate_orb_bonus(orb_arcminutes: float) -> float:
    if orb_arcminutes <= 2:
        return 1.5
    elif orb_arcminutes <= 4:
        return 1.3
    elif orb_arcminutes <= 6:
        return 1.1
    else:
        return 1.0


def get_planet_significance(planet_name: str) -> float:
    significance = {
        "太阳": 1.5,
        "月亮": 1.4,
        "金星": 1.3,
        "火星": 1.2,
        "水星": 1.1,
        "木星": 1.0,
        "土星": 1.0,
        "天王星": 0.8,
        "海王星": 0.7,
        "冥王星": 0.9
    }
    return significance.get(planet_name, 0.5)


def calculate_compatibility_score(synastry_data: Dict[str, Any]) -> Dict[str, Any]:
    aspects = synastry_data.get("synastry", {}).get("aspects", [])
    aspect_summary = synastry_data.get("synastry", {}).get("aspect_summary", {})
    
    person_a = synastry_data.get("person_a", {})
    person_b = synastry_data.get("person_b", {})
    
    chart_a = person_a.get("chart", {})
    chart_b = person_b.get("chart", {})
    
    dimension_scores = {
        "emotional": {"score": 50, "aspects": [], "positive_count": 0, "negative_count": 0},
        "communication": {"score": 50, "aspects": [], "positive_count": 0, "negative_count": 0},
        "romantic": {"score": 50, "aspects": [], "positive_count": 0, "negative_count": 0},
        "values": {"score": 50, "aspects": [], "positive_count": 0, "negative_count": 0},
        "growth": {"score": 50, "aspects": [], "positive_count": 0, "negative_count": 0}
    }
    
    key_aspects_analysis = []
    
    for aspect in aspects:
        planet_a = aspect.get("planet_a", "")
        planet_b = aspect.get("planet_b", "")
        aspect_type = aspect.get("aspect", "")
        nature = aspect.get("nature", "neutral")
        orb = aspect.get("orb_arcminutes", 0)
        
        orb_bonus = calculate_orb_bonus(orb)
        p1_sig = get_planet_significance(planet_a)
        p2_sig = get_planet_significance(planet_b)
        avg_sig = (p1_sig + p2_sig) / 2
        
        base_score = ASPECT_NATURE_SCORE.get(nature, 0)
        aspect_score = base_score * orb_bonus * avg_sig
        
        dimension = classify_aspect_dimension(planet_a, planet_b, aspect_type)
        
        if dimension in dimension_scores:
            dimension_scores[dimension]["aspects"].append({
                "planet_a": planet_a,
                "planet_b": planet_b,
                "aspect": aspect_type,
                "aspect_symbol": aspect.get("aspect_symbol", ""),
                "nature": nature,
                "orb_arcminutes": orb,
                "score_contribution": aspect_score
            })
            
            if nature == "harmonious":
                dimension_scores[dimension]["positive_count"] += 1
            elif nature == "challenging":
                dimension_scores[dimension]["negative_count"] += 1
            
            dimension_scores[dimension]["score"] += aspect_score
        
        is_key = (planet_a, planet_b) in KEY_PLANET_PAIRS or (planet_b, planet_a) in KEY_PLANET_PAIRS
        if is_key:
            key_aspects_analysis.append({
                "planet_a": planet_a,
                "planet_b": planet_b,
                "aspect": aspect_type,
                "aspect_symbol": aspect.get("aspect_symbol", ""),
                "nature": nature,
                "orb_arcminutes": orb,
                "importance": "high" if nature in ["harmonious", "challenging"] else "medium",
                "interpretation": generate_aspect_interpretation(planet_a, planet_b, aspect_type, nature)
            })
    
    for dim in dimension_scores:
        score = dimension_scores[dim]["score"]
        score = max(30, min(100, score))
        dimension_scores[dim]["score"] = round(score)
    
    total_score = 0
    for dim, weight in SYNASTRY_DIMENSION_WEIGHTS.items():
        total_score += dimension_scores[dim]["score"] * weight
    
    total_score = round(total_score)
    
    element_compatibility = analyze_element_compatibility(chart_a, chart_b)
    
    return {
        "total_score": total_score,
        "score_level": get_score_level(total_score),
        "dimensions": {
            "emotional": {
                "name": "情感共鸣",
                "score": dimension_scores["emotional"]["score"],
                "description": "衡量两人在情感表达和感受上的契合程度",
                "positive_count": dimension_scores["emotional"]["positive_count"],
                "negative_count": dimension_scores["emotional"]["negative_count"],
                "key_aspects": dimension_scores["emotional"]["aspects"][:5]
            },
            "communication": {
                "name": "沟通交流",
                "score": dimension_scores["communication"]["score"],
                "description": "衡量两人在思维方式和沟通方式上的契合程度",
                "positive_count": dimension_scores["communication"]["positive_count"],
                "negative_count": dimension_scores["communication"]["negative_count"],
                "key_aspects": dimension_scores["communication"]["aspects"][:5]
            },
            "romantic": {
                "name": "浪漫吸引",
                "score": dimension_scores["romantic"]["score"],
                "description": "衡量两人在爱情吸引力和浪漫表达上的契合程度",
                "positive_count": dimension_scores["romantic"]["positive_count"],
                "negative_count": dimension_scores["romantic"]["negative_count"],
                "key_aspects": dimension_scores["romantic"]["aspects"][:5]
            },
            "values": {
                "name": "价值观",
                "score": dimension_scores["values"]["score"],
                "description": "衡量两人在人生价值观和生活态度上的契合程度",
                "positive_count": dimension_scores["values"]["positive_count"],
                "negative_count": dimension_scores["values"]["negative_count"],
                "key_aspects": dimension_scores["values"]["aspects"][:5]
            },
            "growth": {
                "name": "成长潜力",
                "score": dimension_scores["growth"]["score"],
                "description": "衡量两人关系中促进彼此成长和发展的潜力",
                "positive_count": dimension_scores["growth"]["positive_count"],
                "negative_count": dimension_scores["growth"]["negative_count"],
                "key_aspects": dimension_scores["growth"]["aspects"][:5]
            }
        },
        "element_compatibility": element_compatibility,
        "key_aspects": key_aspects_analysis,
        "aspect_summary": aspect_summary
    }


def classify_aspect_dimension(planet_a: str, planet_b: str, aspect_type: str) -> str:
    emotional_planets = ["月亮", "太阳", "金星"]
    communication_planets = ["水星", "木星", "天王星"]
    romantic_planets = ["金星", "火星", "太阳", "月亮"]
    values_planets = ["木星", "土星", "太阳"]
    growth_planets = ["土星", "天王星", "冥王星", "木星"]
    
    def has_match(planets_list):
        return planet_a in planets_list or planet_b in planets_list
    
    if (planet_a in romantic_planets and planet_b in romantic_planets) and \
       (planet_a in ["金星", "火星"] or planet_b in ["金星", "火星"]):
        return "romantic"
    elif planet_a in emotional_planets and planet_b in emotional_planets:
        return "emotional"
    elif planet_a in communication_planets and planet_b in communication_planets:
        return "communication"
    elif planet_a in growth_planets and planet_b in growth_planets:
        return "growth"
    elif planet_a in values_planets and planet_b in values_planets:
        return "values"
    
    if has_match(emotional_planets):
        return "emotional"
    if has_match(romantic_planets):
        return "romantic"
    if has_match(communication_planets):
        return "communication"
    
    return "values"


def get_score_level(score: int) -> Dict[str, Any]:
    if score >= 85:
        return {
            "level": "极高契合",
            "color": "#22c55e",
            "description": "你们的关系具有极高的天然契合度，这是非常难得的缘分。",
            "recommendation": "珍惜这份难得的缘分，用真诚和付出去经营这段关系。"
        }
    elif score >= 70:
        return {
            "level": "高度契合",
            "color": "#16a34a",
            "description": "你们的关系有很好的基础，多数时候能够和谐相处。",
            "recommendation": "发挥优势，同时注意处理那些可能引发冲突的相位。"
        }
    elif score >= 55:
        return {
            "level": "中等契合",
            "color": "#eab308",
            "description": "你们的关系有一定的吸引力，也存在需要磨合的地方。",
            "recommendation": "这是大多数关系的常态，需要双方共同努力去理解和包容。"
        }
    elif score >= 40:
        return {
            "level": "需要磨合",
            "color": "#f97316",
            "description": "你们的关系面临较多挑战，需要更多的理解和耐心。",
            "recommendation": "不要灰心，许多深刻的关系都经历过困难的磨合期。"
        }
    else:
        return {
            "level": "极具挑战",
            "color": "#ef4444",
            "description": "你们的关系面临重大挑战，差异可能带来强烈的吸引力或冲突。",
            "recommendation": "如果决定继续这段关系，需要极大的耐心、理解和专业的指导。"
        }


def analyze_element_compatibility(chart_a: Dict, chart_b: Dict) -> Dict[str, Any]:
    element_map = {
        "白羊座": "火", "狮子座": "火", "射手座": "火",
        "金牛座": "土", "处女座": "土", "摩羯座": "土",
        "双子座": "风", "天秤座": "风", "水瓶座": "风",
        "巨蟹座": "水", "天蝎座": "水", "双鱼座": "水"
    }
    
    sun_a = chart_a.get("sun_sign", {}).get("sign", "")
    sun_b = chart_b.get("sun_sign", {}).get("sign", "")
    
    moon_a = chart_a.get("moon_sign", {}).get("sign", "")
    moon_b = chart_b.get("moon_sign", {}).get("sign", "")
    
    element_a = element_map.get(sun_a, "")
    element_b = element_map.get(sun_b, "")
    
    compatibility_matrix = {
        "火": {"火": 80, "土": 60, "风": 85, "水": 50},
        "土": {"火": 60, "土": 75, "风": 55, "水": 85},
        "风": {"火": 85, "土": 55, "风": 70, "水": 45},
        "水": {"火": 50, "土": 85, "风": 45, "水": 75}
    }
    
    element_names = {
        "火": "火象",
        "土": "土象",
        "风": "风象",
        "水": "水象"
    }
    
    element_descriptions = {
        "火": "热情、主动、充满活力",
        "土": "稳重、务实、追求稳定",
        "风": "灵活、善于沟通、追求变化",
        "水": "敏感、情感丰富、直觉强"
    }
    
    element_compatibility = {
        "fire_fire": "双火象：热情四射，但可能缺乏耐心。",
        "fire_earth": "火与土：火象的热情可以点燃土象的稳定，但需要相互理解。",
        "fire_air": "火与风：最佳组合之一，风象可以为火象提供想法，火象可以将想法付诸行动。",
        "fire_water": "火与水：火象的直接可能伤害水象的敏感，需要更多的温柔和理解。",
        "earth_earth": "双土象：非常稳定可靠，但可能缺乏变化和激情。",
        "earth_air": "土与风：土象的实际与风象的思维可能产生冲突，需要找到平衡点。",
        "earth_water": "土与水：最佳组合之一，土象可以给水象安全感，水象可以滋润土象的情感。",
        "air_air": "双风象：沟通顺畅，思想活跃，但可能缺乏深度和行动力。",
        "air_water": "风与水：风象的理性与水象的情感可能难以融合，需要更多的共情。",
        "water_water": "双水象：情感深度极高，能够深刻理解彼此，但可能过于敏感。"
    }
    
    score = 60
    if element_a and element_b:
        score = compatibility_matrix.get(element_a, {}).get(element_b, 60)
    
    key = f"{element_a}_{element_b}".lower()
    if key not in element_compatibility:
        key = f"{element_b}_{element_a}".lower()
    
    description = element_compatibility.get(key, "你们的元素组合具有独特的化学反应。")
    
    return {
        "sun_element_a": element_a,
        "sun_element_b": element_b,
        "sun_element_name_a": element_names.get(element_a, ""),
        "sun_element_name_b": element_names.get(element_b, ""),
        "sun_element_desc_a": element_descriptions.get(element_a, ""),
        "sun_element_desc_b": element_descriptions.get(element_b, ""),
        "compatibility_score": score,
        "description": description,
        "sun_sign_a": sun_a,
        "sun_sign_b": sun_b,
        "moon_sign_a": moon_a,
        "moon_sign_b": moon_b
    }


def generate_aspect_interpretation(planet_a: str, planet_b: str, aspect_type: str, nature: str) -> str:
    interpretations = {
        "太阳": {
            "月亮": {
                "合相": "太阳与月亮合相，你们的自我认同与情感需求高度融合。一方能够深刻理解另一方的感受，关系中充满温暖和默契。",
                "三分相": "太阳与月亮形成三分相，这是极其和谐的配置。你们能够自然地理解和支持对方，情感交流顺畅而温暖。",
                "六分相": "太阳与月亮形成六分相，你们有很好的情感共鸣。通过简单的努力，就能建立深厚的情感连接。",
                "对分相": "太阳与月亮形成对分相，你们可能在自我表达和情感需求上存在差异。一方需要的是认可，另一方需要的是情感滋养，需要平衡这两种需求。",
                "四分相": "太阳与月亮形成四分相，这是富有挑战性但有成长潜力的配置。你们的自我意志与情感需求可能产生冲突，但通过努力可以实现深度的整合。"
            },
            "金星": {
                "合相": "太阳与金星合相，这是充满爱意和吸引力的相位。你们欣赏彼此的价值，关系中充满浪漫和欣赏。",
                "三分相": "太阳与金星形成三分相，爱意自然流露。你们欣赏彼此的美好，关系中充满和谐与甜蜜。",
                "六分相": "太阳与金星形成六分相，通过简单的表达就能增进彼此的爱意。这是促进感情发展的有利配置。",
                "对分相": "太阳与金星形成对分相，你们在价值观和爱的表达上可能存在差异。需要学会欣赏对方独特的表达方式。",
                "四分相": "太阳与金星形成四分相，自我表达与价值取向可能产生冲突。但这种张力也可以激发深刻的自我认知和成长。"
            }
        },
        "月亮": {
            "月亮": {
                "合相": "月亮与月亮合相，你们的情感频率高度一致。能够深刻感知对方的情绪变化，关系中充满情感共鸣。",
                "三分相": "月亮与月亮形成三分相，情感交流极其和谐。你们能够自然地理解和支持对方的情感需求。",
                "六分相": "月亮与月亮形成六分相，有良好的情感理解基础。通过关心和倾听，可以建立深厚的情感连接。",
                "对分相": "月亮与月亮形成对分相，情感需求可能完全不同或完全互补。需要学会理解和接纳对方独特的情感表达方式。",
                "四分相": "月亮与月亮形成四分相，情感表达方式可能产生冲突。但这种挑战也促使你们更深入地理解自己和对方的情感。"
            },
            "金星": {
                "合相": "月亮与金星合相，情感与爱的表达完美融合。关系中充满温柔、关爱和浪漫，是非常甜蜜的配置。",
                "三分相": "月亮与金星形成三分相，情感滋养与爱意表达高度和谐。你们能够自然地给予和接受爱与关怀。",
                "六分相": "月亮与金星形成六分相，通过温柔和关怀可以轻松增进感情。这是促进亲密关系的有利相位。",
                "对分相": "月亮与金星形成对分相，情感需求与爱的表达可能存在差异。需要学会理解对方独特的爱的语言。",
                "四分相": "月亮与金星形成四分相，情感需求与价值取向可能产生摩擦。但这种张力也可以促使你们更深入地探索爱的真谛。"
            },
            "火星": {
                "合相": "月亮与火星合相，情感与行动力紧密结合。关系中充满激情，但也可能有情绪的突然爆发。",
                "三分相": "月亮与火星形成三分相，情感驱动着积极的行动。你们能够以建设性的方式表达情感需求。",
                "六分相": "月亮与火星形成六分相，通过主动关心和行动可以增进情感连接。这是积极的情感动力。",
                "对分相": "月亮与火星形成对分相，情感需求与行动方式可能产生对立。需要平衡温柔与直接的表达。",
                "四分相": "月亮与火星形成四分相，情感与行动可能产生冲突，可能导致情绪爆发或压抑。但学会表达后可以转化为强大的动力。"
            }
        },
        "金星": {
            "火星": {
                "合相": "金星与火星合相，这是强烈的浪漫和性吸引力的标志。关系中充满激情，但需要平衡爱与欲望。",
                "三分相": "金星与火星形成三分相，浪漫吸引力和谐流动。爱与行动完美结合，关系中充满甜蜜的激情。",
                "六分相": "金星与火星形成六分相，有良好的浪漫吸引力基础。通过积极的表达，可以增进彼此的吸引力。",
                "对分相": "金星与火星形成对分相，爱的表达与行动方式可能对立。这种张力既吸引又挑战，需要找到平衡点。",
                "四分相": "金星与火星形成四分相，爱与行动可能产生摩擦。但这种张力如果处理得当，可以转化为强大的激情和成长动力。"
            }
        }
    }
    
    default_interpretations = {
        "harmonious": f"{planet_a}与{planet_b}形成{aspect_type}，这是一个和谐的相位。你们能够自然地理解和支持对方在这方面的能量。",
        "challenging": f"{planet_a}与{planet_b}形成{aspect_type}，这是一个富有挑战性但有成长潜力的相位。你们在这方面的能量可能产生冲突，但通过努力可以实现深度的整合。",
        "neutral": f"{planet_a}与{planet_b}形成{aspect_type}，这是一个中性的相位。你们在这方面的能量相互强调，影响取决于涉及的行星。"
    }
    
    planet_interps = interpretations.get(planet_a, {})
    specific_interps = planet_interps.get(planet_b, {})
    
    if aspect_type in specific_interps:
        return specific_interps[aspect_type]
    
    planet_interps_b = interpretations.get(planet_b, {})
    specific_interps_b = planet_interps_b.get(planet_a, {})
    
    if aspect_type in specific_interps_b:
        return specific_interps_b[aspect_type]
    
    return default_interpretations.get(nature, default_interpretations["neutral"])


def generate_personality_compatibility(synastry_data: Dict, compatibility_data: Dict) -> Dict[str, Any]:
    dimensions = compatibility_data.get("dimensions", {})
    elements = compatibility_data.get("element_compatibility", {})
    
    strengths = []
    challenges = []
    
    for dim_key, dim_data in dimensions.items():
        score = dim_data.get("score", 50)
        name = dim_data.get("name", "")
        
        if score >= 75:
            strengths.append({
                "dimension": name,
                "score": score,
                "description": f"你们在{name}方面有很高的契合度，这是关系中的宝贵资产。"
            })
        elif score < 50:
            challenges.append({
                "dimension": name,
                "score": score,
                "description": f"你们在{name}方面需要更多的理解和努力，这是关系成长的机会。"
            })
    
    interaction_style = analyze_interaction_style(synastry_data)
    future_advice = generate_future_advice(compatibility_data)
    
    return {
        "summary": generate_overall_summary(compatibility_data),
        "strengths": strengths,
        "challenges": challenges,
        "interaction_style": interaction_style,
        "future_advice": future_advice,
        "element_analysis": elements
    }


def analyze_interaction_style(synastry_data: Dict) -> Dict[str, Any]:
    aspects = synastry_data.get("synastry", {}).get("aspects", [])
    
    romantic_aspects = 0
    harmonious_count = 0
    challenging_count = 0
    
    key_romantic_planets = ["金星", "火星", "月亮", "太阳"]
    
    for aspect in aspects:
        p_a = aspect.get("planet_a", "")
        p_b = aspect.get("planet_b", "")
        nature = aspect.get("nature", "")
        
        if p_a in key_romantic_planets and p_b in key_romantic_planets:
            romantic_aspects += 1
        
        if nature == "harmonious":
            harmonious_count += 1
        elif nature == "challenging":
            challenging_count += 1
    
    total = harmonious_count + challenging_count
    harmony_ratio = harmonious_count / total if total > 0 else 0.5
    
    styles = []
    
    if harmony_ratio >= 0.6:
        styles.append("和谐型")
    elif harmony_ratio <= 0.4:
        styles.append("挑战型")
    else:
        styles.append("平衡型")
    
    if romantic_aspects >= 3:
        styles.append("激情型")
    elif romantic_aspects >= 1:
        styles.append("温暖型")
    
    return {
        "style_names": styles,
        "description": generate_style_description(styles),
        "romantic_aspect_count": romantic_aspects,
        "harmonious_ratio": round(harmony_ratio * 100),
        "challenging_ratio": round((1 - harmony_ratio) * 100)
    }


def generate_style_description(styles: List[str]) -> str:
    descriptions = {
        "和谐型": "你们的关系以和谐为主，大多数时候能够顺畅沟通、相互理解。这种和谐让你们感到舒适和放松。",
        "挑战型": "你们的关系充满张力和挑战。这些挑战虽然困难，但也是深度成长和转化的催化剂。",
        "平衡型": "你们的关系既有和谐的时刻，也有需要磨合的地方。这种平衡是大多数关系的常态。",
        "激情型": "你们之间有强烈的浪漫和性吸引力。这种激情为关系注入活力，但也需要理性来平衡。",
        "温暖型": "你们之间有温暖的情感连接。这种温暖让关系充满关爱和支持。"
    }
    
    result = []
    for style in styles:
        if style in descriptions:
            result.append(descriptions[style])
    
    return " ".join(result) if result else "你们的关系有独特的互动模式。"


def generate_future_advice(compatibility_data: Dict) -> List[Dict[str, Any]]:
    dimensions = compatibility_data.get("dimensions", {})
    advices = []
    
    for dim_key, dim_data in dimensions.items():
        score = dim_data.get("score", 50)
        name = dim_data.get("name", "")
        desc = dim_data.get("description", "")
        
        if score >= 75:
            advices.append({
                "type": "strength",
                "title": f"发挥{name}优势",
                "content": f"你们在{name}方面有很高的契合度。继续保持并深化这方面的连接，它将成为关系中的稳定力量。{desc}"
            })
        elif score < 50:
            advices.append({
                "type": "improvement",
                "title": f"改善{name}",
                "content": f"你们在{name}方面需要更多的关注和努力。试着站在对方的角度思考问题，学会理解和接纳差异。{desc}"
            })
    
    total_score = compatibility_data.get("total_score", 60)
    if total_score < 60:
        advices.append({
            "type": "warning",
            "title": "专业建议",
            "content": "考虑到你们的匹配度评分，建议在遇到严重分歧时寻求专业的关系咨询。不要因为困难而轻易放弃，每一段关系都需要经营和努力。"
        })
    
    return advices


def generate_overall_summary(compatibility_data: Dict) -> Dict[str, Any]:
    total_score = compatibility_data.get("total_score", 60)
    score_level = compatibility_data.get("score_level", {})
    dimensions = compatibility_data.get("dimensions", {})
    
    high_dims = []
    low_dims = []
    
    for dim_key, dim_data in dimensions.items():
        score = dim_data.get("score", 50)
        name = dim_data.get("name", "")
        if score >= 75:
            high_dims.append(name)
        elif score < 50:
            low_dims.append(name)
    
    summary_parts = []
    
    if high_dims:
        summary_parts.append(f"你们在{', '.join(high_dims)}方面有出色的契合度。")
    
    if low_dims:
        summary_parts.append(f"在{', '.join(low_dims)}方面需要更多的理解和努力。")
    
    level_desc = score_level.get("description", "")
    if level_desc:
        summary_parts.append(level_desc)
    
    return {
        "text": " ".join(summary_parts) if summary_parts else "你们的关系具有独特的特质和潜力。",
        "score_level": score_level
    }


def generate_full_analysis(synastry_data: Dict) -> Dict[str, Any]:
    compatibility = calculate_compatibility_score(synastry_data)
    personality = generate_personality_compatibility(synastry_data, compatibility)
    
    person_a = synastry_data.get("person_a", {})
    person_b = synastry_data.get("person_b", {})
    
    chart_a = person_a.get("chart", {})
    chart_b = person_b.get("chart", {})
    
    return {
        "analysis_info": {
            "generated_at": datetime.utcnow().isoformat(),
            "version": "2.0"
        },
        "basic_info": {
            "person_a": {
                "name": person_a.get("name", "人物A"),
                "sun_sign": chart_a.get("sun_sign", {}).get("sign", ""),
                "sun_sign_symbol": chart_a.get("sun_sign", {}).get("sign_symbol", ""),
                "moon_sign": chart_a.get("moon_sign", {}).get("sign", ""),
                "moon_sign_symbol": chart_a.get("moon_sign", {}).get("sign_symbol", ""),
                "ascendant": chart_a.get("ascendant", {}).get("sign", ""),
                "ascendant_symbol": chart_a.get("ascendant", {}).get("sign_symbol", "")
            },
            "person_b": {
                "name": person_b.get("name", "人物B"),
                "sun_sign": chart_b.get("sun_sign", {}).get("sign", ""),
                "sun_sign_symbol": chart_b.get("sun_sign", {}).get("sign_symbol", ""),
                "moon_sign": chart_b.get("moon_sign", {}).get("sign", ""),
                "moon_sign_symbol": chart_b.get("moon_sign", {}).get("sign_symbol", ""),
                "ascendant": chart_b.get("ascendant", {}).get("sign", ""),
                "ascendant_symbol": chart_b.get("ascendant", {}).get("sign_symbol", "")
            }
        },
        "compatibility": compatibility,
        "personality_analysis": personality,
        "original_synastry": synastry_data
    }
