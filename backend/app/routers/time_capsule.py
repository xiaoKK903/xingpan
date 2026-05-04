import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from app.database import get_db
from app.models import User, TimeCapsule, TimeCapsuleNotification, TimeCapsuleSkin
from app.routers.users import get_current_user, get_current_active_user
from app.schemas import ApiResponse
from app.services.time_capsule_service import (
    init_default_skins, get_available_skins, get_skin_by_key,
    create_capsule, get_user_capsules, get_received_capsules,
    get_capsule_by_id, update_capsule, delete_capsule, open_capsule,
    process_expired_capsules, get_user_notifications, mark_notification_read,
    check_capsule_quota, get_or_create_user_quota,
    capsule_to_dict, skin_to_dict, notification_to_dict,
    TimeCapsuleStatus, TimeCapsuleRecipientType, TimeCapsuleUnlockDuration
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["时间胶囊"], prefix="/time-capsules")


def get_current_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


class CreateCapsuleRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="胶囊标题")
    content: str = Field(..., min_length=1, description="胶囊内容")
    recipient_type: str = Field(default=TimeCapsuleRecipientType.SELF.value, description="接收对象类型: self/friend")
    recipient_user_id: Optional[int] = Field(default=None, description="接收者用户ID（写给好友时必填）")
    unlock_duration: str = Field(default=TimeCapsuleUnlockDuration.ONE_YEAR.value, description="解锁时长: 3months/1year/3years")
    skin_key: str = Field(default="classic_star", description="皮肤key")
    extra_metadata: Optional[Dict[str, Any]] = Field(default=None, description="额外元数据")


class UpdateCapsuleRequest(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200, description="胶囊标题")
    content: Optional[str] = Field(default=None, min_length=1, description="胶囊内容")
    skin_key: Optional[str] = Field(default=None, description="皮肤key")
    extra_metadata: Optional[Dict[str, Any]] = Field(default=None, description="额外元数据")


@router.post("/init-data", response_model=ApiResponse)
def initialize_capsule_data(
    db: Session = Depends(get_db)
):
    init_default_skins(db)
    
    skins_count = db.query(TimeCapsuleSkin).count()
    
    return ApiResponse(
        message="时间胶囊数据初始化完成",
        data={
            "skins_count": skins_count
        }
    )


