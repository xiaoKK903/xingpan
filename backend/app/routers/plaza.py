from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from dataclasses import asdict
import json
import logging
import asyncio

from app.schemas import ApiResponse, SynastryPersonInput, SynastryCalculateRequest
from app.synastry import calculate_synastry_chart
from app.services.aspect_conflict_service import (
    detect_conflict_aspects,
    analyze_conflict_intensity,
    extract_conflict_context_for_ai
)
from app.services.story_generator_service import (
    StoryContext,
    CharacterPanel,
    generate_story_v2,
    analyze_encounter_v2,
    STORY_STYLES,
    STORY_LEVELS,
    safe_get,
    get_default_story,
    determine_story_level,
    calculate_combat_outcome,
    build_character_panel_from_data,
    generate_game_character_safe
)
from app.services.plaza_advanced_service import (
    SessionState,
    EncounterType,
    SceneMemory,
    StorySession,
    SESSION_STORE,
    get_session,
    create_session,
    clear_old_sessions,
    ResourceCost,
    ItemDrop,
    BondResult,
    calculate_drop_rates,
    roll_for_drops,
    calculate_bond_gains,
    calculate_resource_cost,
    determine_mood_from_conflict,
    generate_card_panel,
    generate_scene_effects,
    generate_continuation,
    RARITY_COLORS,
    RARITY_NAMES,
    ITEM_DROP_TABLE
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["平行人生广场"])

AI_TIMEOUT_SECONDS = 45
MAX_RETRIES = 1


class StoryStyleEnum(str):
    medieval = "medieval"
    ancient = "ancient"
    scifi = "scifi"
    modern = "modern"


class PlazaEncounterRequest(BaseModel):
    person_a: SynastryPersonInput = Field(..., description="角色A的星盘信息")
    person_b: SynastryPersonInput = Field(..., description="角色B的星盘信息")
    style: str = Field("modern", description="剧情风格: medieval/ancient/scifi/modern")
    location: str = Field("广场", description="相遇地点")
    generate_story: bool = Field(True, description="是否生成AI剧情对话")
    use_cache: bool = Field(True, description="是否使用缓存")
    generate_characters: bool = Field(True, description="是否生成游戏角色面板")
    session_id: Optional[str] = Field(None, description="可选的会话ID，用于延续对话")
    encounter_type: str = Field("fated", description="相遇类型: random/fated/challenge/cooperation")


class ContinueStoryRequest(BaseModel):
    session_id: str = Field(..., description="会话ID")
    user_input: Optional[str] = Field(None, description="用户引导文本（可选）")


class ItemDropResponse(BaseModel):
    item_id: str
    item_name: str
    item_type: str
    rarity: str
    rarity_name: str
    rarity_color: str
    description: str
    quantity: int


class BondResultResponse(BaseModel):
    bond_points_gained: int
    relationship_shift: str
    new_bond_level: Optional[int] = None
    unlock_bond_story: bool = False


class ResourceCostResponse(BaseModel):
    spiritual_energy: int = 0
    physical_stamina: int = 0
    gold_coins: int = 0
    premium_points: int = 0


class CardPanelResponse(BaseModel):
    name: str
    title: str
    quality_icon: str
    element: str
    colors: Dict[str, Any]
    zodiac: Dict[str, str]
    stats: Dict[str, Any]
    passives: List[Dict[str, Any]]
    appearance: Dict[str, str]
    status: Optional[str] = None
    is_primary: bool = False


class SceneEffectsResponse(BaseModel):
    mood: str
    filter: Dict[str, Any]
    bgm: Dict[str, Any]
    particles: Dict[str, Any]
    camera: Dict[str, Any]
    vfx: Dict[str, Any]


class PlazaEncounterFullResponse(BaseModel):
    success: bool
    message: str = "success"
    encounter_id: Optional[str] = None
    session_id: Optional[str] = None
    
    conflict_analysis: Optional[Dict[str, Any]] = None
    story: Optional[Dict[str, Any]] = None
    basic_info: Optional[Dict[str, Any]] = None
    
    character_panels: Optional[Dict[str, CardPanelResponse]] = None
    combat_result: Optional[Dict[str, Any]] = None
    
    story_level: Optional[str] = None
    story_level_name: Optional[str] = None
    
    from_cache: Optional[bool] = None
    from_default: Optional[bool] = None
    
    resource_cost: Optional[ResourceCostResponse] = None
    item_drops: Optional[List[ItemDropResponse]] = None
    bond_result: Optional[BondResultResponse] = None
    
    scene_effects: Optional[SceneEffectsResponse] = None
    mood: Optional[str] = None


@router.get("/styles", response_model=ApiResponse)
async def get_available_styles():
    """获取可用的剧情风格列表"""
    styles_info = []
    for key, value in STORY_STYLES.items():
        styles_info.append({
            "key": key,
            "name": value["name"],
            "description": value["description"],
            "atmosphere": value["atmosphere_adjectives"],
            "scene_elements": value["scene_elements"]
        })
    
    return ApiResponse(
        message="获取剧情风格列表成功",
        data={"styles": styles_info}
    )


@router.get("/levels", response_model=ApiResponse)
async def get_available_levels():
    """获取可用的剧情等级列表"""
    levels_info = []
    for key, value in STORY_LEVELS.items():
        levels_info.append({
            "key": key,
            "name": value["name"],
            "max_severity": value["max_severity"],
            "style_guide": value["style_guide"],
            "dialogue_rounds": value["dialogue_rounds"]
        })
    
    return ApiResponse(
        message="获取剧情等级列表成功",
        data={"levels": levels_info}
    )


@router.get("/drop-table", response_model=ApiResponse)
async def get_drop_table():
    """获取掉落表"""
    drop_table_info = {}
    for rarity, items in ITEM_DROP_TABLE.items():
        drop_table_info[rarity] = {
            "rarity_name": RARITY_NAMES.get(rarity, rarity),
            "rarity_color": RARITY_COLORS.get(rarity, "#9CA3AF"),
            "items": [
                {
                    "item_id": item["item_id"],
                    "name": item["name"],
                    "type": item["type"],
                    "desc": item["desc"]
                }
                for item in items
            ]
        }
    
    return ApiResponse(
        message="获取掉落表成功",
        data={"drop_table": drop_table_info}
    )


