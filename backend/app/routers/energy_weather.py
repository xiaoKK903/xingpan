from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import json
import logging

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.schemas import ApiResponse
from app.database import get_db
from app.models import (
    User,
    StarDustTransaction,
    MissionCompletion,
    EnergyContribution
)
from app.routers.users import get_current_user, get_current_user_optional
from app.services.energy_weather_service import (
    energy_weather_service,
    ENERGY_CONTRIBUTION_TYPES,
    WARM_MISSION_TEMPLATES,
    OMINOUS_EVENTS,
    WEATHER_SEVERITY_CONFIG
)
from app.services.energy_mission_service import energy_mission_service
from app.services.energy_contribution_service import energy_contribution_service
from app.services.websocket_manager import websocket_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["能量气象站"])

CURRENCY_FRAGMENT = "fragment"
CURRENCY_POINT = "point"

CURRENCY_CONFIG = {
    CURRENCY_FRAGMENT: {
        "name": "星元碎片",
        "name_cn": "星元碎片",
        "description": "任务奖励获得，用于星能共鸣池",
        "is_reward": True,
        "user_field": "stardust_fragment_balance"
    },
    CURRENCY_POINT: {
        "name": "星尘积分",
        "name_cn": "星尘积分",
        "description": "消耗型货币，用于能量注入等操作",
        "is_reward": False,
        "user_field": "stardust_point_balance"
    }
}


def get_user_balance(user: User, currency_type: str) -> int:
    """获取用户指定货币类型的余额"""
    if currency_type == CURRENCY_FRAGMENT:
        return user.stardust_fragment_balance or 0
    elif currency_type == CURRENCY_POINT:
        return user.stardust_point_balance or 0
    return 0


def update_user_balance(user: User, currency_type: str, amount: int):
    """更新用户余额"""
    if currency_type == CURRENCY_FRAGMENT:
        if user.stardust_fragment_balance is None:
            user.stardust_fragment_balance = 0
        user.stardust_fragment_balance += amount
    elif currency_type == CURRENCY_POINT:
        if user.stardust_point_balance is None:
            user.stardust_point_balance = 0
        user.stardust_point_balance += amount


def create_transaction(
    db: Session,
    user_id: int,
    transaction_type: str,
    amount: int,
    currency_type: str,
    balance_before: int,
    balance_after: int,
    related_type: Optional[str] = None,
    related_id: Optional[str] = None,
    related_ref: Optional[str] = None,
    description: Optional[str] = None
) -> StarDustTransaction:
    """创建交易记录"""
    transaction = StarDustTransaction(
        user_id=user_id,
        transaction_type=transaction_type,
        currency_type=currency_type,
        amount=amount,
        balance_before=balance_before,
        balance_after=balance_after,
        related_type=related_type,
        related_id=str(related_id) if related_id else None,
        related_ref=related_ref,
        description=description,
        created_at=datetime.utcnow()
    )
    db.add(transaction)
    db.flush()
    return transaction


class MissionCompleteRequest(BaseModel):
    mission_instance_id: str = Field(..., description="任务实例ID")
    completed_actions: Optional[List[str]] = Field(None, description="完成的动作列表")
    proof_text: Optional[str] = Field(None, description="完成证明文本")


class EnergyContributionRequest(BaseModel):
    contribution_type: str = Field(..., description="贡献类型，如: sun_energy, moon_energy 等")


class WeatherLevel(str, Enum):
    CLEAR = "clear"
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"


def generate_completion_key(user_id: int, mission_instance_id: str) -> str:
    """生成任务完成的唯一键"""
    return f"u{user_id}_m{mission_instance_id}"


