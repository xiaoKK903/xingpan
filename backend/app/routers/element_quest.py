from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime, date
import json
import logging
import random

from app.database import get_db
from app.models import (
    User, Chart, UserElementProfile, UserEnergyTag,
    BlindBoxMatch, QuestLog, DailyQuestLimit, StarDustTransaction
)
from app.schemas import ApiResponse
from app.routers.users import get_current_active_user, get_current_user_optional
from app.services.element_deficiency_service import (
    element_deficiency_service, Element, ENERGY_LEVEL_LABELS
)
from app.services.chart_service import get_or_create_chart_data

logger = logging.getLogger(__name__)

router = APIRouter()

DEFAULT_DAILY_QUEST_LIMIT = 3
DEFAULT_REFRESH_LIMIT = 1
BLIND_BOX_REWARD = 10


def get_today_date_str() -> str:
    return date.today().strftime("%Y-%m-%d")


def get_or_create_daily_limit(
    db: Session,
    user_id: int,
    quest_type: str = "blind_box_match"
) -> DailyQuestLimit:
    today = get_today_date_str()
    
    limit = db.query(DailyQuestLimit).filter(
        DailyQuestLimit.user_id == user_id,
        DailyQuestLimit.limit_date == today,
        DailyQuestLimit.quest_type == quest_type
    ).first()
    
    if not limit:
        limit = DailyQuestLimit(
            user_id=user_id,
            limit_date=today,
            quest_type=quest_type,
            used_count=0,
            max_count=DEFAULT_DAILY_QUEST_LIMIT,
            refresh_count=0,
            max_refresh=DEFAULT_REFRESH_LIMIT
        )
        db.add(limit)
        db.commit()
        db.refresh(limit)
    
    return limit


def check_quest_availability(
    db: Session,
    user_id: int,
    quest_type: str = "blind_box_match"
) -> Dict[str, Any]:
    limit = get_or_create_daily_limit(db, user_id, quest_type)
    
    total_available = limit.max_count + limit.vip_extra_count
    remaining = max(0, total_available - limit.used_count)
    refresh_remaining = max(0, limit.max_refresh - limit.refresh_count)
    
    return {
        "can_quest": remaining > 0,
        "used_count": limit.used_count,
        "max_count": total_available,
        "remaining_count": remaining,
        "refresh_count": limit.refresh_count,
        "max_refresh": limit.max_refresh,
        "refresh_remaining": refresh_remaining,
        "is_vip": limit.is_vip
    }