@router.post("/analyze-conflict", response_model=ApiResponse)
async def analyze_aspect_conflict(request: SynastryCalculateRequest):
    """
    分析合盘相位冲突（不生成AI对话）
    """
    try:
        person_a = {
            "name": request.person_a.name or "角色A",
            "birth_date": request.person_a.birth_date,
            "birth_time": request.person_a.birth_time,
            "birth_place": request.person_a.birth_place or "",
            "latitude": request.person_a.latitude,
            "longitude": request.person_a.longitude,
            "house_system": request.person_a.house_system
        }
        
        person_b = {
            "name": request.person_b.name or "角色B",
            "birth_date": request.person_b.birth_date,
            "birth_time": request.person_b.birth_time,
            "birth_place": request.person_b.birth_place or "",
            "latitude": request.person_b.latitude,
            "longitude": request.person_b.longitude,
            "house_system": request.person_b.house_system
        }
        
        logger.info(f"开始合盘相位冲突分析: {person_a['name']} & {person_b['name']}")
        
        synastry_data = calculate_synastry_chart(person_a, person_b)
        
        aspects = synastry_data.get("synastry", {}).get("aspects", [])
        
        conflicts = detect_conflict_aspects(aspects)
        intensity = analyze_conflict_intensity(conflicts)
        conflict_context = extract_conflict_context_for_ai(
            conflicts, intensity, person_a["name"], person_b["name"]
        )
        
        story_level = determine_story_level(intensity)
        
        chart_a = synastry_data.get("person_a", {}).get("chart", {})
        chart_b = synastry_data.get("person_b", {}).get("chart", {})
        
        result = {
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
            "story_level": story_level,
            "story_level_name": STORY_LEVELS.get(story_level, {}).get("name", "中度"),
            "basic_info": {
                "person_a": {
                    "name": person_a["name"],
                    "sun_sign": chart_a.get("sun_sign", {}).get("sign", ""),
                    "moon_sign": chart_a.get("moon_sign", {}).get("sign", ""),
                    "ascendant": chart_a.get("ascendant", {}).get("sign", "")
                },
                "person_b": {
                    "name": person_b["name"],
                    "sun_sign": chart_b.get("sun_sign", {}).get("sign", ""),
                    "moon_sign": chart_b.get("moon_sign", {}).get("sign", ""),
                    "ascendant": chart_b.get("ascendant", {}).get("sign", "")
                },
                "aspect_summary": synastry_data.get("synastry", {}).get("aspect_summary", {})
            }
        }
        
        logger.info(f"相位冲突分析完成: 检测到{len(conflicts)}个关键相位, 剧情等级: {story_level}")
        
        return ApiResponse(
            message="相位冲突分析完成",
            data=result
        )
        
    except Exception as e:
        logger.error(f"相位冲突分析失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"相位冲突分析失败: {str(e)}"
        )


async def generate_story_with_timeout(
    context: StoryContext,
    use_cache: bool = True,
    timeout: int = AI_TIMEOUT_SECONDS
) -> Dict[str, Any]:
    """带超时控制的剧情生成"""
    try:
        result = await asyncio.wait_for(
            generate_story_v2(context, use_cache=use_cache, timeout_seconds=timeout),
            timeout=timeout + 5
        )
        return result
    except asyncio.TimeoutError:
        logger.warning(f"剧情生成超时 ({timeout}秒)，使用默认剧情")
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
        logger.error(f"剧情生成异常，使用默认剧情: {e}")
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


def convert_item_drops_to_response(drops: List[ItemDrop]) -> List[Dict[str, Any]]:
    return [
        {
            "item_id": drop.item_id,
            "item_name": drop.item_name,
            "item_type": drop.item_type,
            "rarity": drop.rarity,
            "rarity_name": RARITY_NAMES.get(drop.rarity, drop.rarity),
            "rarity_color": RARITY_COLORS.get(drop.rarity, "#9CA3AF"),
            "description": drop.description,
            "quantity": drop.quantity
        }
        for drop in drops
    ]


