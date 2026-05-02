import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models import User
from app.schemas import (
    ApiResponse,
    CheckInStatusResponse,
    CheckInPerformResponse,
    CheckInHistoryResponse
)
from app.routers.users import get_current_active_user
from app.services.checkin_service import get_checkin_service, CheckInService

logger = logging.getLogger(__name__)
router = APIRouter()


def get_client_ip(request: Request) -> str:
    """获取客户端IP地址"""
    x_forwarded_for = request.headers.get('X-Forwarded-For')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.client.host if request.client else ""


def get_device_info(request: Request) -> str:
    """获取设备信息"""
    user_agent = request.headers.get('User-Agent', '')
    return user_agent[:500]


@router.get("/status", response_model=ApiResponse)
def get_checkin_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    获取签到状态
    
    返回用户今日是否已签到、连续签到天数、奖励配置等信息
    """
    try:
        service = get_checkin_service()
        
        service.initialize_default_rewards(db)
        
        result = service.get_checkin_status(db, current_user.id)
        
        if not result.get("success"):
            error_code = result.get("error_code", "CHECKIN_STATUS_FAILED")
            logger.warning(f"用户 {current_user.id} 获取签到状态失败: {result.get('error')}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "获取签到状态失败")
            )
        
        return ApiResponse(
            code=200,
            message="success",
            data=result.get("data")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取签到状态接口异常: 用户ID={current_user.id}, 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="系统异常，请稍后重试",
            data=None
        )


@router.post("/sign", response_model=ApiResponse)
def perform_checkin(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    执行签到
    
    完成每日签到，自动发放对应天数的奖励
    """
    try:
        service = get_checkin_service()
        
        service.initialize_default_rewards(db)
        
        ip_address = get_client_ip(request)
        device_info = get_device_info(request)
        
        result = service.perform_checkin(
            db=db,
            user_id=current_user.id,
            ip_address=ip_address,
            device_info=device_info
        )
        
        if not result.get("success"):
            error_code = result.get("error_code", "CHECKIN_FAILED")
            
            if error_code == "ALREADY_CHECKED_IN":
                logger.warning(f"用户 {current_user.id} 重复签到请求")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="今日已签到"
                )
            elif error_code == "USER_NOT_FOUND":
                logger.warning(f"用户 {current_user.id} 不存在")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="用户不存在"
                )
            else:
                logger.warning(f"用户 {current_user.id} 签到失败: {result.get('error')}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result.get("error", "签到失败")
                )
        
        logger.info(f"用户 {current_user.id} 签到成功，连续签到: {result.get('data', {}).get('current_streak', 0)} 天")
        return ApiResponse(
            code=200,
            message=result.get("message", "签到成功"),
            data=result.get("data")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"执行签到接口异常: 用户ID={current_user.id}, 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="签到失败，请稍后重试",
            data=None
        )


@router.get("/rewards", response_model=ApiResponse)
def get_checkin_rewards(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    获取所有签到奖励配置
    """
    service = get_checkin_service()
    
    service.initialize_default_rewards(db)
    
    rewards = service.get_active_rewards(db)
    
    return ApiResponse(
        code=200,
        message="success",
        data={"rewards": rewards}
    )


@router.get("/history", response_model=ApiResponse)
def get_checkin_history(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    获取签到历史记录
    """
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 20
    
    service = get_checkin_service()
    
    result = service.get_checkin_history(
        db=db,
        user_id=current_user.id,
        page=page,
        page_size=page_size
    )
    
    return ApiResponse(
        code=200,
        message="success",
        data=result.get("data")
    )


@router.post("/init-rewards", response_model=ApiResponse)
def init_checkin_rewards(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    初始化签到奖励配置（管理员使用）
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以执行此操作"
        )
    
    service = get_checkin_service()
    
    rewards = service.initialize_default_rewards(db)
    
    return ApiResponse(
        code=200,
        message="初始化成功",
        data={"rewards": rewards}
    )
