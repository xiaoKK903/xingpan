import logging
import json
from enum import Enum
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models import (
    User,
    TimeCapsule,
    TimeCapsuleSkin,
    TimeCapsuleNotification,
    UserCapsuleQuota
)
from app.services.vip_service import check_and_update_vip_status, get_vip_plan_by_type

logger = logging.getLogger(__name__)


class TimeCapsuleStatus(str, Enum):
    PENDING = "pending"
    UNLOCKED = "unlocked"
    OPENED = "opened"
    EXPIRED = "expired"


class TimeCapsuleRecipientType(str, Enum):
    SELF = "self"
    FRIEND = "friend"


class TimeCapsuleUnlockDuration(str, Enum):
    THREE_MONTHS = "3months"
    ONE_YEAR = "1year"
    THREE_YEARS = "3years"


class TimeCapsuleNotificationType(str, Enum):
    CAPSULE_RECEIVED = "capsule_received"
    CAPSULE_UNLOCKED = "capsule_unlocked"
    CAPSULE_EXPIRED = "capsule_expired"


DEFAULT_CAPSULE_LIMIT = 3
VIP_EXTRA_CAPSULE_LIMIT = 7
PREMIUM_CAPSULE_LIMIT = 0


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


def calculate_unlock_at(duration: str, now: datetime) -> datetime:
    duration_map = {
        TimeCapsuleUnlockDuration.THREE_MONTHS.value: timedelta(days=90),
        TimeCapsuleUnlockDuration.ONE_YEAR.value: timedelta(days=365),
        TimeCapsuleUnlockDuration.THREE_YEARS.value: timedelta(days=1095),
    }
    return now + duration_map.get(duration, timedelta(days=365))


def skin_to_dict(skin: TimeCapsuleSkin) -> Dict[str, Any]:
    if not skin:
        return {}
    return {
        "id": skin.id,
        "skin_key": skin.skin_key,
        "name": skin.name,
        "description": skin.description,
        "image_url": skin.preview_image_url,
        "is_vip_only": skin.is_vip_only,
        "is_premium": skin.is_premium,
        "price": skin.price,
        "is_locked": skin.is_locked,
        "sort_order": skin.sort_order
    }


def capsule_to_dict(capsule: TimeCapsule, include_content: bool = False) -> Dict[str, Any]:
    if not capsule:
        return {}
    
    data = {
        "id": capsule.id,
        "user_id": capsule.user_id,
        "title": capsule.title,
        "recipient_type": capsule.recipient_type,
        "recipient_user_id": capsule.recipient_user_id,
        "unlock_duration": capsule.unlock_duration,
        "unlock_at": capsule.unlock_at.isoformat() if capsule.unlock_at else None,
        "skin_key": capsule.skin_key,
        "status": capsule.status,
        "is_unlocked": capsule.is_unlocked,
        "is_opened": capsule.is_opened,
        "created_at": capsule.created_at.isoformat() if capsule.created_at else None,
        "opened_at": capsule.opened_at.isoformat() if capsule.opened_at else None
    }
    
    if include_content:
        data["content"] = capsule.content
    
    return data


def notification_to_dict(notification: TimeCapsuleNotification) -> Dict[str, Any]:
    if not notification:
        return {}
    return {
        "id": notification.id,
        "capsule_id": notification.capsule_id,
        "user_id": notification.user_id,
        "notification_type": notification.notification_type,
        "title": notification.title,
        "content": notification.content,
        "is_read": notification.is_read,
        "read_at": notification.read_at.isoformat() if notification.read_at else None,
        "created_at": notification.created_at.isoformat() if notification.created_at else None
    }