@router.post("/encounter", response_model=ApiResponse)
async def plaza_encounter(request: PlazaEncounterRequest):
    """
    广场相遇：合盘相位冲突检测 + AI剧情生成 + 完整商业化系统
    
    这个接口会：
    1. 计算两人的合盘
    2. 检测关键相位冲突
    3. 生成游戏角色面板（可选）
    4. 计算战力对比和胜负判定
    5. 生成AI剧情对话（可选）
    6. 计算灵力体力消耗
    7. 生成道具掉落
    8. 计算羁绊积分
    9. 输出卡牌面板和场景特效数据
    """
    try:
        person_a = {
            "name": request.person_a.name or "角色A",
            "birth_date": request.person_a.birth_date,
            "birth_time": request.person_a.birth_time,
            "birth_place": request.person_a.birth_place or "",
            "latitude": request.person_a.latitude,
            "longitude": request.person_a.longitude,
            "house_system": request.person_a.house_system
        }
        
        person_b = {
            "name": request.person_b.name or "角色B",
            "birth_date": request.person_b.birth_date,
            "birth_time": request.person_b.birth_time,
            "birth_place": request.person_b.birth_place or "",
            "latitude": request.person_b.latitude,
            "longitude": request.person_b.longitude,
            "house_system": request.person_b.house_system
        }
        
        logger.info(f"开始广场相遇分析: {person_a['name']} & {person_b['name']}")
        logger.info(f"剧情风格: {request.style}, 地点: {request.location}")
        
        encounter_analysis = None
        
        try:
            synastry_data = calculate_synastry_chart(person_a, person_b)
            
            encounter_analysis = await analyze_encounter_v2(
                synastry_data,
                style=request.style,
                location=request.location,
                generate_characters=request.generate_characters
            )
            
            if not encounter_analysis["success"]:
                logger.warning(f"相遇分析部分失败: {encounter_analysis.get('error')}")
                
        except Exception as e:
            logger.error(f"合盘计算失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"合盘计算失败: {str(e)}"
            )
        
        conflict_analysis = encounter_analysis.get("conflict_analysis", {})
        conflict_context = conflict_analysis.get("context", {})
        intensity = conflict_analysis.get("intensity", {})
        story_level = encounter_analysis.get("story_level", "medium")
        
        result = {
            "encounter_id": f"enc_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "conflict_analysis": conflict_analysis,
            "basic_info": encounter_analysis.get("basic_info"),
            "character_panels": None,
            "combat_result": encounter_analysis.get("combat_result"),
            "story_level": story_level,
            "story_level_name": STORY_LEVELS.get(story_level, {}).get("name", "中度"),
            "story": None,
            "from_cache": False,
            "from_default": False,
            "resource_cost": None,
            "item_drops": None,
            "bond_result": None,
            "scene_effects": None,
            "mood": None
        }
        
        character_panels = encounter_analysis.get("character_panels")
        if character_panels:
            char_a = character_panels.get("person_a")
            char_b = character_panels.get("person_b")
            combat_result = encounter_analysis.get("combat_result")
            
            if char_a:
                char_a_obj = CharacterPanel(
                    name=char_a.get("name", "角色A"),
                    sun_sign=char_a.get("sun_sign", "未知"),
                    moon_sign=char_a.get("moon_sign", "未知"),
                    ascendant=char_a.get("ascendant", "未知"),
                    dominant_element=char_a.get("dominant_element", ""),
                    dominant_quality=char_a.get("dominant_quality", ""),
                    combat_power=char_a.get("combat_power", 0),
                    stats=char_a.get("stats", {}),
                    passives=char_a.get("passives", []),
                    appearance=char_a.get("appearance", {})
                )
                result["character_panels"] = result["character_panels"] or {}
                result["character_panels"]["person_a"] = generate_card_panel(
                    char_a_obj, is_primary=True, combat_result=combat_result
                )
            
            if char_b:
                char_b_obj = CharacterPanel(
                    name=char_b.get("name", "角色B"),
                    sun_sign=char_b.get("sun_sign", "未知"),
                    moon_sign=char_b.get("moon_sign", "未知"),
                    ascendant=char_b.get("ascendant", "未知"),
                    dominant_element=char_b.get("dominant_element", ""),
                    dominant_quality=char_b.get("dominant_quality", ""),
                    combat_power=char_b.get("combat_power", 0),
                    stats=char_b.get("stats", {}),
                    passives=char_b.get("passives", []),
                    appearance=char_b.get("appearance", {})
                )
                result["character_panels"] = result["character_panels"] or {}
                result["character_panels"]["person_b"] = generate_card_panel(
                    char_b_obj, is_primary=False, combat_result=combat_result
                )
        
        mood = determine_mood_from_conflict(conflict_context, story_level)
        result["mood"] = mood
        
        scene_effects = generate_scene_effects(mood, story_level, request.style)
        result["scene_effects"] = scene_effects
        
        encounter_type = EncounterType(request.encounter_type) if request.encounter_type in [e.value for e in EncounterType] else EncounterType.FATED
        resource_cost = calculate_resource_cost(story_level, encounter_type)
        result["resource_cost"] = {
            "spiritual_energy": resource_cost.spiritual_energy,
            "physical_stamina": resource_cost.physical_stamina,
            "gold_coins": resource_cost.gold_coins,
            "premium_points": resource_cost.premium_points
        }
        
        drop_rates = calculate_drop_rates(story_level, intensity)
        drops = roll_for_drops(drop_rates, max_drops=3)
        result["item_drops"] = convert_item_drops_to_response(drops)
        
        is_harmonious = intensity.get("harmonious_count", 0) > intensity.get("challenging_count", 0)
        bond_result = calculate_bond_gains(story_level, intensity, is_harmonious)
        result["bond_result"] = {
            "bond_points_gained": bond_result.bond_points_gained,
            "relationship_shift": bond_result.relationship_shift,
            "new_bond_level": bond_result.new_bond_level,
            "unlock_bond_story": bond_result.unlock_bond_story
        }
        
        if request.generate_story:
            story_context = encounter_analysis.get("story_context")
            if story_context:
                logger.info(f"开始生成AI剧情对话...")
                
                story_result = await generate_story_with_timeout(
                    story_context,
                    use_cache=request.use_cache,
                    timeout=AI_TIMEOUT_SECONDS
                )
                
                if story_result.get("success"):
                    result["story"] = story_result.get("story")
                    result["from_cache"] = story_result.get("from_cache", False)
                    result["from_default"] = story_result.get("from_default", False)
                    
                    if story_result.get("from_cache"):
                        logger.info(f"使用缓存剧情")
                    elif story_result.get("from_default"):
                        logger.info(f"使用默认剧情（超时或错误）")
                    else:
                        logger.info(f"AI剧情生成成功")
                else:
                    logger.warning(f"AI剧情生成失败，使用默认剧情")
                    default_story = get_default_story(story_level, story_context)
                    result["story"] = default_story
                    result["from_default"] = True
        
        if request.session_id:
            session = get_session(request.session_id)
            if session and result.get("story"):
                session.update_memory(result["story"])
                result["session_id"] = session.session_id
                logger.info(f"更新会话: {session.session_id}")
        else:
            session = create_session()
            session.person_a = encounter_analysis.get("character_panels", {}).get("person_a")
            session.person_b = encounter_analysis.get("character_panels", {}).get("person_b")
            session.style = request.style
            session.story_level = story_level
            session.story_context = encounter_analysis.get("story_context")
            session.conflict_analysis = conflict_analysis
            session.combat_result = encounter_analysis.get("combat_result", {})
            session.state = SessionState.STORY_READY
            
            if result.get("story"):
                session.update_memory(result["story"])
            
            result["session_id"] = session.session_id
            logger.info(f"创建新会话: {session.session_id}")
        
        return ApiResponse(
            message="广场相遇分析完成",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"广场相遇分析失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"广场相遇分析失败: {str(e)}"
        )