@router.get("/profile/me", response_model=ApiResponse)
def get_my_element_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    获取当前用户的元素画像
    """
    profile = db.query(UserElementProfile).filter(
        UserElementProfile.user_id == current_user.id
    ).first()
    
    if profile:
        element_data = json.loads(profile.element_data) if profile.element_data else None
        
        return ApiResponse(
            code=200,
            message="获取元素画像成功",
            data={
                "profile_id": profile.id,
                "fire_score": profile.fire_score,
                "earth_score": profile.earth_score,
                "air_score": profile.air_score,
                "water_score": profile.water_score,
                "fire_level": profile.fire_level,
                "earth_level": profile.earth_level,
                "air_level": profile.air_level,
                "water_level": profile.water_level,
                "fire_level_label": ENERGY_LEVEL_LABELS.get(profile.fire_level, profile.fire_level),
                "earth_level_label": ENERGY_LEVEL_LABELS.get(profile.earth_level, profile.earth_level),
                "air_level_label": ENERGY_LEVEL_LABELS.get(profile.air_level, profile.air_level),
                "water_level_label": ENERGY_LEVEL_LABELS.get(profile.water_level, profile.water_level),
                "total_score": profile.total_score,
                "average_score": profile.average_score,
                "dominant_element": profile.dominant_element,
                "secondary_dominant": profile.secondary_dominant,
                "primary_deficiency": profile.primary_deficiency,
                "has_deficiency": profile.has_deficiency,
                "deficiency_count": profile.deficiency_count,
                "element_data": element_data,
                "last_analyzed_at": profile.last_analyzed_at.isoformat() if profile.last_analyzed_at else None,
                "updated_at": profile.updated_at.isoformat() if profile.updated_at else None
            }
        )
    
    return ApiResponse(
        code=200,
        message="尚未创建元素画像，请先进行分析",
        data={
            "has_profile": False
        }
    )


@router.post("/analyze-temporary", response_model=ApiResponse)
def analyze_element_temporary(
    chart_data: Dict[str, Any]
):
    """
    临时分析星盘元素能量，无需登录保存

    用于在星盘计算完成后立即展示元素分析结果，无需用户登录或保存星盘。
    
    Args:
        chart_data: 完整的星盘数据，包含 planets, ascendant, aspects 等

    Returns:
        元素能量分析结果和能量标签
    """
    if not chart_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="缺少星盘数据"
        )
    
    element_analysis = element_deficiency_service.calculate_element_energies(chart_data)
    
    energy_tags = element_deficiency_service.generate_energy_tags(element_analysis)
    
    return ApiResponse(
        code=200,
        message="元素分析完成",
        data={
            "element_analysis": element_analysis,
            "energy_tags": [
                {
                    "key": t.key,
                    "name": t.name,
                    "category": t.category,
                    "score": t.score,
                    "description": t.description
                }
                for t in energy_tags
            ]
        }
    )


@router.post("/analyze", response_model=ApiResponse)
def analyze_element_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    分析用户的星盘，生成四元素能量分布和缺角分析
    """
    user_chart = db.query(Chart).filter(
        Chart.user_id == current_user.id,
        Chart.is_deleted == False
    ).order_by(Chart.created_at.desc()).first()
    
    if not user_chart:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先创建星盘"
        )
    
    chart_data, chart_record = get_or_create_chart_data(
        db, user_chart.id, current_user.id
    )
    
    if not chart_data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="无法获取星盘数据"
        )
    
    element_analysis = element_deficiency_service.calculate_element_energies(chart_data)
    
    elements = element_analysis.get("elements", {})
    sorted_elements = element_analysis.get("sorted_elements", [])
    dominant = element_analysis.get("dominant_elements", [])
    deficient = element_analysis.get("deficient_elements", [])
    primary_deficiency = element_analysis.get("primary_deficiency")
    
    fire_elem = elements.get(Element.FIRE.value, {})
    earth_elem = elements.get(Element.EARTH.value, {})
    air_elem = elements.get(Element.AIR.value, {})
    water_elem = elements.get(Element.WATER.value, {})
    
    profile = db.query(UserElementProfile).filter(
        UserElementProfile.user_id == current_user.id
    ).first()
    
    if not profile:
        profile = UserElementProfile(
            user_id=current_user.id,
            chart_id=user_chart.id
        )
        db.add(profile)
    
    profile.fire_score = fire_elem.get("score", 0.0)
    profile.earth_score = earth_elem.get("score", 0.0)
    profile.air_score = air_elem.get("score", 0.0)
    profile.water_score = water_elem.get("score", 0.0)
    
    profile.fire_level = fire_elem.get("level", "balanced")
    profile.earth_level = earth_elem.get("level", "balanced")
    profile.air_level = air_elem.get("level", "balanced")
    profile.water_level = water_elem.get("level", "balanced")
    
    profile.total_score = element_analysis.get("total_score", 0.0)
    profile.average_score = element_analysis.get("average_score", 25.0)
    
    if dominant:
        profile.dominant_element = dominant[0].get("element")
        if len(dominant) > 1:
            profile.secondary_dominant = dominant[1].get("element")
    
    if primary_deficiency:
        profile.primary_deficiency = primary_deficiency.get("element")
    
    profile.has_deficiency = element_analysis.get("has_deficiency", False)
    profile.deficiency_count = len(deficient)
    profile.element_data = json.dumps(element_analysis, ensure_ascii=False)
    profile.last_analyzed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(profile)
    
    energy_tags = element_deficiency_service.generate_energy_tags(element_analysis)
    
    for tag in energy_tags:
        existing_tag = db.query(UserEnergyTag).filter(
            UserEnergyTag.user_id == current_user.id,
            UserEnergyTag.tag_key == tag.key
        ).first()
        
        if existing_tag:
            existing_tag.tag_score = tag.score
            existing_tag.occurrence_count += 1
            existing_tag.last_seen_at = datetime.utcnow()
        else:
            new_tag = UserEnergyTag(
                user_id=current_user.id,
                profile_id=profile.id,
                tag_key=tag.key,
                tag_name=tag.name,
                tag_category=tag.category,
                tag_score=tag.score,
                description=tag.description
            )
            db.add(new_tag)
    
    db.commit()
    
    return ApiResponse(
        code=200,
        message="元素分析完成",
        data={
            "profile_id": profile.id,
            "element_analysis": element_analysis,
            "energy_tags": [
                {
                    "key": t.key,
                    "name": t.name,
                    "category": t.category,
                    "score": t.score,
                    "description": t.description
                }
                for t in energy_tags
            ]
        }
    )