def init_default_skins(db: Session):
    existing_skins = db.query(TimeCapsuleSkin).count()
    if existing_skins > 0:
        return
    
    default_skins = [
        TimeCapsuleSkin(
            skin_key="classic_star",
            name="经典星盘",
            description="深蓝色星盘背景，星光闪烁",
            image_url=None,
            is_vip_only=False,
            is_premium=False,
            price=0,
            is_locked=False,
            sort_order=1
        ),
        TimeCapsuleSkin(
            skin_key="nebula_pink",
            name="星云粉",
            description="粉色星云背景，浪漫温馨",
            image_url=None,
            is_vip_only=False,
            is_premium=False,
            price=0,
            is_locked=False,
            sort_order=2
        ),
        TimeCapsuleSkin(
            skin_key="ocean_blue",
            name="深海蓝",
            description="深邃海洋背景，神秘莫测",
            image_url=None,
            is_vip_only=False,
            is_premium=False,
            price=0,
            is_locked=False,
            sort_order=3
        ),
        TimeCapsuleSkin(
            skin_key="sunset_gold",
            name="落日金",
            description="金黄色日落背景，温暖治愈",
            image_url=None,
            is_vip_only=False,
            is_premium=False,
            price=0,
            is_locked=False,
            sort_order=4
        ),
        TimeCapsuleSkin(
            skin_key="aurora_green",
            name="极光绿",
            description="北极光背景，梦幻神秘",
            image_url=None,
            is_vip_only=True,
            is_premium=False,
            price=0,
            is_locked=False,
            sort_order=5
        ),
        TimeCapsuleSkin(
            skin_key="cosmic_purple",
            name="宇宙紫",
            description="深紫色宇宙背景，广阔无垠",
            image_url=None,
            is_vip_only=True,
            is_premium=False,
            price=0,
            is_locked=False,
            sort_order=6
        ),
        TimeCapsuleSkin(
            skin_key="diamond_crystal",
            name="钻石水晶",
            description="璀璨钻石背景，高贵典雅",
            image_url=None,
            is_vip_only=False,
            is_premium=True,
            price=99,
            is_locked=True,
            sort_order=7
        ),
        TimeCapsuleSkin(
            skin_key="rainbow_bridge",
            name="彩虹之桥",
            description="七彩虹桥背景，梦幻绚烂",
            image_url=None,
            is_vip_only=False,
            is_premium=True,
            price=99,
            is_locked=True,
            sort_order=8
        )
    ]
    
    for skin in default_skins:
        db.add(skin)
    
    db.commit()
    logger.info("时间胶囊默认皮肤初始化完成")


def get_available_skins(db: Session, user_id: int = None) -> List[TimeCapsuleSkin]:
    query = db.query(TimeCapsuleSkin).order_by(TimeCapsuleSkin.sort_order)
    skins = query.all()
    
    if user_id:
        is_vip, _ = check_and_update_vip_status(db, user_id)
        for skin in skins:
            if skin.is_vip_only and not is_vip:
                skin.is_locked = True
            elif skin.is_premium and skin.price > 0:
                pass
    
    return skins


def get_skin_by_key(db: Session, skin_key: str) -> Optional[TimeCapsuleSkin]:
    return db.query(TimeCapsuleSkin).filter(TimeCapsuleSkin.skin_key == skin_key).first()


def get_or_create_user_quota(db: Session, user_id: int) -> UserCapsuleQuota:
    quota = db.query(UserCapsuleQuota).filter(UserCapsuleQuota.user_id == user_id).first()
    
    if not quota:
        quota = UserCapsuleQuota(
            user_id=user_id,
            total_limit=DEFAULT_CAPSULE_LIMIT,
            total_used=0,
            vip_extra_limit=0,
            vip_extra_used=0,
            premium_limit=PREMIUM_CAPSULE_LIMIT,
            premium_used=0,
            is_vip=False
        )
        db.add(quota)
        db.flush()
    
    return quota


def get_or_create_user_quota_with_lock(db: Session, user_id: int) -> UserCapsuleQuota:
    quota = db.query(UserCapsuleQuota).filter(
        UserCapsuleQuota.user_id == user_id
    ).with_for_update().first()
    
    if not quota:
        quota = UserCapsuleQuota(
            user_id=user_id,
            total_limit=DEFAULT_CAPSULE_LIMIT,
            total_used=0,
            vip_extra_limit=0,
            vip_extra_used=0,
            premium_limit=PREMIUM_CAPSULE_LIMIT,
            premium_used=0,
            is_vip=False
        )
        db.add(quota)
        db.flush()
    
    return quota