@router.post("/encounter/continue", response_model=ApiResponse)
async def continue_story(request: ContinueStoryRequest):
    """
    延续对话：基于会话记忆继续生成剧情
    
    避免多轮对话失忆、剧情割裂
    """
    try:
        session = get_session(request.session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"会话不存在: {request.session_id}"
            )
        
        if session.state == SessionState.ERROR:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"会话处于错误状态: {session.error_message}"
            )
        
        logger.info(f"延续对话: 会话 {session.session_id}, 第 {session.memory.round + 1} 轮")
        
        session.state = SessionState.CONTINUING
        
        continuation_result = await generate_continuation(
            session,
            user_input=request.user_input
        )
        
        if continuation_result.get("success"):
            session.state = SessionState.STORY_READY
            
            story = continuation_result.get("story", {})
            conflict_context = session.conflict_analysis.get("context", {})
            intensity = session.conflict_analysis.get("intensity", {})
            
            drop_rates = calculate_drop_rates(session.story_level, intensity)
            drops = roll_for_drops(drop_rates, max_drops=2)
            
            is_harmonious = intensity.get("harmonious_count", 0) > intensity.get("challenging_count", 0)
            bond_result = calculate_bond_gains(session.story_level, intensity, is_harmonious)
            
            result = {
                "success": True,
                "story": story,
                "session_id": session.session_id,
                "round": session.memory.round,
                "memory_summary": session.memory.to_summary(),
                "item_drops": convert_item_drops_to_response(drops),
                "bond_result": {
                    "bond_points_gained": bond_result.bond_points_gained,
                    "relationship_shift": bond_result.relationship_shift,
                    "new_bond_level": bond_result.new_bond_level,
                    "unlock_bond_story": bond_result.unlock_bond_story
                }
            }
            
            return ApiResponse(
                message="对话延续成功",
                data=result
            )
        else:
            session.state = SessionState.ERROR
            session.error_message = continuation_result.get("error", "未知错误")
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"延续对话失败: {continuation_result.get('error')}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"延续对话失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"延续对话失败: {str(e)}"
        )


@router.get("/session/{session_id}", response_model=ApiResponse)
async def get_session_info(session_id: str):
    """获取会话信息"""
    session = get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"会话不存在: {session_id}"
        )
    
    result = {
        "session_id": session.session_id,
        "state": session.state.value,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
        "style": session.style,
        "story_level": session.story_level,
        "memory": {
            "encounter_id": session.memory.encounter_id,
            "round": session.memory.round,
            "scene_description": session.memory.scene_description,
            "mood": session.memory.mood,
            "key_events": session.memory.key_events,
            "relationship_shift": session.memory.relationship_shift,
            "dialogue_count": len(session.memory.dialogues)
        },
        "error_message": session.error_message
    }
    
    return ApiResponse(
        message="获取会话信息成功",
        data=result
    )


@router.get("/session/{session_id}/dialogues", response_model=ApiResponse)
async def get_session_dialogues(session_id: str, limit: int = Query(20, ge=1, le=100)):
    """获取会话对话历史"""
    session = get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"会话不存在: {session_id}"
        )
    
    dialogues = session.memory.dialogues[-limit:]
    
    result = {
        "session_id": session.session_id,
        "total_dialogues": len(session.memory.dialogues),
        "returned_count": len(dialogues),
        "dialogues": dialogues
    }
    
    return ApiResponse(
        message="获取对话历史成功",
        data=result
    )


@router.delete("/session/{session_id}", response_model=ApiResponse)
async def delete_session(session_id: str):
    """删除会话"""
    if session_id in SESSION_STORE:
        del SESSION_STORE[session_id]
        return ApiResponse(
            message=f"会话已删除: {session_id}",
            data={"session_id": session_id, "deleted": True}
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"会话不存在: {session_id}"
        )


async def generate_streaming_story_v2(context: StoryContext, use_cache: bool = True):
    """
    生成流式剧情输出（优化版）
    """
    yield "data: " + json.dumps({
        "type": "start",
        "message": "开始分析相位冲突..."
    }, ensure_ascii=False) + "\n\n"
    
    await asyncio.sleep(0.1)
    
    yield "data: " + json.dumps({
        "type": "progress",
        "message": "相位冲突分析完成，正在调用AI生成剧情..."
    }, ensure_ascii=False) + "\n\n"
    
    story_result = await generate_story_with_timeout(context, use_cache=use_cache)
    
    if story_result.get("from_cache"):
        yield "data: " + json.dumps({
            "type": "progress",
            "message": "从缓存读取剧情..."
        }, ensure_ascii=False) + "\n\n"
    elif story_result.get("from_default"):
        yield "data: " + json.dumps({
            "type": "progress",
            "message": "AI响应较慢，使用预设剧情..."
        }, ensure_ascii=False) + "\n\n"
    
    if not story_result.get("success"):
        yield "data: " + json.dumps({
            "type": "error",
            "message": story_result.get("error", "生成失败")
        }, ensure_ascii=False) + "\n\n"
        yield "data: [DONE]\n\n"
        return
    
    story = story_result.get("story", {})
    
    scene = story.get("scene_description", "")
    if scene:
        yield "data: " + json.dumps({
            "type": "scene",
            "content": scene
        }, ensure_ascii=False) + "\n\n"
        await asyncio.sleep(0.05)
    
    dialogues = story.get("dialogues", [])
    for dialogue in dialogues:
        speaker = dialogue.get("speaker", "")
        line = dialogue.get("line", "")
        emotion = dialogue.get("emotion", "")
        inner_thought = dialogue.get("inner_thought", "")
        
        dialogue_data = {
            "speaker": speaker,
            "emotion": emotion,
            "line": "",
            "inner_thought": inner_thought
        }
        
        for i, char in enumerate(line):
            dialogue_data["line"] = line[:i+1]
            
            yield "data: " + json.dumps({
                "type": "dialogue",
                "content": dialogue_data
            }, ensure_ascii=False) + "\n\n"
            
            await asyncio.sleep(0.02)
        
        dialogue_data["line"] = line
        yield "data: " + json.dumps({
            "type": "dialogue_complete",
            "content": dialogue_data
        }, ensure_ascii=False) + "\n\n"
    
    atmosphere = story.get("atmosphere_summary", "")
    if atmosphere:
        yield "data: " + json.dumps({
            "type": "atmosphere",
            "content": atmosphere
        }, ensure_ascii=False) + "\n\n"
    
    conflict_hint = story.get("conflict_hint", "")
    if conflict_hint:
        yield "data: " + json.dumps({
            "type": "conflict_hint",
            "content": conflict_hint
        }, ensure_ascii=False) + "\n\n"
    
    yield "data: " + json.dumps({
        "type": "complete",
        "full_story": story,
        "from_cache": story_result.get("from_cache", False),
        "from_default": story_result.get("from_default", False)
    }, ensure_ascii=False) + "\n\n"
    
    yield "data: [DONE]\n\n"


