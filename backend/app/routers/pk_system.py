import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from app.database import get_db
from app.models import User
from app.routers.users import get_current_user, get_current_active_user
from app.schemas import ApiResponse
from app.services.pk_service import (
    get_pk_service,
    PKService,
    PKMatchService,
    PKBattleEngine,
    PKShopService,
    PKBattleErrorCode
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["星盘能量PK"])


class RandomMatchRequest(BaseModel):
    wager_fragments: int = Field(default=10, description="赌注星元碎片数量，默认10", ge=10, le=500)


class FriendInviteRequest(BaseModel):
    invitee_id: int = Field(..., description="被邀请用户ID")
    wager_fragments: int = Field(default=10, description="赌注星元碎片数量，默认10", ge=10, le=500)


class AcceptInviteRequest(BaseModel):
    invite_code: str = Field(..., description="邀请码")


class DeclineInviteRequest(BaseModel):
    invite_code: str = Field(..., description="邀请码")


class PurchaseChallengesRequest(BaseModel):
    count: int = Field(default=1, description="购买次数，默认1", ge=1)


@router.get("/status", response_model=ApiResponse)
def get_pk_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    获取用户PK状态
    """
    try:
        service = get_pk_service()
        status_data = service.get_user_pk_status(db, current_user.id)

        return ApiResponse(
            message="success",
            data=status_data
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取PK状态异常: 用户ID={current_user.id}, 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="获取PK状态失败，请稍后重试",
            data=None
        )


@router.post("/random-match", response_model=ApiResponse)
def start_random_match(
    request: RandomMatchRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    开始随机匹配
    """
    try:
        service = get_pk_service()
        match, err_code, msg = service.match_service.start_random_match(
            db, current_user.id, request.wager_fragments
        )

        if not match:
            error_msg = _get_error_message(err_code)
            return ApiResponse(
                code=400,
                message=error_msg or msg or "匹配失败",
                data={"error_code": err_code.value if err_code else None}
            )

        match_dict = service._match_to_dict(match, current_user.id)

        logger.info(f"用户 {current_user.id} 开始随机匹配: match_id={match.id}, wager={request.wager_fragments}")

        return ApiResponse(
            message=msg,
            data=match_dict
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"开始随机匹配异常: 用户ID={current_user.id}, 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="匹配失败，请稍后重试",
            data=None
        )


