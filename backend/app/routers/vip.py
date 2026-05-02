import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from app.database import get_db
from app.models import User
from app.routers.users import get_current_user, get_current_active_user
from app.schemas import (
    ApiResponse, VIPPlanResponse, VIPPrivilegeResponse, 
    UserVIPResponse, VIPSubscriptionResponse,
    UserVIPWithPrivilegesResponse
)
from app.services.vip_service import (
    init_vip_plans, init_vip_privileges,
    get_or_create_user_vip, check_vip_status,
    get_vip_days_remaining, get_active_vip_plans,
    get_active_vip_privileges, get_vip_plan_by_type,
    get_free_reports_remaining, get_user_subscriptions,
    cancel_auto_renew, check_privilege
)
from app.services.payment_service import create_vip_subscription_order
from app.services.vip_service import VIPPlanType

logger = logging.getLogger(__name__)
router = APIRouter(tags=["VIP会员"])


def init_vip_data(db: Session):
    init_vip_plans(db)
    init_vip_privileges(db)


@router.get("/plans", response_model=ApiResponse)
def get_vip_plans(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    init_vip_data(db)
    
    plans = get_active_vip_plans(db)
    
    plans_response = [
        VIPPlanResponse.model_validate(plan).model_dump()
        for plan in plans
    ]
    
    user_vip_data = None
    if current_user:
        is_vip, user_vip = check_vip_status(db, current_user.id)
        if user_vip:
            user_vip_data = {
                "is_vip": is_vip,
                "days_remaining": get_vip_days_remaining(user_vip) if is_vip else 0,
                "plan_type": user_vip.plan_type,
                "free_reports_remaining": get_free_reports_remaining(db, current_user.id)
            }
    
    return ApiResponse(
        message="success",
        data={
            "plans": plans_response,
            "user_vip": user_vip_data
        }
    )


@router.get("/privileges", response_model=ApiResponse)
def get_vip_privileges(
    db: Session = Depends(get_db)
):
    init_vip_data(db)
    
    privileges = get_active_vip_privileges(db)
    
    privileges_response = [
        VIPPrivilegeResponse.model_validate(p).model_dump()
        for p in privileges
    ]
    
    return ApiResponse(
        message="success",
        data={"privileges": privileges_response}
    )


@router.get("/status", response_model=ApiResponse)
def get_my_vip_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        init_vip_data(db)
        
        is_vip, user_vip = check_vip_status(db, current_user.id)
        
        privileges = []
        if is_vip:
            all_privileges = get_active_vip_privileges(db)
            for p in all_privileges:
                has_privilege, value_data = check_privilege(db, current_user.id, p.privilege_key)
                if has_privilege:
                    p_dict = VIPPrivilegeResponse.model_validate(p).model_dump()
                    p_dict["value_data"] = value_data
                    privileges.append(p_dict)
        
        current_plan = None
        if is_vip and user_vip.plan_type:
            plan = get_vip_plan_by_type(db, user_vip.plan_type)
            if plan:
                current_plan = VIPPlanResponse.model_validate(plan).model_dump()
        
        response_data = {
            "vip_status": UserVIPResponse.model_validate(user_vip).model_dump(),
            "privileges": privileges,
            "current_plan": current_plan,
            "days_remaining": get_vip_days_remaining(user_vip) if is_vip else 0,
            "free_reports_remaining": get_free_reports_remaining(db, current_user.id)
        }
        
        logger.info(f"用户 {current_user.id} 获取VIP状态: is_vip={is_vip}")
        return ApiResponse(
            message="success",
            data=response_data
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取VIP状态接口异常: 用户ID={current_user.id}, 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="获取VIP状态失败，请稍后重试",
            data=None
        )


@router.post("/subscribe", response_model=ApiResponse)
def subscribe_vip(
    plan_type: str = Query(..., description="套餐类型: monthly 或 yearly"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    init_vip_data(db)
    
    if plan_type not in [VIPPlanType.MONTHLY.value, VIPPlanType.YEARLY.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的套餐类型，可选: monthly, yearly"
        )
    
    plan = get_vip_plan_by_type(db, plan_type)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="套餐不存在或已下架"
        )
    
    order, error = create_vip_subscription_order(
        db=db,
        user_id=current_user.id,
        plan_type=plan_type
    )
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error or "创建订单失败"
        )
    
    return ApiResponse(
        message="订单创建成功",
        data={
            "order_no": order.order_no,
            "amount": order.final_amount,
            "plan_type": plan_type,
            "plan_name": plan.name,
            "duration_days": plan.duration_days,
            "is_sandbox": order.is_sandbox,
            "payment_url": f"/api/payment/sandbox/pay?order_no={order.order_no}"
        }
    )


@router.post("/auto-renew/cancel", response_model=ApiResponse)
def cancel_my_auto_renew(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    success, message = cancel_auto_renew(db, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return ApiResponse(
        message=message,
        data=None
    )


@router.get("/subscriptions", response_model=ApiResponse)
def get_my_subscriptions(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    subscriptions = get_user_subscriptions(db, current_user.id, limit)
    
    subscriptions_response = [
        VIPSubscriptionResponse.model_validate(s).model_dump()
        for s in subscriptions
    ]
    
    return ApiResponse(
        message="success",
        data={
            "subscriptions": subscriptions_response,
            "total": len(subscriptions_response)
        }
    )


@router.get("/check-privilege/{privilege_key}", response_model=ApiResponse)
def check_my_privilege(
    privilege_key: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    has_privilege, value_data = check_privilege(db, current_user.id, privilege_key)
    
    return ApiResponse(
        message="success",
        data={
            "has_privilege": has_privilege,
            "privilege_key": privilege_key,
            "value_data": value_data
        }
    )


@router.post("/init-data", response_model=ApiResponse)
def initialize_vip_data(
    db: Session = Depends(get_db)
):
    init_vip_data(db)
    
    plans_count = db.query(__import__('app.models', fromlist=['VIPPlan']).VIPPlan).count()
    privileges_count = db.query(__import__('app.models', fromlist=['VIPPrivilege']).VIPPrivilege).count()
    
    return ApiResponse(
        message="VIP数据初始化完成",
        data={
            "plans_count": plans_count,
            "privileges_count": privileges_count
        }
    )
