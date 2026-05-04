import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.database import get_db
from app.models import User
from app.routers.users import get_current_user, get_current_active_user
from app.schemas import ApiResponse
from app.services.leaderboard_service import (
    get_leaderboard_service,
    LeaderboardService,
)
from app.models import LeaderboardType, LeaderboardCycle

logger = logging.getLogger(__name__)
router = APIRouter(tags=["荣誉排行榜"])


def init_leaderboards_data(db: Session):
    """初始化排行榜数据"""
    service = get_leaderboard_service()
    service.initialize_default_configs(db)


@router.get("/configs", response_model=ApiResponse)
def get_leaderboard_configs(
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取所有激活的排行榜配置
    """
    try:
        init_leaderboards_data(db)
        
        service = get_leaderboard_service()
        configs = service.get_active_configs(db)
        
        return ApiResponse(
            message="success",
            data={
                "configs": configs,
                "total_count": len(configs)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取排行榜配置异常: 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="获取排行榜配置失败，请稍后重试",
            data=None
        )


@router.get("/board/{board_key}", response_model=ApiResponse)
def get_leaderboard_data(
    board_key: str,
    cycle_key: Optional[str] = Query(None, description="周期key，不传则使用当前周期"),
    limit: int = Query(20, ge=1, le=100, description="获取数量"),
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取排行榜数据
    """
    try:
        init_leaderboards_data(db)
        
        service = get_leaderboard_service()
        result = service.get_leaderboard_data(db, board_key, cycle_key, limit)
        
        if not result.get("success"):
            return ApiResponse(
                code=404,
                message=result.get("error", "排行榜不存在"),
                data=None
            )
        
        user_rank_data = None
        if current_user:
            user_rank_result = service.get_user_rank(db, current_user.id, board_key, cycle_key)
            if user_rank_result.get("success"):
                user_rank_data = user_rank_result.get("data")
        
        data = result.get("data", {})
        data["user_rank"] = user_rank_data
        
        return ApiResponse(
            message="success",
            data=data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取排行榜数据异常: board_key={board_key}, 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="获取排行榜数据失败，请稍后重试",
            data=None
        )


@router.get("/my-rank/{board_key}", response_model=ApiResponse)
def get_my_rank(
    board_key: str,
    cycle_key: Optional[str] = Query(None, description="周期key，不传则使用当前周期"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    获取当前用户的排名
    """
    try:
        init_leaderboards_data(db)
        
        service = get_leaderboard_service()
        result = service.get_user_rank(db, current_user.id, board_key, cycle_key)
        
        if not result.get("success"):
            return ApiResponse(
                code=404,
                message=result.get("error", "获取排名失败"),
                data=None
            )
        
        return ApiResponse(
            message="success",
            data=result.get("data")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户排名异常: 用户ID={current_user.id}, board_key={board_key}, 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="获取排名失败，请稍后重试",
            data=None
        )


@router.get("/my-badges", response_model=ApiResponse)
def get_my_badges(
    include_expired: bool = Query(False, description="是否包含已过期的徽章"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    获取当前用户的徽章列表
    """
    try:
        from app.models import UserBadge
        
        now = datetime.utcnow()
        
        query = db.query(UserBadge).filter(
            UserBadge.user_id == current_user.id
        )
        
        if not include_expired:
            query = query.filter(
                (UserBadge.valid_until == None) | (UserBadge.valid_until > now)
            )
        
        badges = query.order_by(
            UserBadge.is_equipped.desc(),
            UserBadge.created_at.desc()
        ).all()
        
        badges_data = []
        for badge in badges:
            badges_data.append({
                "id": badge.id,
                "badge_key": badge.badge_key,
                "badge_name": badge.badge_name,
                "badge_description": badge.badge_description,
                "badge_icon": badge.badge_icon,
                "badge_animation": badge.badge_animation,
                "badge_rarity": badge.badge_rarity,
                "source_type": badge.source_type,
                "source_reference": badge.source_reference,
                "is_equipped": badge.is_equipped,
                "equipped_at": badge.equipped_at.isoformat() if badge.equipped_at else None,
                "is_limited": badge.is_limited,
                "valid_from": badge.valid_from.isoformat() if badge.valid_from else None,
                "valid_until": badge.valid_until.isoformat() if badge.valid_until else None,
                "created_at": badge.created_at.isoformat() if badge.created_at else None
            })
        
        return ApiResponse(
            message="success",
            data={
                "badges": badges_data,
                "total_count": len(badges_data),
                "equipped_count": sum(1 for b in badges if b.is_equipped)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户徽章异常: 用户ID={current_user.id}, 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="获取徽章失败，请稍后重试",
            data=None
        )


@router.get("/my-titles", response_model=ApiResponse)
def get_my_titles(
    include_expired: bool = Query(False, description="是否包含已过期的称号"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    获取当前用户的称号列表
    """
    try:
        from app.models import UserTitle
        
        now = datetime.utcnow()
        
        query = db.query(UserTitle).filter(
            UserTitle.user_id == current_user.id
        )
        
        if not include_expired:
            query = query.filter(
                (UserTitle.valid_until == None) | (UserTitle.valid_until > now)
            )
        
        titles = query.order_by(
            UserTitle.is_equipped.desc(),
            UserTitle.created_at.desc()
        ).all()
        
        titles_data = []
        for title in titles:
            titles_data.append({
                "id": title.id,
                "title_key": title.title_key,
                "title_name": title.title_name,
                "title_description": title.title_description,
                "title_color": title.title_color,
                "title_effect": title.title_effect,
                "source_type": title.source_type,
                "source_reference": title.source_reference,
                "is_equipped": title.is_equipped,
                "equipped_at": title.equipped_at.isoformat() if title.equipped_at else None,
                "is_limited": title.is_limited,
                "valid_from": title.valid_from.isoformat() if title.valid_from else None,
                "valid_until": title.valid_until.isoformat() if title.valid_until else None,
                "created_at": title.created_at.isoformat() if title.created_at else None
            })
        
        return ApiResponse(
            message="success",
            data={
                "titles": titles_data,
                "total_count": len(titles_data),
                "equipped_count": sum(1 for t in titles if t.is_equipped)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户称号异常: 用户ID={current_user.id}, 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="获取称号失败，请稍后重试",
            data=None
        )


@router.post("/refresh-board/{board_key}", response_model=ApiResponse)
def refresh_leaderboard(
    board_key: str,
    cycle_key: Optional[str] = Query(None, description="周期key，不传则使用当前周期"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    刷新排行榜数据（管理接口）
    
    注意：这个接口应该由后台任务定时调用，而不是频繁由用户调用
    """
    try:
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有管理员可以刷新排行榜"
            )
        
        init_leaderboards_data(db)
        
        service = get_leaderboard_service()
        result = service.calculate_and_update_leaderboard(db, board_key, cycle_key)
        
        if not result.get("success"):
            return ApiResponse(
                code=400,
                message=result.get("error", "刷新排行榜失败"),
                data=None
            )
        
        logger.info(f"管理员 {current_user.id} 刷新排行榜: board_key={board_key}")
        
        return ApiResponse(
            message="排行榜刷新成功",
            data=result.get("data")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刷新排行榜异常: board_key={board_key}, 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="刷新排行榜失败，请稍后重试",
            data=None
        )


@router.post("/distribute-rewards/{board_key}", response_model=ApiResponse)
def distribute_board_rewards(
    board_key: str,
    cycle_key: Optional[str] = Query(None, description="周期key，不传则使用当前周期"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    发放排行榜奖励（管理接口）
    """
    try:
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有管理员可以发放排行榜奖励"
            )
        
        init_leaderboards_data(db)
        
        service = get_leaderboard_service()
        result = service.distribute_leaderboard_rewards(db, board_key, cycle_key)
        
        if not result.get("success"):
            return ApiResponse(
                code=400,
                message=result.get("error", "发放奖励失败"),
                data=None
            )
        
        logger.info(f"管理员 {current_user.id} 发放排行榜奖励: board_key={board_key}")
        
        return ApiResponse(
            message="排行榜奖励发放成功",
            data=result.get("data")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"发放排行榜奖励异常: board_key={board_key}, 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="发放奖励失败，请稍后重试",
            data=None
        )


@router.get("/board-types", response_model=ApiResponse)
def get_board_types(
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取排行榜类型列表
    """
    board_types = [
        {
            "type": LeaderboardType.WEEKLY_ENERGY.value,
            "name": "周能量榜",
            "description": "每周能量贡献排行榜"
        },
        {
            "type": LeaderboardType.PREDICTION_HIT.value,
            "name": "预言家命中榜",
            "description": "预言家礼堂竞猜命中排行榜"
        },
        {
            "type": LeaderboardType.FRIEND_NETWORK.value,
            "name": "人脉好友榜",
            "description": "人脉好友数量排行榜"
        }
    ]
    
    cycle_types = [
        {
            "type": LeaderboardCycle.DAILY.value,
            "name": "每日"
        },
        {
            "type": LeaderboardCycle.WEEKLY.value,
            "name": "每周"
        },
        {
            "type": LeaderboardCycle.MONTHLY.value,
            "name": "每月"
        },
        {
            "type": LeaderboardCycle.SEASONAL.value,
            "name": "赛季"
        }
    ]
    
    return ApiResponse(
        message="success",
        data={
            "board_types": board_types,
            "cycle_types": cycle_types
        }
    )


@router.post("/init-data", response_model=ApiResponse)
def initialize_leaderboards_data(
    db: Session = Depends(get_db)
):
    """
    初始化排行榜数据（管理接口）
    """
    try:
        init_leaderboards_data(db)
        
        from app.models import LeaderboardConfig, LeaderboardReward
        configs_count = db.query(LeaderboardConfig).count()
        rewards_count = db.query(LeaderboardReward).count()
        
        return ApiResponse(
            message="排行榜数据初始化完成",
            data={
                "configs_count": configs_count,
                "rewards_count": rewards_count
            }
        )
        
    except Exception as e:
        logger.error(f"初始化排行榜数据异常: 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message=f"初始化失败: {str(e)}",
            data=None
        )