@router.post("/encounter/stream")
async def plaza_encounter_stream(request: PlazaEncounterRequest):
    """
    广场相遇（流式输出）
    
    使用 Server-Sent Events (SSE) 实现流式输出，
    让用户可以实时看到对话生成过程。
    """
    try:
        person_a = {
            "name": request.person_a.name or "角色A",
            "birth_date": request.person_a.birth_date,
            "birth_time": request.person_a.birth_time,
            "birth_place": request.person_a.birth_place or "",
            "latitude": request.person_a.latitude,
            "longitude": request.person_a.longitude,
            "house_system": request.person_a.house_system
        }
        
        person_b = {
            "name": request.person_b.name or "角色B",
            "birth_date": request.person_b.birth_date,
            "birth_time": request.person_b.birth_time,
            "birth_place": request.person_b.birth_place or "",
            "latitude": request.person_b.latitude,
            "longitude": request.person_b.longitude,
            "house_system": request.person_b.house_system
        }
        
        synastry_data = calculate_synastry_chart(person_a, person_b)
        
        encounter_analysis = await analyze_encounter_v2(
            synastry_data,
            style=request.style,
            location=request.location,
            generate_characters=request.generate_characters
        )
        
        if not encounter_analysis["success"]:
            return JSONResponse(
                status_code=500,
                content={
                    "error": encounter_analysis.get("error", "分析失败")
                }
            )
        
        story_context = encounter_analysis.get("story_context")
        
        if not story_context:
            return JSONResponse(
                status_code=500,
                content={
                    "error": "无法创建剧情上下文"
                }
            )
        
        return StreamingResponse(
            generate_streaming_story_v2(story_context, use_cache=request.use_cache),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except Exception as e:
        logger.error(f"流式相遇分析失败: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": str(e)
            }
        )


@router.post("/test-encounter", response_model=ApiResponse)
async def test_plaza_encounter():
    """
    测试接口：使用预设数据快速测试广场相遇功能
    """
    test_person_a = {
        "name": "夜行者",
        "birth_date": "1988-10-25",
        "birth_time": "22:30",
        "birth_place": "北京",
        "latitude": 39.9042,
        "longitude": 116.4074,
        "house_system": "placidus"
    }
    
    test_person_b = {
        "name": "光明使者",
        "birth_date": "1990-07-15",
        "birth_time": "08:15",
        "birth_place": "上海",
        "latitude": 31.2304,
        "longitude": 121.4737,
        "house_system": "placidus"
    }
    
    try:
        from app.schemas import SynastryPersonInput
        
        request = PlazaEncounterRequest(
            person_a=SynastryPersonInput(**test_person_a),
            person_b=SynastryPersonInput(**test_person_b),
            style="modern",
            location="神秘广场",
            generate_story=True,
            use_cache=True,
            generate_characters=True,
            encounter_type="fated"
        )
        
        return await plaza_encounter(request)
        
    except Exception as e:
        logger.error(f"测试相遇分析失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"测试相遇分析失败: {str(e)}"
        )


from app.services.energy_weather_service import (
    energy_weather_service,
    ENERGY_CONTRIBUTION_TYPES,
    WARM_MISSION_TEMPLATES,
    OMINOUS_EVENTS,
    WEATHER_SEVERITY_CONFIG,
    WeatherSeverity
)
from app.services.energy_mission_service import energy_mission_service
from app.services.community_energy_service import community_energy_service
from app.services.websocket_manager import websocket_manager
from app.database import get_db
from app.models import User, MissionCompletion
from app.routers.users import get_current_user

SIMULATED_OMINOUS_STATE = {
    "is_active": False,
    "event_key": None,
    "event_name": None,
    "severity": None,
    "activated_at": None,
    "duration_minutes": 30
}


class SimulateOminousRequest(BaseModel):
    event_key: str = Field(..., description="凶星天象事件key: mars_retrograde, mercury_retrograde 等")
    duration_minutes: int = Field(30, description="模拟持续时间(分钟)", ge=1, le=1440)


class PlazaWeatherPanelResponse(BaseModel):
    energy_score: float
    collective_mood: str
    collective_mood_label: str
    
    weather_severity: str
    weather_label: str
    weather_icon: str
    weather_color: str
    weather_bg_color: str
    weather_description: str
    
    has_warning: bool
    is_critical: bool
    warning_level: str
    
    online_user_count: int
    users_with_chart: int
    
    dominant_planets: List[Dict[str, Any]]
    dominant_aspects: List[Dict[str, Any]]
    
    ominous_events: List[Dict[str, Any]]
    dimension_energies: List[Dict[str, Any]]
    
    moon_phase: Optional[Dict[str, Any]]
    mercury_status: Optional[Dict[str, Any]]
    
    triggered_missions: List[Dict[str, Any]]
    user_assets: Optional[Dict[str, Any]]
    
    simulated_ominous: Optional[Dict[str, Any]]


