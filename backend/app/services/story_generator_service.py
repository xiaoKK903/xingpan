from typing import Dict, List, Any, Optional, AsyncGenerator
from dataclasses import dataclass, field
import logging
import json
import re
import hashlib
import asyncio
from datetime import datetime, timedelta

from app.services.aspect_conflict_service import (
    ConflictAspect,
    detect_conflict_aspects,
    analyze_conflict_intensity,
    extract_conflict_context_for_ai
)
from app.services.game_character_service import generate_game_character
from app.services.ai_service import call_deepseek_api
from app.config import settings

logger = logging.getLogger(__name__)


STORY_CACHE: Dict[str, Dict[str, Any]] = {}
CACHE_TTL_MINUTES = 60


STORY_STYLES = {
    "medieval": {
        "name": "中世纪",
        "description": "骑士、城堡、贵族、宗教、魔法、神秘主义",
        "atmosphere_adjectives": ["古老的", "神秘的", "庄严的", "浪漫的", "危险的"],
        "scene_elements": ["石板路", "蜡烛", "剑", "盾牌", "旗帜", "修道院", "酒馆"],
        "speech_pattern": "略微复古，有时使用敬语，表达较为正式",
    },
    "ancient": {
        "name": "古风",
        "description": "古代中国、仙侠、江湖、宫廷、诗词",
        "atmosphere_adjectives": ["飘逸的", "诗意的", "雅致的", "神秘的", "侠义的"],
        "scene_elements": ["宣纸", "毛笔", "剑", "玉佩", "折扇", "山水", "楼阁"],
        "speech_pattern": "文雅含蓄，善用比喻，有时引用诗句",
    },
    "scifi": {
        "name": "科幻",
        "description": "未来、太空、科技、人工智能、赛博朋克",
        "atmosphere_adjectives": ["科技感的", "冰冷的", "霓虹的", "未来的", "神秘的"],
        "scene_elements": ["全息投影", "机甲", "飞船", "植入物", "霓虹灯", "量子计算机"],
        "speech_pattern": "简洁直接，有时使用技术术语，略带疏离感",
    },
    "modern": {
        "name": "现代都市",
        "description": "现代都市生活、职场、社交网络",
        "atmosphere_adjectives": ["快节奏的", "喧嚣的", "孤独的", "时尚的", "现实的"],
        "scene_elements": ["智能手机", "咖啡馆", "写字楼", "地铁", "霓虹灯"],
        "speech_pattern": "自然随意，符合现代人的表达方式",
    }
}


STORY_LEVELS = {
    "low": {
        "name": "轻度",
        "max_severity": 3,
        "style_guide": "对话轻松愉快，冲突表现为微妙的误会或小摩擦，结局温馨有趣",
        "temperature": 0.7,
        "max_tokens": 1500,
        "dialogue_rounds": 2
    },
    "medium": {
        "name": "中度",
        "max_severity": 6,
        "style_guide": "对话有明显的张力，表现为观点分歧或性格碰撞，但最终能够达成某种理解",
        "temperature": 0.8,
        "max_tokens": 2000,
        "dialogue_rounds": 3
    },
    "high": {
        "name": "高度",
        "max_severity": 10,
        "style_guide": "对话充满戏剧性张力，表现为激烈的冲突、权力斗争或深刻的情感碰撞，结局开放且充满可能性",
        "temperature": 0.85,
        "max_tokens": 2500,
        "dialogue_rounds": 4
    }
}


