import logging
import json
import uuid
import random
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models import (
    User, Chart, SynastryRecord,
    PastLifeRecord, PastLifeSynastryRecord,
    PastLifeTheme, PastLifeRelationshipType,
    PaymentOrder, PaymentStatus, PaymentType
)
from app.services.ai_service import call_deepseek_api, call_qwen_api
from app.services.payment_service import create_payment_order, simulate_payment, get_order_by_no
from app.services.synastry_highlights_service import extract_synastry_highlights

logger = logging.getLogger(__name__)

PAST_LIFE_THEME_CONFIG = {
    "warrior": {
        "name": "江湖侠士",
        "icon": "⚔️",
        "keywords": ["勇气", "冒险", "守护", "战斗", "自由"],
        "core_planets": ["火星", "太阳", "木星"],
        "description": "前世是一位行走江湖的侠士，锄强扶弱，快意恩仇"
    },
    "scholar": {
        "name": "文人墨客",
        "icon": "📜",
        "keywords": ["智慧", "学习", "思考", "表达", "知识"],
        "core_planets": ["水星", "月亮", "天王星"],
        "description": "前世是一位博学鸿儒，著书立说，传道授业"
    },
    "artist": {
        "name": "艺术大家",
        "icon": "🎨",
        "keywords": ["美感", "创造", "和谐", "爱", "表达"],
        "core_planets": ["金星", "海王星", "月亮"],
        "description": "前世是一位艺术天才，琴棋书画，才情横溢"
    },
    "royal": {
        "name": "王室贵族",
        "icon": "👑",
        "keywords": ["责任", "权力", "结构", "地位", "荣耀"],
        "core_planets": ["土星", "太阳", "冥王星"],
        "description": "前世是一位王室成员，肩负重任，执掌一方"
    },
    "monk": {
        "name": "修行隐士",
        "icon": "🧘",
        "keywords": ["灵性", "内省", "超脱", "修行", "智慧"],
        "core_planets": ["海王星", "冥王星", "土星"],
        "description": "前世是一位修行者，深山问道，寻求真谛"
    },
    "merchant": {
        "name": "富商巨贾",
        "icon": "💰",
        "keywords": ["资源", "价值", "积累", "交易", "务实"],
        "core_planets": ["金星", "土星", "水星"],
        "description": "前世是一位成功商人，财源广进，乐善好施"
    },
    "healer": {
        "name": "神医济世",
        "icon": "💚",
        "keywords": ["疗愈", "关怀", "服务", "健康", "净化"],
        "core_planets": ["冥王星", "海王星", "月亮"],
        "description": "前世是一位医者，救死扶伤，仁心仁术"
    },
    "adventurer": {
        "name": "探险家",
        "icon": "🧭",
        "keywords": ["探索", "自由", "远方", "知识", "冒险"],
        "core_planets": ["木星", "天王星", "火星"],
        "description": "前世是一位探险家，跋山涉水，寻觅未知"
    }
}

PAST_LIFE_RELATIONSHIP_CONFIG = {
    "lovers": {
        "name": "宿命恋人",
        "icon": "💕",
        "keywords": ["深爱", "羁绊", "前世姻缘", "遗憾", "重逢"],
        "key_aspects": [("金星", "火星"), ("金星", "冥王星"), ("太阳", "月亮")],
        "description": "前世是刻骨铭心的恋人，这份缘分延续至今"
    },
    "mentor": {
        "name": "师徒传承",
        "icon": "👨‍🏫",
        "keywords": ["教导", "传承", "指引", "恩情", "成长"],
        "key_aspects": [("土星", "太阳"), ("土星", "水星"), ("木星", "太阳")],
        "description": "前世是师徒关系，一方给予智慧，一方虚心学习"
    },
    "rival": {
        "name": "宿敌羁绊",
        "icon": "⚔️",
        "keywords": ["竞争", "张力", "成长", "较量", "惺惺相惜"],
        "key_aspects": [("火星", "土星"), ("冥王星", "太阳"), ("天王星", "金星")],
        "description": "前世是竞争对手，但这份张力也促进了彼此的成长"
    },
    "soulmate": {
        "name": "灵魂知己",
        "icon": "💫",
        "keywords": ["理解", "共鸣", "默契", "陪伴", "认同"],
        "key_aspects": [("月亮", "月亮"), ("太阳", "月亮"), ("水星", "水星")],
        "description": "前世是灵魂伴侣，无需言语便能深刻理解彼此"
    },
    "family": {
        "name": "前世家人",
        "icon": "🏠",
        "keywords": ["亲情", "守护", "血脉", "照顾", "归属"],
        "key_aspects": [("月亮", "土星"), ("太阳", "月亮"), ("金星", "月亮")],
        "description": "前世是家人，有着深厚的血缘羁绊和情感连接"
    },
    "comrade": {
        "name": "生死之交",
        "icon": "🤝",
        "keywords": ["信任", "并肩", "承诺", "义气", "患难与共"],
        "key_aspects": [("火星", "木星"), ("太阳", "火星"), ("土星", "太阳")],
        "description": "前世是并肩作战的伙伴，共同经历过生死考验"
    },
    "stranger": {
        "name": "命中邂逅",
        "icon": "✨",
        "keywords": ["偶然", "缘分", "相遇", "新开始", "可能性"],
        "key_aspects": [("天王星", "太阳"), ("水星", "金星")],
        "description": "前世缘分较浅，但今生的相遇可能开启新的故事"
    }
}

