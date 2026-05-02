from typing import Dict, List, Any, Optional, AsyncGenerator, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging
import json
import re
import hashlib
import asyncio
import random
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from app.services.story_generator_service import (
    CharacterPanel,
    StoryContext,
    STORY_STYLES,
    STORY_LEVELS,
    DEFAULT_STORIES,
    safe_get,
    determine_story_level,
    calculate_combat_outcome,
    build_character_profile,
    build_story_system_prompt_v2,
    build_story_user_prompt_v2,
    robust_json_parse,
    get_default_story,
    STORY_CACHE,
    CACHE_TTL_MINUTES
)
from app.services.ai_service import call_deepseek_api, DEEPSEEK_FLASH_MODEL, FAST_DEEPSEEK_MODEL

logger = logging.getLogger(__name__)


class SessionState(Enum):
    IDLE = "idle"
    ANALYZING = "analyzing"
    GENERATING = "generating"
    STORY_READY = "story_ready"
    CONTINUING = "continuing"
    ERROR = "error"


class EncounterType(Enum):
    RANDOM = "random"
    FATED = "fated"
    CHALLENGE = "challenge"
    COOPERATION = "cooperation"


@dataclass
class SceneMemory:
    encounter_id: str = ""
    round: int = 0
    scene_description: str = ""
    dialogues: List[Dict[str, Any]] = field(default_factory=list)
    atmosphere_summary: str = ""
    conflict_hint: str = ""
    mood: str = "neutral"
    key_events: List[str] = field(default_factory=list)
    relationship_shift: str = "neutral"
    
    def to_summary(self) -> str:
        parts = []
        parts.append(f"场景: {self.scene_description[:100]}...")
        parts.append(f"已进行 {self.round} 轮对话")
        if self.key_events:
            parts.append(f"关键事件: {', '.join(self.key_events[-3:])}")
        parts.append(f"关系变化: {self.relationship_shift}")
        parts.append(f"当前氛围: {self.mood}")
        return " | ".join(parts)
    
    def to_dialogue_summary(self, max_lines: int = 6) -> str:
        recent = self.dialogues[-max_lines:]
        lines = []
        for d in recent:
            speaker = d.get("speaker", "某人")
            line = d.get("line", "")
            emotion = d.get("emotion", "")
            if emotion:
                lines.append(f"[{speaker} ({emotion})]: {line}")
            else:
                lines.append(f"[{speaker}]: {line}")
        return "\n".join(lines)


@dataclass
class StorySession:
    session_id: str
    state: SessionState = SessionState.IDLE
    person_a: Optional[CharacterPanel] = None
    person_b: Optional[CharacterPanel] = None
    style: str = "modern"
    story_level: str = "medium"
    story_context: Optional[StoryContext] = None
    conflict_analysis: Dict[str, Any] = field(default_factory=dict)
    combat_result: Dict[str, Any] = field(default_factory=dict)
    memory: SceneMemory = field(default_factory=SceneMemory)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    error_message: Optional[str] = None
    
    def update_memory(self, story_data: Dict[str, Any]):
        self.memory.round += 1
        self.memory.scene_description = story_data.get("scene_description", self.memory.scene_description)
        
        new_dialogues = story_data.get("dialogues", [])
        self.memory.dialogues.extend(new_dialogues)
        
        self.memory.atmosphere_summary = story_data.get("atmosphere_summary", self.memory.atmosphere_summary)
        self.memory.conflict_hint = story_data.get("conflict_hint", self.memory.conflict_hint)
        self.updated_at = datetime.now()


SESSION_STORE: Dict[str, StorySession] = {}


def get_session(session_id: str) -> Optional[StorySession]:
    return SESSION_STORE.get(session_id)


def create_session(session_id: str = None) -> StorySession:
    if not session_id:
        session_id = f"sess_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"
    session = StorySession(session_id=session_id)
    SESSION_STORE[session_id] = session
    return session


def clear_old_sessions(max_age_minutes: int = 60):
    now = datetime.now()
    to_delete = []
    for sid, session in SESSION_STORE.items():
        if (now - session.updated_at) > timedelta(minutes=max_age_minutes):
            to_delete.append(sid)
    for sid in to_delete:
        del SESSION_STORE[sid]
    if to_delete:
        logger.info(f"清理了 {len(to_delete)} 个过期会话")