@dataclass
class CharacterPanel:
    name: str = ""
    sun_sign: str = ""
    moon_sign: str = ""
    ascendant: str = ""
    dominant_element: str = ""
    dominant_quality: str = ""
    combat_power: int = 0
    stats: Dict[str, Any] = field(default_factory=dict)
    passives: List[Dict[str, Any]] = field(default_factory=list)
    appearance: Dict[str, Any] = field(default_factory=dict)
    stelliums: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class StoryContext:
    person_a: CharacterPanel = field(default_factory=CharacterPanel)
    person_b: CharacterPanel = field(default_factory=CharacterPanel)
    conflict_context: Dict[str, Any] = field(default_factory=dict)
    style: str = "modern"
    location: str = "广场"
    story_level: str = "medium"
    combat_result: Dict[str, Any] = field(default_factory=dict)
    
    def get_cache_key(self) -> str:
        key_parts = [
            self.person_a.sun_sign,
            self.person_a.moon_sign,
            self.person_b.sun_sign,
            self.person_b.moon_sign,
            self.style,
            self.story_level,
            json.dumps(self.conflict_context.get("dominant_tag", ""), ensure_ascii=False)
        ]
        key_str = "_".join(str(p) for p in key_parts)
        return hashlib.md5(key_str.encode("utf-8")).hexdigest()


def safe_get(data: Dict[str, Any], keys: List[str], default: Any = "") -> Any:
    """安全地从嵌套字典中获取值，避免KeyError"""
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, default if key == keys[-1] else {})
        else:
            return default
    return current


def clean_markdown(text: str) -> str:
    """清洗Markdown格式"""
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'`(.*?)`', r'\1', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def robust_json_parse(text: str) -> Dict[str, Any]:
    """鲁棒的JSON解析"""
    text = clean_markdown(text)
    
    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        json_str = json_match.group()
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
    
    scene_match = re.search(r'scene_description["\s:]+([^"\n]+)', text, re.IGNORECASE)
    dialogue_matches = re.findall(r'speaker["\s:]+([^"\n]+).*?line["\s:]+([^"\n]+)', text, re.IGNORECASE | re.DOTALL)
    
    fallback = {
        "scene_description": scene_match.group(1) if scene_match else "两人在广场偶然相遇",
        "dialogues": [],
        "atmosphere_summary": "",
        "conflict_hint": ""
    }
    
    for speaker, line in dialogue_matches[:6]:
        fallback["dialogues"].append({
            "speaker": speaker.strip(),
            "line": line.strip(),
            "emotion": "",
            "inner_thought": ""
        })
    
    return fallback


def determine_story_level(conflict_intensity: Dict[str, Any]) -> str:
    """根据冲突强度确定剧情等级"""
    code = conflict_intensity.get("conflict_level_code", 1)
    avg_severity = conflict_intensity.get("average_severity", 0)
    
    if code <= 1 or avg_severity <= 3:
        return "low"
    elif code <= 2 or avg_severity <= 6:
        return "medium"
    else:
        return "high"


def calculate_combat_outcome(
    char_a: CharacterPanel,
    char_b: CharacterPanel,
    conflict_context: Dict[str, Any]
) -> Dict[str, Any]:
    """计算战斗结果，形成数值→剧情闭环"""
    cp_a = char_a.combat_power or 0
    cp_b = char_b.combat_power or 0
    
    is_challenging = conflict_context.get("intensity", {}).get("challenging_count", 0) > 0
    is_harmonious = conflict_context.get("intensity", {}).get("harmonious_count", 0) > 0
    
    conflict_modifier = 1.0
    if is_challenging:
        conflict_modifier = 1.2
    elif is_harmonious:
        conflict_modifier = 0.9
    
    effective_a = cp_a * conflict_modifier
    effective_b = cp_b * conflict_modifier
    
    passives_a = char_a.passives or []
    passives_b = char_b.passives or []
    
    for p in passives_a:
        if p.get("effect_type") == "attack_burn":
            effective_a *= 1.1
        elif p.get("effect_type") == "damage_reduction":
            effective_b *= 0.9
        elif p.get("effect_type") == "extra_action":
            effective_a *= 1.05
        elif p.get("effect_type") == "healing":
            effective_a *= 1.05
    
    for p in passives_b:
        if p.get("effect_type") == "attack_burn":
            effective_b *= 1.1
        elif p.get("effect_type") == "damage_reduction":
            effective_a *= 0.9
        elif p.get("effect_type") == "extra_action":
            effective_b *= 1.05
        elif p.get("effect_type") == "healing":
            effective_b *= 1.05
    
    diff = effective_a - effective_b
    threshold = max(cp_a, cp_b) * 0.1
    
    if diff > threshold:
        winner = char_a.name or "角色A"
        outcome = "压倒性优势"
    elif diff < -threshold:
        winner = char_b.name or "角色B"
        outcome = "压倒性优势"
    else:
        if cp_a > cp_b:
            winner = char_a.name or "角色A"
        elif cp_b > cp_a:
            winner = char_b.name or "角色B"
        else:
            winner = "平局"
        outcome = "势均力敌"
    
    return {
        "winner": winner,
        "outcome": outcome,
        "power_a": round(effective_a),
        "power_b": round(effective_b),
        "base_power_a": cp_a,
        "base_power_b": cp_b,
        "conflict_modifier": conflict_modifier,
        "passive_effects": {
            "a_applied": len(passives_a),
            "b_applied": len(passives_b)
        }
    }


