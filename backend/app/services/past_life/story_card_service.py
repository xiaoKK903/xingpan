"""
故事卡生成服务 - 基于合盘特征智能生成羁绊故事卡
"""
import logging
import random
import json
import hashlib
import secrets
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from app.services.synastry_highlights_service import (
    extract_synastry_highlights,
    analyze_element_compatibility,
    determine_match_type
)

from .config import (
    STORY_CARD_TEMPLATE_CONFIG,
    STORY_CARD_RARITY_CONFIG,
    ASPECT_NATURE_MAPPING,
    DOMINANT_ELEMENT_SIGN_MAPPING
)

logger = logging.getLogger(__name__)


def generate_share_code() -> str:
    """生成唯一分享码"""
    return secrets.token_urlsafe(12)[:15]


def extract_synastry_features(
    synastry_data: Dict[str, Any],
    analysis_data: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    从合盘数据提取关键特征，用于故事卡模板匹配
    
    Args:
        synastry_data: 合盘计算结果
        analysis_data: 合盘分析结果（可选）
        
    Returns:
        包含合盘特征的字典
    """
    features = {
        "aspects": [],
        "aspect_pairs": [],
        "compatibility_score": 50,
        "match_type": "neutral",
        "dominant_element": None,
        "person_a_sun_sign": None,
        "person_b_sun_sign": None,
        "person_a_moon_sign": None,
        "person_b_moon_sign": None,
        "harmonious_aspects": 0,
        "challenging_aspects": 0,
        "total_aspects": 0,
        "key_highlights": [],
    }
    
    try:
        aspects = synastry_data.get("synastry", {}).get("aspects", [])
        aspect_summary = synastry_data.get("synastry", {}).get("aspect_summary", {})
        
        for aspect in aspects:
            planet_a = aspect.get("planet_a", "")
            planet_b = aspect.get("planet_b", "")
            aspect_type = aspect.get("aspect", "")
            nature = aspect.get("nature", "neutral")
            orb = aspect.get("orb_arcminutes", 10)
            
            if planet_a and planet_b:
                features["aspects"].append({
                    "planet_a": planet_a,
                    "planet_b": planet_b,
                    "aspect_type": aspect_type,
                    "nature": nature,
                    "orb": orb
                })
                features["aspect_pairs"].append((planet_a, planet_b))
                
                if nature == "harmonious":
                    features["harmonious_aspects"] += 1
                elif nature == "challenging":
                    features["challenging_aspects"] += 1
        
        features["total_aspects"] = len(aspects)
        
        if not aspects and analysis_data:
            highlights = analysis_data.get("highlights", [])
            for h in highlights:
                matched = h.get("matched_aspects", [])
                for m in matched:
                    planet_a = m.get("planet_a", "")
                    planet_b = m.get("planet_b", "")
                    if planet_a and planet_b:
                        features["aspect_pairs"].append((planet_a, planet_b))
        
        person_a = synastry_data.get("person_a", {})
        person_b = synastry_data.get("person_b", {})
        
        chart_a = person_a.get("chart", {})
        chart_b = person_b.get("chart", {})
        
        features["person_a_sun_sign"] = chart_a.get("sun_sign", {}).get("sign", "")
        features["person_b_sun_sign"] = chart_b.get("sun_sign", {}).get("sign", "")
        features["person_a_moon_sign"] = chart_a.get("moon_sign", {}).get("sign", "")
        features["person_b_moon_sign"] = chart_b.get("moon_sign", {}).get("sign", "")
        
        features["dominant_element"] = determine_dominant_element(
            features["person_a_sun_sign"],
            features["person_b_sun_sign"]
        )
        
        if analysis_data:
            compat = analysis_data.get("compatibility", {})
            features["compatibility_score"] = compat.get("total_score", 50)
            
            highlights_list = analysis_data.get("highlights", [])
            if highlights_list:
                features["key_highlights"] = [h.get("category", "") for h in highlights_list[:3]]
                
                if "soulmate_connection" in features["key_highlights"]:
                    features["match_type"] = "soulmate"
                elif "passion_chemistry" in features["key_highlights"]:
                    features["match_type"] = "passionate"
                elif "growth_challenge" in features["key_highlights"]:
                    features["match_type"] = "challenging"
                elif features["compatibility_score"] >= 75:
                    features["match_type"] = "harmonious"
                else:
                    features["match_type"] = "complementary"
        
        if features["total_aspects"] > 0:
            harmony_ratio = features["harmonious_aspects"] / features["total_aspects"]
            if features["match_type"] == "neutral":
                if harmony_ratio >= 0.7:
                    features["match_type"] = "harmonious"
                elif harmony_ratio <= 0.3:
                    features["match_type"] = "challenging"
                else:
                    features["match_type"] = "complementary"
        
    except Exception as e:
        logger.error(f"提取合盘特征失败: {e}")
    
    return features


def determine_dominant_element(sun_sign_a: str, sun_sign_b: str) -> Optional[str]:
    """
    根据两人的太阳星座确定主导元素
    
    Returns:
        fire/earth/air/water 或 None
    """
    element_map = {}
    for elem, signs in DOMINANT_ELEMENT_SIGN_MAPPING.items():
        for sign in signs:
            element_map[sign] = elem
    
    elem_a = element_map.get(sun_sign_a)
    elem_b = element_map.get(sun_sign_b)
    
    if elem_a == elem_b and elem_a:
        return elem_a
    
    if elem_a and elem_b:
        if (elem_a == "fire" and elem_b == "air") or (elem_a == "air" and elem_b == "fire"):
            return "fire"
        if (elem_a == "earth" and elem_b == "water") or (elem_a == "water" and elem_b == "earth"):
            return "earth"
    
    return elem_a or elem_b


def calculate_template_match_score(
    template_key: str,
    features: Dict[str, Any]
) -> Dict[str, Any]:
    """
    计算模板匹配分数
    
    Args:
        template_key: 模板键名
        features: 合盘特征
        
    Returns:
        包含匹配分数和匹配详情的字典
    """
    template = STORY_CARD_TEMPLATE_CONFIG.get(template_key, {})
    conditions = template.get("match_conditions", {})
    
    score = 0
    max_score = 0
    matched_conditions = []
    missing_conditions = []
    
    required_aspects = conditions.get("required_aspects", [])
    if required_aspects:
        max_score += 40
        aspect_pairs = features.get("aspect_pairs", [])
        
        matched_aspect_count = 0
        for req_pair in required_aspects:
            found = False
            for actual_pair in aspect_pairs:
                if (actual_pair[0] == req_pair[0] and actual_pair[1] == req_pair[1]) or \
                   (actual_pair[0] == req_pair[1] and actual_pair[1] == req_pair[0]):
                    found = True
                    break
            
            if found:
                matched_aspect_count += 1
                matched_conditions.append(f"相位匹配: {req_pair[0]}-{req_pair[1]}")
            else:
                missing_conditions.append(f"缺少相位: {req_pair[0]}-{req_pair[1]}")
        
        if matched_aspect_count > 0:
            score += int(40 * (matched_aspect_count / len(required_aspects)))
    
    compatibility_threshold = conditions.get("compatibility_threshold")
    if compatibility_threshold is not None:
        max_score += 30
        compat_score = features.get("compatibility_score", 50)
        
        if compat_score >= compatibility_threshold:
            score += 30
            matched_conditions.append(f"兼容性达标: {compat_score} >= {compatibility_threshold}")
        elif compat_score >= compatibility_threshold - 10:
            score += 15
            matched_conditions.append(f"兼容性接近: {compat_score} (阈值: {compatibility_threshold})")
        else:
            missing_conditions.append(f"兼容性不足: {compat_score} < {compatibility_threshold}")
    
    dominant_element = conditions.get("dominant_element")
    if dominant_element:
        max_score += 20
        actual_elem = features.get("dominant_element")
        
        if actual_elem == dominant_element:
            score += 20
            matched_conditions.append(f"主导元素匹配: {dominant_element}")
        else:
            missing_conditions.append(f"主导元素不匹配: 需要{dominant_element}，实际{actual_elem}")
    
    match_type = conditions.get("match_type")
    if match_type:
        max_score += 10
        actual_type = features.get("match_type", "neutral")
        
        if actual_type == match_type:
            score += 10
            matched_conditions.append(f"匹配类型匹配: {match_type}")
        else:
            missing_conditions.append(f"匹配类型不匹配: 需要{match_type}，实际{actual_type}")
    
    rarity = template.get("rarity", "common")
    rarity_config = STORY_CARD_RARITY_CONFIG.get(rarity, {})
    base_probability = rarity_config.get("probability", 0.1)
    
    if max_score == 0:
        normalized_score = 50
    else:
        normalized_score = int((score / max_score) * 100)
    
    return {
        "template_key": template_key,
        "template_name": template.get("name", template_key),
        "score": score,
        "max_score": max_score,
        "normalized_score": normalized_score,
        "matched_conditions": matched_conditions,
        "missing_conditions": missing_conditions,
        "base_probability": base_probability,
        "rarity": rarity
    }


def select_best_template(
    features: Dict[str, Any],
    include_fallback: bool = True
) -> Tuple[str, Dict[str, Any]]:
    """
    选择最佳匹配的故事卡模板
    
    Args:
        features: 合盘特征
        include_fallback: 是否包含兜底模板
        
    Returns:
        (模板键名, 匹配分数详情)
    """
    template_scores = []
    
    for template_key in STORY_CARD_TEMPLATE_CONFIG.keys():
        match_result = calculate_template_match_score(template_key, features)
        template_scores.append(match_result)
    
    template_scores.sort(key=lambda x: (
        x["normalized_score"],
        STORY_CARD_RARITY_CONFIG.get(x["rarity"], {}).get("probability", 0)
    ), reverse=True)
    
    if not template_scores:
        return "familiar_strangers", calculate_template_match_score("familiar_strangers", features)
    
    top_score = template_scores[0]["normalized_score"]
    
    if top_score >= 70:
        selected = template_scores[0]
    elif top_score >= 50:
        candidates = [t for t in template_scores if t["normalized_score"] >= 40]
        selected = random.choice(candidates) if candidates else template_scores[0]
    else:
        if include_fallback:
            fallback = next((t for t in template_scores if t["template_key"] == "familiar_strangers"), None)
            if fallback:
                selected = fallback
            else:
                selected = template_scores[-1]
        else:
            selected = template_scores[0]
    
    return selected["template_key"], selected


def generate_story_content(
    template_key: str,
    person_a_name: str,
    person_b_name: str,
    features: Dict[str, Any]
) -> Dict[str, Any]:
    """
    根据模板生成故事内容
    
    Args:
        template_key: 模板键名
        person_a_name: 人物A名称
        person_b_name: 人物B名称
        features: 合盘特征
        
    Returns:
        包含标题、副标题、故事内容的字典
    """
    template = STORY_CARD_TEMPLATE_CONFIG.get(template_key, {})
    if not template:
        template = STORY_CARD_TEMPLATE_CONFIG.get("familiar_strangers", {})
    
    templates = template.get("story_templates", [])
    if not templates:
        return {
            "headline": f"{person_a_name} 与 {person_b_name}",
            "subheadline": "特别的缘分",
            "story_content": f"{person_a_name} 和 {person_b_name} 之间有着特别的缘分。",
            "story_short": f"{person_a_name} 和 {person_b_name} 之间有着特别的缘分。"
        }
    
    selected_story = random.choice(templates)
    
    def replace_vars(text: str) -> str:
        if not text:
            return text
        text = text.replace("{{person_a}}", person_a_name)
        text = text.replace("{{person_b}}", person_b_name)
        return text
    
    headline = replace_vars(template.get("headline_template", ""))
    subheadline = replace_vars(template.get("subheadline_template", ""))
    
    opening = replace_vars(selected_story.get("opening", ""))
    middle = replace_vars(selected_story.get("middle", ""))
    closing = replace_vars(selected_story.get("closing", ""))
    
    story_content = "\n\n".join([p for p in [opening, middle, closing] if p])
    
    story_short = generate_story_short(story_content, opening)
    
    return {
        "headline": headline,
        "subheadline": subheadline,
        "story_content": story_content,
        "story_short": story_short,
        "template_used": template_key
    }


def generate_story_short(full_story: str, opening: str = "") -> str:
    """
    生成故事摘要
    
    Args:
        full_story: 完整故事
        opening: 开头部分
        
    Returns:
        故事摘要
    """
    if not full_story:
        return ""
    
    if opening and len(opening) <= 150:
        return opening
    
    if len(full_story) <= 200:
        return full_story
    
    first_period = full_story.find("。")
    first_exclaim = full_story.find("！")
    first_break = full_story.find("\n")
    
    break_points = [
        p for p in [first_period, first_exclaim, first_break] if p > 0
    ]
    
    if break_points:
        short_end = min(break_points) + 1
        short_story = full_story[:short_end].strip()
        
        if len(short_story) >= 50:
            return short_story
    
    end_idx = 150
    while end_idx < len(full_story) and full_story[end_idx] not in ["。", "！", "，", " "]:
        end_idx += 1
    
    if end_idx < len(full_story):
        return full_story[:end_idx + 1].strip() + "..."
    
    return full_story[:150] + "..."


def calculate_story_card_rarity(
    template_key: str,
    features: Dict[str, Any],
    match_score: Dict[str, Any]
) -> Dict[str, Any]:
    """
    计算故事卡稀有度
    
    Args:
        template_key: 模板键名
        features: 合盘特征
        match_score: 匹配分数
        
    Returns:
        包含稀有度信息的字典
    """
    template = STORY_CARD_TEMPLATE_CONFIG.get(template_key, {})
    base_rarity = template.get("rarity", "common")
    
    normalized_score = match_score.get("normalized_score", 50)
    compatibility_score = features.get("compatibility_score", 50)
    
    rarity_order = ["common", "rare", "epic", "legendary"]
    current_index = rarity_order.index(base_rarity) if base_rarity in rarity_order else 0
    
    boost = 0
    if normalized_score >= 90:
        boost += 1
    if compatibility_score >= 90:
        boost += 1
    if len(features.get("aspect_pairs", [])) >= 8:
        boost += 1
    
    final_index = min(len(rarity_order) - 1, current_index + boost)
    final_rarity = rarity_order[final_index]
    
    rarity_config = STORY_CARD_RARITY_CONFIG.get(final_rarity, {})
    
    return {
        "rarity": final_rarity,
        "rarity_name": rarity_config.get("name", final_rarity),
        "color": rarity_config.get("color", "#94a3b8"),
        "glow_color": rarity_config.get("glow_color", "rgba(148, 163, 184, 0.3)"),
        "share_bonus": rarity_config.get("share_bonus", 1),
        "base_rarity": base_rarity
    }


def generate_story_card(
    synastry_data: Dict[str, Any],
    analysis_data: Dict[str, Any] = None,
    person_a_name: str = "人物A",
    person_b_name: str = "人物B",
    user_id: int = None,
    synastry_record_id: int = None,
    target_user_id: int = None
) -> Dict[str, Any]:
    """
    生成完整的故事卡
    
    Args:
        synastry_data: 合盘数据
        analysis_data: 分析数据
        person_a_name: 人物A名称
        person_b_name: 人物B名称
        user_id: 用户ID
        synastry_record_id: 合盘记录ID
        target_user_id: 目标用户ID
        
    Returns:
        完整的故事卡数据
    """
    try:
        features = extract_synastry_features(synastry_data, analysis_data)
        
        template_key, match_score = select_best_template(features)
        
        story_content = generate_story_content(
            template_key,
            person_a_name,
            person_b_name,
            features
        )
        
        rarity_info = calculate_story_card_rarity(template_key, features, match_score)
        
        template = STORY_CARD_TEMPLATE_CONFIG.get(template_key, {})
        
        key_aspect = None
        if features.get("aspects"):
            sorted_aspects = sorted(
                features["aspects"],
                key=lambda x: (
                    0 if x["nature"] == "harmonious" else (1 if x["nature"] == "challenging" else 2),
                    x["orb"]
                )
            )
            if sorted_aspects:
                best = sorted_aspects[0]
                key_aspect = f"{best['planet_a']} {best['aspect_type']} {best['planet_b']}"
        
        card_id = generate_card_id(person_a_name, person_b_name)
        
        story_card = {
            "card_id": card_id,
            "user_id": user_id,
            "synastry_record_id": synastry_record_id,
            "card_template": template_key,
            "template_name": template.get("name", template_key),
            "template_icon": template.get("icon", "✨"),
            
            "person_a_name": person_a_name,
            "person_b_name": person_b_name,
            "target_user_id": target_user_id,
            
            "headline": story_content["headline"],
            "subheadline": story_content["subheadline"],
            "story_content": story_content["story_content"],
            "story_short": story_content["story_short"],
            
            "compatibility_score": features.get("compatibility_score", 50),
            "match_type": features.get("match_type", "neutral"),
            "dominant_element": features.get("dominant_element"),
            "key_aspect": key_aspect,
            
            "rarity": rarity_info["rarity"],
            "rarity_name": rarity_info["rarity_name"],
            "rarity_color": rarity_info["color"],
            "rarity_glow_color": rarity_info["glow_color"],
            "share_bonus": rarity_info["share_bonus"],
            
            "is_mounted": False,
            "mounted_at": None,
            "is_public": False,
            "share_code": generate_share_code(),
            "share_count": 0,
            
            "match_score": match_score["normalized_score"],
            "matched_conditions": match_score["matched_conditions"],
            
            "features": {
                "person_a_sun_sign": features.get("person_a_sun_sign"),
                "person_b_sun_sign": features.get("person_b_sun_sign"),
                "total_aspects": features.get("total_aspects", 0),
                "harmonious_aspects": features.get("harmonious_aspects", 0),
                "challenging_aspects": features.get("challenging_aspects", 0)
            },
            
            "generated_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"生成故事卡成功: 模板={template_key}, 稀有度={rarity_info['rarity']}, 分数={match_score['normalized_score']}")
        
        return {
            "success": True,
            "story_card": story_card,
            "match_details": match_score
        }
        
    except Exception as e:
        logger.error(f"生成故事卡失败: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "story_card": None
        }


def generate_card_id(name_a: str, name_b: str) -> str:
    """生成唯一卡牌ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    combined = f"{name_a}_{name_b}_{timestamp}_{random.randint(1000, 9999)}"
    hash_obj = hashlib.md5(combined.encode())
    return f"SC_{hash_obj.hexdigest()[:10].upper()}"


def get_template_list() -> List[Dict[str, Any]]:
    """
    获取所有故事卡模板列表
    
    Returns:
        模板列表
    """
    templates = []
    for key, config in STORY_CARD_TEMPLATE_CONFIG.items():
        rarity = config.get("rarity", "common")
        rarity_config = STORY_CARD_RARITY_CONFIG.get(rarity, {})
        
        templates.append({
            "key": key,
            "name": config.get("name", key),
            "icon": config.get("icon", "✨"),
            "rarity": rarity,
            "rarity_name": config.get("rarity_name", rarity_config.get("name", rarity)),
            "keywords": config.get("keywords", []),
            "description": f"稀有度: {config.get('rarity_name', rarity)}",
            "match_conditions": config.get("match_conditions", {}),
            "color": rarity_config.get("color", "#94a3b8")
        })
    
    templates.sort(key=lambda x: {
        "legendary": 0,
        "epic": 1,
        "rare": 2,
        "common": 3
    }.get(x["rarity"], 4))
    
    return templates


def get_rarity_config() -> Dict[str, Any]:
    """
    获取稀有度配置
    
    Returns:
        稀有度配置
    """
    return STORY_CARD_RARITY_CONFIG