PAST_LIFE_PRICE = 990
PAST_LIFE_SYNASTRY_PRICE = 990


def generate_share_code() -> str:
    """生成唯一分享码"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_part = uuid.uuid4().hex[:6].upper()
    return f"PL{timestamp[-8:]}{random_part}"


def safe_get(data: Dict, keys: List[str], default: Any = "") -> Any:
    """安全地从嵌套字典获取值"""
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, default if key == keys[-1] else {})
        else:
            return default
    return current


def extract_core_planets(chart_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """从星盘数据提取核心行星信息"""
    planets = chart_data.get("planets", [])
    main_planet_names = ["太阳", "月亮", "水星", "金星", "火星", "木星", "土星", "天王星", "海王星", "冥王星"]
    
    result = []
    for planet in planets:
        name = planet.get("name", "")
        if name in main_planet_names:
            zodiac = planet.get("zodiac", {})
            result.append({
                "name": name,
                "sign": zodiac.get("sign", "未知"),
                "house": planet.get("house", 0),
                "is_retrograde": planet.get("is_retrograde", False),
                "element": _get_element_by_sign(zodiac.get("sign", "")),
                "quality": _get_quality_by_sign(zodiac.get("sign", ""))
            })
    return result


def _get_element_by_sign(sign: str) -> str:
    element_map = {
        "白羊座": "火", "狮子座": "火", "射手座": "火",
        "金牛座": "土", "处女座": "土", "摩羯座": "土",
        "双子座": "风", "天秤座": "风", "水瓶座": "风",
        "巨蟹座": "水", "天蝎座": "水", "双鱼座": "水"
    }
    return element_map.get(sign, "未知")


def _get_quality_by_sign(sign: str) -> str:
    quality_map = {
        "白羊座": "开创", "巨蟹座": "开创", "天秤座": "开创", "摩羯座": "开创",
        "金牛座": "固定", "狮子座": "固定", "天蝎座": "固定", "水瓶座": "固定",
        "双子座": "变动", "处女座": "变动", "射手座": "变动", "双鱼座": "变动"
    }
    return quality_map.get(sign, "未知")


def determine_past_life_theme(planets: List[Dict[str, Any]], chart_data: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """根据星盘确定前世主题"""
    theme_scores = {}
    
    for theme_key, config in PAST_LIFE_THEME_CONFIG.items():
        score = 0
        matched_planets = []
        
        for planet in planets:
            planet_name = planet.get("name", "")
            if planet_name in config["core_planets"]:
                base_score = 20
                
                sign = planet.get("sign", "")
                house = planet.get("house", 0)
                
                if house in [1, 5, 10]:
                    base_score += 15
                elif house in [4, 7, 8]:
                    base_score += 10
                
                if planet.get("is_retrograde"):
                    base_score += 5
                
                score += base_score
                matched_planets.append({
                    "planet": planet_name,
                    "sign": sign,
                    "house": house
                })
        
        theme_scores[theme_key] = {
            "score": score,
            "matched_planets": matched_planets
        }
    
    sorted_themes = sorted(
        theme_scores.items(),
        key=lambda x: x[1]["score"],
        reverse=True
    )
    
    if sorted_themes:
        top_theme = sorted_themes[0]
        return top_theme[0], top_theme[1]
    
    return "adventurer", {"score": 0, "matched_planets": []}


def determine_past_life_relationship(synastry_highlights: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """根据合盘数据确定前世关系类型"""
    highlights = synastry_highlights.get("highlights", [])
    aspect_stats = synastry_highlights.get("aspect_stats", {})
    overall_theme = synastry_highlights.get("overall_theme", {})
    
    theme_type = overall_theme.get("type", "neutral")
    
    relationship_scores = {}
    
    for rel_key, config in PAST_LIFE_RELATIONSHIP_CONFIG.items():
        score = 0
        
        key_aspects = config.get("key_aspects", [])
        
        for highlight in highlights:
            category = highlight.get("category", "")
            matched_aspects = highlight.get("matched_aspects", [])
            
            for aspect in matched_aspects:
                planet_a = aspect.get("planet_a", "")
                planet_b = aspect.get("planet_b", "")
                
                for key_pair in key_aspects:
                    if (planet_a == key_pair[0] and planet_b == key_pair[1]) or \
                       (planet_a == key_pair[1] and planet_b == key_pair[0]):
                        base_score = 30
                        nature = aspect.get("nature", "neutral")
                        
                        if nature == "harmonious":
                            base_score += 20
                        elif nature == "challenging":
                            base_score += 10
                        
                        orb = aspect.get("orb_arcminutes", 0)
                        if orb <= 2:
                            base_score += 15
                        elif orb <= 4:
                            base_score += 10
                        
                        score += base_score
        
        if theme_type == "soulmate" and rel_key == "soulmate":
            score += 50
        elif theme_type == "passionate" and rel_key in ["lovers", "rival"]:
            score += 30
        elif theme_type == "harmonious" and rel_key in ["soulmate", "family", "comrade"]:
            score += 25
        
        relationship_scores[rel_key] = score
    
    if relationship_scores:
        sorted_rels = sorted(
            relationship_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        top_rel = sorted_rels[0]
        
        if top_rel[1] < 20:
            return "stranger", {"score": top_rel[1], "reason": "没有明显的强烈相位连接"}
        
        return top_rel[0], {"score": top_rel[1]}
    
    return "stranger", {"score": 0, "reason": "无法确定关系类型"}


def build_past_life_prompt(
    theme: str,
    planets: List[Dict[str, Any]],
    chart_data: Dict[str, Any],
    is_deep: bool = False,
    name: str = "用户"
) -> str:
    """构建前世故事生成提示词"""
    theme_config = PAST_LIFE_THEME_CONFIG.get(theme, PAST_LIFE_THEME_CONFIG["adventurer"])
    
    sun_sign = safe_get(chart_data, ["sun_sign", "sign"], "未知")
    moon_sign = safe_get(chart_data, ["moon_sign", "sign"], "未知")
    ascendant = safe_get(chart_data, ["ascendant", "sign"], "未知")
    
    prompt_parts = [
        f"""你是一位精通宿命轮回的古风仙侠故事讲述者。现在要为{name}生成一段前世故事。