def build_character_profile(char: CharacterPanel) -> str:
    """构建角色简介，用于提示词"""
    parts = []
    
    parts.append(f"【{char.name}】")
    
    parts.append(f"星盘特质：太阳{char.sun_sign}，月亮{char.moon_sign}，上升{char.ascendant}")
    
    if char.dominant_element:
        element_desc = {
            "火": "火象主导，热情主动，充满活力",
            "土": "土象主导，稳重务实，追求稳定",
            "风": "风象主导，灵活善变，善于沟通",
            "水": "水象主导，敏感细腻，情感丰富"
        }.get(char.dominant_element, f"{char.dominant_element}象主导")
        parts.append(f"元素特质：{element_desc}")
    
    if char.dominant_quality:
        quality_desc = {
            "开创": "开创特质，积极主动，善于发起",
            "固定": "固定特质，坚韧执着，善于坚持",
            "变动": "变动特质，灵活适应，善于变化"
        }.get(char.dominant_quality, f"{char.dominant_quality}特质")
        parts.append(f"性格特质：{quality_desc}")
    
    if char.combat_power > 0:
        parts.append(f"综合战力：{char.combat_power}")
    
    if char.appearance and char.appearance.get("overall_description"):
        appearance_desc = char.appearance["overall_description"][:100]
        if len(appearance_desc) == 100:
            appearance_desc += "..."
        parts.append(f"外貌气质：{appearance_desc}")
    
    if char.passives and len(char.passives) > 0:
        passive_names = [p.get("name", "") for p in char.passives[:2] if p.get("name")]
        if passive_names:
            parts.append(f"天赋技能：{', '.join(passive_names)}")
    
    return "\n".join(parts)


def build_story_system_prompt_v2(style: str, story_level: str) -> str:
    """优化版系统提示词，更简洁明确"""
    style_info = STORY_STYLES.get(style, STORY_STYLES["modern"])
    level_info = STORY_LEVELS.get(story_level, STORY_LEVELS["medium"])
    
    return f"""你是{style_info['name']}风格对话生成助手。

【任务】
根据两人的星盘特质和相位冲突，生成{style_info['name']}风格的相遇对话。

【风格要求】
- 场景：{style_info['name']}风格的广场
- 对话：{style_info['speech_pattern']}
- 氛围：{', '.join(style_info['atmosphere_adjectives'])}
- 场景元素：{', '.join(style_info['scene_elements'])}

【剧情等级：{level_info['name']}】
{level_info['style_guide']}
对话轮数：每人{level_info['dialogue_rounds']}轮

【输出格式（JSON）】
{{
    "scene_description": "场景描述（50-100字）",
    "dialogues": [
        {{
            "speaker": "角色名",
            "line": "对话内容",
            "emotion": "情绪/动作描述",
            "inner_thought": "（可选）内心独白"
        }}
    ],
    "atmosphere_summary": "氛围总结（30-50字）",
    "conflict_hint": "相位冲突体现（20-40字）"
}}

【重要】
1. 严格输出JSON，不要其他内容
2. 对话要自然，不要解释占星知识
3. 冲突体现在语气、用词、潜台词中
4. 角色性格要符合星盘特质"""