@router.get("/skins", response_model=ApiResponse)
def get_skins(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    user_id = current_user.id if current_user else None
    skins = get_available_skins(db, user_id)
    
    skins_response = [skin_to_dict(skin) for skin in skins]
    
    return ApiResponse(
        message="success",
        data={
            "skins": skins_response,
            "total": len(skins_response)
        }
    )


@router.get("/quota", response_model=ApiResponse)
def get_my_quota(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    has_quota, quota_msg, quota_info = check_capsule_quota(db, current_user.id)
    
    return ApiResponse(
        message=quota_msg,
        data=quota_info
    )


@router.get("/notifications", response_model=ApiResponse)
def get_my_notifications(
    is_read: Optional[bool] = Query(None, description="是否已读"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    notifications, total = get_user_notifications(
        db=db,
        user_id=current_user.id,
        is_read=is_read,
        skip=skip,
        limit=limit
    )
    
    notifications_response = [notification_to_dict(n) for n in notifications]
    
    return ApiResponse(
        message="success",
        data={
            "notifications": notifications_response,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    )


@router.post("/notifications/{notification_id}/read", response_model=ApiResponse)
def mark_notification_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    success, message = mark_notification_read(db, notification_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message
        )
    
    return ApiResponse(
        message=message,
        data=None
    )


@router.post("/process-expired", response_model=ApiResponse)
def process_expired_capsules_task(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    processed_count = process_expired_capsules(db)
    
    logger.info(f"管理员触发过期胶囊处理: 处理了 {processed_count} 个胶囊")
    
    return ApiResponse(
        message="处理完成",
        data={
            "processed_count": processed_count
        }
    )


@router.get("/stats", response_model=ApiResponse)
def get_my_capsule_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    pending_count = db.query(TimeCapsule).filter(
        TimeCapsule.user_id == current_user.id,
        TimeCapsule.status == TimeCapsuleStatus.PENDING.value,
        TimeCapsule.is_deleted == False
    ).count()
    
    unlocked_count = db.query(TimeCapsule).filter(
        TimeCapsule.user_id == current_user.id,
        TimeCapsule.status == TimeCapsuleStatus.UNLOCKED.value,
        TimeCapsule.is_deleted == False
    ).count()
    
    opened_count = db.query(TimeCapsule).filter(
        TimeCapsule.user_id == current_user.id,
        TimeCapsule.status == TimeCapsuleStatus.OPENED.value,
        TimeCapsule.is_deleted == False
    ).count()
    
    received_pending = db.query(TimeCapsule).filter(
        TimeCapsule.recipient_user_id == current_user.id,
        TimeCapsule.recipient_type == TimeCapsuleRecipientType.FRIEND.value,
        TimeCapsule.status == TimeCapsuleStatus.PENDING.value,
        TimeCapsule.is_deleted == False
    ).count()
    
    received_unlocked = db.query(TimeCapsule).filter(
        TimeCapsule.recipient_user_id == current_user.id,
        TimeCapsule.recipient_type == TimeCapsuleRecipientType.FRIEND.value,
        TimeCapsule.status == TimeCapsuleStatus.UNLOCKED.value,
        TimeCapsule.is_deleted == False
    ).count()
    
    unread_notifications = db.query(TimeCapsuleNotification).filter(
        TimeCapsuleNotification.user_id == current_user.id,
        TimeCapsuleNotification.is_read == False
    ).count()
    
    has_quota, quota_msg, quota_info = check_capsule_quota(db, current_user.id)
    
    return ApiResponse(
        message="success",
        data={
            "created": {
                "pending": pending_count,
                "unlocked": unlocked_count,
                "opened": opened_count,
                "total": pending_count + unlocked_count + opened_count
            },
            "received": {
                "pending": received_pending,
                "unlocked": received_unlocked,
                "total": received_pending + received_unlocked
            },
            "unread_notifications": unread_notifications,
            "quota": quota_info
        }
    )


@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_new_capsule(
    request: CreateCapsuleRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if request.unlock_duration not in [
        TimeCapsuleUnlockDuration.THREE_MONTHS.value,
        TimeCapsuleUnlockDuration.ONE_YEAR.value,
        TimeCapsuleUnlockDuration.THREE_YEARS.value
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的解锁时长，可选: 3months, 1year, 3years"
        )
    
    if request.recipient_type not in [
        TimeCapsuleRecipientType.SELF.value,
        TimeCapsuleRecipientType.FRIEND.value
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的接收对象类型，可选: self, friend"
        )
    
    if request.recipient_type == TimeCapsuleRecipientType.FRIEND.value and not request.recipient_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="写给好友时需要指定 recipient_user_id"
        )
    
    if request.recipient_type == TimeCapsuleRecipientType.FRIEND.value and request.recipient_user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能写给自己，请选择其他用户"
        )
    
    capsule, message, quota_info = create_capsule(
        db=db,
        user_id=current_user.id,
        title=request.title,
        content=request.content,
        recipient_type=request.recipient_type,
        recipient_user_id=request.recipient_user_id,
        unlock_duration=request.unlock_duration,
        skin_key=request.skin_key,
        extra_metadata=request.extra_metadata
    )
    
    if not capsule:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    logger.info(f"用户 {current_user.id} 创建时间胶囊: capsule_id={capsule.id}")
    
    return ApiResponse(
        message=message,
        data={
            "capsule": capsule_to_dict(capsule),
            "quota": quota_info
        }
    )


@router.get("", response_model=ApiResponse)
def get_my_capsules(
    status_filter: Optional[str] = Query(None, alias="status", description="状态过滤: pending/unlocked/opened/expired"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if status_filter and status_filter not in [
        TimeCapsuleStatus.PENDING.value,
        TimeCapsuleStatus.UNLOCKED.value,
        TimeCapsuleStatus.OPENED.value,
        TimeCapsuleStatus.EXPIRED.value
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的状态值"
        )
    
    capsules, total = get_user_capsules(
        db=db,
        user_id=current_user.id,
        status=status_filter,
        skip=skip,
        limit=limit
    )
    
    capsules_response = [capsule_to_dict(capsule) for capsule in capsules]
    
    return ApiResponse(
        message="success",
        data={
            "capsules": capsules_response,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    )


@router.get("/received", response_model=ApiResponse)
def get_received_capsules_list(
    status_filter: Optional[str] = Query(None, alias="status", description="状态过滤: pending/unlocked/opened/expired"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if status_filter and status_filter not in [
        TimeCapsuleStatus.PENDING.value,
        TimeCapsuleStatus.UNLOCKED.value,
        TimeCapsuleStatus.OPENED.value,
        TimeCapsuleStatus.EXPIRED.value
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的状态值"
        )
    
    capsules, total = get_received_capsules(
        db=db,
        user_id=current_user.id,
        status=status_filter,
        skip=skip,
        limit=limit
    )
    
    capsules_response = [capsule_to_dict(capsule) for capsule in capsules]
    
    return ApiResponse(
        message="success",
        data={
            "capsules": capsules_response,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    )


@router.get("/{capsule_id}", response_model=ApiResponse)
def get_capsule_detail(
    capsule_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    capsule, message, can_view = get_capsule_by_id(db, capsule_id, current_user.id)
    
    if not capsule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message
        )
    
    if not can_view:
        return ApiResponse(
            code=403,
            message=message,
            data={
                "capsule": capsule_to_dict(capsule, include_content=False),
                "can_view": False
            }
        )
    
    return ApiResponse(
        message="success",
        data={
            "capsule": capsule_to_dict(capsule, include_content=True),
            "can_view": True
        }
    )


@router.put("/{capsule_id}", response_model=ApiResponse)
def update_existing_capsule(
    capsule_id: int,
    request: UpdateCapsuleRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    capsule, message = update_capsule(
        db=db,
        capsule_id=capsule_id,
        user_id=current_user.id,
        title=request.title,
        content=request.content,
        skin_key=request.skin_key,
        extra_metadata=request.extra_metadata
    )
    
    if not capsule:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    logger.info(f"用户 {current_user.id} 更新时间胶囊: capsule_id={capsule_id}")
    
    return ApiResponse(
        message=message,
        data={
            "capsule": capsule_to_dict(capsule)
        }
    )


@router.delete("/{capsule_id}", response_model=ApiResponse)
def delete_existing_capsule(
    capsule_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    success, message = delete_capsule(db, capsule_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    logger.info(f"用户 {current_user.id} 删除时间胶囊: capsule_id={capsule_id}")
    
    return ApiResponse(
        message=message,
        data=None
    )


@router.post("/{capsule_id}/open", response_model=ApiResponse)
def open_existing_capsule(
    capsule_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    capsule, message = open_capsule(db, capsule_id, current_user.id)
    
    if not capsule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message
        )
    
    logger.info(f"用户 {current_user.id} 打开时间胶囊: capsule_id={capsule_id}")
    
    return ApiResponse(
        message=message,
        data={
            "capsule": capsule_to_dict(capsule, include_content=True)
        }
    )