@router.get("/weather-panel", response_model=ApiResponse)
async def get_plaza_weather_panel(
    db=Depends(get_db),
    current_user: Optional[User] = Depends(lambda: None)
):
    """
    广场顶部能量气象面板 - 完整数据接口
    
    一进广场就能看到的全局气象面板，包含：
    - 实时场域能量值
    - 天象状态（含凶星预警）
    - 行星分布统计
    - 相位格局分析
    - 维度能量分布
    - 触发的暖心任务
    - 用户资产信息
    """
    try:
        global SIMULATED_OMINOUS_STATE
        
        weather = energy_weather_service.get_current_weather(db)
        
        simulated_info = None
        if SIMULATED_OMINOUS_STATE["is_active"]:
            now = datetime.utcnow()
            activated_at = SIMULATED_OMINOUS_STATE.get("activated_at")
            duration = SIMULATED_OMINOUS_STATE.get("duration_minutes", 30)
            
            if activated_at and (now - activated_at).total_seconds() < duration * 60:
                event_key = SIMULATED_OMINOUS_STATE["event_key"]
                if event_key in OMINOUS_EVENTS:
                    event_config = OMINOUS_EVENTS[event_key]
                    severity = event_config.get("severity", WeatherSeverity.SEVERE)
                    
                    weather["weather_severity"] = severity.value if hasattr(severity, "value") else severity
                    
                    severity_config = WEATHER_SEVERITY_CONFIG.get(severity)
                    if severity_config:
                        weather["weather_label"] = severity_config.get("label", "雷雨")
                        weather["weather_icon"] = severity_config.get("icon", "⛈️")
                        weather["weather_color"] = severity_config.get("color", "#DC2626")
                        weather["weather_bg_color"] = severity_config.get("bg_color", "#FEF2F2")
                        weather["weather_description"] = severity_config.get("description", "")
                    
                    weather["has_warning"] = True
                    weather["is_critical"] = severity_config.get("is_critical", False) if severity_config else False
                    weather["warning_level"] = "critical" if weather["is_critical"] else "severe"
                    
                    simulated_event = {
                        "event_key": event_key,
                        "name": event_config.get("name", "未知凶星"),
                        "planet": event_config.get("planet") or event_config.get("planets"),
                        "icon": event_config.get("icon", "⚠️"),
                        "severity": severity.value if hasattr(severity, "value") else severity,
                        "description": event_config.get("description", ""),
                        "affected_areas": event_config.get("affected_areas", []),
                        "recommendations": event_config.get("recommendations", []),
                        "is_ominous": True,
                        "is_warning": True,
                        "is_critical": weather["is_critical"],
                        "is_simulated": True
                    }
                    
                    existing_ominous = weather.get("ominous_events", [])
                    weather["ominous_events"] = [simulated_event] + existing_ominous
                    
                    simulated_info = {
                        "is_active": True,
                        "event_key": event_key,
                        "event_name": event_config.get("name"),
                        "severity": severity.value if hasattr(severity, "value") else severity,
                        "activated_at": activated_at.isoformat() if activated_at else None,
                        "duration_minutes": duration,
                        "remaining_seconds": int(duration * 60 - (now - activated_at).total_seconds()) if activated_at else 0
                    }
                    
                    triggered_missions = weather.get("triggered_missions", [])
                    challenging_missions = WARM_MISSION_TEMPLATES.get("challenging", [])
                    
                    for mission in triggered_missions:
                        mission["is_bonus"] = True
                        mission["bonus_multiplier"] = 1.5
                        mission["bonus_reason"] = "凶星天象预警加成"
                    
                    if challenging_missions:
                        for mission in challenging_missions[:2]:
                            if mission.get("id") not in [m.get("template_id") for m in triggered_missions]:
                                triggered_missions.append({
                                    "id": f"sim_mission_{datetime.now().strftime('%Y%m%d%H%M')}_{len(triggered_missions)}",
                                    "type": mission.get("mission_type"),
                                    "title": mission.get("title"),
                                    "description": mission.get("description"),
                                    "difficulty": mission.get("difficulty"),
                                    "difficulty_label": {
                                        "easy": "简单",
                                        "medium": "中等",
                                        "hard": "困难"
                                    }.get(mission.get("difficulty", "medium"), "中等"),
                                    "base_reward": mission.get("base_reward", 15),
                                    "reward_currency": "星元碎片",
                                    "is_bonus": True,
                                    "bonus_multiplier": 1.5,
                                    "bonus_reason": "凶星天象特护任务 - 完成可获得额外50%星元碎片",
                                    "duration_minutes": mission.get("duration_minutes"),
                                    "energy_requirement": mission.get("energy_requirement"),
                                    "mood_trigger": "challenging",
                                    "generated_at": datetime.now().isoformat(),
                                    "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
                                    "is_triggered": True,
                                    "template_id": mission.get("id")
                                })
                    
                    weather["triggered_missions"] = triggered_missions
            else:
                SIMULATED_OMINOUS_STATE = {
                    "is_active": False,
                    "event_key": None,
                    "event_name": None,
                    "severity": None,
                    "activated_at": None,
                    "duration_minutes": 30
                }
        
        user_assets = None
        if current_user:
            user_assets = {
                "stardust_fragment_balance": current_user.stardust_fragment_balance or 0,
                "stardust_point_balance": current_user.stardust_point_balance or 0,
                "currency_info": {
                    "fragment": {
                        "name": "星元碎片",
                        "name_cn": "星元碎片",
                        "description": "任务奖励获得，用于星能共鸣池"
                    },
                    "point": {
                        "name": "星尘积分",
                        "name_cn": "星尘积分",
                        "description": "消耗型货币，用于能量注入"
                    }
                }
            }
        
        panel_data = {
            "energy_score": weather.get("overall_energy_score", 50.0),
            "collective_mood": weather.get("collective_mood", "balanced"),
            "collective_mood_label": weather.get("collective_mood_label", "平稳"),
            
            "weather_severity": weather.get("weather_severity", "mild"),
            "weather_label": weather.get("weather_label", "多云"),
            "weather_icon": weather.get("weather_icon", "⛅"),
            "weather_color": weather.get("weather_color", "#6B7280"),
            "weather_bg_color": weather.get("weather_bg_color", "#F3F4F6"),
            "weather_description": weather.get("weather_description", ""),
            
            "has_warning": weather.get("has_warning", False),
            "is_critical": weather.get("is_critical", False),
            "warning_level": weather.get("warning_level", "none"),
            
            "online_user_count": weather.get("online_user_count", 0),
            "users_with_chart": weather.get("users_with_chart", 0),
            
            "dominant_planets": weather.get("dominant_planets", []),
            "dominant_aspects": weather.get("dominant_aspects", []),
            
            "ominous_events": weather.get("ominous_events", []),
            "dimension_energies": weather.get("dimension_energies", []),
            
            "moon_phase": weather.get("moon_phase"),
            "mercury_status": weather.get("mercury_status"),
            
            "triggered_missions": weather.get("triggered_missions", []),
            "user_assets": user_assets,
            
            "simulated_ominous": simulated_info,
            
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return ApiResponse(
            message="获取广场气象面板成功",
            data=panel_data
        )
        
    except Exception as e:
        logger.error(f"获取广场气象面板失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取广场气象面板失败: {str(e)}"
        )


@router.post("/simulate-ominous", response_model=ApiResponse)
async def simulate_ominous_event(
    request: SimulateOminousRequest,
    db=Depends(get_db),
    current_user: Optional[User] = Depends(lambda: None)
):
    """
    模拟触发凶星天象 - 用于测试红色预警功能
    
    可用的事件key:
    - mars_retrograde: 火星逆行 (CRITICAL - 红色预警)
    - mercury_retrograde: 水星逆行 (SEVERE - 雷雨预警)
    - saturn_retrograde: 土星逆行 (SEVERE)
    - mars_square_saturn: 火星四分土星 (CRITICAL)
    - uranus_square_pluto: 天王星四分冥王星 (CRITICAL)
    - full_moon_eclipse: 月食 (SEVERE)
    - solar_eclipse: 日食 (SEVERE)
    """
    global SIMULATED_OMINOUS_STATE
    
    event_key = request.event_key
    
    if event_key not in OMINOUS_EVENTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_EVENT_KEY",
                "message": f"无效的凶星天象事件key: {event_key}",
                "available_events": list(OMINOUS_EVENTS.keys())
            }
        )
    
    event_config = OMINOUS_EVENTS[event_key]
    severity = event_config.get("severity", WeatherSeverity.SEVERE)
    
    SIMULATED_OMINOUS_STATE = {
        "is_active": True,
        "event_key": event_key,
        "event_name": event_config.get("name"),
        "severity": severity.value if hasattr(severity, "value") else severity,
        "activated_at": datetime.utcnow(),
        "duration_minutes": request.duration_minutes
    }
    
    severity_config = WEATHER_SEVERITY_CONFIG.get(severity)
    
    simulated_info = {
        "event_key": event_key,
        "event_name": event_config.get("name"),
        "planet": event_config.get("planet") or event_config.get("planets"),
        "icon": event_config.get("icon"),
        "severity": severity.value if hasattr(severity, "value") else severity,
        "severity_label": severity_config.get("label") if severity_config else None,
        "description": event_config.get("description"),
        "affected_areas": event_config.get("affected_areas", []),
        "recommendations": event_config.get("recommendations", []),
        
        "is_warning": severity_config.get("is_warning", False) if severity_config else True,
        "is_critical": severity_config.get("is_critical", False) if severity_config else False,
        
        "activated_at": SIMULATED_OMINOUS_STATE["activated_at"].isoformat(),
        "duration_minutes": request.duration_minutes,
        "expires_at": (SIMULATED_OMINOUS_STATE["activated_at"] + timedelta(minutes=request.duration_minutes)).isoformat()
    }
    
    try:
        await websocket_manager.broadcast(
            message_type="ominous_event_simulated",
            data={
                "event": simulated_info,
                "weather_override": {
                    "severity": severity.value if hasattr(severity, "value") else severity,
                    "label": severity_config.get("label") if severity_config else "雷雨",
                    "icon": severity_config.get("icon", "⛈️") if severity_config else "⛈️",
                    "color": severity_config.get("color", "#DC2626") if severity_config else "#DC2626",
                    "bg_color": severity_config.get("bg_color", "#FEF2F2") if severity_config else "#FEF2F2",
                    "is_warning": True,
                    "is_critical": severity_config.get("is_critical", False) if severity_config else False
                }
            },
            channel="global"
        )
    except Exception as e:
        logger.warning(f"WebSocket 广播模拟凶星事件失败: {e}")
    
    logger.warning(
        f"模拟凶星事件已激活: {event_key} ({event_config.get('name')}), "
        f"持续 {request.duration_minutes} 分钟, "
        f"严重程度: {severity.value if hasattr(severity, 'value') else severity}"
    )
    
    return ApiResponse(
        message=f"凶星天象「{event_config.get('name')}」模拟已激活，持续 {request.duration_minutes} 分钟",
        data={
            "success": True,
            "event": simulated_info,
            "warning": {
                "message": "红色预警已触发！页面将显示红色背景，任务奖励增加50%",
                "ui_effects": {
                    "bg_color_override": severity_config.get("bg_color", "#FEE2E2") if severity_config else "#FEE2E2",
                    "text_color_override": severity_config.get("color", "#991B1B") if severity_config else "#991B1B",
                    "show_warning_icon": True,
                    "show_recommendation_panel": True
                }
            }
        }
    )