def find_mission_by_id(
    db: Session,
    mission_instance_id: str,
    triggered_missions: List[Dict[str, Any]],
    active_missions: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    根据任务ID查找任务
    
    优先查找触发的任务，然后查找活跃任务
    """
    for mission in triggered_missions:
        if mission.get("instance_id") == mission_instance_id:
            return {
                **mission,
                "is_triggered": True,
                "source": "triggered"
            }
    
    for mission in active_missions:
        mission_id = mission.get("id")
        if str(mission_id) == mission_instance_id or mission_id == mission_instance_id:
            return {
                **mission,
                "is_triggered": False,
                "source": "active"
            }
    
    return None


@router.get("/current", response_model=ApiResponse)
async def get_current_weather(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(lambda: None)
):
    """
    获取当前能量天气
    
    平行人生广场入口，一进广场就能看到集体能量天气。
    """
    try:
        weather = energy_weather_service.get_current_weather(db)
        
        user_assets = None
        if current_user:
            user_assets = {
                "stardust_fragment_balance": current_user.stardust_fragment_balance or 0,
                "stardust_point_balance": current_user.stardust_point_balance or 0,
                "currency_info": {
                    "fragment": CURRENCY_CONFIG[CURRENCY_FRAGMENT],
                    "point": CURRENCY_CONFIG[CURRENCY_POINT]
                }
            }
        
        return ApiResponse(
            message="获取能量天气成功",
            data={
                "weather": weather,
                "user_assets": user_assets,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"获取能量天气失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取能量天气失败: {str(e)}"
        )


@router.get("/history", response_model=ApiResponse)
async def get_weather_history(
    hours: int = Query(12, ge=1, le=24, description="历史小时数"),
    db: Session = Depends(get_db)
):
    """
    获取能量天气历史
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


@router.get("/missions", response_model=ApiResponse)
async def get_active_missions(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(lambda: None)
):
    """
    获取当前可用的暖心小任务
    """
    try:
        weather = energy_weather_service.get_current_weather(db)
        triggered_missions = weather.get("triggered_missions", [])
        
        active_missions = energy_mission_service.get_active_missions(db, limit=10)
        
        all_missions = []
        
        for mission in triggered_missions:
            all_missions.append({
                "id": mission.get("instance_id"),
                "type": mission.get("mission_type"),
                "title": mission.get("title"),
                "description": mission.get("description"),
                "difficulty": mission.get("difficulty"),
                "difficulty_label": {
                    "easy": "简单",
                    "medium": "中等",
                    "hard": "困难"
                }.get(mission.get("difficulty", "medium"), "中等"),
                "base_reward": mission.get("base_reward"),
                "reward_currency": "星元碎片",
                "duration_minutes": mission.get("duration_minutes"),
                "energy_requirement": mission.get("energy_requirement"),
                "mood_trigger": mission.get("mood_trigger"),
                "generated_at": mission.get("generated_at"),
                "expires_at": mission.get("expires_at"),
                "is_triggered": True,
                "template_id": mission.get("id")
            })
        
        for mission in active_missions:
            all_missions.append({
                "id": mission.get("id"),
                "type": mission.get("type"),
                "title": mission.get("title"),
                "description": mission.get("description"),
                "difficulty": mission.get("difficulty"),
                "difficulty_label": mission.get("difficulty_label"),
                "base_reward": mission.get("base_reward"),
                "reward_currency": "星元碎片",
                "duration_minutes": mission.get("duration_minutes"),
                "energy_requirement": mission.get("energy_requirement"),
                "start_at": mission.get("start_at"),
                "end_at": mission.get("end_at"),
                "participant_count": mission.get("participant_count"),
                "is_triggered": False
            })
        
        user_completed_missions = []
        if current_user:
            recent_completions = db.query(MissionCompletion).filter(
                MissionCompletion.user_id == current_user.id,
                MissionCompletion.created_at >= datetime.utcnow() - timedelta(hours=24)
            ).all()
            user_completed_missions = [c.mission_id for c in recent_completions]
        
        return ApiResponse(
            message="获取任务列表成功",
            data={
                "missions": all_missions,
                "count": len(all_missions),
                "collective_mood": weather.get("collective_mood"),
                "weather_label": weather.get("weather_label"),
                "currency_info": {
                    "fragment": CURRENCY_CONFIG[CURRENCY_FRAGMENT],
                    "point": CURRENCY_CONFIG[CURRENCY_POINT]
                },
                "user_completed_today": user_completed_missions
            }
        )
        
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务列表失败: {str(e)}"
        )