@router.post("/friend-invite", response_model=ApiResponse)
def create_friend_invite(
    request: FriendInviteRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    创建好友对战邀请
    """
    try:
        service = get_pk_service()
        invite, err_code, msg = service.match_service.create_friend_invite(
            db, current_user.id, request.invitee_id, request.wager_fragments
        )

        if not invite:
            error_msg = _get_error_message(err_code)
            return ApiResponse(
                code=400,
                message=error_msg or msg or "创建邀请失败",
                data={"error_code": err_code.value if err_code else None}
            )

        invite_dict = {
            "id": invite.id,
            "invite_code": invite.invite_code,
            "inviter_id": invite.inviter_id,
            "invitee_id": invite.invitee_id,
            "wager_fragments": invite.wager_fragments,
            "expires_at": invite.expires_at.isoformat() if invite.expires_at else None,
            "created_at": invite.created_at.isoformat() if invite.created_at else None,
        }

        logger.info(f"用户 {current_user.id} 创建好友邀请: invite_code={invite.invite_code}, invitee={request.invitee_id}")

        return ApiResponse(
            message=msg,
            data=invite_dict
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建好友邀请异常: 用户ID={current_user.id}, 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="创建邀请失败，请稍后重试",
            data=None
        )


@router.post("/accept-invite", response_model=ApiResponse)
def accept_invite(
    request: AcceptInviteRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    接受好友对战邀请
    """
    try:
        service = get_pk_service()
        match, err_code, msg = service.match_service.accept_invite(
            db, current_user.id, request.invite_code
        )

        if not match:
            error_msg = _get_error_message(err_code)
            return ApiResponse(
                code=400,
                message=error_msg or msg or "接受邀请失败",
                data={"error_code": err_code.value if err_code else None}
            )

        match_dict = service._match_to_dict(match, current_user.id)

        logger.info(f"用户 {current_user.id} 接受邀请: invite_code={request.invite_code}, match_id={match.id}")

        return ApiResponse(
            message=msg,
            data=match_dict
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"接受邀请异常: 用户ID={current_user.id}, 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="接受邀请失败，请稍后重试",
            data=None
        )


@router.post("/decline-invite", response_model=ApiResponse)
def decline_invite(
    request: DeclineInviteRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    拒绝好友对战邀请
    """
    try:
        service = get_pk_service()
        success, err_code, msg = service.match_service.decline_invite(
            db, current_user.id, request.invite_code
        )

        if not success:
            error_msg = _get_error_message(err_code)
            return ApiResponse(
                code=400,
                message=error_msg or msg or "拒绝邀请失败",
                data={"error_code": err_code.value if err_code else None}
            )

        logger.info(f"用户 {current_user.id} 拒绝邀请: invite_code={request.invite_code}")

        return ApiResponse(
            message=msg,
            data=None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"拒绝邀请异常: 用户ID={current_user.id}, 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="拒绝邀请失败，请稍后重试",
            data=None
        )


@router.post("/battle/{match_id}", response_model=ApiResponse)
def execute_battle(
    match_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    执行PK战斗
    """
    try:
        service = get_pk_service()

        match, err_code, msg = service.battle_engine.execute_battle(db, match_id)

        if not match:
            error_msg = _get_error_message(err_code)
            return ApiResponse(
                code=400,
                message=error_msg or msg or "战斗执行失败",
                data={"error_code": err_code.value if err_code else None}
            )

        match_dict = service._match_to_dict(match, current_user.id, include_detail=True)

        logger.info(f"用户 {current_user.id} 执行战斗: match_id={match_id}, result={match.result}")

        return ApiResponse(
            message=msg,
            data=match_dict
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"执行战斗异常: 用户ID={current_user.id}, match_id={match_id}, 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="战斗执行失败，请稍后重试",
            data=None
        )


@router.get("/match/{match_id}", response_model=ApiResponse)
def get_match_detail(
    match_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    获取对战详情
    """
    try:
        service = get_pk_service()
        match_dict = service.get_match_detail(db, match_id, current_user.id)

        if not match_dict:
            return ApiResponse(
                code=404,
                message="对战不存在或无权查看",
                data=None
            )

        return ApiResponse(
            message="success",
            data=match_dict
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取对战详情异常: 用户ID={current_user.id}, match_id={match_id}, 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="获取对战详情失败，请稍后重试",
            data=None
        )


@router.get("/pending-invites", response_model=ApiResponse)
def get_pending_invites(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    获取待处理的邀请列表
    """
    try:
        service = get_pk_service()
        invites = service.get_pending_invites(db, current_user.id)

        return ApiResponse(
            message="success",
            data={
                "invites": invites,
                "total_count": len(invites)
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取待处理邀请异常: 用户ID={current_user.id}, 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="获取邀请列表失败，请稍后重试",
            data=None
        )


@router.get("/sent-invites", response_model=ApiResponse)
def get_sent_invites(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    获取已发送的邀请列表
    """
    try:
        service = get_pk_service()
        invites = service.get_sent_invites(db, current_user.id)

        return ApiResponse(
            message="success",
            data={
                "invites": invites,
                "total_count": len(invites)
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取已发送邀请异常: 用户ID={current_user.id}, 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="获取邀请列表失败，请稍后重试",
            data=None
        )


@router.get("/waiting-matches", response_model=ApiResponse)
def get_waiting_matches(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    获取等待中的匹配列表
    """
    try:
        service = get_pk_service()
        matches = service.get_waiting_matches(db, current_user.id)

        return ApiResponse(
            message="success",
            data={
                "matches": matches,
                "total_count": len(matches)
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取等待匹配异常: 用户ID={current_user.id}, 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="获取匹配列表失败，请稍后重试",
            data=None
        )


@router.post("/cancel-match/{match_id}", response_model=ApiResponse)
def cancel_waiting_match(
    match_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    取消等待中的匹配
    """
    try:
        service = get_pk_service()
        success, err_code, msg = service.cancel_waiting_match(db, match_id, current_user.id)

        if not success:
            error_msg = _get_error_message(err_code)
            return ApiResponse(
                code=400,
                message=error_msg or msg or "取消匹配失败",
                data={"error_code": err_code.value if err_code else None}
            )

        logger.info(f"用户 {current_user.id} 取消等待匹配: match_id={match_id}")

        return ApiResponse(
            message=msg,
            data=None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消匹配异常: 用户ID={current_user.id}, match_id={match_id}, 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="取消匹配失败，请稍后重试",
            data=None
        )


@router.post("/shop/purchase-challenges", response_model=ApiResponse)
def purchase_challenges(
    request: PurchaseChallengesRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    购买额外PK挑战次数
    """
    try:
        service = get_pk_service()
        purchase, err_code, msg = service.shop_service.purchase_challenges(
            db, current_user.id, request.count
        )

        if not purchase:
            error_msg = _get_error_message(err_code)
            return ApiResponse(
                code=400,
                message=error_msg or msg or "购买失败",
                data={"error_code": err_code.value if err_code else None}
            )

        purchase_dict = {
            "id": purchase.id,
            "purchase_no": purchase.purchase_no,
            "challenges_purchased": purchase.challenges_purchased,
            "price_per_challenge": purchase.price_per_challenge,
            "total_price": purchase.total_price,
            "currency_type": purchase.currency_type,
            "purchase_date": purchase.purchase_date,
            "paid_at": purchase.paid_at.isoformat() if purchase.paid_at else None,
        }

        logger.info(f"用户 {current_user.id} 购买挑战次数: count={request.count}, total_price={purchase.total_price}")

        return ApiResponse(
            message=msg,
            data=purchase_dict
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"购买挑战次数异常: 用户ID={current_user.id}, 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="购买失败，请稍后重试",
            data=None
        )


@router.post("/shop/purchase-double-energy", response_model=ApiResponse)
def purchase_double_energy(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    购买当日能量翻倍Buff
    """
    try:
        service = get_pk_service()
        boost, err_code, msg = service.shop_service.purchase_double_energy_boost(db, current_user.id)

        if not boost:
            error_msg = _get_error_message(err_code)
            return ApiResponse(
                code=400,
                message=error_msg or msg or "购买失败",
                data={"error_code": err_code.value if err_code else None}
            )

        boost_dict = {
            "id": boost.id,
            "boost_type": boost.boost_type,
            "boost_name": boost.boost_name,
            "boost_description": boost.boost_description,
            "energy_multiplier": boost.energy_multiplier,
            "critical_hit_chance": boost.critical_hit_chance,
            "protection_rate": boost.protection_rate,
            "valid_from": boost.valid_from.isoformat() if boost.valid_from else None,
            "valid_until": boost.valid_until.isoformat() if boost.valid_until else None,
        }

        logger.info(f"用户 {current_user.id} 购买能量翻倍Buff: boost_id={boost.id}")

        return ApiResponse(
            message=msg,
            data=boost_dict
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"购买能量Buff异常: 用户ID={current_user.id}, 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="购买失败，请稍后重试",
            data=None
        )


@router.get("/shop/config", response_model=ApiResponse)
def get_shop_config(
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取PK商店配置
    """
    try:
        from app.services.pk_service import DEFAULT_CONFIG

        config = {
            "free_challenges_per_day": DEFAULT_CONFIG.get("free_challenges_per_day", 3),
            "wager_min_fragments": DEFAULT_CONFIG.get("wager_min_fragments", 10),
            "wager_max_fragments": DEFAULT_CONFIG.get("wager_max_fragments", 500),
            "winner_fraction_rate": DEFAULT_CONFIG.get("winner_fraction_rate", 0.8),
            "challenge_purchase_price_points": DEFAULT_CONFIG.get("challenge_purchase_price_points", 50),
            "double_energy_price_points": DEFAULT_CONFIG.get("double_energy_price_points", 100),
            "critical_hit_base_chance": DEFAULT_CONFIG.get("critical_hit_base_chance", 0.05),
            "critical_hit_multiplier": DEFAULT_CONFIG.get("critical_hit_multiplier", 1.5),
            "invite_expiry_minutes": DEFAULT_CONFIG.get("invite_expiry_minutes", 10),
            "match_waiting_timeout_seconds": DEFAULT_CONFIG.get("match_waiting_timeout_seconds", 60),
        }

        return ApiResponse(
            message="success",
            data=config
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取商店配置异常: 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="获取配置失败，请稍后重试",
            data=None
        )


def _get_error_message(err_code: Optional[PKBattleErrorCode]) -> str:
    """获取错误码对应的错误消息"""
    error_messages = {
        PKBattleErrorCode.USER_NOT_FOUND: "用户不存在",
        PKBattleErrorCode.NO_CHALLENGES_LEFT: "今日挑战次数已用完，请购买额外次数",
        PKBattleErrorCode.INSUFFICIENT_FRAGMENTS: "星元碎片不足",
        PKBattleErrorCode.INVALID_WAGER: "赌注金额无效，请输入10-500之间的数值",
        PKBattleErrorCode.MATCH_NOT_FOUND: "匹配不存在",
        PKBattleErrorCode.MATCH_NOT_IN_PROGRESS: "匹配不在进行中",
        PKBattleErrorCode.OPPONENT_NOT_FOUND: "对手不存在",
        PKBattleErrorCode.INVITE_NOT_FOUND: "邀请不存在",
        PKBattleErrorCode.INVITE_EXPIRED: "邀请已过期",
        PKBattleErrorCode.INVITE_ALREADY_ACCEPTED: "邀请已被处理",
        PKBattleErrorCode.CANNOT_INVITE_SELF: "不能邀请自己",
        PKBattleErrorCode.NO_MATCHES_AVAILABLE: "没有可用的匹配",
        PKBattleErrorCode.MATCH_ALREADY_COMPLETED: "匹配已完成",
        PKBattleErrorCode.BOOST_NOT_FOUND: "Buff不存在",
        PKBattleErrorCode.BOOST_EXPIRED: "Buff已过期",
        PKBattleErrorCode.INSUFFICIENT_POINTS: "星元点数不足",
        PKBattleErrorCode.PURCHASE_FAILED: "购买失败",
    }
    return error_messages.get(err_code, "操作失败")