def build_story_user_prompt_v2(context: StoryContext) -> str:
    """优化版用户提示词，更简洁"""
    level_info = STORY_LEVELS.get(context.story_level, STORY_LEVELS["medium"])
    
    parts = []
    
    parts.append("【角色信息】")
    parts.append(build_character_profile(context.person_a))
    parts.append("")
    parts.append(build_character_profile(context.person_b))
    
    if context.combat_result and context.combat_result.get("winner") != "平局":
        parts.append("")
        parts.append("【战力对比】")
        parts.append(f"{context.person_a.name}战力：{context.combat_result.get('power_a', 0)}")
        parts.append(f"{context.person_b.name}战力：{context.combat_result.get('power_b', 0)}")
        parts.append(f"结果：{context.combat_result.get('winner', '未知')} {context.combat_result.get('outcome', '')}")
    
    conflict_ctx = context.conflict_context
    if conflict_ctx.get("has_conflict", False):
        parts.append("")
        parts.append("【相位冲突】")
        parts.append(conflict_ctx.get("summary", ""))
        
        dominant_tag = conflict_ctx.get("dominant_tag")
        if dominant_tag:
            parts.append(f"核心冲突：{dominant_tag}")
        
        details = conflict_ctx.get("conflict_details", [])
        if details:
            parts.append("关键相位：")
            for d in details[:3]:
                parts.append(f"- {d.get('planet_pair', '')} {d.get('aspect_type', '')}：{d.get('drama_theme', '')}")
    else:
        parts.append("")
        parts.append("【关系基调】")
        parts.append("没有明显冲突相位，关系基调和谐。创作温馨有趣的相遇场景。")
    
    parts.append("")
    parts.append("【相遇设定】")
    parts.append(f"地点：{context.location}")
    parts.append(f"风格：{STORY_STYLES.get(context.style, STORY_STYLES['modern'])['name']}")
    parts.append(f"对话轮数：每人{level_info['dialogue_rounds']}轮")
    
    return "\n".join(parts)


def get_cached_story(cache_key: str) -> Optional[Dict[str, Any]]:
    """从缓存获取剧情"""
    if cache_key in STORY_CACHE:
        cached = STORY_CACHE[cache_key]
        if datetime.now() - cached["timestamp"] < timedelta(minutes=CACHE_TTL_MINUTES):
            logger.info(f"缓存命中: {cache_key}")
            return cached["data"]
        else:
            del STORY_CACHE[cache_key]
    return None


def set_cached_story(cache_key: str, data: Dict[str, Any]):
    """设置缓存"""
    STORY_CACHE[cache_key] = {
        "data": data,
        "timestamp": datetime.now()
    }
    if len(STORY_CACHE) > 100:
        oldest = min(STORY_CACHE.keys(), key=lambda k: STORY_CACHE[k]["timestamp"])
        del STORY_CACHE[oldest]


async def generate_game_character_safe(chart_data: Dict[str, Any], name: str) -> Dict[str, Any]:
    """安全地生成游戏角色"""
    try:
        return await generate_game_character(chart_data, name)
    except Exception as e:
        logger.warning(f"生成游戏角色失败，使用默认值: {e}")
        return {
            "success": False,
            "character": {
                "name": name,
                "stats": {"combat_power": 100},
                "passives": [],
                "appearance": {"overall_description": "气质独特的旅人"},
                "astro_source": {}
            }
        }


def build_character_panel_from_data(
    chart_data: Dict[str, Any],
    game_character: Optional[Dict[str, Any]],
    name: str
) -> CharacterPanel:
    """从数据构建角色面板"""
    panel = CharacterPanel(name=name or "神秘旅人")
    
    panel.sun_sign = safe_get(chart_data, ["sun_sign", "sign"], "未知")
    panel.moon_sign = safe_get(chart_data, ["moon_sign", "sign"], "未知")
    panel.ascendant = safe_get(chart_data, ["ascendant", "sign"], "未知")
    
    if game_character and game_character.get("success"):
        char_data = game_character.get("character", {})
        
        panel.combat_power = safe_get(char_data, ["stats", "combat_power"], 0)
        panel.stats = safe_get(char_data, ["stats"], {})
        panel.passives = safe_get(char_data, ["passives"], [])
        panel.appearance = safe_get(char_data, ["appearance"], {})
        
        astro_source = safe_get(char_data, ["astro_source"], {})
        panel.dominant_element = safe_get(astro_source, ["dominant_element"], "")
        panel.dominant_quality = safe_get(astro_source, ["dominant_quality"], "")
        panel.stelliums = safe_get(astro_source, ["stelliums"], [])
    
    return panel


