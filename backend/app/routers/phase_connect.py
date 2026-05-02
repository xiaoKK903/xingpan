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
from app.models import User, Chart, SynastryRecord, UserElementProfile, UserTag, OnlineUserPresence
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

router = APIRouter(tags=["相位连连看"])


class PhaseMatchRequest(BaseModel):
    chart_id: Optional[int] = None
    search_radius_km: Optional[float] = 50.0
    match_type: Optional[str] = "all"


class StartPhaseConnectRequest(BaseModel):
    matched_user_id: int
    matched_chart_id: Optional[int] = None


@router.get("/my-status", response_model=ApiResponse)
def get_my_phase_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的相位连接状态"""
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
                    "available_matches": 0,
                    "connections_made": 0,
                    "aspects": []
                }
            )
        
        chart_data = {}
        if my_chart.chart_data:
            try:
                chart_data = json.loads(my_chart.chart_data)
            except:
                pass
        
        aspects = chart_data.get("aspects", [])
        
        ASPECT_NATURE_MAP = {
            "合相": "neutral",
            "六分相": "harmonious",
            "四分相": "challenging",
            "三分相": "harmonious",
            "对分相": "challenging"
        }
        
        def get_aspect_nature(aspect_item):
            if "nature" in aspect_item:
                return aspect_item["nature"]
            aspect_name = aspect_item.get("aspect", "")
            return ASPECT_NATURE_MAP.get(aspect_name, "neutral")
        
        harmonious_count = 0
        challenging_count = 0
        neutral_count = 0
        
        for a in aspects:
            nature = get_aspect_nature(a)
            if nature == "harmonious":
                harmonious_count += 1
            elif nature == "challenging":
                challenging_count += 1
            else:
                neutral_count += 1
        
        recent_connections = db.query(SynastryRecord).filter(
            SynastryRecord.user_id == current_user.id,
            SynastryRecord.is_deleted == False
        ).count()
        
        online_users = db.query(OnlineUserPresence).filter(
            OnlineUserPresence.is_online == True,
            OnlineUserPresence.user_id != current_user.id
        ).count()
        
        return ApiResponse(
            message="获取相位连接状态成功",
            data={
                "has_chart": True,
                "chart_id": my_chart.id,
                "chart_info": {
                    "birth_date": my_chart.birth_date,
                    "birth_time": my_chart.birth_time,
                    "birth_place": my_chart.birth_place
                },
                "aspect_summary": {
                    "total": len(aspects),
                    "harmonious": harmonious_count,
                    "challenging": challenging_count,
                    "neutral": neutral_count
                },
                "key_aspects": aspects[:8] if aspects else [],
                "match_status": {
                    "available_matches": min(online_users + random.randint(3, 8), 30),
                    "connections_made": recent_connections,
                    "pending_reveals": random.randint(0, 3)
                }
            }
        )
        
    except Exception as e:
        logger.error(f"获取相位连接状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取相位连接状态失败: {str(e)}"
        )


@router.post("/search-matches", response_model=ApiResponse)
def search_phase_matches(
    request: PhaseMatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """搜索相位匹配用户"""
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
        
        potential_charts = db.query(Chart).filter(
            Chart.user_id != current_user.id,
            Chart.is_deleted == False
        ).limit(20).all()
        
        if not potential_charts:
            return ApiResponse(
                message="暂无匹配用户",
                data={
                    "matches": [],
                    "search_timestamp": datetime.utcnow().isoformat()
                }
            )
        
        my_chart_data = {}
        if my_chart.chart_data:
            try:
                my_chart_data = json.loads(my_chart.chart_data)
            except:
                pass
        
        matches = []
        match_types = {
            "all": ["harmonious", "challenging", "neutral"],
            "harmonious": ["harmonious"],
            "challenging": ["challenging"]
        }
        allowed_types = match_types.get(request.match_type, match_types["all"])
        
        for chart in potential_charts:
            user = db.query(User).filter(User.id == chart.user_id).first()
            if not user:
                continue
            
            match_score, match_type, shared_aspects = calculate_phase_match_score(
                my_chart_data, chart, current_user.id, chart.user_id
            )
            
            if match_type not in allowed_types and request.match_type != "all":
                continue
            
            matches.append({
                "matched_user_id": chart.user_id,
                "matched_user_name": user.username,
                "matched_chart_id": chart.id,
                "compatibility_score": match_score,
                "match_type": match_type,
                "match_type_label": get_match_type_label(match_type),
                "shared_aspects": shared_aspects,
                "shared_aspects_details": generate_aspect_details(shared_aspects),
                "created_at": datetime.utcnow().isoformat()
            })
        
        matches.sort(key=lambda x: x["compatibility_score"], reverse=True)
        
        return ApiResponse(
            message=f"找到 {len(matches)} 个相位匹配用户",
            data={
                "matches": matches,
                "search_timestamp": datetime.utcnow().isoformat(),
                "search_criteria": {
                    "match_type": request.match_type,
                    "search_radius_km": request.search_radius_km
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"搜索相位匹配失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"搜索相位匹配失败: {str(e)}"
        )


@router.post("/start-connection", response_model=ApiResponse)
def start_phase_connection(
    request: StartPhaseConnectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """开始相位连接，生成合盘分析"""
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
        
        matched_chart = db.query(Chart).filter(
            Chart.user_id == request.matched_user_id,
            Chart.is_deleted == False
        ).first()
        
        if not matched_chart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="对方星盘不存在"
            )
        
        matched_user = db.query(User).filter(User.id == request.matched_user_id).first()
        
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
            "name": matched_user.username if matched_user else "神秘用户",
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
        
        total_score = analysis_data.get('compatibility', {}).get('total_score', 50)
        
        synastry_preview = generate_synastry_preview(analysis_data, highlights, emotional_analysis)
        
        return ApiResponse(
            message="相位连接成功",
            data={
                "connection_id": f"conn_{current_user.id}_{request.matched_user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "matched_user": {
                    "id": request.matched_user_id,
                    "name": matched_user.username if matched_user else "神秘用户"
                },
                "compatibility_score": total_score,
                "shared_aspects_details": synastry_preview.get("shared_aspects", []),
                "synastry_preview": synastry_preview.get("preview", {}),
                "highlights_summary": {
                    "highlights": highlights.get("highlights", [])[:3],
                    "special_indicators": highlights.get("special_indicators", []),
                    "overall_theme": highlights.get("overall_theme", {})
                },
                "emotional_analysis": emotional_analysis
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"开始相位连接失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"开始相位连接失败: {str(e)}"
        )


@router.get("/recent-connections", response_model=ApiResponse)
def get_recent_connections(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取近期相位连接记录"""
    try:
        query = db.query(SynastryRecord).filter(
            SynastryRecord.user_id == current_user.id,
            SynastryRecord.is_deleted == False
        )
        
        total = query.count()
        
        records = query.order_by(
            SynastryRecord.created_at.desc()
        ).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        connections = []
        for record in records:
            analysis_data = None
            if record.analysis_data:
                try:
                    analysis_data = json.loads(record.analysis_data)
                except:
                    pass
            
            connections.append({
                "id": record.id,
                "matched_user_name": record.person_b_name or "神秘用户",
                "compatibility_score": record.total_score or 50,
                "shared_aspects": extract_shared_aspects(analysis_data),
                "created_at": record.created_at.isoformat() if record.created_at else None
            })
        
        return ApiResponse(
            message="获取近期连接成功",
            data={
                "total": total,
                "page": page,
                "page_size": page_size,
                "connections": connections
            }
        )
        
    except Exception as e:
        logger.error(f"获取近期连接失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取近期连接失败: {str(e)}"
        )