@dataclass
class ResourceCost:
    spiritual_energy: int = 0
    physical_stamina: int = 0
    gold_coins: int = 0
    premium_points: int = 0


@dataclass
class ItemDrop:
    item_id: str
    item_name: str
    item_type: str
    rarity: str
    description: str
    quantity: int = 1
    icon: Optional[str] = None


@dataclass
class BondResult:
    bond_points_gained: int
    relationship_shift: str
    new_bond_level: Optional[int] = None
    unlock_bond_story: bool = False


ITEM_DROP_TABLE: Dict[str, List[Dict[str, Any]]] = {
    "common": [
        {"item_id": "crystal_fragment", "name": "灵力碎片", "type": "material", "rarity": "common", "desc": "蕴含微弱灵力的碎片", "weight": 50},
        {"item_id": "stamina_potion", "name": "体力药剂", "type": "consumable", "rarity": "common", "desc": "恢复少量体力", "weight": 30},
        {"item_id": "gold_coin", "name": "金币", "type": "currency", "rarity": "common", "desc": "通用货币", "weight": 20},
    ],
    "uncommon": [
        {"item_id": "star_essence", "name": "星辰精华", "type": "material", "rarity": "uncommon", "desc": "蕴含星辰之力的精华", "weight": 40},
        {"item_id": "bond_crystal", "name": "羁绊水晶", "type": "special", "rarity": "uncommon", "desc": "可增加羁绊值的特殊水晶", "weight": 35},
        {"item_id": "lucky_charm", "name": "幸运符", "type": "consumable", "rarity": "uncommon", "desc": "提升下次掉落概率", "weight": 25},
    ],
    "rare": [
        {"item_id": "fate_medal", "name": "宿命徽章", "type": "special", "rarity": "rare", "desc": "宿命相遇的纪念徽章", "weight": 50},
        {"item_id": "astral_gem", "name": "星灵宝石", "type": "material", "rarity": "rare", "desc": "蕴含强大灵力的宝石", "weight": 30},
        {"item_id": "premium_ticket", "name": "高级券", "type": "ticket", "rarity": "rare", "desc": "可用于高级抽卡", "weight": 20},
    ],
    "legendary": [
        {"item_id": "destiny_book", "name": "命运之书", "type": "legendary", "rarity": "legendary", "desc": "记录两人命运的神秘书籍", "weight": 60},
        {"item_id": "soul_contract", "name": "灵魂契约", "type": "legendary", "rarity": "legendary", "desc": "绑定灵魂的契约", "weight": 40},
    ]
}

RARITY_COLORS = {
    "common": "#9CA3AF",
    "uncommon": "#22C55E",
    "rare": "#3B82F6",
    "legendary": "#A855F7"
}

RARITY_NAMES = {
    "common": "普通",
    "uncommon": "精良",
    "rare": "稀有",
    "legendary": "传说"
}


def calculate_drop_rates(story_level: str, conflict_intensity: Dict[str, Any]) -> Dict[str, float]:
    base_rates = {
        "low": {"common": 0.85, "uncommon": 0.14, "rare": 0.01, "legendary": 0.0},
        "medium": {"common": 0.65, "uncommon": 0.28, "rare": 0.065, "legendary": 0.005},
        "high": {"common": 0.45, "uncommon": 0.35, "rare": 0.17, "legendary": 0.03}
    }
    
    level = story_level if story_level in base_rates else "medium"
    rates = base_rates[level].copy()
    
    severity = conflict_intensity.get("average_severity", 5)
    if severity > 7:
        rates["rare"] += 0.03
        rates["legendary"] += 0.01
        rates["common"] -= 0.04
    
    is_harmonious = conflict_intensity.get("harmonious_count", 0) > conflict_intensity.get("challenging_count", 0)
    if is_harmonious:
        rates["uncommon"] += 0.02
        rates["common"] -= 0.02
    
    return rates