DEFAULT_STORIES = {
    "low": {
        "scene_description": "阳光明媚的广场上，两个路人偶然相撞，手中的物品散落一地。空气中弥漫着轻松友好的气息。",
        "dialogues": [
            {"speaker": "角色A", "line": "抱歉抱歉！没看到你过来，东西掉了一地。", "emotion": "弯腰捡东西，有些尴尬", "inner_thought": "真是的，走路也不看路..."},
            {"speaker": "角色B", "line": "没关系没关系，我也没注意看路。这些是你的吗？", "emotion": "帮忙捡起物品，微笑着", "inner_thought": "这个人看起来还挺友善的"},
            {"speaker": "角色A", "line": "太感谢了！今天真是幸运，遇到你这么好的人。", "emotion": "接过物品，感激地说", "inner_thought": ""},
            {"speaker": "角色B", "line": "小事一桩。既然这么有缘，要不要一起喝杯咖啡？", "emotion": "友好地提议", "inner_thought": "感觉可以交个朋友"}
        ],
        "atmosphere_summary": "轻松愉快的相遇，两人之间充满友好的气息。",
        "conflict_hint": "没有明显的相位冲突，展现了和谐的互动。"
    },
    "medium": {
        "scene_description": "广场中央，两个气场截然不同的人目光交汇。空气中弥漫着微妙的张力，仿佛命运在此刻做出了某种安排。",
        "dialogues": [
            {"speaker": "角色A", "line": "我们是不是在哪里见过？你的眼神让我感觉...很熟悉。", "emotion": "直视对方，带着探究的意味", "inner_thought": "这个人...有种说不出的吸引力"},
            {"speaker": "角色B", "line": "也许是在另一个时空吧。不过现在，我们确实是在这里相遇了。", "emotion": "微微一笑，眼神中带着深意", "inner_thought": "他/她似乎能感觉到什么..."},
            {"speaker": "角色A", "line": "你相信命运吗？还是说，一切都只是偶然？", "emotion": "走近一步，认真地问", "inner_thought": "我想更了解这个人"},
            {"speaker": "角色B", "line": "命运？偶然？也许两者都是。重要的是，你现在想怎么做？", "emotion": "毫不退缩地对视", "inner_thought": "有趣，这个人很特别"}
        ],
        "atmosphere_summary": "微妙的张力中带着吸引力，两人之间存在着某种宿命般的连接。",
        "conflict_hint": "相位冲突体现在微妙的目光交汇和试探性的对话中。"
    },
    "high": {
        "scene_description": "雷雨将至的广场，两个气场强大的人迎面而立。空气中充满了电荷般的张力，仿佛一场风暴即将爆发。",
        "dialogues": [
            {"speaker": "角色A", "line": "你挡到我的路了。这是故意的吗？", "emotion": "冷眼看着对方，语气中带着挑战", "inner_thought": "这个人...气场很强"},
            {"speaker": "角色B", "line": "路是大家的，我站在这里碍着你什么事了？", "emotion": "毫不示弱地回视，嘴角带着挑衅的笑", "inner_thought": "想和我斗？奉陪到底"},
            {"speaker": "角色A", "line": "有意思。很久没有人敢这样和我说话了。", "emotion": "释放出更强的气场，逼近一步", "inner_thought": "这个人...有点意思"},
            {"speaker": "角色B", "line": "那是因为你还没遇到真正的对手。", "emotion": "纹丝不动，气场反而更强", "inner_thought": "想压我？没那么容易"}
        ],
        "atmosphere_summary": "激烈的权力对峙，两人之间充满了对抗的张力，但也隐藏着致命的吸引力。",
        "conflict_hint": "相位冲突体现在强烈的气场碰撞和权力对抗中。"
    }
}


