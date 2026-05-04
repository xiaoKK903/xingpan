import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from app.database import get_db
from app.models import User, ActivityStatus, ActivityType, BenefitType, ZodiacSign
from app.schemas import ApiResponse
from app.routers.users import get_current_active_user, get_current_user_optional
from app.services.activity_service import get_activity_service, ActivityService

logger = logging.getLogger(__name__)
router = APIRouter()


class ActivityBenefitCreate(BaseModel):
    benefit_type: str
    benefit_name: str
    description: Optional[str] = None
    multiplier: float = 1.0
    discount_percent: Optional[int] = None
    rate_up_percent: Optional[int] = None
    free_count: int = 0
    item_id: Optional[int] = None
    item_quantity: int = 1
    target_module: Optional[str] = None
    eligibility_filter: Optional[Dict[str, Any]] = None
    is_active: bool = True
    daily_limit: Optional[int] = None
    total_limit: Optional[int] = None
    sort_order: int = 0


class ActivityCreate(BaseModel):
    activity_key: Optional[str] = None
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    activity_type: str = Field(default=ActivityType.FESTIVAL)
    status: Optional[str] = Field(default=ActivityStatus.DRAFT)
    start_time: str
    end_time: str
    target_zodiac_sign: Optional[str] = None
    brand_name: Optional[str] = None
    brand_logo_url: Optional[str] = None
    rules_text: Optional[str] = None
    display_image_url: Optional[str] = None
    banner_image_url: Optional[str] = None
    is_auto_activated: bool = True
    priority: int = 0
    metadata: Optional[Dict[str, Any]] = None
    benefits: List[ActivityBenefitCreate] = Field(default_factory=list)


class ActivityUpdate(BaseModel):
    name: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    activity_type: Optional[str] = None
    status: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    target_zodiac_sign: Optional[str] = None
    brand_name: Optional[str] = None
    brand_logo_url: Optional[str] = None
    rules_text: Optional[str] = None
    display_image_url: Optional[str] = None
    banner_image_url: Optional[str] = None
    is_auto_activated: Optional[bool] = None
    priority: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