@router.get("/tags/me", response_model=ApiResponse)
def get_my_energy_tags(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    获取当前用户的能量标签
    """
    tags = db.query(UserEnergyTag).filter(
        UserEnergyTag.user_id == current_user.id,
        UserEnergyTag.is_active == True
    ).order_by(UserEnergyTag.tag_score.desc()).all()
    
    return ApiResponse(
        code=200,
        message="获取能量标签成功",
        data={
            "tags": [
                {
                    "id": t.id,
                    "tag_key": t.tag_key,
                    "tag_name": t.tag_name,
                    "tag_category": t.tag_category,
                    "tag_score": t.tag_score,
                    "description": t.description,
                    "occurrence_count": t.occurrence_count,
                    "created_at": t.created_at.isoformat()
                }
                for t in tags
            ],
            "total_count": len(tags)
        }
    )


@router.get("/quest/status", response_model=ApiResponse)
def get_quest_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    获取当前用户的寻宝状态和每日限制
    """
    availability = check_quest_availability(db, current_user.id)
    
    today = get_today_date_str()
    today_logs = db.query(QuestLog).filter(
        QuestLog.user_id == current_user.id,
        QuestLog.quest_date == today
    ).order_by(QuestLog.created_at.desc()).all()
    
    active_blind_boxes = db.query(BlindBoxMatch).filter(
        BlindBoxMatch.user_id == current_user.id,
        BlindBoxMatch.status == "active",
        BlindBoxMatch.is_revealed == False
    ).order_by(BlindBoxMatch.created_at.desc()).all()
    
    return ApiResponse(
        code=200,
        message="获取寻宝状态成功",
        data={
            "availability": availability,
            "today_quests": [
                {
                    "id": log.id,
                    "quest_type": log.quest_type,
                    "reward_earned": log.reward_earned,
                    "reward_type": log.reward_type,
                    "created_at": log.created_at.isoformat()
                }
                for log in today_logs
            ],
            "active_blind_boxes": [
                {
                    "id": box.id,
                    "blind_box_id": box.blind_box_id,
                    "complement_score": box.complement_score,
                    "match_type": box.match_type,
                    "created_at": box.created_at.isoformat()
                }
                for box in active_blind_boxes
            ],
            "today_date": today
        }
    )


@router.post("/quest/blind-box", response_model=ApiResponse)
def create_blind_box_match(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    创建一个新的盲盒匹配
    """
    availability = check_quest_availability(db, current_user.id)
    
    if not availability["can_quest"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="今日寻宝次数已用完，请明天再来"
        )
    
    my_profile = db.query(UserElementProfile).filter(
        UserElementProfile.user_id == current_user.id
    ).first()
    
    if not my_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先完成元素分析"
        )
    
    my_element_data = json.loads(my_profile.element_data) if my_profile.element_data else {}
    
    other_profiles = db.query(UserElementProfile).filter(
        UserElementProfile.user_id != current_user.id
    ).all()
    
    if not other_profiles:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="暂无可匹配的用户"
        )
    
    other_users_data = []
    for profile in other_profiles:
        user = db.query(User).filter(User.id == profile.user_id).first()
        if user and user.is_active:
            element_data = json.loads(profile.element_data) if profile.element_data else {}
            other_users_data.append({
                "user_id": user.id,
                "username": user.username,
                "avatar_info": None,
                "element_analysis": element_data
            })
    
    if not other_users_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="暂无可匹配的用户"
        )
    
    matched_users = element_deficiency_service.find_complementary_users(
        my_element_data,
        other_users_data,
        limit=5
    )
    
    if not matched_users:
        random_match = random.choice(other_users_data)
        matched_user = random_match
        complement_score = 20.0
        complement_details = [{
            "element": "random",
            "match_type": "random",
            "description": "随机匹配"
        }]
    else:
        matched_user = matched_users[0]
        complement_score = matched_user["complement_score"]
        complement_details = matched_user["complement_details"]
    
    matched_user_id = matched_user["user_id"]
    
    blind_box_data = element_deficiency_service.generate_blind_box_clues(
        matched_user,
        my_element_data
    )
    
    match_analysis = matched_user.get("element_analysis", {})
    completeness_score = element_deficiency_service.calculate_deficiency_completeness_score(
        my_element_data,
        match_analysis
    )
    
    blind_box = BlindBoxMatch(
        user_id=current_user.id,
        matched_user_id=matched_user_id,
        blind_box_id=blind_box_data["blind_box_id"],
        complement_score=complement_score,
        match_type="complementary" if matched_users else "random",
        clues_data=json.dumps(blind_box_data, ensure_ascii=False),
        complement_details=json.dumps(complement_details, ensure_ascii=False),
        completeness_data=json.dumps(completeness_score, ensure_ascii=False),
        status="active"
    )
    
    db.add(blind_box)
    
    limit = get_or_create_daily_limit(db, current_user.id)
    limit.used_count += 1
    
    quest_log = QuestLog(
        user_id=current_user.id,
        quest_date=get_today_date_str(),
        quest_type="blind_box_match",
        quest_status="completed"
    )
    db.add(quest_log)
    
    db.commit()
    db.refresh(blind_box)
    db.refresh(limit)
    
    return ApiResponse(
        code=200,
        message="盲盒匹配成功",
        data={
            "blind_box_id": blind_box.blind_box_id,
            "db_id": blind_box.id,
            "clues": blind_box_data.get("clues", []),
            "complement_score": complement_score,
            "match_type": blind_box.match_type,
            "completeness_score": completeness_score.get("overall_completeness", 0),
            "created_at": blind_box.created_at.isoformat(),
            "remaining_count": max(0, limit.max_count + limit.vip_extra_count - limit.used_count)
        }
    )


@router.get("/quest/blind-boxes", response_model=ApiResponse)
def get_my_blind_boxes(
    status: Optional[str] = Query(None, description="筛选状态: active/revealed/claimed"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    获取当前用户的盲盒列表
    """
    query = db.query(BlindBoxMatch).filter(
        BlindBoxMatch.user_id == current_user.id
    )
    
    if status:
        query = query.filter(BlindBoxMatch.status == status)
    
    boxes = query.order_by(BlindBoxMatch.created_at.desc()).all()
    
    return ApiResponse(
        code=200,
        message="获取盲盒列表成功",
        data={
            "boxes": [
                {
                    "id": box.id,
                    "blind_box_id": box.blind_box_id,
                    "complement_score": box.complement_score,
                    "match_type": box.match_type,
                    "is_revealed": box.is_revealed,
                    "is_claimed": box.is_claimed,
                    "status": box.status,
                    "reward_earned": box.reward_earned,
                    "created_at": box.created_at.isoformat(),
                    "revealed_at": box.revealed_at.isoformat() if box.revealed_at else None
                }
                for box in boxes
            ],
            "total_count": len(boxes)
        }
    )


@router.get("/quest/blind-box/{box_id}", response_model=ApiResponse)
def get_blind_box_detail(
    box_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    获取盲盒详情
    """
    box = db.query(BlindBoxMatch).filter(
        BlindBoxMatch.id == box_id,
        BlindBoxMatch.user_id == current_user.id
    ).first()
    
    if not box:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="盲盒不存在"
        )
    
    clues_data = json.loads(box.clues_data) if box.clues_data else {}
    completeness_data = json.loads(box.completeness_data) if box.completeness_data else {}
    complement_details = json.loads(box.complement_details) if box.complement_details else []
    
    matched_user = db.query(User).filter(User.id == box.matched_user_id).first()
    matched_profile = db.query(UserElementProfile).filter(
        UserElementProfile.user_id == box.matched_user_id
    ).first()
    
    return ApiResponse(
        code=200,
        message="获取盲盒详情成功",
        data={
            "id": box.id,
            "blind_box_id": box.blind_box_id,
            "complement_score": box.complement_score,
            "match_type": box.match_type,
            "clues": clues_data.get("clues", []),
            "complement_details": complement_details,
            "completeness_score": completeness_data.get("overall_completeness", 0),
            "element_details": completeness_data.get("element_details", {}),
            "is_revealed": box.is_revealed,
            "is_claimed": box.is_claimed,
            "status": box.status,
            "reward_earned": box.reward_earned,
            "matched_user_info": {
                "user_id": matched_user.id,
                "username": matched_user.username if matched_user else None,
                "profile_id": matched_profile.id if matched_profile else None
            } if box.is_revealed else None,
            "created_at": box.created_at.isoformat(),
            "revealed_at": box.revealed_at.isoformat() if box.revealed_at else None
        }
    )


@router.post("/quest/blind-box/{box_id}/reveal", response_model=ApiResponse)
def reveal_blind_box(
    box_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    揭示盲盒，查看匹配用户的完整信息
    """
    box = db.query(BlindBoxMatch).filter(
        BlindBoxMatch.id == box_id,
        BlindBoxMatch.user_id == current_user.id
    ).first()
    
    if not box:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="盲盒不存在"
        )
    
    if box.is_revealed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该盲盒已经揭示过了"
        )
    
    matched_user = db.query(User).filter(User.id == box.matched_user_id).first()
    matched_profile = db.query(UserElementProfile).filter(
        UserElementProfile.user_id == box.matched_user_id
    ).first()
    
    box.is_revealed = True
    box.revealed_at = datetime.utcnow()
    box.reward_earned = BLIND_BOX_REWARD
    
    db.commit()
    db.refresh(box)
    
    matched_element_data = None
    if matched_profile and matched_profile.element_data:
        matched_element_data = json.loads(matched_profile.element_data)
    
    return ApiResponse(
        code=200,
        message="盲盒揭示成功",
        data={
            "blind_box_id": box.blind_box_id,
            "matched_user": {
                "user_id": matched_user.id if matched_user else None,
                "username": matched_user.username if matched_user else None,
                "element_profile": {
                    "fire_score": matched_profile.fire_score if matched_profile else 0,
                    "earth_score": matched_profile.earth_score if matched_profile else 0,
                    "air_score": matched_profile.air_score if matched_profile else 0,
                    "water_score": matched_profile.water_score if matched_profile else 0,
                    "fire_level": matched_profile.fire_level if matched_profile else "balanced",
                    "earth_level": matched_profile.earth_level if matched_profile else "balanced",
                    "air_level": matched_profile.air_level if matched_profile else "balanced",
                    "water_level": matched_profile.water_level if matched_profile else "balanced",
                    "dominant_element": matched_profile.dominant_element if matched_profile else None,
                    "primary_deficiency": matched_profile.primary_deficiency if matched_profile else None,
                },
                "element_analysis": matched_element_data
            },
            "reward_earned": box.reward_earned,
            "revealed_at": box.revealed_at.isoformat()
        }
    )


@router.post("/quest/blind-box/{box_id}/claim", response_model=ApiResponse)
def claim_blind_box_reward(
    box_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    领取盲盒奖励
    """
    box = db.query(BlindBoxMatch).filter(
        BlindBoxMatch.id == box_id,
        BlindBoxMatch.user_id == current_user.id
    ).first()
    
    if not box:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="盲盒不存在"
        )
    
    if not box.is_revealed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先揭示盲盒"
        )
    
    if box.is_claimed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该盲盒奖励已经领取过了"
        )
    
    reward_amount = box.reward_earned or BLIND_BOX_REWARD
    
    current_user.stardust_fragment_balance = (current_user.stardust_fragment_balance or 0) + reward_amount
    
    transaction = StarDustTransaction(
        user_id=current_user.id,
        transaction_type="blind_box_reward",
        currency_type="fragment",
        amount=reward_amount,
        balance_before=current_user.stardust_fragment_balance - reward_amount,
        balance_after=current_user.stardust_fragment_balance,
        related_type="blind_box_match",
        related_id=str(box.id),
        description=f"盲盒寻宝奖励: +{reward_amount} 星元碎片"
    )
    db.add(transaction)
    
    box.is_claimed = True
    box.claimed_at = datetime.utcnow()
    
    quest_log = db.query(QuestLog).filter(
        QuestLog.blind_box_match_id == box.id
    ).first()
    if quest_log:
        quest_log.reward_earned = reward_amount
    
    db.commit()
    db.refresh(current_user)
    db.refresh(box)
    
    return ApiResponse(
        code=200,
        message="奖励领取成功",
        data={
            "blind_box_id": box.blind_box_id,
            "reward_amount": reward_amount,
            "reward_type": "星元碎片",
            "new_balance": current_user.stardust_fragment_balance,
            "claimed_at": box.claimed_at.isoformat()
        }
    )


@router.post("/quest/refresh", response_model=ApiResponse)
def refresh_blind_box_match(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    刷新今日的寻宝次数限制（消耗星尘碎片）
    """
    limit = get_or_create_daily_limit(db, current_user.id)
    
    if limit.refresh_count >= limit.max_refresh:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="今日刷新次数已用完"
        )
    
    refresh_cost = 20
    
    if (current_user.stardust_fragment_balance or 0) < refresh_cost:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"星元碎片不足，需要 {refresh_cost} 个"
        )
    
    current_user.stardust_fragment_balance -= refresh_cost
    limit.used_count = 0
    limit.refresh_count += 1
    
    transaction = StarDustTransaction(
        user_id=current_user.id,
        transaction_type="quest_refresh",
        currency_type="fragment",
        amount=-refresh_cost,
        balance_before=current_user.stardust_fragment_balance + refresh_cost,
        balance_after=current_user.stardust_fragment_balance,
        description=f"刷新寻宝次数: -{refresh_cost} 星元碎片"
    )
    db.add(transaction)
    
    db.commit()
    db.refresh(limit)
    
    return ApiResponse(
        code=200,
        message="刷新成功",
        data={
            "refresh_cost": refresh_cost,
            "new_balance": current_user.stardust_fragment_balance,
            "availability": {
                "used_count": limit.used_count,
                "max_count": limit.max_count + limit.vip_extra_count,
                "remaining_count": limit.max_count + limit.vip_extra_count - limit.used_count,
                "refresh_count": limit.refresh_count,
                "max_refresh": limit.max_refresh
            }
        }
    )


@router.get("/quest/history", response_model=ApiResponse)
def get_quest_history(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    获取寻宝历史记录
    """
    logs = db.query(QuestLog).filter(
        QuestLog.user_id == current_user.id
    ).order_by(QuestLog.created_at.desc()).limit(limit).all()
    
    total_reward = sum(log.reward_earned or 0 for log in logs)
    
    return ApiResponse(
        code=200,
        message="获取寻宝历史成功",
        data={
            "history": [
                {
                    "id": log.id,
                    "quest_date": log.quest_date,
                    "quest_type": log.quest_type,
                    "quest_status": log.quest_status,
                    "reward_earned": log.reward_earned,
                    "reward_type": log.reward_type,
                    "blind_box_match_id": log.blind_box_match_id,
                    "created_at": log.created_at.isoformat()
                }
                for log in logs
            ],
            "total_count": len(logs),
            "total_reward_earned": total_reward
        }
    )