def get_default_story(story_level: str, context: Optional[StoryContext] = None) -> Dict[str, Any]:
    """获取默认剧情，超时时使用"""
    level_key = story_level if story_level in DEFAULT_STORIES else "medium"
    story = DEFAULT_STORIES[level_key].copy()
    
    if context:
        for dialogue in story["dialogues"]:
            if dialogue["speaker"] == "角色A" and context.person_a.name:
                dialogue["speaker"] = context.person_a.name
            elif dialogue["speaker"] == "角色B" and context.person_b.name:
                dialogue["speaker"] = context.person_b.name
    
    return story


async def generate_story_v2(
    context: StoryContext,
    use_cache: bool = True,
    timeout_seconds: int = 60
) -> Dict[str, Any]:
    """优化版剧情生成"""
    cache_key = context.get_cache_key()
    
    if use_cache:
        cached = get_cached_story(cache_key)
        if cached:
            return {
                "success": True,
                "story": cached,
                "from_cache": True,
                "context_info": {
                    "person_a_name": context.person_a.name,
                    "person_b_name": context.person_b.name,
                    "style": context.style,
                    "story_level": context.story_level
                }
            }
    
    level_info = STORY_LEVELS.get(context.story_level, STORY_LEVELS["medium"])
    
    try:
        system_prompt = build_story_system_prompt_v2(context.style, context.story_level)
        user_prompt = build_story_user_prompt_v2(context)
        
        logger.info(f"生成剧情: {context.person_a.name} & {context.person_b.name}, 等级: {context.story_level}")
        
        response = await call_deepseek_api(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=level_info["temperature"],
            max_tokens=level_info["max_tokens"],
            fast_mode=True
        )
        
        story_data = robust_json_parse(response)
        
        if story_data and story_data.get("dialogues"):
            set_cached_story(cache_key, story_data)
            
            return {
                "success": True,
                "story": story_data,
                "from_cache": False,
                "raw_response": response,
                "context_info": {
                    "person_a_name": context.person_a.name,
                    "person_b_name": context.person_b.name,
                    "style": context.style,
                    "story_level": context.story_level
                }
            }
        else:
            logger.warning("AI返回格式异常，使用默认剧情")
            default_story = get_default_story(context.story_level, context)
            return {
                "success": True,
                "story": default_story,
                "from_default": True,
                "raw_response": response,
                "context_info": {
                    "person_a_name": context.person_a.name,
                    "person_b_name": context.person_b.name,
                    "style": context.style,
                    "story_level": context.story_level
                }
            }
            
    except asyncio.TimeoutError:
        logger.warning("AI调用超时，使用默认剧情")
        default_story = get_default_story(context.story_level, context)
        return {
            "success": True,
            "story": default_story,
            "from_default": True,
            "timeout": True,
            "context_info": {
                "person_a_name": context.person_a.name,
                "person_b_name": context.person_b.name,
                "style": context.style,
                "story_level": context.story_level
            }
        }
    except Exception as e:
        logger.error(f"生成剧情失败，使用默认剧情: {e}")
        default_story = get_default_story(context.story_level, context)
        return {
            "success": True,
            "story": default_story,
            "from_default": True,
            "error": str(e),
            "context_info": {
                "person_a_name": context.person_a.name,
                "person_b_name": context.person_b.name,
                "style": context.style,
                "story_level": context.story_level
            }
        }