【用户星盘信息】
- 太阳星座：{sun_sign}
- 月亮星座：{moon_sign}
- 上升星座：{ascendant}

【前世主题】
- 主题：{theme_config['name']} {theme_config['icon']}
- 核心特质：{', '.join(theme_config['keywords'])}
- 主题描述：{theme_config['description']}

【核心行星配置】
"""
    ]
    
    for planet in planets[:5]:
        prompt_parts.append(
            f"- {planet.get('name')}：{planet.get('sign')}，第{planet.get('house')}宫"
            f"{' (逆行)' if planet.get('is_retrograde') else ''}"
        )
    
    if is_deep:
        prompt_parts.append(f"""

【故事要求（深度版）】
请生成一个完整、细腻、充满画面感的前世故事，要求：

1. **故事结构**：
   - 开端：身世背景和童年经历（150-200字）
   - 发展：人生中的关键事件和转折点（300-400字）
   - 高潮：最刻骨铭心的经历或抉择（200-300字）
   - 结局：生命的终章和对今生的影响（150-200字）

2. **风格要求**：
   - 古风仙侠风格，语言优美，富有诗意
   - 融入具体的场景描写（山水、建筑、天气等）
   - 包含细腻的情感描写和内心独白
   - 适当加入武侠/仙侠元素（剑法、丹药、修行、门派等）