def calculate_phase_match_score(
    my_chart_data: Dict,
    target_chart: Chart,
    my_user_id: int,
    target_user_id: int
) -> Tuple[int, str, List[str]]:
    """计算相位匹配分数"""
    target_chart_data = {}
    if target_chart.chart_data:
        try:
            target_chart_data = json.loads(target_chart.chart_data)
        except:
            pass
    
    my_aspects = my_chart_data.get("aspects", [])
    target_aspects = target_chart_data.get("aspects", [])
    
    shared_aspects = []
    harmonious_shared = 0
    challenging_shared = 0
    
    aspect_keywords = {
        "三分相": "harmonious",
        "六分相": "harmonious",
        "合相": "neutral",
        "四分相": "challenging",
        "对分相": "challenging"
    }
    
    for my_aspect in my_aspects[:10]:
        for target_aspect in target_aspects[:10]:
            my_p1 = my_aspect.get("planet1", "")
            my_p2 = my_aspect.get("planet2", "")
            my_type = my_aspect.get("aspect", "")
            
            t_p1 = target_aspect.get("planet1", "")
            t_p2 = target_aspect.get("planet2", "")
            t_type = target_aspect.get("aspect", "")
            
            if (my_p1 == t_p1 and my_p2 == t_p2) or (my_p1 == t_p2 and my_p2 == t_p1):
                aspect_type = aspect_keywords.get(my_type, "neutral")
                
                aspect_str = f"{my_p1}{my_type}{my_p2}"
                if aspect_str not in [a.get("aspect_str", "") for a in shared_aspects]:
                    shared_aspects.append({
                        "aspect_str": aspect_str,
                        "planet1": my_p1,
                        "planet2": my_p2,
                        "aspect": my_type,
                        "type": aspect_type
                    })
                    
                    if aspect_type == "harmonious":
                        harmonious_shared += 1
                    elif aspect_type == "challenging":
                        challenging_shared += 1
    
    base_score = 50 + random.randint(-10, 10)
    
    match_type = "neutral"
    if harmonious_shared > challenging_shared:
        match_type = "harmonious"
        base_score += harmonious_shared * 5
    elif challenging_shared > harmonious_shared:
        match_type = "challenging"
        base_score += challenging_shared * 4
    
    if len(shared_aspects) >= 3:
        base_score += 10
    
    final_score = min(98, max(30, base_score))
    
    aspect_strings = [a["aspect_str"] for a in shared_aspects]
    
    return final_score, match_type, aspect_strings