async def analyze_encounter_v2(
    synastry_data: Dict[str, Any],
    style: str = "modern",
    location: str = "广场",
    generate_characters: bool = True
) -> Dict[str, Any]:
    """优化版相遇分析"""
    try:
        person_a = safe_get(synastry_data, ["person_a"], {})
        person_b = safe_get(synastry_data, ["person_b"], {})
        
        name_a = safe_get(person_a, ["name"], "角色A")
        name_b = safe_get(person_b, ["name"], "角色B")
        
        chart_a = safe_get(person_a, ["chart"], {})
        chart_b = safe_get(person_b, ["chart"], {})
        
        synastry = safe_get(synastry_data, ["synastry"], {})
        aspects = safe_get(synastry, ["aspects"], [])
        
        conflicts = detect_conflict_aspects(aspects)
        intensity = analyze_conflict_intensity(conflicts)
        conflict_context = extract_conflict_context_for_ai(conflicts, intensity, name_a, name_b)
        
        story_level = determine_story_level(intensity)
        
        char_a = CharacterPanel(name=name_a)
        char_b = CharacterPanel(name=name_b)
        
        if generate_characters:
            try:
                game_char_a = await generate_game_character_safe(chart_a, name_a)
                game_char_b = await generate_game_character_safe(chart_b, name_b)
                
                char_a = build_character_panel_from_data(chart_a, game_char_a, name_a)
                char_b = build_character_panel_from_data(chart_b, game_char_b, name_b)
            except Exception as e:
                logger.warning(f"生成角色面板失败: {e}")
                char_a.sun_sign = safe_get(chart_a, ["sun_sign", "sign"], "未知")
                char_a.moon_sign = safe_get(chart_a, ["moon_sign", "sign"], "未知")
                char_a.ascendant = safe_get(chart_a, ["ascendant", "sign"], "未知")
                
                char_b.sun_sign = safe_get(chart_b, ["sun_sign", "sign"], "未知")
                char_b.moon_sign = safe_get(chart_b, ["moon_sign", "sign"], "未知")
                char_b.ascendant = safe_get(chart_b, ["ascendant", "sign"], "未知")
        
        context = StoryContext(
            person_a=char_a,
            person_b=char_b,
            conflict_context=conflict_context,
            style=style,
            location=location,
            story_level=story_level
        )
        
        combat_result = calculate_combat_outcome(char_a, char_b, conflict_context)
        context.combat_result = combat_result
        
        return {
            "success": True,
            "story_context": context,
            "conflict_analysis": {
                "conflicts": [
                    {
                        "planet_pair": f"{c.planet_a}与{c.planet_b}",
                        "aspect_type": c.aspect_type,
                        "drama_theme": c.drama_theme,
                        "atmosphere": c.atmosphere,
                        "conflict_tags": c.conflict_tags,
                        "severity": c.severity,
                        "is_harmonious": c.is_harmonious,
                        "orb_arcminutes": round(c.orb_arcminutes, 2) if c.orb_arcminutes else 0
                    }
                    for c in conflicts
                ],
                "intensity": intensity,
                "context": conflict_context
            },
            "character_panels": {
                "person_a": {
                    "name": char_a.name,
                    "sun_sign": char_a.sun_sign,
                    "moon_sign": char_a.moon_sign,
                    "ascendant": char_a.ascendant,
                    "dominant_element": char_a.dominant_element,
                    "dominant_quality": char_a.dominant_quality,
                    "combat_power": char_a.combat_power,
                    "stats": char_a.stats,
                    "passives": char_a.passives,
                    "appearance": char_a.appearance
                },
                "person_b": {
                    "name": char_b.name,
                    "sun_sign": char_b.sun_sign,
                    "moon_sign": char_b.moon_sign,
                    "ascendant": char_b.ascendant,
                    "dominant_element": char_b.dominant_element,
                    "dominant_quality": char_b.dominant_quality,
                    "combat_power": char_b.combat_power,
                    "stats": char_b.stats,
                    "passives": char_b.passives,
                    "appearance": char_b.appearance
                }
            },
            "combat_result": combat_result,
            "story_level": story_level,
            "basic_info": {
                "person_a": {
                    "name": name_a,
                    "sun_sign": char_a.sun_sign,
                    "moon_sign": char_a.moon_sign,
                    "ascendant": char_a.ascendant
                },
                "person_b": {
                    "name": name_b,
                    "sun_sign": char_b.sun_sign,
                    "moon_sign": char_b.moon_sign,
                    "ascendant": char_b.ascendant
                },
                "style": style,
                "location": location,
                "story_level": story_level
            }
        }
        
    except Exception as e:
        logger.error(f"分析相遇场景失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }
