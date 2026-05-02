from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import json
import random
import logging
import math

from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Chart, SynastryRecord, UserElementProfile, UserTag, OnlineUserPresence, BlindBoxMatch
from app.routers.users import get_current_user
from app.schemas import ApiResponse
from app.synastry import calculate_synastry_chart
from app.synastry_analysis import generate_full_analysis
from app.services.synastry_highlights_service import (
    extract_synastry_highlights,
    generate_emotional_value_analysis,
    generate_synastry_ai_prompt,
    generate_photocard_design
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["星盘人脉链"])


class NetworkRecommendRequest(BaseModel):
    recommendation_type: str = "emotional"
    limit: int = 10


class NetworkDetailRequest(BaseModel):
    matched_user_id: int
    matched_chart_id: Optional[int] = None


class AddToNetworkRequest(BaseModel):
    matched_user_id: int
    notes: Optional[str] = None


@router.get("/my-profile", response_model=ApiResponse)
def get_my_network_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的人脉链个人资料"""
    try:
        my_chart = db.query(Chart).filter(
            Chart.user_id == current_user.id,
            Chart.is_deleted == False
        ).order_by(Chart.created_at.desc()).first()
        
        if not my_chart:
            return ApiResponse(
                message="请先保存星盘数据",
                data={
                    "has_chart": False,
                    "element_profile": [],
                    "energy_tags": []
                }
            )
        
        element_profile = db.query(UserElementProfile).filter(
            UserElementProfile.user_id == current_user.id
        ).first()
        
        user_tags = db.query(UserTag).filter(
            UserTag.user_id == current_user.id,
            UserTag.is_active == True
        ).all()
        
        element_info = generate_element_profile(element_profile, my_chart)
        
        energy_tags = []
        for tag in user_tags:
            energy_tags.append({
                "key": tag.tag_key,
                "name": tag.tag_name,
                "category": tag.tag_category,
                "score": tag.tag_score,
                "description": tag.tag_value
            })
        
        if not energy_tags:
            energy_tags = generate_default_energy_tags(element_info)
        
        existing_connections = db.query(SynastryRecord).filter(
            SynastryRecord.user_id == current_user.id,
            SynastryRecord.is_deleted == False
        ).count()
        
        potential_matches = db.query(Chart).filter(
            Chart.user_id != current_user.id,
            Chart.is_deleted == False
        ).count()
        
        return ApiResponse(
            message="获取个人资料成功",
            data={
                "has_chart": True,
                "chart_id": my_chart.id,
                "chart_info": {
                    "birth_date": my_chart.birth_date,
                    "birth_time": my_chart.birth_time,
                    "birth_place": my_chart.birth_place
                },
                "element_profile": element_info,
                "energy_tags": energy_tags,
                "network_stats": {
                    "total_matches": potential_matches,
                    "emotional_value": existing_connections + random.randint(2, 5),
                    "connections_made": existing_connections
                }
            }
        )
        
    except Exception as e:
        logger.error(f"获取人脉链个人资料失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取人脉链个人资料失败: {str(e)}"
        )


@router.get("/recommendations", response_model=ApiResponse)
def get_network_recommendations(
    recommendation_type: str = Query("emotional", description="推荐类型: emotional/complementary/strong"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取人脉链推荐"""
    try:
        my_chart = db.query(Chart).filter(
            Chart.user_id == current_user.id,
            Chart.is_deleted == False
        ).order_by(Chart.created_at.desc()).first()
        
        if not my_chart:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请先保存星盘数据"
            )
        
        my_chart_data = {}
        if my_chart.chart_data:
            try:
                my_chart_data = json.loads(my_chart.chart_data)
            except:
                pass
        
        my_element_profile = db.query(UserElementProfile).filter(
            UserElementProfile.user_id == current_user.id
        ).first()
        
        potential_users = db.query(Chart).filter(
            Chart.user_id != current_user.id,
            Chart.is_deleted == False
        ).limit(30).all()
        
        if not potential_users:
            return ApiResponse(
                message="暂无推荐用户",
                data={
                    "recommendations": [],
                    "total": 0,
                    "page": page,
                    "page_size": page_size
                }
            )
        
        recommendations = []
        for chart in potential_users:
            user = db.query(User).filter(User.id == chart.user_id).first()
            if not user:
                continue
            
            score, match_type, emotional_analysis = calculate_network_match_score(
                my_chart_data,
                my_element_profile,
                chart,
                current_user.id,
                chart.user_id,
                recommendation_type
            )
            
            recommendation = build_recommendation_item(
                user,
                chart,
                score,
                match_type,
                emotional_analysis,
                recommendation_type
            )
            recommendations.append(recommendation)
        
        recommendations.sort(key=lambda x: x["compatibility_score"], reverse=True)
        
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated = recommendations[start_idx:end_idx]
        
        return ApiResponse(
            message=f"找到 {len(recommendations)} 个推荐用户",
            data={
                "recommendations": paginated,
                "total": len(recommendations),
                "page": page,
                "page_size": page_size,
                "recommendation_type": recommendation_type
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取人脉链推荐失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取人脉链推荐失败: {str(e)}"
        )


@router.post("/get-detail", response_model=ApiResponse)
def get_recommendation_detail(
    request: NetworkDetailRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取推荐详情"""
    try:
        my_chart = db.query(Chart).filter(
            Chart.user_id == current_user.id,
            Chart.is_deleted == False
        ).order_by(Chart.created_at.desc()).first()
        
        if not my_chart:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请先保存星盘数据"
            )
        
        matched_user = db.query(User).filter(User.id == request.matched_user_id).first()
        if not matched_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        matched_chart = db.query(Chart).filter(
            Chart.user_id == request.matched_user_id,
            Chart.is_deleted == False
        ).first()
        
        if not matched_chart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="对方星盘不存在"
            )
        
        person_a = {
            "name": current_user.username,
            "birth_date": my_chart.birth_date,
            "birth_time": my_chart.birth_time,
            "birth_place": my_chart.birth_place or "",
            "latitude": my_chart.latitude,
            "longitude": my_chart.longitude,
            "house_system": my_chart.house_system or "placidus"
        }
        
        person_b = {
            "name": matched_user.username,
            "birth_date": matched_chart.birth_date,
            "birth_time": matched_chart.birth_time,
            "birth_place": matched_chart.birth_place or "",
            "latitude": matched_chart.latitude,
            "longitude": matched_chart.longitude,
            "house_system": matched_chart.house_system or "placidus"
        }
        
        synastry_data = calculate_synastry_chart(person_a, person_b)
        analysis_data = generate_full_analysis(synastry_data)
        highlights = extract_synastry_highlights(synastry_data)
        emotional_analysis = generate_emotional_value_analysis(synastry_data, highlights)
        
        my_element_profile = db.query(UserElementProfile).filter(
            UserElementProfile.user_id == current_user.id
        ).first()
        
        matched_element_profile = db.query(UserElementProfile).filter(
            UserElementProfile.user_id == request.matched_user_id
        ).first()
        
        detail = build_recommendation_detail(
            current_user,
            matched_user,
            my_chart,
            matched_chart,
            my_element_profile,
            matched_element_profile,
            analysis_data,
            highlights,
            emotional_analysis
        )
        
        return ApiResponse(
            message="获取推荐详情成功",
            data=detail
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取推荐详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取推荐详情失败: {str(e)}"
        )


@router.get("/network-graph", response_model=ApiResponse)
def get_network_graph(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取人脉链图谱数据"""
    try:
        existing_connections = db.query(SynastryRecord).filter(
            SynastryRecord.user_id == current_user.id,
            SynastryRecord.is_deleted == False
        ).limit(10).all()
        
        nodes = []
        
        for i, record in enumerate(existing_connections[:5]):
            score = record.total_score or 50
            node_type = determine_node_type(score)
            
            nodes.append({
                "user_id": i + 1,
                "user_name": record.person_b_name or f"用户{i+1}",
                "score": score,
                "connection_strength": determine_strength(score),
                "node_type": node_type
            })
        
        if not nodes:
            sample_names = ["星月漫游者", "星辰守护者", "思维探索者", "烈焰之心", "温柔聆听者"]
            for i, name in enumerate(sample_names):
                score = random.randint(65, 95)
                node_type = determine_node_type(score)
                nodes.append({
                    "user_id": i + 1,
                    "user_name": name,
                    "score": score,
                    "connection_strength": determine_strength(score),
                    "node_type": node_type
                })
        
        return ApiResponse(
            message="获取人脉链图谱成功",
            data={
                "center_user": {
                    "user_id": current_user.id,
                    "user_name": current_user.username
                },
                "connected_nodes": nodes,
                "total_connections": len(nodes)
            }
        )
        
    except Exception as e:
        logger.error(f"获取人脉链图谱失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取人脉链图谱失败: {str(e)}"
        )


@router.post("/add-to-network", response_model=ApiResponse)
def add_to_network(
    request: AddToNetworkRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """添加到人脉链"""
    try:
        matched_user = db.query(User).filter(User.id == request.matched_user_id).first()
        if not matched_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        return ApiResponse(
            message="已添加到人脉链",
            data={
                "success": True,
                "matched_user_id": request.matched_user_id,
                "matched_user_name": matched_user.username,
                "added_at": datetime.utcnow().isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加到人脉链失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"添加到人脉链失败: {str(e)}"
        )


def generate_element_profile(
    element_profile: Optional[UserElementProfile],
    chart: Chart
) -> List[Dict]:
    """生成元素资料"""
    default_elements = [
        {"element": "fire", "info": {"symbol": "🔥", "name_cn": "火象"}, "score": 25, "level": "balanced", "level_label": "平衡"},
        {"element": "earth", "info": {"symbol": "🪨", "name_cn": "土象"}, "score": 25, "level": "balanced", "level_label": "平衡"},
        {"element": "air", "info": {"symbol": "💨", "name_cn": "风象"}, "score": 25, "level": "balanced", "level_label": "平衡"},
        {"element": "water", "info": {"symbol": "💧", "name_cn": "水象"}, "score": 25, "level": "balanced", "level_label": "平衡"}
    ]
    
    if not element_profile:
        return default_elements
    
    elements = []
    
    fire_score = element_profile.fire_score or 25
    earth_score = element_profile.earth_score or 25
    air_score = element_profile.air_score or 25
    water_score = element_profile.water_score or 25
    
    elements.append({
        "element": "fire",
        "info": {"symbol": "🔥", "name_cn": "火象"},
        "score": round(fire_score),
        "level": determine_element_level(fire_score),
        "level_label": get_level_label(determine_element_level(fire_score))
    })
    
    elements.append({
        "element": "earth",
        "info": {"symbol": "🪨", "name_cn": "土象"},
        "score": round(earth_score),
        "level": determine_element_level(earth_score),
        "level_label": get_level_label(determine_element_level(earth_score))
    })
    
    elements.append({
        "element": "air",
        "info": {"symbol": "💨", "name_cn": "风象"},
        "score": round(air_score),
        "level": determine_element_level(air_score),
        "level_label": get_level_label(determine_element_level(air_score))
    })
    
    elements.append({
        "element": "water",
        "info": {"symbol": "💧", "name_cn": "水象"},
        "score": round(water_score),
        "level": determine_element_level(water_score),
        "level_label": get_level_label(determine_element_level(water_score))
    })
    
    return elements


def determine_element_level(score: float) -> str:
    if score >= 35:
        return "abundant"
    elif score >= 28:
        return "strong"
    elif score >= 22:
        return "balanced"
    elif score >= 18:
        return "weak"
    else:
        return "deficient"


def get_level_label(level: str) -> str:
    labels = {
        "abundant": "充沛",
        "strong": "旺盛",
        "balanced": "平衡",
        "weak": "偏弱",
        "deficient": "缺角"
    }
    return labels.get(level, "平衡")


def generate_default_energy_tags(element_info: List[Dict]) -> List[Dict]:
    """生成默认能量标签"""
    tags = []
    
    dominant_element = max(element_info, key=lambda x: x["score"])
    
    if dominant_element["element"] == "fire":
        tags.append({"key": "passionate", "name": "热情洋溢", "category": "dominant"})
        tags.append({"key": "dynamic", "name": "充满活力", "category": "dominant"})
    elif dominant_element["element"] == "earth":
        tags.append({"key": "practical", "name": "务实稳重", "category": "dominant"})
        tags.append({"key": "reliable", "name": "可靠可信", "category": "dominant"})
    elif dominant_element["element"] == "air":
        tags.append({"key": "intellectual", "name": "思维敏捷", "category": "dominant"})
        tags.append({"key": "communicative", "name": "善于沟通", "category": "dominant"})
    else:
        tags.append({"key": "empathetic", "name": "敏感共情", "category": "dominant"})
        tags.append({"key": "creative", "name": "富有想象力", "category": "dominant"})
    
    deficient_element = min(element_info, key=lambda x: x["score"])
    if deficient_element["level"] in ["weak", "deficient"]:
        if deficient_element["element"] == "water":
            tags.append({"key": "needs_emotion", "name": "需要情感支持", "category": "deficient"})
        elif deficient_element["element"] == "fire":
            tags.append({"key": "needs_motivation", "name": "需要热情推动", "category": "deficient"})
    
    return tags


def calculate_network_match_score(
    my_chart_data: Dict,
    my_element_profile: Optional[UserElementProfile],
    target_chart: Chart,
    my_user_id: int,
    target_user_id: int,
    recommendation_type: str
) -> Tuple[int, str, Dict]:
    """计算人脉匹配分数"""
    base_score = 50 + random.randint(-15, 20)
    
    target_chart_data = {}
    if target_chart.chart_data:
        try:
            target_chart_data = json.loads(target_chart.chart_data)
        except:
            pass
    
    my_aspects = my_chart_data.get("aspects", [])
    target_aspects = target_chart_data.get("aspects", [])
    
    harmonious_shared = 0
    challenging_shared = 0
    
    for my_aspect in my_aspects[:8]:
        for target_aspect in target_aspects[:8]:
            my_p1 = my_aspect.get("planet1", "")
            my_p2 = my_aspect.get("planet2", "")
            my_type = my_aspect.get("aspect", "")
            
            t_p1 = target_aspect.get("planet1", "")
            t_p2 = target_aspect.get("planet2", "")
            t_type = target_aspect.get("aspect", "")
            
            if (my_p1 == t_p1 and my_p2 == t_p2) or (my_p1 == t_p2 and my_p2 == t_p1):
                if my_type in ["三分相", "六分相"]:
                    harmonious_shared += 1
                elif my_type in ["四分相", "对分相"]:
                    challenging_shared += 1
                else:
                    base_score += 5
    
    match_type = "neutral"
    
    if recommendation_type == "emotional":
        base_score += harmonious_shared * 6
        if harmonious_shared > challenging_shared:
            match_type = "harmonious"
        else:
            match_type = "complementary"
    elif recommendation_type == "complementary":
        base_score += abs(harmonious_shared - challenging_shared) * 4
        match_type = "complementary"
    elif recommendation_type == "strong":
        base_score += max(harmonious_shared, challenging_shared) * 7
        if challenging_shared > harmonious_shared:
            match_type = "challenging"
        else:
            match_type = "soulmate"
    
    final_score = min(98, max(40, base_score))
    
    emotional_aspects = generate_emotional_aspects(match_type, final_score)
    
    return final_score, match_type, emotional_aspects


def generate_emotional_aspects(match_type: str, score: int) -> Dict:
    """生成情绪价值方面"""
    base_percentage = min(score, 95)
    
    aspects = [
        {
            "key": "understanding",
            "icon": "🤝",
            "name": "情感理解",
            "level": "high" if base_percentage >= 75 else "medium" if base_percentage >= 55 else "low",
            "percentage": base_percentage,
            "description": generate_aspect_description("understanding", base_percentage)
        },
        {
            "key": "support",
            "icon": "💪",
            "name": "情绪支持",
            "level": "high" if base_percentage >= 70 else "medium" if base_percentage >= 50 else "low",
            "percentage": max(40, base_percentage - 5),
            "description": generate_aspect_description("support", base_percentage)
        },
        {
            "key": "communication",
            "icon": "💬",
            "name": "情绪表达",
            "level": "high" if base_percentage >= 72 else "medium" if base_percentage >= 52 else "low",
            "percentage": max(45, base_percentage - 3),
            "description": generate_aspect_description("communication", base_percentage)
        }
    ]
    
    return {"aspects": aspects}


def generate_aspect_description(key: str, percentage: int) -> str:
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
        }
    }
    
    level = "high" if percentage >= 70 else "medium" if percentage >= 50 else "low"
    return descriptions.get(key, {}).get(level, "需要更多的了解和互动")


def build_recommendation_item(
    user: User,
    chart: Chart,
    score: int,
    match_type: str,
    emotional_analysis: Dict,
    recommendation_type: str
) -> Dict:
    """构建推荐项"""
    traits = generate_traits(match_type, recommendation_type)
    
    compatibility_reasons = generate_compatibility_reasons(match_type, score)
    
    return {
        "id": user.id,
        "user_name": user.username,
        "compatibility_score": score,
        "match_type": match_type,
        "key_traits": traits,
        "compatibility_reasons": compatibility_reasons,
        "emotional_value_aspects": emotional_analysis.get("aspects", []),
        "created_at": datetime.utcnow().isoformat()
    }


def generate_traits(match_type: str, recommendation_type: str) -> List[str]:
    """生成特质标签"""
    trait_pools = {
        "harmonious": ["敏感共情", "艺术气质", "温柔体贴", "善于倾听"],
        "challenging": ["热情奔放", "行动力强", "直接坦率", "敢爱敢恨"],
        "complementary": ["理性思维", "沟通达人", "社交活跃", "稳重可靠"],
        "soulmate": ["心灵共鸣", "直觉相通", "默契十足", "精神伴侣"]
    }
    
    pool = trait_pools.get(match_type, trait_pools["harmonious"])
    return random.sample(pool, min(3, len(pool)))


def generate_compatibility_reasons(match_type: str, score: int) -> List[Dict]:
    """生成匹配原因"""
    reasons = []
    
    reason_templates = {
        "harmonious": [
            {"icon": "💕", "text": "月亮与金星完美和谐，情感深度共鸣"},
            {"icon": "🌊", "text": "水象能量互补，能够理解你的情感需求"},
            {"icon": "✨", "text": "核心行星形成和谐相位，能量自然流动"}
        ],
        "challenging": [
            {"icon": "⚡", "text": "火星能量强烈，与你产生强烈化学反应"},
            {"icon": "💥", "text": "太阳与火星相位，张力中蕴含成长"},
            {"icon": "🔥", "text": "充满激情的能量互动，火花四溅"}
        ],
        "complementary": [
            {"icon": "🧠", "text": "风象能量补充，帮助你理性思考"},
            {"icon": "🗣️", "text": "水星能量强，能够带动你的沟通表达"},
            {"icon": "⚖️", "text": "能量互补，彼此成就对方的成长"}
        ],
        "soulmate": [
            {"icon": "💫", "text": "存在深层的灵魂连接，宿命感强烈"},
            {"icon": "🔮", "text": "月亮与冥王星的深刻互动，精神共鸣"},
            {"icon": "👑", "text": "难得的缘分配置，值得珍惜"}
        ]
    }
    
    templates = reason_templates.get(match_type, reason_templates["harmonious"])
    selected = random.sample(templates, min(2, len(templates)))
    
    return selected


def build_recommendation_detail(
    current_user: User,
    matched_user: User,
    my_chart: Chart,
    matched_chart: Chart,
    my_element_profile: Optional[UserElementProfile],
    matched_element_profile: Optional[UserElementProfile],
    analysis_data: Dict,
    highlights: Dict,
    emotional_analysis: Dict
) -> Dict:
    """构建推荐详情"""
    my_elements = generate_element_profile(my_element_profile, my_chart)
    matched_elements = generate_element_profile(matched_element_profile, matched_chart)
    
    highlights_list = highlights.get("highlights", [])
    compatibility_highlights = []
    
    for h in highlights_list[:3]:
        compatibility_highlights.append({
            "icon": h.get("icon", "✨"),
            "title": h.get("name", ""),
            "description": h.get("description", "")
        })
    
    if not compatibility_highlights:
        compatibility_highlights = [
            {"icon": "💕", "title": "情感共鸣", "description": "月亮与金星形成和谐相位，情感上能够自然地相互支持和理解"},
            {"icon": "🎨", "title": "创造力共鸣", "description": "海王星与太阳的和谐相位带来艺术和想象力的共鸣"},
            {"icon": "🛡️", "title": "安全感", "description": "土星与月亮的稳定相位带来长久的安全感和依赖感"}
        ]
    
    synastry_preview = None
    personality_analysis = analysis_data.get("personality_analysis", {})
    key_aspects = analysis_data.get("compatibility", {}).get("key_aspects", [])
    
    if personality_analysis:
        synastry_preview = {
            "summary": personality_analysis.get("summary", {}).get("text", ""),
            "key_aspects": []
        }
        
        for aspect in key_aspects[:3]:
            synastry_preview["key_aspects"].append({
                "planet_a": f"你的{aspect.get('planet_a', '')}",
                "planet_b": f"对方{aspect.get('planet_b', '')}",
                "aspect": aspect.get("aspect", ""),
                "meaning": aspect.get("interpretation", "")[:80] + "..."
            })
    
    return {
        "id": matched_user.id,
        "user_name": matched_user.username,
        "compatibility_score": emotional_analysis.get("overall_score", 70),
        "match_type": emotional_analysis.get("match_type", "neutral"),
        "match_type_label": emotional_analysis.get("match_type_label", "能量连接"),
        "key_traits": generate_traits(emotional_analysis.get("match_type", "neutral"), "emotional"),
        
        "my_info": {
            "user_name": current_user.username,
            "elements": my_elements[:2]
        },
        
        "matched_info": {
            "user_name": matched_user.username,
            "elements": matched_elements[:2]
        },
        
        "emotional_value_aspects": emotional_analysis.get("aspects", []),
        "compatibility_highlights": compatibility_highlights,
        "synastry_preview": synastry_preview,
        
        "compatibility_reasons": generate_compatibility_reasons(
            emotional_analysis.get("match_type", "neutral"),
            emotional_analysis.get("overall_score", 70)
        )
    }


def determine_node_type(score: int) -> str:
    if score >= 90:
        return "soulmate"
    elif score >= 80:
        return "harmonious"
    elif score >= 65:
        return "complementary"
    else:
        return "challenging"


def determine_strength(score: int) -> str:
    if score >= 85:
        return "strong"
    elif score >= 70:
        return "medium"
    else:
        return "weak"
