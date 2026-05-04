from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from app.database import get_db
from app.models import User, InviteCode, InviteRelation, InviteReward, InviteShareLog
from app.routers.users import get_current_user, get_current_user_optional
from app.schemas import ApiResponse
from app.services.invite_service import (
    get_or_create_invite_code,
    get_invite_code_by_code,
    create_invite_relation,
    get_invite_relation_by_invitee,
    process_share_reward,
    log_invite_share,
    get_user_invite_stats,
    get_invite_rewards_list,
    check_user_has_chart,
    on_user_chart_created,
    SHARE_REWARD_FRAGMENTS,
    REGISTER_COMPLETE_REWARD_TICKETS,
    REGISTER_COMPLETE_VIP_DAYS,
    FIRST_PAYMENT_REWARD_RATE
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["邀请系统"])


@router.get("/code", response_model=ApiResponse)
def get_my_invite_code(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        invite_code = get_or_create_invite_code(db, current_user.id)
        
        return ApiResponse(
            message="获取邀请码成功",
            data={
                "invite_code": invite_code.invite_code,
                "total_invites": invite_code.total_invites,
                "valid_invites": invite_code.valid_invites,
                "paid_invites": invite_code.paid_invites,
                "total_rewards_earned": invite_code.total_rewards_earned
            }
        )
        
    except Exception as e:
        logger.error(f"获取邀请码失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取邀请码失败: {str(e)}"
        )


@router.get("/stats", response_model=ApiResponse)
def get_invite_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        stats = get_user_invite_stats(db, current_user.id)
        
        return ApiResponse(
            message="获取邀请统计成功",
            data=stats
        )
        
    except Exception as e:
        logger.error(f"获取邀请统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取邀请统计失败: {str(e)}"
        )


@router.get("/rewards", response_model=ApiResponse)
def get_my_rewards(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        offset = (page - 1) * page_size
        result = get_invite_rewards_list(db, current_user.id, page_size, offset)
        
        return ApiResponse(
            message="获取奖励列表成功",
            data={
                "total": result["total"],
                "page": page,
                "page_size": page_size,
                "rewards": result["rewards"]
            }
        )
        
    except Exception as e:
        logger.error(f"获取奖励列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取奖励列表失败: {str(e)}"
        )


@router.post("/share", response_model=ApiResponse)
def record_share(
    request: Request,
    share_type: str = "general",
    share_platform: Optional[str] = None,
    synastry_record_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        invite_code = get_or_create_invite_code(db, current_user.id)
        
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("User-Agent")
        
        log_invite_share(
            db=db,
            user_id=current_user.id,
            share_type=share_type,
            share_platform=share_platform,
            invite_code=invite_code.invite_code,
            synastry_record_id=synastry_record_id,
            share_ip=client_ip,
            share_device=user_agent
        )
        
        share_url = f"/register?invite_code={invite_code.invite_code}"
        
        return ApiResponse(
            message="记录分享成功",
            data={
                "invite_code": invite_code.invite_code,
                "share_url": share_url,
                "share_type": share_type
            }
        )
        
    except Exception as e:
        logger.error(f"记录分享失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"记录分享失败: {str(e)}"
        )


@router.post("/synastry-share", response_model=ApiResponse)
def record_synastry_share(
    request: Request,
    synastry_record_id: int,
    share_platform: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        invite_code = get_or_create_invite_code(db, current_user.id)
        
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("User-Agent")
        
        log_invite_share(
            db=db,
            user_id=current_user.id,
            share_type="synastry_card",
            share_platform=share_platform,
            invite_code=invite_code.invite_code,
            synastry_record_id=synastry_record_id,
            share_ip=client_ip,
            share_device=user_agent
        )
        
        share_url = f"/register?invite_code={invite_code.invite_code}&synastry_id={synastry_record_id}"
        
        return ApiResponse(
            message="记录合盘分享成功",
            data={
                "invite_code": invite_code.invite_code,
                "share_url": share_url,
                "synastry_record_id": synastry_record_id
            }
        )
        
    except Exception as e:
        logger.error(f"记录合盘分享失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"记录合盘分享失败: {str(e)}"
        )


@router.get("/validate-code", response_model=ApiResponse)
def validate_invite_code(
    invite_code: str = Query(..., description="邀请码"),
    db: Session = Depends(get_db)
):
    try:
        code = get_invite_code_by_code(db, invite_code)
        
        if not code:
            return ApiResponse(
                code=404,
                message="邀请码无效或已过期",
                data={"valid": False, "inviter": None}
            )
        
        inviter = db.query(User).filter(User.id == code.user_id).first()
        
        return ApiResponse(
            message="邀请码有效",
            data={
                "valid": True,
                "inviter": {
                    "id": inviter.id if inviter else None,
                    "username": inviter.username if inviter else None
                },
                "share_reward": f"双方各得 {SHARE_REWARD_FRAGMENTS} 星元碎片",
                "register_complete_reward": f"邀请人得 {REGISTER_COMPLETE_REWARD_TICKETS} 张星图盲盒券，被邀请人得 {REGISTER_COMPLETE_VIP_DAYS} 天VIP体验",
                "first_payment_reward": f"邀请人获得付费金额 {FIRST_PAYMENT_REWARD_RATE*100}% 返利"
            }
        )
        
    except Exception as e:
        logger.error(f"验证邀请码失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"验证邀请码失败: {str(e)}"
        )


@router.get("/my-invitees", response_model=ApiResponse)
def get_my_invitees(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        from sqlalchemy import desc
        
        from app.models import InviteRelation
        
        query = db.query(InviteRelation).filter(
            InviteRelation.inviter_id == current_user.id
        )
        
        total = query.count()
        
        relations = query.order_by(
            desc(InviteRelation.created_at)
        ).offset((page - 1) * page_size).limit(page_size).all()
        
        invitees = []
        for relation in relations:
            invitee = db.query(User).filter(User.id == relation.invitee_id).first()
            if invitee:
                invitees.append({
                    "user_id": invitee.id,
                    "username": invitee.username,
                    "invite_code_used": relation.invite_code_used,
                    "is_register_completed": relation.is_register_completed,
                    "register_completed_at": relation.register_completed_at.isoformat() if relation.register_completed_at else None,
                    "has_first_payment": relation.has_first_payment,
                    "first_payment_at": relation.first_payment_at.isoformat() if relation.first_payment_at else None,
                    "first_payment_amount": relation.first_payment_amount,
                    "is_valid": relation.is_valid,
                    "invalid_reason": relation.invalid_reason,
                    "created_at": relation.created_at.isoformat() if relation.created_at else None
                })
        
        return ApiResponse(
            message="获取邀请列表成功",
            data={
                "total": total,
                "page": page,
                "page_size": page_size,
                "invitees": invitees
            }
        )
        
    except Exception as e:
        logger.error(f"获取邀请列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取邀请列表失败: {str(e)}"
        )


@router.get("/rules", response_model=ApiResponse)
def get_invite_rules():
    return ApiResponse(
        message="获取邀请规则成功",
        data={
            "rules": [
                {
                    "stage": "share",
                    "stage_name": "分享注册",
                    "description": "分享 App 给好友，好友通过您的邀请码注册",
                    "inviter_reward": {
                        "type": "fragment",
                        "amount": SHARE_REWARD_FRAGMENTS,
                        "name": "星元碎片"
                    },
                    "invitee_reward": {
                        "type": "fragment",
                        "amount": SHARE_REWARD_FRAGMENTS,
                        "name": "星元碎片"
                    }
                },
                {
                    "stage": "register_complete",
                    "stage_name": "完成星盘",
                    "description": "好友注册后完成个人星盘设置",
                    "inviter_reward": {
                        "type": "ticket",
                        "amount": REGISTER_COMPLETE_REWARD_TICKETS,
                        "name": "星图盲盒券"
                    },
                    "invitee_reward": {
                        "type": "vip_trial",
                        "amount": REGISTER_COMPLETE_VIP_DAYS,
                        "name": "VIP会员体验"
                    }
                },
                {
                    "stage": "first_payment",
                    "stage_name": "首次付费",
                    "description": "好友完成首次任意付费消费",
                    "inviter_reward": {
                        "type": "rebate",
                        "rate": FIRST_PAYMENT_REWARD_RATE,
                        "name": "付费金额返利",
                        "description": f"获得好友付费金额 {FIRST_PAYMENT_REWARD_RATE*100}% 的返利，以星元碎片形式发放"
                    },
                    "invitee_reward": None
                }
            ],
            "anti_cheat": {
                "description": "为防止刷邀请行为，系统会进行以下检测：",
                "rules": [
                    "同一IP地址24小时内最多可邀请5人",
                    "同一邀请人短时间内不能重复邀请同一IP地址",
                    "异常行为可能导致邀请关系无效"
                ]
            }
        }
    )


@router.post("/test-bind-relation", response_model=ApiResponse)
def test_bind_invite_relation(
    request: Request,
    inviter_id: int,
    invitee_id: int,
    db: Session = Depends(get_db)
):
    try:
        from app.models import User
        
        inviter = db.query(User).filter(User.id == inviter_id).first()
        invitee = db.query(User).filter(User.id == invitee_id).first()
        
        if not inviter or not invitee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        invite_code = get_or_create_invite_code(db, inviter_id)
        
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("User-Agent")
        
        relation, error = create_invite_relation(
            db=db,
            inviter_id=inviter_id,
            invitee_id=invitee_id,
            invite_code=invite_code.invite_code,
            ip=client_ip,
            device=user_agent
        )
        
        if not relation:
            return ApiResponse(
                code=400,
                message=error or "绑定邀请关系失败",
                data=None
            )
        
        if relation.is_valid:
            process_share_reward(db, relation)
        
        return ApiResponse(
            message="绑定邀请关系成功",
            data={
                "relation_id": relation.id,
                "inviter_id": relation.inviter_id,
                "invitee_id": relation.invitee_id,
                "invite_code": relation.invite_code_used,
                "is_valid": relation.is_valid,
                "invalid_reason": relation.invalid_reason
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"绑定邀请关系失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"绑定邀请关系失败: {str(e)}"
        )