@router.post("/clear-simulated-ominous", response_model=ApiResponse)
async def clear_simulated_ominous(
    db=Depends(get_db),
    current_user: Optional[User] = Depends(lambda: None)
):
    """
    清除模拟的凶星天象状态
    """
    global SIMULATED_OMINOUS_STATE
    
    previous_state = dict(SIMULATED_OMINOUS_STATE)
    
    SIMULATED_OMINOUS_STATE = {
        "is_active": False,
        "event_key": None,
        "event_name": None,
        "severity": None,
        "activated_at": None,
        "duration_minutes": 30
    }
    
    try:
        await websocket_manager.broadcast(
            message_type="ominous_event_cleared",
            data={
                "message": "模拟凶星天象已清除",
                "previous_state": previous_state
            },
            channel="global"
        )
    except Exception as e:
        logger.warning(f"WebSocket 广播清除凶星事件失败: {e}")
    
    logger.info("模拟凶星事件已清除")
    
    return ApiResponse(
        message="模拟凶星天象已清除",
        data={
            "success": True,
            "cleared_event": previous_state if previous_state.get("is_active") else None
        }
    )


@router.get("/simulated-status", response_model=ApiResponse)
async def get_simulated_ominous_status(
    db=Depends(get_db)
):
    """
    获取当前模拟凶星天象的状态
    """
    global SIMULATED_OMINOUS_STATE
    
    state = dict(SIMULATED_OMINOUS_STATE)
    
    if state.get("activated_at"):
        state["activated_at"] = state["activated_at"].isoformat()
        
        now = datetime.utcnow()
        duration = state.get("duration_minutes", 30)
        activated_at = SIMULATED_OMINOUS_STATE.get("activated_at")
        
        if activated_at:
            elapsed = (now - activated_at).total_seconds()
            remaining = max(0, duration * 60 - elapsed)
            state["remaining_seconds"] = int(remaining)
            state["elapsed_seconds"] = int(elapsed)
    
    return ApiResponse(
        message="获取模拟状态成功",
        data={
            "simulated_state": state,
            "available_events": [
                {
                    "key": key,
                    "name": config.get("name"),
                    "icon": config.get("icon"),
                    "severity": config.get("severity").value if hasattr(config.get("severity"), "value") else config.get("severity"),
                    "is_critical": WEATHER_SEVERITY_CONFIG.get(config.get("severity"), {}).get("is_critical", False)
                }
                for key, config in OMINOUS_EVENTS.items()
            ]
        }
    )