def get_match_type_label(match_type: str) -> str:
    labels = {
        "harmonious": "和谐共鸣",
        "challenging": "张力吸引",
        "neutral": "普通连接"
    }
    return labels.get(match_type, "相位连接")


def generate_aspect_details(shared_aspects: List[str]) -> List[Dict]:
    """生成相位详情"""
    details = []
    
    aspect_meanings = {
        "太阳": {
            "月亮": {
                "三分相": "你们的情感能够自然地相互支持，彼此理解对方的核心需求",
                "六分相": "通过简单的努力就能建立深厚的情感连接",
                "合相": "自我认同与情感需求高度融合",
                "四分相": "自我意志与情感需求可能产生冲突，但蕴含成长潜力",
                "对分相": "在自我表达和情感需求上存在差异，需要平衡"
            },
            "金星": {
                "三分相": "爱意自然流露，关系中充满和谐与甜蜜",
                "六分相": "通过简单的表达就能增进彼此的爱意",
                "合相": "充满爱意和吸引力的相位",
                "四分相": "自我表达与价值取向可能产生冲突",
                "对分相": "在价值观和爱的表达上存在差异"
            }
        },
        "金星": {
            "火星": {
                "三分相": "浪漫吸引力和谐流动，爱与行动完美结合",
                "六分相": "有良好的浪漫吸引力基础",
                "合相": "强烈的浪漫和性吸引力",
                "四分相": "爱与行动可能产生摩擦",
                "对分相": "爱的表达与行动方式可能对立"
            }
        }
    }
    
    for aspect_str in shared_aspects:
        found_meaning = "这是一个独特的相位连接"
        
        for p1, rest in aspect_meanings.items():
            for p2, aspects in rest.items():
                for aspect_type, meaning in aspects.items():
                    if p1 in aspect_str and p2 in aspect_str and aspect_type in aspect_str:
                        found_meaning = meaning
                        break
        
        aspect_type = "neutral"
        if "三分相" in aspect_str or "六分相" in aspect_str:
            aspect_type = "harmonious"
        elif "四分相" in aspect_str or "对分相" in aspect_str:
            aspect_type = "challenging"
        
        details.append({
            "planet_a": aspect_str.split("三分相")[0].split("六分相")[0].split("合相")[0].split("四分相")[0].split("对分相")[0],
            "planet_b": "",
            "aspect": "",
            "type": aspect_type,
            "meaning": found_meaning
        })
    
    return details


def generate_synastry_preview(
    analysis_data: Dict,
    highlights: Dict,
    emotional_analysis: Dict
) -> Dict:
    """生成合盘预览"""
    compatibility = analysis_data.get("compatibility", {})
    highlights_list = highlights.get("highlights", [])
    
    preview_highlights = []
    for h in highlights_list[:3]:
        preview_highlights.append({
            "icon": h.get("icon", "✨"),
            "title": h.get("name", ""),
            "description": h.get("description", "")
        })
    
    if not preview_highlights:
        preview_highlights = [
            {"icon": "💕", "title": "情感共鸣", "description": "月亮与金星的互动带来情感上的理解"},
            {"icon": "⚡", "title": "化学反应", "description": "火星与太阳的互动带来吸引力"},
            {"icon": "🧠", "title": "思维契合", "description": "水星相位显示沟通上的默契"}
        ]
    
    shared_aspects_details = []
    key_aspects = highlights.get("highlights", [])
    for h in key_aspects[:2]:
        matched = h.get("matched_aspects", [])
        for aspect in matched[:1]:
            shared_aspects_details.append({
                "planet_a": aspect.get("planet_a", ""),
                "planet_b": aspect.get("planet_b", ""),
                "aspect": aspect.get("aspect", ""),
                "aspect_icon": aspect.get("aspect_symbol", ""),
                "type": aspect.get("nature", "neutral"),
                "meaning": aspect.get("interpretation", "")[:100] + "..."
            })
    
    return {
        "shared_aspects": shared_aspects_details,
        "preview": {
            "highlights": preview_highlights,
            "summary": analysis_data.get("personality_analysis", {}).get("summary", {}).get("text", "")
        }
    }


def extract_shared_aspects(analysis_data: Dict) -> List[str]:
    """从分析数据中提取共同相位"""
    if not analysis_data:
        return []
    
    highlights = analysis_data.get("highlights", [])
    aspects = []
    
    for h in highlights[:2]:
        matched = h.get("matched_aspects", [])
        for aspect in matched[:1]:
            aspects.append(f"{aspect.get('planet_a')}{aspect.get('aspect')}{aspect.get('planet_b')}")
    
    return aspects