3. **细节要求**：
   - 给前世的自己起一个古风名字
   - 设定具体的年代和地点背景
   - 包含1-2个关键道具或信物
   - 描述与至少一个重要人物的关系（师父、爱人、朋友、敌人等）
   - 结尾要连接到今生：前世的经历如何影响今生的性格和命运

4. **字数要求**：总字数约 1200-1500 字

【输出格式】
请使用以下格式输出：

## 前世名号
[一个古风名字]

## 时代背景
[具体年代和地域]

## 完整故事
[分段落的完整故事，包含开端、发展、高潮、结局]

## 关键信物
[1-2个重要物品，描述其意义]

## 今生回响
[前世经历对今生性格和命运的影响]

请直接输出故事内容，不要添加任何其他说明。
""")
    else:
        prompt_parts.append(f"""

【故事要求（基础版）】
请生成一段简洁但富有画面感的前世故事摘要，要求：

1. **内容要求**：
   - 用古风仙侠的语言描述前世的身份和主要经历
   - 突出核心行星特质对应的性格和行为
   - 包含1-2个关键场景或事件
   - 结尾简要提及对今生的影响

2. **风格要求**：
   - 语言优美，富有诗意
   - 适合截图分享
   - 字数约 300-400 字

【输出格式】
请直接输出故事内容，不要添加任何其他说明。故事开头可以这样：

"你的前世是一位{theme_config['name']}，..."

""")
    
    return "\n".join(prompt_parts)


def build_synastry_past_life_prompt(
    relationship_type: str,
    person_a: Dict[str, Any],
    person_b: Dict[str, Any],
    synastry_highlights: Dict[str, Any],
    is_deep: bool = False
) -> str:
    """构建合盘前世关系故事提示词"""
    rel_config = PAST_LIFE_RELATIONSHIP_CONFIG.get(
        relationship_type, 
        PAST_LIFE_RELATIONSHIP_CONFIG["stranger"]
    )
    
    name_a = person_a.get("name", "人物A")
    name_b = person_b.get("name", "人物B")
    
    sun_a = person_a.get("sun_sign", "未知")
    sun_b = person_b.get("sun_sign", "未知")
    
    highlights = synastry_highlights.get("highlights", [])
    overall_theme = synastry_highlights.get("overall_theme", {})
    
    prompt_parts = [
        f"""你是一位精通宿命轮回的古风仙侠故事讲述者。现在要为{name_a}和{name_b}生成一段前世关系故事。

【两人基本信息】
- {name_a}：太阳{sun_a}
- {name_b}：太阳{sun_b}

【前世关系类型】
- 关系：{rel_config['name']} {rel_config['icon']}
- 核心特质：{', '.join(rel_config['keywords'])}
- 关系描述：{rel_config['description']}

【合盘亮点】
"""
    ]
    
    for h in highlights[:3]:
        prompt_parts.append(f"- {h.get('icon', '')} {h.get('name', '')}：{h.get('description', '')}")
    
    theme_name = overall_theme.get("name", "")
    if theme_name:
        prompt_parts.append(f"\n整体关系基调：{theme_name}")
    
    if is_deep:
        prompt_parts.append(f"""

【故事要求（深度版）】
请生成一个完整、细腻、充满情感的前世关系故事，要求：

1. **故事结构**：
   - 相遇：两人如何初次相遇（150-200字）
   - 羁绊：关系如何发展和深化（300-400字）
   - 考验：经历了什么困难或考验（200-300字）
   - 终章：前世关系的结局（150-200字）
   - 今生：这份羁绊对今生的影响（100-150字）

2. **风格要求**：
   - 古风仙侠风格，语言优美，富有诗意
   - 根据关系类型调整语气：
     * 恋人/灵魂知己：浪漫深情，略带宿命感
     * 师徒/家人：温暖感人，强调恩情和守护
     * 宿敌：张力十足，但也要体现惺惺相惜
     * 生死之交：豪迈义气，强调信任和承诺

3. **细节要求**：
   - 给两人起古风名字
   - 设定具体的时代背景
   - 包含共同经历的关键事件
   - 描述1-2个共同的记忆场景
   - 结尾要连接到今生：前世的关系如何影响今生的相遇和互动

4. **字数要求**：总字数约 1000-1200 字

【输出格式】
请使用以下格式输出：