@router.get("/plaza-missions", response_model=ApiResponse)
async def get_plaza_missions(
    db=Depends(get_db),
    current_user: Optional[User] = Depends(lambda: None)
):
    """
    获取广场专属的能量暖心任务列表
    
    基于当前场域情绪自动下发的任务，包含：
    - 触发的暖心任务（基于天象和场域情绪）
    - 活跃的系统任务
    - 用户已完成的任务标记
    """
    try:
        global SIMULATED_OMINOUS_STATE
        
        weather = energy_weather_service.get_current_weather(db)
        triggered_missions = weather.get("triggered_missions", [])
        active_missions = energy_mission_service.get_active_missions(db, limit=10)
        
        is_simulated_ominous = SIMULATED_OMINOUS_STATE.get("is_active", False)
        
        if is_simulated_ominous:
            for mission in triggered_missions:
                mission["is_bonus"] = True
                mission["bonus_multiplier"] = 1.5
                mission["bonus_reason"] = "凶星天象预警加成"
        
        user_completed_missions = []
        if current_user:
            recent_completions = db.query(MissionCompletion).filter(
                MissionCompletion.user_id == current_user.id,
                MissionCompletion.created_at >= datetime.utcnow() - timedelta(hours=24)
            ).all()
            user_completed_missions = [c.mission_id for c in recent_completions]
        
        all_missions = []
        
        for mission in triggered_missions:
            mission_id = mission.get("instance_id") or mission.get("id")
            is_completed = mission_id in user_completed_missions
            
            all_missions.append({
                "id": mission_id,
                "type": mission.get("mission_type"),
                "title": mission.get("title"),
                "description": mission.get("description"),
                "difficulty": mission.get("difficulty"),
                "difficulty_label": {
                    "easy": "简单",
                    "medium": "中等",
                    "hard": "困难"
                }.get(mission.get("difficulty", "medium"), "中等"),
                "base_reward": mission.get("base_reward", 10),
                "reward_currency": "星元碎片",
                "is_bonus": mission.get("is_bonus", False),
                "bonus_multiplier": mission.get("bonus_multiplier"),
                "bonus_reason": mission.get("bonus_reason"),
                "duration_minutes": mission.get("duration_minutes"),
                "energy_requirement": mission.get("energy_requirement"),
                "mood_trigger": mission.get("mood_trigger"),
                "generated_at": mission.get("generated_at"),
                "expires_at": mission.get("expires_at"),
                "is_triggered": True,
                "template_id": mission.get("id") or mission.get("template_id"),
                "is_completed": is_completed
            })
        
        for mission in active_missions:
            mission_id = str(mission.get("id"))
            is_completed = mission_id in user_completed_missions
            
            all_missions.append({
                "id": mission_id,
                "type": mission.get("type"),
                "title": mission.get("title"),
                "description": mission.get("description"),
                "difficulty": mission.get("difficulty"),
                "difficulty_label": mission.get("difficulty_label"),
                "base_reward": mission.get("base_reward", 10),
                "reward_currency": "星元碎片",
                "is_bonus": False,
                "duration_minutes": mission.get("duration_minutes"),
                "energy_requirement": mission.get("energy_requirement"),
                "start_at": mission.get("start_at"),
                "end_at": mission.get("end_at"),
                "participant_count": mission.get("participant_count"),
                "is_triggered": False,
                "is_completed": is_completed
            })
        
        return ApiResponse(
            message="获取广场任务成功",
            data={
                "missions": all_missions,
                "count": len(all_missions),
                "collective_mood": weather.get("collective_mood"),
                "weather_label": weather.get("weather_label"),
                "has_warning": weather.get("has_warning", False) or is_simulated_ominous,
                "is_critical": weather.get("is_critical", False),
                "user_completed_today": user_completed_missions,
                "simulated_ominous": {
                    "is_active": is_simulated_ominous,
                    "event_key": SIMULATED_OMINOUS_STATE.get("event_key")
                } if is_simulated_ominous else None
            }
        )
        
    except Exception as e:
        logger.error(f"获取广场任务失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取广场任务失败: {str(e)}"
        )


@router.get("/weather-history", response_model=ApiResponse)
async def get_plaza_weather_history(
    hours: int = Query(12, ge=1, le=24, description="历史小时数"),
    db=Depends(get_db)
):
    """
    获取广场能量天气历史
    """
    try:
        history = energy_weather_service.get_weather_history(hours)
        
        return ApiResponse(
            message="获取天气历史成功",
            data={
                "history": history,
                "hours": hours,
                "count": len(history)
            }
        )
        
    except Exception as e:
        logger.error(f"获取天气历史失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取天气历史失败: {str(e)}"
        )


@router.get("/ominous-info", response_model=ApiResponse)
async def get_ominous_events_info():
    """
    获取所有凶星天象的说明信息
    """
    try:
        events_info = []
        for key, config in OMINOUS_EVENTS.items():
            severity = config.get("severity")
            severity_value = severity.value if hasattr(severity, "value") else severity
            severity_config = WEATHER_SEVERITY_CONFIG.get(severity)
            
            events_info.append({
                "event_key": key,
                "name": config.get("name"),
                "planet": config.get("planet") or config.get("planets"),
                "icon": config.get("icon"),
                "severity": severity_value,
                "severity_config": severity_config,
                "description": config.get("description"),
                "affected_areas": config.get("affected_areas"),
                "recommendations": config.get("recommendations")
            })
        
        return ApiResponse(
            message="获取凶星天象信息成功",
            data={
                "ominous_events": events_info,
                "count": len(events_info),
                "weather_severity_config": {
                    level.value if hasattr(level, "value") else level: config
                    for level, config in WEATHER_SEVERITY_CONFIG.items()
                }
            }
        )
        
    except Exception as e:
        logger.error(f"获取凶星天象信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取凶星天象信息失败: {str(e)}"
        )