@router.post("/missions/complete", response_model=ApiResponse)
async def complete_mission(
    request: MissionCompleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    完成暖心小任务，获得星元碎片奖励
    
    流程：
    1. 校验任务是否存在
    2. 校验用户是否已完成该任务（唯一性校验）
    3. 计算奖励金额（含预警加成）
    4. 更新用户余额
    5. 记录交易流水
    6. 记录任务完成
    """
    mission_instance_id = request.mission_instance_id
    
    try:
        weather = energy_weather_service.get_current_weather(db)
        triggered_missions = weather.get("triggered_missions", [])
        active_missions = energy_mission_service.get_active_missions(db, limit=100)
        
        mission = find_mission_by_id(
            db=db,
            mission_instance_id=mission_instance_id,
            triggered_missions=triggered_missions,
            active_missions=active_missions
        )
        
        if not mission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "MISSION_NOT_FOUND",
                    "message": f"任务不存在: {mission_instance_id}",
                    "mission_id": mission_instance_id
                }
            )
        
        completion_key = generate_completion_key(current_user.id, mission_instance_id)
        
        existing_completion = db.query(MissionCompletion).filter(
            MissionCompletion.completion_key == completion_key
        ).first()
        
        if existing_completion:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "MISSION_ALREADY_COMPLETED",
                    "message": "您已完成该任务，无法重复领取奖励",
                    "mission_id": mission_instance_id,
                    "completed_at": existing_completion.created_at.isoformat() if existing_completion.created_at else None,
                    "reward_amount": existing_completion.reward_amount
                }
            )
        
        base_reward = mission.get("base_reward", 10)
        mission_title = mission.get("title", "暖心任务")
        mission_type = mission.get("type", "warm_mission")
        
        is_bonus = False
        bonus_reason = None
        
        has_warning = weather.get("has_warning", False)
        if has_warning:
            base_reward = int(base_reward * 1.5)
            is_bonus = True
            bonus_reason = "凶星天象预警加成"
        
        reward_amount = base_reward
        currency_type = CURRENCY_FRAGMENT
        
        try:
            balance_before = get_user_balance(current_user, currency_type)
            balance_after = balance_before + reward_amount
            
            transaction = create_transaction(
                db=db,
                user_id=current_user.id,
                transaction_type="mission_reward",
                amount=reward_amount,
                currency_type=currency_type,
                balance_before=balance_before,
                balance_after=balance_after,
                related_type="mission",
                related_id=mission_instance_id,
                related_ref=completion_key,
                description=f"完成任务「{mission_title}」获得{CURRENCY_CONFIG[currency_type]['name_cn']}奖励"
            )
            
            update_user_balance(current_user, currency_type, reward_amount)
            
            completion_data = {}
            if request.completed_actions:
                completion_data["completed_actions"] = request.completed_actions
            
            mission_completion = MissionCompletion(
                user_id=current_user.id,
                mission_id=mission_instance_id,
                mission_type=mission_type,
                mission_title=mission_title,
                completion_key=completion_key,
                reward_amount=reward_amount,
                currency_type=currency_type,
                transaction_id=transaction.id,
                proof_text=request.proof_text,
                completion_data=json.dumps(completion_data, ensure_ascii=False) if completion_data else None,
                is_bonus=is_bonus,
                bonus_reason=bonus_reason,
                created_at=datetime.utcnow()
            )
            
            db.add(mission_completion)
            db.commit()
            db.refresh(transaction)
            db.refresh(mission_completion)
            db.refresh(current_user)
            
        except Exception as e:
            db.rollback()
            logger.error(f"任务完成事务失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"任务奖励发放失败: {str(e)}"
            )
        
        logger.info(
            f"用户 {current_user.id} 完成任务 {mission_instance_id}, "
            f"获得 {reward_amount} {CURRENCY_CONFIG[currency_type]['name_cn']}, "
            f"余额: {balance_before} -> {balance_after}"
        )
        
        try:
            await websocket_manager.send_to_user(
                user_id=str(current_user.id),
                message_type="mission_completed",
                data={
                    "mission_id": mission_instance_id,
                    "mission_title": mission_title,
                    "reward_amount": reward_amount,
                    "reward_currency": CURRENCY_CONFIG[currency_type]['name_cn'],
                    "is_bonus": is_bonus,
                    "bonus_reason": bonus_reason,
                    "balance_before": balance_before,
                    "balance_after": balance_after,
                    "transaction": {
                        "id": transaction.id,
                        "type": transaction.transaction_type,
                        "currency_type": transaction.currency_type,
                        "amount": transaction.amount,
                        "description": transaction.description,
                        "created_at": transaction.created_at.isoformat() if transaction.created_at else None
                    }
                }
            )
        except Exception as e:
            logger.warning(f"WebSocket 通知失败: {e}")
        
        return ApiResponse(
            message="任务完成成功",
            data={
                "success": True,
                "mission_id": mission_instance_id,
                "mission_title": mission_title,
                "mission_type": mission_type,
                "reward": {
                    "amount": reward_amount,
                    "currency": CURRENCY_CONFIG[currency_type]['name_cn'],
                    "currency_type": currency_type
                },
                "is_bonus": is_bonus,
                "bonus_reason": bonus_reason,
                "balance": {
                    "before": balance_before,
                    "after": balance_after
                },
                "transaction": {
                    "id": transaction.id,
                    "type": transaction.transaction_type,
                    "description": transaction.description,
                    "created_at": transaction.created_at.isoformat() if transaction.created_at else None
                },
                "completion_id": mission_completion.id,
                "completed_at": mission_completion.created_at.isoformat() if mission_completion.created_at else None
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"完成任务失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"完成任务失败: {str(e)}"
        )


@router.get("/contribution-types", response_model=ApiResponse)
async def get_contribution_types(
    current_user: Optional[User] = Depends(lambda: None)
):
    """
    获取可用的能量贡献类型
    """
    try:
        types = energy_weather_service.get_available_contribution_types()
        
        for contrib in types:
            contrib["cost_currency"] = "星尘积分"
        
        return ApiResponse(
            message="获取贡献类型成功",
            data={
                "contribution_types": types,
                "count": len(types),
                "currency_info": CURRENCY_CONFIG[CURRENCY_POINT]
            }
        )
        
    except Exception as e:
        logger.error(f"获取贡献类型失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取贡献类型失败: {str(e)}"
        )


@router.post("/contribute", response_model=ApiResponse)
async def contribute_energy(
    request: EnergyContributionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    注入行星能量，提升集体场域
    
    流程：
    1. 校验贡献类型是否有效
    2. 校验用户余额是否足够
    3. 扣除用户资产（星尘积分）
    4. 记录交易流水
    5. 创建能量贡献记录
    6. 广播到全服
    """
    contribution_type = request.contribution_type
    
    try:
        if contribution_type not in ENERGY_CONTRIBUTION_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_CONTRIBUTION_TYPE",
                    "message": f"无效的贡献类型: {contribution_type}",
                    "contribution_type": contribution_type
                }
            )
        
        config = ENERGY_CONTRIBUTION_TYPES[contribution_type]
        cost_stardust = config.get("cost_stardust", 5)
        base_energy = config.get("base_energy", 10.0)
        planet_name = config.get("name", "行星能量")
        
        currency_type = CURRENCY_POINT
        
        balance_before = get_user_balance(current_user, currency_type)
        
        if balance_before < cost_stardust:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INSUFFICIENT_BALANCE",
                    "message": f"星尘积分不足，需要 {cost_stardust}，当前余额 {balance_before}",
                    "required": cost_stardust,
                    "current_balance": balance_before,
                    "currency": CURRENCY_CONFIG[currency_type]['name_cn']
                }
            )
        
        try:
            balance_after = balance_before - cost_stardust
            
            transaction = create_transaction(
                db=db,
                user_id=current_user.id,
                transaction_type="contribution_cost",
                amount=-cost_stardust,
                currency_type=currency_type,
                balance_before=balance_before,
                balance_after=balance_after,
                related_type="contribution",
                related_ref=contribution_type,
                description=f"注入{planet_name}消耗{CURRENCY_CONFIG[currency_type]['name_cn']}"
            )
            
            update_user_balance(current_user, currency_type, -cost_stardust)
            
            contribution_result = energy_contribution_service.contribute_energy(
                db=db,
                user_id=current_user.id,
                contribution_type=contribution_type,
                scope="global"
            )
            
            if not contribution_result.get("success"):
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=contribution_result.get("error", "能量注入失败")
                )
            
            db.commit()
            db.refresh(transaction)
            db.refresh(current_user)
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"能量注入事务失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"能量注入失败: {str(e)}"
            )
        
        contribution = contribution_result.get("contribution", {})
        
        logger.info(
            f"用户 {current_user.id} 注入 {contribution_type}, "
            f"消耗 {cost_stardust} {CURRENCY_CONFIG[currency_type]['name_cn']}, "
            f"余额: {balance_before} -> {balance_after}"
        )
        
        try:
            await websocket_manager.broadcast(
                message_type="energy_contributed",
                data={
                    "user_id": current_user.id,
                    "username": current_user.username,
                    "contribution_type": contribution_type,
                    "planet_name": planet_name,
                    "planet_icon": config.get("icon", "✨"),
                    "base_energy": base_energy,
                    "energy_amount": contribution.get("energy_amount"),
                    "cost": {
                        "amount": cost_stardust,
                        "currency": CURRENCY_CONFIG[currency_type]['name_cn']
                    },
                    "message": f"{current_user.username} 注入了 {planet_name}！"
                },
                channel="global"
            )
        except Exception as e:
            logger.warning(f"WebSocket 广播失败: {e}")
        
        return ApiResponse(
            message=contribution_result.get("message", "能量注入成功"),
            data={
                "success": True,
                "contribution": contribution,
                "cost": {
                    "amount": cost_stardust,
                    "currency": CURRENCY_CONFIG[currency_type]['name_cn'],
                    "currency_type": currency_type
                },
                "balance": {
                    "before": balance_before,
                    "after": balance_after
                },
                "transaction": {
                    "id": transaction.id,
                    "type": transaction.transaction_type,
                    "description": transaction.description,
                    "created_at": transaction.created_at.isoformat() if transaction.created_at else None
                },
                "config": {
                    "name": planet_name,
                    "planet": config.get("planet"),
                    "icon": config.get("icon"),
                    "color": config.get("color"),
                    "base_energy": config.get("base_energy"),
                    "duration_minutes": config.get("duration_minutes")
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"注入能量失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注入能量失败: {str(e)}"
        )


@router.get("/my-completions", response_model=ApiResponse)
async def get_my_completions(
    limit: int = Query(20, ge=1, le=100, description="限制数量"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    获取我的任务完成记录
    如果用户未登录，返回空列表
    """
    try:
        if not current_user:
            return ApiResponse(
                message="获取完成记录成功",
                data={
                    "completions": [],
                    "count": 0,
                    "total_rewards": 0,
                    "is_logged_in": False
                }
            )
        
        completions = db.query(MissionCompletion).filter(
            MissionCompletion.user_id == current_user.id
        ).order_by(
            MissionCompletion.created_at.desc()
        ).limit(limit).all()
        
        result = []
        for c in completions:
            result.append({
                "id": c.id,
                "mission_id": c.mission_id,
                "mission_type": c.mission_type,
                "mission_title": c.mission_title,
                "reward_amount": c.reward_amount,
                "reward_currency": CURRENCY_CONFIG.get(c.currency_type, {}).get("name_cn", c.currency_type),
                "is_bonus": c.is_bonus,
                "bonus_reason": c.bonus_reason,
                "proof_text": c.proof_text,
                "created_at": c.created_at.isoformat() if c.created_at else None
            })
        
        total_rewards = sum(c.reward_amount or 0 for c in completions)
        
        return ApiResponse(
            message="获取完成记录成功",
            data={
                "completions": result,
                "count": len(result),
                "total_rewards": total_rewards,
                "is_logged_in": True
            }
        )
        
    except Exception as e:
        logger.error(f"获取完成记录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取完成记录失败: {str(e)}"
        )


@router.get("/my-transactions", response_model=ApiResponse)
async def get_my_transactions(
    currency_type: Optional[str] = Query(None, description="货币类型: fragment, point"),
    limit: int = Query(20, ge=1, le=100, description="限制数量"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    获取我的交易记录
    如果用户未登录，返回空列表
    """
    try:
        if not current_user:
            return ApiResponse(
                message="获取交易记录成功",
                data={
                    "transactions": [],
                    "count": 0,
                    "currency_filter": currency_type,
                    "current_balances": {
                        "fragment": 0,
                        "point": 0
                    },
                    "is_logged_in": False
                }
            )
        
        query = db.query(StarDustTransaction).filter(
            StarDustTransaction.user_id == current_user.id
        )
        
        if currency_type:
            query = query.filter(StarDustTransaction.currency_type == currency_type)
        
        transactions = query.order_by(
            StarDustTransaction.created_at.desc()
        ).limit(limit).all()
        
        result = []
        for t in transactions:
            result.append({
                "id": t.id,
                "transaction_type": t.transaction_type,
                "currency_type": t.currency_type,
                "currency_name": CURRENCY_CONFIG.get(t.currency_type, {}).get("name_cn", t.currency_type),
                "amount": t.amount,
                "balance_before": t.balance_before,
                "balance_after": t.balance_after,
                "related_type": t.related_type,
                "related_id": t.related_id,
                "description": t.description,
                "created_at": t.created_at.isoformat() if t.created_at else None
            })
        
        return ApiResponse(
            message="获取交易记录成功",
            data={
                "transactions": result,
                "count": len(result),
                "currency_filter": currency_type,
                "current_balances": {
                    "fragment": current_user.stardust_fragment_balance or 0,
                    "point": current_user.stardust_point_balance or 0
                },
                "is_logged_in": True
            }
        )
        
    except Exception as e:
        logger.error(f"获取交易记录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取交易记录失败: {str(e)}"
        )


@router.get("/my-contributions", response_model=ApiResponse)
async def get_my_contributions(
    only_active: bool = Query(True, description="只获取活跃的贡献"),
    limit: int = Query(20, ge=1, le=100, description="限制数量"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    获取我的能量贡献记录
    如果用户未登录，返回空列表
    """
    try:
        if not current_user:
            return ApiResponse(
                message="获取贡献记录成功",
                data={
                    "contributions": [],
                    "count": 0,
                    "only_active": only_active,
                    "is_logged_in": False
                }
            )
        
        contributions = energy_contribution_service.get_user_contributions(
            db=db,
            user_id=current_user.id,
            only_active=only_active,
            limit=limit
        )
        
        return ApiResponse(
            message="获取贡献记录成功",
            data={
                "contributions": contributions,
                "count": len(contributions),
                "only_active": only_active,
                "is_logged_in": True
            }
        )
        
    except Exception as e:
        logger.error(f"获取贡献记录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取贡献记录失败: {str(e)}"
        )


@router.get("/ominous-events", response_model=ApiResponse)
async def get_ominous_events_info(
    db: Session = Depends(get_db)
):
    """
    获取所有凶星天象的说明信息
    """
    try:
        events_info = []
        for key, config in OMINOUS_EVENTS.items():
            severity = config.get("severity")
            severity_value = severity.value if hasattr(severity, "value") else severity
            
            events_info.append({
                "event_key": key,
                "name": config.get("name"),
                "planet": config.get("planet") or config.get("planets"),
                "icon": config.get("icon"),
                "severity": severity_value,
                "severity_config": WEATHER_SEVERITY_CONFIG.get(
                    severity,
                    WEATHER_SEVERITY_CONFIG.get(WeatherLevel.SEVERE)
                ) if severity else None,
                "description": config.get("description"),
                "affected_areas": config.get("affected_areas"),
                "recommendations": config.get("recommendations")
            })
        
        return ApiResponse(
            message="获取凶星天象信息成功",
            data={
                "ominous_events": events_info,
                "count": len(events_info)
            }
        )
        
    except Exception as e:
        logger.error(f"获取凶星天象信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取凶星天象信息失败: {str(e)}"
        )


@router.get("/mission-templates", response_model=ApiResponse)
async def get_mission_templates(
    mood_type: Optional[str] = Query(None, description="情绪类型: harmonious_high, balanced, tense, challenging")
):
    """
    获取暖心小任务模板库
    """
    try:
        templates = {}
        
        if mood_type:
            if mood_type in WARM_MISSION_TEMPLATES:
                templates[mood_type] = WARM_MISSION_TEMPLATES[mood_type]
        else:
            templates = dict(WARM_MISSION_TEMPLATES)
        
        return ApiResponse(
            message="获取任务模板成功",
            data={
                "templates": templates,
                "mood_type": mood_type,
                "available_moods": list(WARM_MISSION_TEMPLATES.keys())
            }
        )
        
    except Exception as e:
        logger.error(f"获取任务模板失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务模板失败: {str(e)}"
        )


@router.get("/weather-levels", response_model=ApiResponse)
async def get_weather_levels():
    """
    获取天气等级配置
    """
    try:
        levels_info = {}
        for level, config in WEATHER_SEVERITY_CONFIG.items():
            level_value = level.value if hasattr(level, "value") else level
            levels_info[level_value] = {
                "label": config.get("label"),
                "icon": config.get("icon"),
                "color": config.get("color"),
                "bg_color": config.get("bg_color"),
                "description": config.get("description"),
                "is_warning": config.get("is_warning", False),
                "is_critical": config.get("is_critical", False)
            }
        
        return ApiResponse(
            message="获取天气等级成功",
            data={
                "weather_levels": levels_info,
                "levels_order": [
                    WeatherLevel.CLEAR.value,
                    WeatherLevel.MILD.value,
                    WeatherLevel.MODERATE.value,
                    WeatherLevel.SEVERE.value,
                    WeatherLevel.CRITICAL.value
                ]
            }
        )
        
    except Exception as e:
        logger.error(f"获取天气等级失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取天气等级失败: {str(e)}"
        )


@router.post("/refresh", response_model=ApiResponse)
async def refresh_weather(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(lambda: None)
):
    """
    手动刷新能量天气（用于调试或立即更新）
    """
    try:
        weather = energy_weather_service.calculate_hourly_energy(db)
        weather_dict = energy_weather_service._snapshot_to_dict(weather)
        
        try:
            await websocket_manager.broadcast(
                message_type="energy_weather_update",
                data=weather_dict,
                channel="global"
            )
            
            triggered_missions = weather_dict.get("triggered_missions", [])
            if triggered_missions:
                await websocket_manager.broadcast(
                    message_type="new_warm_missions",
                    data={
                        "missions": triggered_missions,
                        "collective_mood": weather_dict.get("collective_mood"),
                        "weather_label": weather_dict.get("weather_label"),
                        "has_warning": weather_dict.get("has_warning")
                    },
                    channel="global"
                )
        except Exception as e:
            logger.warning(f"WebSocket 广播失败: {e}")
        
        logger.info(f"手动刷新能量天气: {weather_dict.get('weather_label')}")
        
        return ApiResponse(
            message="能量天气刷新成功",
            data={
                "weather": weather_dict,
                "triggered_missions_count": len(weather_dict.get("triggered_missions", []))
            }
        )
        
    except Exception as e:
        logger.error(f"刷新能量天气失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"刷新能量天气失败: {str(e)}"
        )