## 前世名号
{name_a}前世名：[名字]
{name_b}前世名：[名字]

## 时代背景
[具体年代和地域]

## 关系故事
[分段落的完整故事]

## 共同记忆
[1-2个两人共同的深刻记忆场景]

## 今生回响
[前世关系对今生的影响和建议]

请直接输出故事内容，不要添加任何其他说明。
""")
    else:
        prompt_parts.append(f"""

【故事要求（基础版）】
请生成一段简洁但富有情感的前世关系故事摘要，要求：

1. **内容要求**：
   - 描述两人前世的关系和主要经历
   - 突出关系类型的核心特质
   - 包含1-2个关键互动场景
   - 结尾简要提及对今生关系的影响

2. **风格要求**：
   - 古风仙侠风格，语言优美
   - 适合截图分享
   - 字数约 250-350 字

【输出格式】
请直接输出故事内容，不要添加任何其他说明。
""")
    
    return "\n".join(prompt_parts)


async def generate_past_life_story(
    theme: str,
    planets: List[Dict[str, Any]],
    chart_data: Dict[str, Any],
    is_deep: bool = False,
    name: str = "用户"
) -> Dict[str, Any]:
    """生成前世故事"""
    try:
        prompt = build_past_life_prompt(theme, planets, chart_data, is_deep, name)
        
        system_prompt = """你是一位精通宿命轮回的古风仙侠故事讲述者。
你擅长将占星学符号转化为富有画面感的前世故事。
你的语言风格是古风仙侠，优美、诗意、富有想象力。
你善于创造深刻的人物和感人的情节。
请用中文回答。"""
        
        logger.info(f"生成前世故事: theme={theme}, is_deep={is_deep}")
        
        max_tokens = 2000 if is_deep else 1000
        temperature = 0.85 if is_deep else 0.75
        
        content = await call_deepseek_api(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            fast_mode=not is_deep
        )
        
        if not content or not content.strip():
            logger.warning("AI返回内容为空")
            return {
                "success": False,
                "error": "AI生成失败",
                "story": None
            }
        
        short_story = content[:450] + "..." if len(content) > 450 else content
        
        return {
            "success": True,
            "story": content,
            "short_story": short_story
        }
        
    except Exception as e:
        logger.error(f"生成前世故事失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "story": None
        }


async def generate_synastry_past_life_story(
    relationship_type: str,
    person_a: Dict[str, Any],
    person_b: Dict[str, Any],
    synastry_highlights: Dict[str, Any],
    is_deep: bool = False
) -> Dict[str, Any]:
    """生成合盘前世关系故事"""
    try:
        prompt = build_synastry_past_life_prompt(
            relationship_type, person_a, person_b, synastry_highlights, is_deep
        )
        
        system_prompt = """你是一位精通宿命轮回的古风仙侠故事讲述者。