def update_quota_vip_status(db: Session, user_id: int, quota: UserCapsuleQuota) -> UserCapsuleQuota:
    is_vip, vip_plan_type = check_and_update_vip_status(db, user_id)
    
    if is_vip and not quota.is_vip:
        quota.is_vip = True
        quota.vip_plan_type = vip_plan_type
        quota.vip_extra_limit = VIP_EXTRA_CAPSULE_LIMIT
        logger.info(f"更新用户胶囊配额为VIP: user_id={user_id}, extra_limit={VIP_EXTRA_CAPSULE_LIMIT}")
    elif not is_vip and quota.is_vip:
        quota.is_vip = False
        quota.vip_extra_limit = 0
        quota.vip_plan_type = None
        logger.info(f"更新用户胶囊配额为普通用户: user_id={user_id}")
    
    return quota


def check_capsule_quota(db: Session, user_id: int) -> Tuple[bool, str, Dict[str, Any]]:
    quota = get_or_create_user_quota(db, user_id)
    quota = update_quota_vip_status(db, user_id, quota)
    
    total_available = quota.total_limit + quota.vip_extra_limit + quota.premium_limit
    total_used = quota.total_used + quota.vip_extra_used + quota.premium_used
    
    remaining = total_available - total_used
    
    quota_info = {
        "total_limit": quota.total_limit,
        "total_used": quota.total_used,
        "vip_extra_limit": quota.vip_extra_limit,
        "vip_extra_used": quota.vip_extra_used,
        "premium_limit": quota.premium_limit,
        "premium_used": quota.premium_used,
        "total_available": total_available,
        "total_used_all": total_used,
        "remaining": remaining,
        "is_vip": quota.is_vip
    }
    
    if remaining <= 0:
        return False, "胶囊数量已达上限", quota_info
    
    return True, "配额充足", quota_info


def can_use_skin(db: Session, user_id: int, skin_key: str) -> Tuple[bool, str, Optional[TimeCapsuleSkin]]:
    skin = get_skin_by_key(db, skin_key)
    
    if not skin:
        return False, "皮肤不存在", None
    
    if skin.is_vip_only:
        is_vip, _ = check_and_update_vip_status(db, user_id)
        if not is_vip:
            return False, "该皮肤为VIP专属，请先开通会员", skin
    
    if skin.is_premium and skin.price > 0:
        pass
    
    return True, "可以使用", skin