def roll_for_drops(drop_rates: Dict[str, float], max_drops: int = 3) -> List[ItemDrop]:
    drops = []
    num_drops = random.randint(1, max_drops)
    
    for _ in range(num_drops):
        roll = random.random()
        cumulative = 0
        rarity = "common"
        
        for r in ["legendary", "rare", "uncommon", "common"]:
            cumulative += drop_rates.get(r, 0)
            if roll <= cumulative:
                rarity = r
                break
        
        table = ITEM_DROP_TABLE.get(rarity, ITEM_DROP_TABLE["common"])
        total_weight = sum(item["weight"] for item in table)
        roll2 = random.randint(1, total_weight)
        
        current_weight = 0
        selected_item = table[0]
        for item in table:
            current_weight += item["weight"]
            if roll2 <= current_weight:
                selected_item = item
                break
        
        quantity = 1
        if rarity == "common":
            quantity = random.randint(1, 5)
        elif rarity == "uncommon":
            quantity = random.randint(1, 3)
        
        drop = ItemDrop(
            item_id=selected_item["item_id"],
            item_name=selected_item["name"],
            item_type=selected_item["type"],
            rarity=rarity,
            description=selected_item["desc"],
            quantity=quantity
        )
        drops.append(drop)
    
    return drops


def calculate_bond_gains(
    story_level: str,
    conflict_intensity: Dict[str, Any],
    is_harmonious: bool
) -> BondResult:
    base_points = {
        "low": 10,
        "medium": 25,
        "high": 50
    }
    
    points = base_points.get(story_level, 15)
    
    if is_harmonious:
        points = int(points * 1.5)
        relationship = "more_positive"
    else:
        relationship = "more_intense"
    
    if conflict_intensity.get("conflict_level_code", 1) >= 3:
        points += 20
        relationship = "destined"
    
    return BondResult(
        bond_points_gained=points,
        relationship_shift=relationship
    )


def calculate_resource_cost(story_level: str, encounter_type: EncounterType) -> ResourceCost:
    base_costs = {
        "low": {"spiritual": 5, "physical": 3, "gold": 0, "premium": 0},
        "medium": {"spiritual": 15, "physical": 8, "gold": 100, "premium": 0},
        "high": {"spiritual": 30, "physical": 15, "gold": 300, "premium": 0}
    }
    
    costs = base_costs.get(story_level, base_costs["medium"])
    
    if encounter_type == EncounterType.CHALLENGE:
        costs["spiritual"] = int(costs["spiritual"] * 1.5)
        costs["physical"] = int(costs["physical"] * 1.5)
    
    return ResourceCost(
        spiritual_energy=costs["spiritual"],
        physical_stamina=costs["physical"],
        gold_coins=costs["gold"],
        premium_points=costs["premium"]
    )


MOOD_TO_FILTER = {
    "romantic": {"filter": "warm", "intensity": 0.8},
    "tense": {"filter": "dramatic", "intensity": 0.9},
    "mysterious": {"filter": "mystic", "intensity": 0.7},
    "joyful": {"filter": "bright", "intensity": 0.8},
    "melancholic": {"filter": "soft", "intensity": 0.6},
    "epic": {"filter": "cinematic", "intensity": 1.0},
    "neutral": {"filter": "normal", "intensity": 0.5}
}

MOOD_TO_BGM = {
    "romantic": ["bgm_romantic_soft", "bgm_romantic_epic"],
    "tense": ["bgm_tense_suspense", "bgm_tense_battle"],
    "mysterious": ["bgm_mystery_atmos", "bgm_mystery_dark"],
    "joyful": ["bgm_joyful_upbeat", "bgm_joyful_tender"],
    "melancholic": ["bgm_sad_piano", "bgm_sad_strings"],
    "epic": ["bgm_epic_orchestra", "bgm_epic_chorus"],
    "neutral": ["bgm_generic_ambient"]
}

CONFLICT_TAG_TO_MOOD = {
    "致命吸引": "romantic",
    "互相吸引": "romantic",
    "权力斗争": "tense",
    "深度控制": "tense",
    "沟通不畅": "tense",
    "极致激情": "epic",
    "情感共鸣": "romantic",
    "自我与情感融合": "romantic",
    "爱与欲望交织": "romantic",
    "激烈冲突": "tense",
    "宿命连接": "mysterious"
}