你擅长将两人的合盘相位转化为富有情感的前世关系故事。
你的语言风格是古风仙侠，优美、诗意、富有想象力。
你善于刻画人物关系和情感羁绊。
请用中文回答。"""
        
        logger.info(f"生成合盘前世故事: relationship_type={relationship_type}, is_deep={is_deep}")
        
        max_tokens = 2000 if is_deep else 1000
        temperature = 0.85 if is_deep else 0.75
        
        content = await call_deepseek_api(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            fast_mode=not is_deep
        )
        
        if not content or not content.strip():
            logger.warning("AI返回内容为空")
            return {
                "success": False,
                "error": "AI生成失败",
                "story": None
            }
        
        short_story = content[:450] + "..." if len(content) > 450 else content
        
        return {
            "success": True,
            "story": content,
            "short_story": short_story
        }
        
    except Exception as e:
        logger.error(f"生成合盘前世故事失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "story": None
        }


def get_or_create_past_life_record(
    db: Session,
    user_id: int,
    chart_id: Optional[int] = None,
    chart_data: Optional[Dict[str, Any]] = None,
    name: str = "用户"
) -> Tuple[Optional[PastLifeRecord], Optional[str]]:
    """获取或创建前世记录"""
    try:
        existing = None
        if chart_id:
            existing = db.query(PastLifeRecord).filter(
                PastLifeRecord.user_id == user_id,
                PastLifeRecord.chart_id == chart_id,
                PastLifeRecord.is_deleted == False
            ).first()
        
        if existing:
            return existing, None
        
        if not chart_data and chart_id:
            chart = db.query(Chart).filter(
                Chart.id == chart_id,
                Chart.is_deleted == False
            ).first()
            if not chart:
                return None, "星盘不存在"
            try:
                chart_data = json.loads(chart.chart_data)
            except Exception:
                return None, "星盘数据解析失败"
        
        if not chart_data:
            return None, "缺少星盘数据"
        
        planets = extract_core_planets(chart_data)
        theme, theme_info = determine_past_life_theme(planets, chart_data)
        
        theme_config = PAST_LIFE_THEME_CONFIG.get(theme, PAST_LIFE_THEME_CONFIG["adventurer"])
        
        matched_planets = theme_info.get("matched_planets", [])
        core_planet = matched_planets[0] if matched_planets else {}
        
        record = PastLifeRecord(
            user_id=user_id,
            chart_id=chart_id,
            name=name,
            theme=theme,
            theme_name=theme_config["name"],
            core_planet=core_planet.get("planet"),
            core_sign=core_planet.get("sign"),
            core_house=core_planet.get("house"),
            share_code=generate_share_code(),
            story_metadata=json.dumps({
                "theme_score": theme_info.get("score"),
                "matched_planets": theme_info.get("matched_planets"),
                "all_planets": planets
            }, ensure_ascii=False),
            is_deleted=False
        )
        
        db.add(record)
        db.commit()
        db.refresh(record)
        
        return record, None
        
    except Exception as e:
        logger.error(f"创建前世记录失败: {e}")
        db.rollback()
        return None, str(e)


def get_or_create_synastry_past_life_record(
    db: Session,
    user_id: int,
    synastry_record_id: Optional[int] = None,
    synastry_data: Optional[Dict[str, Any]] = None,
    person_a_name: str = "人物A",
    person_b_name: str = "人物B"
) -> Tuple[Optional[PastLifeSynastryRecord], Optional[str]]:
    """获取或创建合盘前世记录"""
    try:
        existing = None
        if synastry_record_id:
            existing = db.query(PastLifeSynastryRecord).filter(
                PastLifeSynastryRecord.user_id == user_id,
                PastLifeSynastryRecord.synastry_record_id == synastry_record_id,
                PastLifeSynastryRecord.is_deleted == False
            ).first()
        
        if existing:
            return existing, None
        
        if not synastry_data and synastry_record_id:
            syn_record = db.query(SynastryRecord).filter(
                SynastryRecord.id == synastry_record_id,
                SynastryRecord.is_deleted == False
            ).first()
            if not syn_record:
                return None, "合盘记录不存在"
            try:
                synastry_data = json.loads(syn_record.synastry_data)
            except Exception:
                return None, "合盘数据解析失败"
        
        if not synastry_data:
            return None, "缺少合盘数据"
        
        highlights = extract_synastry_highlights(synastry_data)
        relationship_type, rel_info = determine_past_life_relationship(highlights)
        
        rel_config = PAST_LIFE_RELATIONSHIP_CONFIG.get(
            relationship_type, 
            PAST_LIFE_RELATIONSHIP_CONFIG["stranger"]
        )
        
        record = PastLifeSynastryRecord(
            user_id=user_id,
            synastry_record_id=synastry_record_id,
            person_a_name=person_a_name,
            person_b_name=person_b_name,
            relationship_type=relationship_type,
            relationship_name=rel_config["name"],
            share_code=generate_share_code(),
            story_metadata=json.dumps({
                "relationship_score": rel_info.get("score"),
                "highlights": highlights
            }, ensure_ascii=False),
            is_deleted=False
        )
        
        db.add(record)
        db.commit()
        db.refresh(record)
        
        return record, None
        
    except Exception as e:
        logger.error(f"创建合盘前世记录失败: {e}")
        db.rollback()
        return None, str(e)


def create_past_life_order(
    db: Session,
    user_id: int,
    record_type: str = "single",
    record_id: Optional[int] = None
) -> Tuple[Optional[PaymentOrder], Optional[str]]:
    """创建前世故事深度版订单"""
    price = PAST_LIFE_PRICE if record_type == "single" else PAST_LIFE_SYNASTRY_PRICE
    
    order, error = create_payment_order(
        db=db,
        user_id=user_id,
        payment_type=PaymentType.SINGLE_PURCHASE.value,
        amount=price,
        related_type=f"past_life_{record_type}",
        related_id=record_id,
        is_sandbox=True
    )
    
    return order, error


def upgrade_to_deep_version(
    db: Session,
    record_id: int,
    user_id: int,
    order_no: str,
    is_synastry: bool = False
) -> Tuple[bool, Optional[str]]:
    """升级到深度版"""
    try:
        order = get_order_by_no(db, order_no)
        
        if not order:
            return False, "订单不存在"
        
        if order.status != PaymentStatus.PAID.value:
            return False, "订单未支付"
        
        if is_synastry:
            record = db.query(PastLifeSynastryRecord).filter(
                PastLifeSynastryRecord.id == record_id,
                PastLifeSynastryRecord.user_id == user_id,
                PastLifeSynastryRecord.is_deleted == False
            ).first()
        else:
            record = db.query(PastLifeRecord).filter(
                PastLifeRecord.id == record_id,
                PastLifeRecord.user_id == user_id,
                PastLifeRecord.is_deleted == False
            ).first()
        
        if not record:
            return False, "记录不存在"
        
        if record.is_paid:
            return True, None
        
        record.is_paid = True
        record.payment_order_id = order.id
        
        db.commit()
        
        return True, None
        
    except Exception as e:
        logger.error(f"升级到深度版失败: {e}")
        db.rollback()
        return False, str(e)


def get_user_past_life_records(
    db: Session,
    user_id: int,
    limit: int = 20,
    offset: int = 0
) -> List[PastLifeRecord]:
    """获取用户的前世记录列表"""
    return db.query(PastLifeRecord).filter(
        PastLifeRecord.user_id == user_id,
        PastLifeRecord.is_deleted == False
    ).order_by(
        PastLifeRecord.created_at.desc()
    ).offset(offset).limit(limit).all()


def get_user_synastry_past_life_records(
    db: Session,
    user_id: int,
    limit: int = 20,
    offset: int = 0
) -> List[PastLifeSynastryRecord]:
    """获取用户的合盘前世记录列表"""
    return db.query(PastLifeSynastryRecord).filter(
        PastLifeSynastryRecord.user_id == user_id,
        PastLifeSynastryRecord.is_deleted == False
    ).order_by(
        PastLifeSynastryRecord.created_at.desc()
    ).offset(offset).limit(limit).all()


def get_past_life_by_share_code(
    db: Session,
    share_code: str
) -> Optional[Dict[str, Any]]:
    """通过分享码获取前世故事（用于分享）"""
    record = db.query(PastLifeRecord).filter(
        PastLifeRecord.share_code == share_code,
        PastLifeRecord.is_deleted == False
    ).first()
    
    if record:
        record.share_count = (record.share_count or 0) + 1
        db.commit()
        
        theme_config = PAST_LIFE_THEME_CONFIG.get(record.theme, {})
        
        return {
            "type": "single",
            "name": record.name,
            "theme": record.theme,
            "theme_name": record.theme_name,
            "theme_icon": theme_config.get("icon", "✨"),
            "basic_story": record.basic_story,
            "basic_story_short": record.basic_story_short,
            "deep_story": record.deep_story if record.is_paid else None,
            "is_paid": record.is_paid,
            "share_count": record.share_count,
            "created_at": record.created_at.isoformat() if record.created_at else None
        }
    
    syn_record = db.query(PastLifeSynastryRecord).filter(
        PastLifeSynastryRecord.share_code == share_code,
        PastLifeSynastryRecord.is_deleted == False
    ).first()
    
    if syn_record:
        syn_record.share_count = (syn_record.share_count or 0) + 1
        db.commit()
        
        rel_config = PAST_LIFE_RELATIONSHIP_CONFIG.get(syn_record.relationship_type, {})
        
        return {
            "type": "synastry",
            "person_a_name": syn_record.person_a_name,
            "person_b_name": syn_record.person_b_name,
            "relationship_type": syn_record.relationship_type,
            "relationship_name": syn_record.relationship_name,
            "relationship_icon": rel_config.get("icon", "✨"),
            "basic_story": syn_record.basic_story,
            "basic_story_short": syn_record.basic_story_short,
            "deep_story": syn_record.deep_story if syn_record.is_paid else None,
            "is_paid": syn_record.is_paid,
            "share_count": syn_record.share_count,
            "created_at": syn_record.created_at.isoformat() if syn_record.created_at else None
        }
    
    return None