def create_capsule_transaction(
    db: Session,
    user_id: int,
    title: str,
    content: str,
    recipient_type: str = TimeCapsuleRecipientType.SELF.value,
    recipient_user_id: int = None,
    unlock_duration: str = TimeCapsuleUnlockDuration.ONE_YEAR.value,
    skin_key: str = "classic_star",
    extra_metadata: Dict = None
) -> Tuple[Optional[TimeCapsule], str, Dict[str, Any]]:
    quota = get_or_create_user_quota_with_lock(db, user_id)
    quota = update_quota_vip_status(db, user_id, quota)
    
    total_available = quota.total_limit + quota.vip_extra_limit + quota.premium_limit
    total_used = quota.total_used + quota.vip_extra_used + quota.premium_used
    remaining = total_available - total_used
    
    quota_info = {
        "total_limit": quota.total_limit,
        "total_used": quota.total_used,
        "vip_extra_limit": quota.vip_extra_limit,
        "vip_extra_used": quota.vip_extra_used,
        "premium_limit": quota.premium_limit,
        "premium_used": quota.premium_used,
        "total_available": total_available,
        "total_used_all": total_used,
        "remaining": remaining,
        "is_vip": quota.is_vip
    }
    
    if remaining <= 0:
        return None, "胶囊数量已达上限", quota_info
    
    if recipient_type == TimeCapsuleRecipientType.FRIEND.value and not recipient_user_id:
        return None, "写给好友时需要指定接收者", quota_info
    
    if recipient_type == TimeCapsuleRecipientType.FRIEND.value and recipient_user_id == user_id:
        return None, "不能写给自己", quota_info
    
    recipient = None
    if recipient_type == TimeCapsuleRecipientType.FRIEND.value:
        recipient = db.query(User).filter(User.id == recipient_user_id).first()
        if not recipient:
            return None, "接收者不存在", quota_info
    
    can_use_skin_result, skin_msg, skin = can_use_skin(db, user_id, skin_key)
    if not can_use_skin_result:
        return None, skin_msg, quota_info
    
    if quota.total_used < quota.total_limit:
        quota.total_used += 1
        quota_info["total_used"] = quota.total_used
    elif quota.vip_extra_used < quota.vip_extra_limit:
        quota.vip_extra_used += 1
        quota_info["vip_extra_used"] = quota.vip_extra_used
    elif quota.premium_used < quota.premium_limit:
        quota.premium_used += 1
        quota_info["premium_used"] = quota.premium_used
    else:
        return None, "配额不足", quota_info
    
    total_used_after = quota.total_used + quota.vip_extra_used + quota.premium_used
    quota_info["total_used_all"] = total_used_after
    quota_info["remaining"] = total_available - total_used_after
    
    now = get_utc_now()
    unlock_at = calculate_unlock_at(unlock_duration, now)
    
    capsule = TimeCapsule(
        user_id=user_id,
        title=title,
        content=content,
        recipient_type=recipient_type,
        recipient_user_id=recipient_user_id,
        unlock_duration=unlock_duration,
        unlock_at=unlock_at,
        skin_id=skin.id if skin else None,
        skin_key=skin_key,
        status=TimeCapsuleStatus.PENDING.value,
        is_unlocked=False,
        is_opened=False,
        is_deleted=False,
        extra_metadata=json.dumps(extra_metadata) if extra_metadata else None
    )
    
    db.add(capsule)
    db.flush()
    
    if recipient_type == TimeCapsuleRecipientType.FRIEND.value and recipient_user_id:
        notification = TimeCapsuleNotification(
            capsule_id=capsule.id,
            user_id=recipient_user_id,
            notification_type=TimeCapsuleNotificationType.CAPSULE_RECEIVED.value,
            title="你收到了一个时间胶囊",
            content=f"用户 {user_id} 给你发送了一个时间胶囊，将在 {unlock_at.strftime('%Y-%m-%d')} 解锁"
        )
        db.add(notification)
        db.flush()
    
    return capsule, "创建成功", quota_info


def create_capsule(
    db: Session,
    user_id: int,
    title: str,
    content: str,
    recipient_type: str = TimeCapsuleRecipientType.SELF.value,
    recipient_user_id: int = None,
    unlock_duration: str = TimeCapsuleUnlockDuration.ONE_YEAR.value,
    skin_key: str = "classic_star",
    extra_metadata: Dict = None
) -> Tuple[Optional[TimeCapsule], str, Dict[str, Any]]:
    try:
        capsule, message, quota_info = create_capsule_transaction(
            db=db,
            user_id=user_id,
            title=title,
            content=content,
            recipient_type=recipient_type,
            recipient_user_id=recipient_user_id,
            unlock_duration=unlock_duration,
            skin_key=skin_key,
            extra_metadata=extra_metadata
        )
        
        if not capsule:
            db.rollback()
            return None, message, quota_info
        
        db.commit()
        db.refresh(capsule)
        
        logger.info(f"创建时间胶囊成功: user_id={user_id}, capsule_id={capsule.id}")
        return capsule, message, quota_info
        
    except Exception as e:
        db.rollback()
        logger.error(f"创建时间胶囊失败: user_id={user_id}, error={str(e)}", exc_info=True)
        return None, f"创建失败: {str(e)}", {}


