from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta, timezone
import json
import random
import logging

from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    User, Chart, DailyCPMatch, DailyCPMatchStatus, TimeLimitedSession,
    SessionExtension, ProfileUnlock, MatchPreference, DailyMatchLimit,
    UserPrivateChat
)
from app.routers.users import get_current_user
from app.schemas import ApiResponse
from app.services.daily_cp_match_service import (
    check_match_availability,
    accept_match,
    reject_match,
    unlock_profile,
    extend_session,
    perform_manual_match,
    get_match_detail,
    get_session_detail,
    get_today_date_str
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["每日CP匹配"])


class AcceptMatchRequest(BaseModel):
    match_id: int


class RejectMatchRequest(BaseModel):
    match_id: int


class UnlockProfileRequest(BaseModel):
    match_id: int
    target_user_id: int


class ExtendSessionRequest(BaseModel):
    session_id: int
    extension_hours: int = 168


class ManualMatchRequest(BaseModel):
    match_type: str = "vip_extra"
    target_zodiac_sign: Optional[str] = None


class UpdatePreferenceRequest(BaseModel):
    target_zodiac_sign: Optional[str] = None
    excluded_zodiac_signs: Optional[List[str]] = None
    prefer_harmonious_aspects: Optional[bool] = None


@router.get("/status", response_model=ApiResponse)
def get_match_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的每日匹配状态"""
    try:
        today = get_today_date_str()
        
        availability_info = check_match_availability(
            db, current_user.id, match_type="free_daily"
        )
        
        todays_match = db.query(DailyCPMatch).filter(
            (DailyCPMatch.user_a_id == current_user.id) | (DailyCPMatch.user_b_id == current_user.id),
            DailyCPMatch.match_date == today
        ).order_by(DailyCPMatch.created_at.desc()).first()
        
        match_detail = None
        if todays_match:
            match_detail = get_match_detail(db, todays_match.id, current_user.id)
        
        active_session = db.query(TimeLimitedSession).filter(
            TimeLimitedSession.is_active == True,
            (TimeLimitedSession.user_a_id == current_user.id) | (TimeLimitedSession.user_b_id == current_user.id)
        ).order_by(TimeLimitedSession.created_at.desc()).first()
        
        session_detail = None
        if active_session:
            session_detail = get_session_detail(db, active_session.id, current_user.id)
        
        preference = db.query(MatchPreference).filter(
            MatchPreference.user_id == current_user.id
        ).first()
        
        return ApiResponse(
            message="获取匹配状态成功",
            data={
                "today": today,
                "availability": {
                    "can_match": availability_info[0],
                    "reason": availability_info[1],
                    "free_matches_remaining": availability_info[2].get("free_matches_remaining", 0),
                    "vip_extra_matches_remaining": availability_info[2].get("vip_extra_matches_remaining", 0)
                },
                "todays_match": match_detail,
                "active_session": session_detail,
                "preference": {
                    "target_zodiac_sign": preference.target_zodiac_sign if preference else None,
                    "excluded_zodiac_signs": preference.excluded_zodiac_signs if preference else None,
                    "prefer_harmonious_aspects": preference.prefer_harmonious_aspects if preference else None
                } if preference else None
            }
        )
        
    except Exception as e:
        logger.error(f"获取匹配状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取匹配状态失败: {str(e)}"
        )


@router.get("/my-matches", response_model=ApiResponse)
def get_my_matches(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的匹配历史"""
    try:
        query = db.query(DailyCPMatch).filter(
            (DailyCPMatch.user_a_id == current_user.id) | (DailyCPMatch.user_b_id == current_user.id)
        )
        
        total = query.count()
        
        matches = query.order_by(
            DailyCPMatch.created_at.desc()
        ).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        match_list = []
        for match in matches:
            detail = get_match_detail(db, match.id, current_user.id)
            if detail:
                match_list.append(detail)
        
        return ApiResponse(
            message="获取匹配历史成功",
            data={
                "total": total,
                "page": page,
                "page_size": page_size,
                "matches": match_list
            }
        )
        
    except Exception as e:
        logger.error(f"获取匹配历史失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取匹配历史失败: {str(e)}"
        )


