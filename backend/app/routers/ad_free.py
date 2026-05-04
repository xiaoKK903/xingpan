import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.database import get_db
from app.models import User
from app.routers.users import get_current_user, get_current_active_user
from app.schemas import ApiResponse
from app.services.ad_free_service import (
    get_ad_free_service,
    AdFreeService,
)
from app.models import AdFreePlanType

logger = logging.getLogger(__name__)
router = APIRouter(tags=["去广告权益"])


def init_ad_free_data(db: Session):
    """初始化去广告数据"""
    service = get_ad_free_service()
    service.initialize_default_plans(db)


@router.get("/plans", response_model=ApiResponse)
def get_ad_free_plans(
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取所有激活的去广告套餐
    """
    try:
        init_ad_free_data(db)
        
        service = get_ad_free_service()
        plans = service.get_active_plans(db)
        
        user_status = None
        if current_user:
            status_result = service.check_ad_free_status(db, current_user.id)
            if status_result.get("success"):
                user_status = status_result.get("data")
        
        return ApiResponse(
            message="success",
            data={
                "plans": plans,
                "user_status": user_status,
                "total_count": len(plans)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取去广告套餐异常: 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="获取套餐列表失败，请稍后重试",
            data=None
        )


@router.get("/my-status", response_model=ApiResponse)
def get_my_ad_free_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    获取当前用户的去广告状态
    """
    try:
        init_ad_free_data(db)
        
        service = get_ad_free_service()
        result = service.check_ad_free_status(db, current_user.id)
        
        if not result.get("success"):
            return ApiResponse(
                code=400,
                message=result.get("error", "获取去广告状态失败"),
                data=None
            )
        
        return ApiResponse(
            message="success",
            data=result.get("data")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取去广告状态异常: 用户ID={current_user.id}, 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="获取去广告状态失败，请稍后重试",
            data=None
        )


@router.get("/my-subscriptions", response_model=ApiResponse)
def get_my_ad_free_subscriptions(
    include_expired: bool = Query(False, description="是否包含已过期的订阅"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    获取当前用户的去广告订阅列表
    """
    try:
        service = get_ad_free_service()
        subscriptions = service.get_user_subscriptions(db, current_user.id, include_expired)
        
        return ApiResponse(
            message="success",
            data={
                "subscriptions": subscriptions,
                "total_count": len(subscriptions)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户订阅列表异常: 用户ID={current_user.id}, 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="获取订阅列表失败，请稍后重试",
            data=None
        )


@router.post("/subscribe", response_model=ApiResponse)
def subscribe_ad_free(
    plan_key: str = Query(..., description="套餐key: ad_free_monthly, ad_free_quarterly, ad_free_yearly"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    创建设去广告订阅订单
    """
    try:
        init_ad_free_data(db)
        
        service = get_ad_free_service()
        order, error = service.create_subscription_order(db, current_user.id, plan_key)
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error or "创建订单失败"
            )
        
        logger.info(f"用户 {current_user.id} 创建设去广告订单: plan_key={plan_key}, order_no={order.order_no}")
        
        return ApiResponse(
            message="订单创建成功",
            data={
                "order_no": order.order_no,
                "amount": order.final_amount,
                "plan_key": plan_key,
                "is_sandbox": order.is_sandbox,
                "payment_url": f"/api/payment/sandbox/pay?order_no={order.order_no}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建设去广告订单异常: 用户ID={current_user.id}, plan_key={plan_key}, 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="创建订单失败，请稍后重试",
            data=None
        )


@router.post("/activate/{payment_order_id}", response_model=ApiResponse)
def activate_ad_free_subscription(
    payment_order_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    支付成功后激活动去广告订阅
    
    注意：这个接口通常由支付回调自动调用，用户一般不需要手动调用
    """
    try:
        service = get_ad_free_service()
        subscription, error = service.activate_subscription(db, current_user.id, payment_order_id)
        
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error or "激活订阅失败"
            )
        
        logger.info(f"用户 {current_user.id} 激活动去广告订阅成功: subscription_no={subscription.subscription_no}")
        
        return ApiResponse(
            message="订阅激活成功",
            data={
                "subscription_no": subscription.subscription_no,
                "started_at": subscription.started_at.isoformat() if subscription.started_at else None,
                "expires_at": subscription.expires_at.isoformat() if subscription.expires_at else None
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"激活动去广告订阅异常: 用户ID={current_user.id}, payment_order_id={payment_order_id}, 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="激活订阅失败，请稍后重试",
            data=None
        )


@router.post("/cancel-auto-renew/{subscription_id}", response_model=ApiResponse)
def cancel_ad_free_auto_renew(
    subscription_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    取消自动续费
    """
    try:
        service = get_ad_free_service()
        success, message = service.cancel_subscription(db, current_user.id, subscription_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        logger.info(f"用户 {current_user.id} 取消自动续费: subscription_id={subscription_id}")
        
        return ApiResponse(
            message=message,
            data=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消自动续费异常: 用户ID={current_user.id}, subscription_id={subscription_id}, 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="操作失败，请稍后重试",
            data=None
        )


@router.get("/plan-types", response_model=ApiResponse)
def get_plan_types(
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取套餐类型列表
    """
    plan_types = [
        {
            "type": AdFreePlanType.MONTHLY.value,
            "name": "月度",
            "duration_days": 30,
            "description": "30天去广告权益"
        },
        {
            "type": AdFreePlanType.QUARTERLY.value,
            "name": "季度",
            "duration_days": 90,
            "description": "90天去广告权益"
        },
        {
            "type": AdFreePlanType.YEARLY.value,
            "name": "年度",
            "duration_days": 365,
            "description": "365天去广告权益"
        }
    ]
    
    return ApiResponse(
        message="success",
        data={
            "plan_types": plan_types
        }
    )


@router.post("/init-data", response_model=ApiResponse)
def initialize_ad_free_data(
    db: Session = Depends(get_db)
):
    """
    初始化去广告数据（管理接口）
    """
    try:
        init_ad_free_data(db)
        
        from app.models import AdFreePlan
        plans_count = db.query(AdFreePlan).count()
        
        return ApiResponse(
            message="去广告数据初始化完成",
            data={
                "plans_count": plans_count
            }
        )
        
    except Exception as e:
        logger.error(f"初始化去广告数据异常: 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message=f"初始化失败: {str(e)}",
            data=None
        )