def determine_mood_from_conflict(conflict_context: Dict[str, Any], story_level: str) -> str:
    dominant_tag = conflict_context.get("dominant_tag", "")
    
    if dominant_tag in CONFLICT_TAG_TO_MOOD:
        return CONFLICT_TAG_TO_MOOD[dominant_tag]
    
    all_tags = conflict_context.get("all_tags", [])
    for tag in all_tags:
        if tag in CONFLICT_TAG_TO_MOOD:
            return CONFLICT_TAG_TO_MOOD[tag]
    
    if story_level == "high":
        return "epic"
    elif story_level == "medium":
        return "mysterious"
    
    return "neutral"


def generate_card_panel(
    character: CharacterPanel,
    is_primary: bool = False,
    combat_result: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    element_colors = {
        "火": {"primary": "#EF4444", "gradient": ["#FCA5A5", "#DC2626"]},
        "土": {"primary": "#92400E", "gradient": ["#D97706", "#78350F"]},
        "风": {"primary": "#059669", "gradient": ["#34D399", "#047857"]},
        "水": {"primary": "#2563EB", "gradient": ["#60A5FA", "#1D4ED8"]}
    }
    
    element = character.dominant_element or "火"
    colors = element_colors.get(element, element_colors["火"])
    
    quality_icons = {
        "开创": "⚡",
        "固定": "🗿",
        "变动": "🌊"
    }
    
    status = None
    if combat_result:
        winner = combat_result.get("winner", "")
        if winner == character.name:
            status = "winner"
        elif winner != "平局":
            status = "loser"
        else:
            status = "draw"
    
    passive_display = []
    for p in (character.passives or [])[:3]:
        passive_display.append({
            "name": p.get("name", ""),
            "desc": p.get("description", "")[:50] + "..." if len(p.get("description", "")) > 50 else p.get("description", ""),
            "effect": p.get("effect_type", ""),
            "value": p.get("effect_value", 0)
        })
    
    stats = character.stats or {}
    cp = stats.get("combat_power", 0) or character.combat_power
    
    cp_level = "E"
    if cp >= 800:
        cp_level = "S"
    elif cp >= 600:
        cp_level = "A"
    elif cp >= 400:
        cp_level = "B"
    elif cp >= 200:
        cp_level = "C"
    elif cp >= 100:
        cp_level = "D"
    
    return {
        "name": character.name,
        "title": f"{character.dominant_element or '神秘'}象{character.dominant_quality or ''}旅者",
        "quality_icon": quality_icons.get(character.dominant_quality, "✨"),
        "element": element,
        "colors": colors,
        "zodiac": {
            "sun": character.sun_sign,
            "moon": character.moon_sign,
            "ascendant": character.ascendant
        },
        "stats": {
            "combat_power": cp,
            "cp_level": cp_level,
            "health": stats.get("health", 100),
            "max_health": stats.get("max_health", 100),
            "attack": stats.get("attack", 10),
            "defense": stats.get("defense", 5),
            "speed": stats.get("speed", 5),
            "critical_rate": stats.get("critical_rate", 5),
            "critical_damage": stats.get("critical_damage", 150)
        },
        "passives": passive_display,
        "appearance": {
            "description": character.appearance.get("overall_description", "")[:100] if character.appearance else "",
            "aura": character.appearance.get("aura", "") if character.appearance else ""
        },
        "status": status,
        "is_primary": is_primary
    }


def generate_scene_effects(
    mood: str,
    story_level: str,
    style: str
) -> Dict[str, Any]:
    filter_info = MOOD_TO_FILTER.get(mood, MOOD_TO_FILTER["neutral"])
    bgm_options = MOOD_TO_BGM.get(mood, MOOD_TO_BGM["neutral"])
    
    style_effects = {
        "modern": {
            "particles": ["sparkle", "glow", "wind"],
            "camera_angle": "dynamic"
        },
        "medieval": {
            "particles": ["dust", "firefly", "light_ray"],
            "camera_angle": "cinematic"
        },
        "ancient": {
            "particles": ["cherry_blossom", "ink_splash", "mist"],
            "camera_angle": "artistic"
        },
        "scifi": {
            "particles": ["hologram", "energy_pulse", "data_stream"],
            "camera_angle": "tech"
        }
    }
    
    effects = style_effects.get(style, style_effects["modern"])
    
    intensity_multiplier = {
        "low": 0.5,
        "medium": 1.0,
        "high": 1.5
    }.get(story_level, 1.0)
    
    return {
        "mood": mood,
        "filter": {
            "type": filter_info["filter"],
            "intensity": filter_info["intensity"] * intensity_multiplier
        },
        "bgm": {
            "options": bgm_options,
            "volume": 0.7 if story_level == "low" else 0.9
        },
        "particles": {
            "types": effects["particles"],
            "density": 0.3 if story_level == "low" else 0.6 if story_level == "medium" else 1.0
        },
        "camera": {
            "angle": effects["camera_angle"],
            "movement": "subtle" if story_level == "low" else "dynamic"
        },
        "vfx": {
            "encounter_animation": f"encounter_{mood}",
            "dialogue_animation": f"dialogue_{story_level}"
        }
    }


def build_continuation_system_prompt(style: str, story_level: str) -> str:
    style_info = STORY_STYLES.get(style, STORY_STYLES["modern"])
    level_info = STORY_LEVELS.get(story_level, STORY_LEVELS["medium"])
    
    return f"""你是{style_info['name']}风格的对话延续助手。

【任务】
根据之前的对话历史，继续两人的对话。保持角色人设一致，延续当前的剧情张力。

【风格要求】
- 场景：{style_info['name']}风格
- 对话：{style_info['speech_pattern']}

【剧情等级：{level_info['name']}】
{level_info['style_guide']}

【输出格式（JSON）】
{{
    "dialogues": [
        {{
            "speaker": "角色名",
            "line": "对话内容",
            "emotion": "情绪/动作描述",
            "inner_thought": "（可选）内心独白"
        }}
    ],
    "mood_shift": "情绪变化描述",
    "key_event": "（可选）关键事件描述"
}}

【重要】
1. 严格延续之前的对话语境
2. 保持角色性格一致
3. 继续推进剧情，不要重复
4. 严格输出JSON"""


def build_continuation_user_prompt(
    session: StorySession,
    user_input: Optional[str] = None
) -> str:
    parts = []
    
    parts.append("【之前的对话历史】")
    parts.append(session.memory.to_dialogue_summary())
    
    parts.append("")
    parts.append("【场景上下文】")
    parts.append(session.memory.to_summary())
    
    parts.append("")
    parts.append("【角色信息】")
    if session.person_a:
        parts.append(build_character_profile(session.person_a))
    parts.append("")
    if session.person_b:
        parts.append(build_character_profile(session.person_b))
    
    if user_input:
        parts.append("")
        parts.append("【用户引导】")
        parts.append(user_input)
    
    parts.append("")
    parts.append("请继续这段对话。每人说1-2轮。")
    
    return "\n".join(parts)


async def generate_continuation(
    session: StorySession,
    user_input: Optional[str] = None,
    use_cache: bool = False
) -> Dict[str, Any]:
    if not session.person_a or not session.person_b:
        return {"success": False, "error": "会话中缺少角色信息"}
    
    system_prompt = build_continuation_system_prompt(session.style, session.story_level)
    user_prompt = build_continuation_user_prompt(session, user_input)
    
    try:
        response = await call_deepseek_api(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.85,
            max_tokens=1500,
            fast_mode=True
        )
        
        story_data = robust_json_parse(response)
        
        if story_data and story_data.get("dialogues"):
            mood_shift = story_data.get("mood_shift", "")
            if mood_shift:
                session.memory.mood = mood_shift
            
            key_event = story_data.get("key_event", "")
            if key_event:
                session.memory.key_events.append(key_event)
            
            session.update_memory(story_data)
            
            return {
                "success": True,
                "story": story_data,
                "session_id": session.session_id,
                "round": session.memory.round
            }
        else:
            return {"success": False, "error": "无法解析AI响应"}
            
    except Exception as e:
        logger.error(f"生成延续对话失败: {e}")
        return {"success": False, "error": str(e)}


async def parallel_preheat(
    person_a: CharacterPanel,
    person_b: CharacterPanel,
    style: str,
    story_level: str
) -> None:
    pass


SESSION_STORE = {}