@router.get("/match/{match_id}", response_model=ApiResponse)
def get_match(
    match_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取匹配详情"""
    try:
        match = db.query(DailyCPMatch).filter(
            DailyCPMatch.id == match_id,
            (DailyCPMatch.user_a_id == current_user.id) | (DailyCPMatch.user_b_id == current_user.id)
        ).first()
        
        if not match:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="匹配记录不存在"
            )
        
        detail = get_match_detail(db, match_id, current_user.id)
        
        return ApiResponse(
            message="获取匹配详情成功",
            data=detail
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取匹配详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取匹配详情失败: {str(e)}"
        )


@router.post("/accept", response_model=ApiResponse)
def accept_match_endpoint(
    request: AcceptMatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """接受匹配"""
    try:
        success, message, data = accept_match(
            db, request.match_id, current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        return ApiResponse(
            message=message,
            data=data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"接受匹配失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"接受匹配失败: {str(e)}"
        )


@router.post("/reject", response_model=ApiResponse)
def reject_match_endpoint(
    request: RejectMatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """拒绝匹配"""
    try:
        success, message = reject_match(
            db, request.match_id, current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        return ApiResponse(
            message=message,
            data=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"拒绝匹配失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"拒绝匹配失败: {str(e)}"
        )


@router.post("/unlock-profile", response_model=ApiResponse)
def unlock_profile_endpoint(
    request: UnlockProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """解锁对方完整资料"""
    try:
        success, message, data = unlock_profile(
            db, request.match_id, current_user.id, request.target_user_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        return ApiResponse(
            message=message,
            data=data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"解锁资料失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"解锁资料失败: {str(e)}"
        )


@router.post("/extend-session", response_model=ApiResponse)
def extend_session_endpoint(
    request: ExtendSessionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """延长会话期限"""
    try:
        success, message, data = extend_session(
            db, request.session_id, current_user.id, request.extension_hours
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        return ApiResponse(
            message=message,
            data=data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"延长会话失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"延长会话失败: {str(e)}"
        )


@router.post("/manual-match", response_model=ApiResponse)
def manual_match_endpoint(
    request: ManualMatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    手动执行匹配（VIP特权）
    
    支持两种类型：
    - vip_extra: VIP额外匹配次数
    - vip_targeted: VIP定向星座匹配（需指定target_zodiac_sign）
    """
    try:
        if request.match_type == "vip_targeted" and not request.target_zodiac_sign:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="定向匹配需要指定目标星座"
            )
        
        success, message, data = perform_manual_match(
            db, current_user, request.match_type, request.target_zodiac_sign
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        return ApiResponse(
            message=message,
            data=data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"手动匹配失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"手动匹配失败: {str(e)}"
        )


@router.get("/preference", response_model=ApiResponse)
def get_match_preference(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取匹配偏好设置"""
    try:
        preference = db.query(MatchPreference).filter(
            MatchPreference.user_id == current_user.id
        ).first()
        
        zodiac_signs = [
            "白羊座", "金牛座", "双子座", "巨蟹座", "狮子座", "处女座",
            "天秤座", "天蝎座", "射手座", "摩羯座", "水瓶座", "双鱼座"
        ]
        
        return ApiResponse(
            message="获取匹配偏好成功",
            data={
                "preference": {
                    "target_zodiac_sign": preference.target_zodiac_sign if preference else None,
                    "excluded_zodiac_signs": preference.excluded_zodiac_signs if preference else None,
                    "prefer_harmonious_aspects": preference.prefer_harmonious_aspects if preference else None
                } if preference else None,
                "available_zodiac_signs": zodiac_signs
            }
        )
        
    except Exception as e:
        logger.error(f"获取匹配偏好失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取匹配偏好失败: {str(e)}"
        )


@router.put("/preference", response_model=ApiResponse)
def update_match_preference(
    request: UpdatePreferenceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新匹配偏好设置"""
    try:
        preference = db.query(MatchPreference).filter(
            MatchPreference.user_id == current_user.id
        ).first()
        
        if not preference:
            preference = MatchPreference(user_id=current_user.id)
            db.add(preference)
        
        if request.target_zodiac_sign is not None:
            preference.target_zodiac_sign = request.target_zodiac_sign
        
        if request.excluded_zodiac_signs is not None:
            preference.excluded_zodiac_signs = request.excluded_zodiac_signs
        
        if request.prefer_harmonious_aspects is not None:
            preference.prefer_harmonious_aspects = request.prefer_harmonious_aspects
        
        preference.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(preference)
        
        return ApiResponse(
            message="更新匹配偏好成功",
            data={
                "target_zodiac_sign": preference.target_zodiac_sign,
                "excluded_zodiac_signs": preference.excluded_zodiac_signs,
                "prefer_harmonious_aspects": preference.prefer_harmonious_aspects
            }
        )
        
    except Exception as e:
        logger.error(f"更新匹配偏好失败: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新匹配偏好失败: {str(e)}"
        )


@router.get("/session/{session_id}", response_model=ApiResponse)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取会话详情"""
    try:
        session = db.query(TimeLimitedSession).filter(
            TimeLimitedSession.id == session_id,
            (TimeLimitedSession.user_a_id == current_user.id) | (TimeLimitedSession.user_b_id == current_user.id)
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )
        
        detail = get_session_detail(db, session_id, current_user.id)
        
        return ApiResponse(
            message="获取会话详情成功",
            data=detail
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取会话详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取会话详情失败: {str(e)}"
        )


@router.get("/vip-privileges", response_model=ApiResponse)
def get_vip_privileges(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取VIP特权信息"""
    try:
        from app.services.vip_service import check_and_update_vip_status
        
        is_vip, user_vip = check_and_update_vip_status(db, current_user.id)
        
        daily_limit = db.query(DailyMatchLimit).filter(
            DailyMatchLimit.user_id == current_user.id,
            DailyMatchLimit.limit_date == get_today_date_str()
        ).first()
        
        plan_name = None
        if user_vip and user_vip.plan_type:
            plan_name = user_vip.plan_type
        
        return ApiResponse(
            message="获取VIP特权信息成功",
            data={
                "is_vip": is_vip,
                "vip_plan": plan_name,
                "has_vip_privileges": is_vip,
                "privileges": {
                    "daily_free_matches": 1,
                    "vip_extra_matches": 3,
                    "can_target_match": is_vip,
                    "can_extend_session": True,
                    "can_unlock_profile": True
                },
                "today_usage": {
                    "free_matches_used": daily_limit.free_match_count if daily_limit else 0,
                    "vip_extra_matches_used": daily_limit.vip_extra_match_count if daily_limit else 0,
                    "targeted_matches_used": daily_limit.targeted_match_count if daily_limit else 0
                }
            }
        )
        
    except Exception as e:
        logger.error(f"获取VIP特权信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取VIP特权信息失败: {str(e)}"
        )