def get_user_capsules(
    db: Session,
    user_id: int,
    status: str = None,
    skip: int = 0,
    limit: int = 20
) -> Tuple[List[TimeCapsule], int]:
    query = db.query(TimeCapsule).filter(
        TimeCapsule.user_id == user_id,
        TimeCapsule.is_deleted == False
    )
    
    if status:
        query = query.filter(TimeCapsule.status == status)
    
    total = query.count()
    
    capsules = query.order_by(
        TimeCapsule.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return capsules, total


def get_received_capsules(
    db: Session,
    user_id: int,
    status: str = None,
    skip: int = 0,
    limit: int = 20
) -> Tuple[List[TimeCapsule], int]:
    query = db.query(TimeCapsule).filter(
        TimeCapsule.recipient_user_id == user_id,
        TimeCapsule.recipient_type == TimeCapsuleRecipientType.FRIEND.value,
        TimeCapsule.is_deleted == False
    )
    
    if status:
        query = query.filter(TimeCapsule.status == status)
    
    total = query.count()
    
    capsules = query.order_by(
        TimeCapsule.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return capsules, total


def get_capsule_by_id(
    db: Session,
    capsule_id: int,
    user_id: int
) -> Tuple[Optional[TimeCapsule], str, bool]:
    capsule = db.query(TimeCapsule).filter(
        TimeCapsule.id == capsule_id,
        TimeCapsule.is_deleted == False
    ).first()
    
    if not capsule:
        return None, "胶囊不存在", False
    
    is_owner = capsule.user_id == user_id
    is_recipient = capsule.recipient_user_id == user_id and capsule.recipient_type == TimeCapsuleRecipientType.FRIEND.value
    
    if not is_owner and not is_recipient:
        return None, "无权限查看该胶囊", False
    
    if not capsule.is_unlocked:
        return capsule, "胶囊尚未解锁", False
    
    return capsule, "获取成功", True


def update_capsule(
    db: Session,
    capsule_id: int,
    user_id: int,
    title: str = None,
    content: str = None,
    skin_key: str = None,
    extra_metadata: Dict = None
) -> Tuple[Optional[TimeCapsule], str]:
    capsule = db.query(TimeCapsule).filter(
        TimeCapsule.id == capsule_id,
        TimeCapsule.user_id == user_id,
        TimeCapsule.is_deleted == False
    ).first()
    
    if not capsule:
        return None, "胶囊不存在或无权限修改"
    
    now = get_utc_now()
    if capsule.is_unlocked or capsule.unlock_at <= now:
        return None, "胶囊已解锁，无法修改"
    
    if skin_key and skin_key != capsule.skin_key:
        can_use_skin_result, skin_msg, skin = can_use_skin(db, user_id, skin_key)
        if not can_use_skin_result:
            return None, skin_msg
        
        capsule.skin_key = skin_key
        capsule.skin_id = skin.id if skin else None
    
    if title:
        capsule.title = title
    
    if content:
        capsule.content = content
    
    if extra_metadata is not None:
        capsule.extra_metadata = json.dumps(extra_metadata)
    
    db.commit()
    db.refresh(capsule)
    
    logger.info(f"更新时间胶囊成功: capsule_id={capsule_id}")
    
    return capsule, "更新成功"


def delete_capsule(
    db: Session,
    capsule_id: int,
    user_id: int
) -> Tuple[bool, str]:
    capsule = db.query(TimeCapsule).filter(
        TimeCapsule.id == capsule_id,
        TimeCapsule.user_id == user_id,
        TimeCapsule.is_deleted == False
    ).first()
    
    if not capsule:
        return False, "胶囊不存在或无权限删除"
    
    now = get_utc_now()
    if capsule.is_unlocked or capsule.unlock_at <= now:
        return False, "胶囊已解锁，无法删除"
    
    try:
        quota = get_or_create_user_quota_with_lock(db, user_id)
        
        capsule.is_deleted = True
        capsule.deleted_at = now
        
        if quota.premium_used > 0:
            quota.premium_used -= 1
        elif quota.vip_extra_used > 0:
            quota.vip_extra_used -= 1
        elif quota.total_used > 0:
            quota.total_used -= 1
        
        db.commit()
        logger.info(f"删除时间胶囊成功: capsule_id={capsule_id}")
        return True, "删除成功"
        
    except Exception as e:
        db.rollback()
        logger.error(f"删除时间胶囊失败: capsule_id={capsule_id}, error={str(e)}", exc_info=True)
        return False, f"删除失败: {str(e)}"


def open_capsule(
    db: Session,
    capsule_id: int,
    user_id: int
) -> Tuple[Optional[TimeCapsule], str]:
    capsule = db.query(TimeCapsule).filter(
        TimeCapsule.id == capsule_id,
        TimeCapsule.is_deleted == False
    ).first()
    
    if not capsule:
        return None, "胶囊不存在"
    
    is_owner = capsule.user_id == user_id
    is_recipient = capsule.recipient_user_id == user_id and capsule.recipient_type == TimeCapsuleRecipientType.FRIEND.value
    
    if not is_owner and not is_recipient:
        return None, "无权限操作该胶囊"
    
    if not capsule.is_unlocked:
        return None, "胶囊尚未解锁"
    
    if not capsule.is_opened:
        capsule.is_opened = True
        capsule.status = TimeCapsuleStatus.OPENED.value
        capsule.opened_at = get_utc_now()
        
        db.commit()
        db.refresh(capsule)
    
    logger.info(f"打开时间胶囊: capsule_id={capsule_id}, user_id={user_id}")
    return capsule, "打开成功"


def get_user_notifications(
    db: Session,
    user_id: int,
    is_read: bool = None,
    skip: int = 0,
    limit: int = 20
) -> Tuple[List[TimeCapsuleNotification], int]:
    query = db.query(TimeCapsuleNotification).filter(
        TimeCapsuleNotification.user_id == user_id
    )
    
    if is_read is not None:
        query = query.filter(TimeCapsuleNotification.is_read == is_read)
    
    total = query.count()
    
    notifications = query.order_by(
        TimeCapsuleNotification.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return notifications, total


def mark_notification_read(
    db: Session,
    notification_id: int,
    user_id: int
) -> Tuple[bool, str]:
    notification = db.query(TimeCapsuleNotification).filter(
        TimeCapsuleNotification.id == notification_id,
        TimeCapsuleNotification.user_id == user_id
    ).first()
    
    if not notification:
        return False, "通知不存在"
    
    notification.is_read = True
    notification.read_at = get_utc_now()
    
    db.commit()
    
    return True, "已标记为已读"


def process_expired_capsules(db: Session) -> int:
    now = get_utc_now()
    
    pending_capsules = db.query(TimeCapsule).filter(
        TimeCapsule.status == TimeCapsuleStatus.PENDING.value,
        TimeCapsule.is_deleted == False,
        TimeCapsule.unlock_at <= now
    ).with_for_update().all()
    
    processed_count = 0
    
    for capsule in pending_capsules:
        try:
            capsule.is_unlocked = True
            capsule.status = TimeCapsuleStatus.UNLOCKED.value
            
            owner_notification = TimeCapsuleNotification(
                capsule_id=capsule.id,
                user_id=capsule.user_id,
                notification_type=TimeCapsuleNotificationType.CAPSULE_UNLOCKED.value,
                title="你的时间胶囊已解锁",
                content=f"你封存的时间胶囊「{capsule.title}」已解锁，快来查看吧！"
            )
            db.add(owner_notification)
            
            if capsule.recipient_type == TimeCapsuleRecipientType.FRIEND.value and capsule.recipient_user_id:
                recipient_notification = TimeCapsuleNotification(
                    capsule_id=capsule.id,
                    user_id=capsule.recipient_user_id,
                    notification_type=TimeCapsuleNotificationType.CAPSULE_UNLOCKED.value,
                    title="你收到的时间胶囊已解锁",
                    content=f"用户 {capsule.user_id} 发给你的时间胶囊「{capsule.title}」已解锁，快来查看吧！"
                )
                db.add(recipient_notification)
            
            processed_count += 1
            logger.info(f"解锁时间胶囊: capsule_id={capsule.id}")
            
        except Exception as e:
            logger.error(f"解锁时间胶囊失败: capsule_id={capsule.id}, error={str(e)}", exc_info=True)
            continue
    
    if processed_count > 0:
        db.commit()
    
    return processed_count