@router.get("/hall", response_model=ApiResponse)
def get_hall_activities(
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    获取副本大厅展示的活动列表
    
    返回进行中、即将开始、已结束的活动
    """
    try:
        service = get_activity_service()
        
        result = service.get_hall_activities(db)
        
        return ApiResponse(
            code=200,
            message="success",
            data=result.get("data")
        )
    except Exception as e:
        logger.error(f"获取副本大厅活动列表异常: 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="获取活动列表失败",
            data=None
        )


@router.get("/benefits/active", response_model=ApiResponse)
def get_active_benefits(
    module_type: Optional[str] = Query(None, description="模块类型: synastry, blind_box, stardust"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    获取当前生效的活动权益
    
    用于前端判断当前有哪些活动权益生效
    """
    try:
        service = get_activity_service()
        
        user_id = current_user.id if current_user else None
        
        benefits = service.get_active_benefits(
            db=db,
            user_id=user_id,
            module_type=module_type
        )
        
        return ApiResponse(
            code=200,
            message="success",
            data={"benefits": benefits}
        )
    except Exception as e:
        logger.error(f"获取活动权益异常: 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="获取活动权益失败",
            data=None
        )


@router.get("/benefits/calculate", response_model=ApiResponse)
def calculate_benefits(
    module_type: str = Query(..., description="模块类型: synastry, blind_box, stardust"),
    user_zodiac_sign: Optional[str] = Query(None, description="用户星座，用于星座月活动判断"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    计算活动权益倍率
    
    返回 multiplier, discount_percent, rate_up_percent, free_count 等信息
    """
    try:
        service = get_activity_service()
        
        user_id = current_user.id if current_user else None
        
        result = service.calculate_benefit_multiplier(
            db=db,
            module_type=module_type,
            user_id=user_id,
            user_zodiac_sign=user_zodiac_sign
        )
        
        return ApiResponse(
            code=200,
            message="success",
            data=result
        )
    except Exception as e:
        logger.error(f"计算活动权益异常: 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="计算活动权益失败",
            data=None
        )


@router.get("/list", response_model=ApiResponse)
def get_activity_list(
    status_filter: Optional[str] = Query(None, description="状态过滤: active, upcoming, ended"),
    activity_type: Optional[str] = Query(None, description="活动类型过滤"),
    include_archived: bool = Query(False, description="是否包含已归档活动"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    获取活动列表（运营后台使用）
    
    需要登录权限
    """
    try:
        service = get_activity_service()
        
        activities = service.get_activity_list(
            db=db,
            status_filter=status_filter,
            activity_type=activity_type,
            include_archived=include_archived
        )
        
        return ApiResponse(
            code=200,
            message="success",
            data={"activities": activities}
        )
    except Exception as e:
        logger.error(f"获取活动列表异常: 用户ID={current_user.id}, 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="获取活动列表失败",
            data=None
        )


@router.get("/{activity_id}", response_model=ApiResponse)
def get_activity_detail(
    activity_id: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    获取活动详情
    """
    try:
        service = get_activity_service()
        
        activity = service.get_activity_by_id(db, activity_id)
        
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="活动不存在"
            )
        
        return ApiResponse(
            code=200,
            message="success",
            data=activity
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取活动详情异常: 活动ID={activity_id}, 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="获取活动详情失败",
            data=None
        )


@router.post("/create", response_model=ApiResponse)
def create_activity(
    activity_data: ActivityCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    创建活动（运营后台使用）
    
    需要管理员权限
    """
    try:
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有管理员可以创建活动"
            )
        
        service = get_activity_service()
        
        result = service.create_activity(
            db=db,
            activity_data=activity_data.model_dump(),
            created_by=current_user.id
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "创建活动失败")
            )
        
        logger.info(f"用户 {current_user.id} 创建活动成功: {result.get('data', {}).get('activity_key')}")
        
        return ApiResponse(
            code=200,
            message="活动创建成功",
            data=result.get("data")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建活动异常: 用户ID={current_user.id}, 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="创建活动失败",
            data=None
        )


@router.put("/{activity_id}", response_model=ApiResponse)
def update_activity(
    activity_id: int,
    update_data: ActivityUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    更新活动（运营后台使用）
    
    需要管理员权限
    """
    try:
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有管理员可以更新活动"
            )
        
        service = get_activity_service()
        
        update_dict = update_data.model_dump(exclude_unset=True)
        
        result = service.update_activity(
            db=db,
            activity_id=activity_id,
            update_data=update_dict
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "更新活动失败")
            )
        
        logger.info(f"用户 {current_user.id} 更新活动成功: 活动ID={activity_id}")
        
        return ApiResponse(
            code=200,
            message="活动更新成功",
            data=result.get("data")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新活动异常: 用户ID={current_user.id}, 活动ID={activity_id}, 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="更新活动失败",
            data=None
        )


@router.patch("/{activity_id}/status", response_model=ApiResponse)
def update_activity_status(
    activity_id: int,
    new_status: str = Query(..., description="新状态: draft, scheduled, active, ended, archived"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    更新活动状态（运营后台使用）
    
    需要管理员权限
    """
    try:
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有管理员可以更新活动状态"
            )
        
        service = get_activity_service()
        
        result = service.update_activity_status(
            db=db,
            activity_id=activity_id,
            new_status=new_status
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "更新活动状态失败")
            )
        
        logger.info(f"用户 {current_user.id} 更新活动状态成功: 活动ID={activity_id} -> {new_status}")
        
        return ApiResponse(
            code=200,
            message="活动状态更新成功",
            data=result.get("data")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新活动状态异常: 用户ID={current_user.id}, 活动ID={activity_id}, 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="更新活动状态失败",
            data=None
        )


@router.delete("/{activity_id}", response_model=ApiResponse)
def delete_activity(
    activity_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    删除活动（软删除，设为已归档）（运营后台使用）
    
    需要管理员权限
    """
    try:
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有管理员可以删除活动"
            )
        
        service = get_activity_service()
        
        result = service.delete_activity(db=db, activity_id=activity_id)
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "删除活动失败")
            )
        
        logger.info(f"用户 {current_user.id} 归档活动成功: 活动ID={activity_id}")
        
        return ApiResponse(
            code=200,
            message=result.get("message", "活动已归档"),
            data=None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除活动异常: 用户ID={current_user.id}, 活动ID={activity_id}, 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="删除活动失败",
            data=None
        )


@router.post("/sync-statuses", response_model=ApiResponse)
def sync_activity_statuses(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    同步活动状态（手动触发自动启停）（运营后台使用）
    
    需要管理员权限
    """
    try:
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有管理员可以同步活动状态"
            )
        
        service = get_activity_service()
        
        result = service.check_and_update_activity_statuses(db=db)
        
        logger.info(f"用户 {current_user.id} 同步活动状态成功: 激活={result.get('data', {}).get('activated_count')}, 结束={result.get('data', {}).get('ended_count')}")
        
        return ApiResponse(
            code=200,
            message="活动状态同步成功",
            data=result.get("data")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"同步活动状态异常: 用户ID={current_user.id}, 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="同步活动状态失败",
            data=None
        )


@router.get("/participations/my", response_model=ApiResponse)
def get_my_participations(
    activity_id: Optional[int] = Query(None, description="活动ID，不传则返回所有参与记录"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    获取当前用户的活动参与记录
    """
    try:
        service = get_activity_service()
        
        participations = service.get_user_activity_participation(
            db=db,
            user_id=current_user.id,
            activity_id=activity_id
        )
        
        return ApiResponse(
            code=200,
            message="success",
            data={"participations": participations}
        )
    except Exception as e:
        logger.error(f"获取用户参与记录异常: 用户ID={current_user.id}, 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="获取参与记录失败",
            data=None
        )
