from enum import Enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
from app.utils.datetime_utils import utc_now as _utc_now


class TimeCapsuleRecipientType(str, Enum):
    SELF = "self"
    FRIEND = "friend"


class TimeCapsuleUnlockDuration(str, Enum):
    THREE_MONTHS = "3months"
    ONE_YEAR = "1year"
    THREE_YEARS = "3years"


class TimeCapsuleStatus(str, Enum):
    PENDING = "pending"
    UNLOCKED = "unlocked"
    OPENED = "opened"
    EXPIRED = "expired"


class TimeCapsuleNotificationType(str, Enum):
    UNLOCK_REMINDER = "unlock_reminder"
    CAPSULE_UNLOCKED = "capsule_unlocked"
    CAPSULE_RECEIVED = "capsule_received"


class TimeCapsule(Base):
    __tablename__ = "time_capsules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)

    recipient_type = Column(String(20), default=TimeCapsuleRecipientType.SELF, index=True)
    recipient_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    unlock_duration = Column(String(20), default=TimeCapsuleUnlockDuration.ONE_YEAR, index=True)
    unlock_at = Column(DateTime(timezone=True), nullable=False, index=True)

    skin_id = Column(Integer, ForeignKey("time_capsule_skins.id"), nullable=True)
    skin_key = Column(String(50), nullable=True)

    status = Column(String(20), default=TimeCapsuleStatus.PENDING, index=True)
    is_unlocked = Column(Boolean, default=False, index=True)
    is_opened = Column(Boolean, default=False, index=True)
    opened_at = Column(DateTime(timezone=True), nullable=True)

    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    extra_metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utc_now, index=True)
    updated_at = Column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now)

    user = relationship("User", foreign_keys=[user_id], backref="time_capsules")
    recipient_user = relationship("User", foreign_keys=[recipient_user_id], backref="received_capsules")
    skin = relationship("TimeCapsuleSkin", backref="capsules")

    __table_args__ = (
        Index('idx_time_capsules_user_status', 'user_id', 'status'),
        Index('idx_time_capsules_recipient_status', 'recipient_user_id', 'status'),
        Index('idx_time_capsules_unlock_at', 'unlock_at', 'is_unlocked'),
    )


class TimeCapsuleSkin(Base):
    __tablename__ = "time_capsule_skins"

    id = Column(Integer, primary_key=True, index=True)
    skin_key = Column(String(50), unique=True, nullable=False, index=True)

    name = Column(String(100), nullable=False)
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    category = Column(String(50), default="default", index=True)
    rarity = Column(String(20), default="common", index=True)

    preview_image_url = Column(String(500), nullable=True)
    cover_color = Column(String(20), nullable=True)
    text_color = Column(String(20), nullable=True)
    accent_color = Column(String(20), nullable=True)

    is_vip_only = Column(Boolean, default=False, index=True)
    is_premium = Column(Boolean, default=False, index=True)
    price = Column(Integer, default=0)
    currency_type = Column(String(20), default="stardust_point")

    is_active = Column(Boolean, default=True, index=True)
    sort_order = Column(Integer, default=0)

    available_from = Column(DateTime(timezone=True), nullable=True)
    available_until = Column(DateTime(timezone=True), nullable=True)

    extra_metadata = Column(JSON, nullable=True)
    is_deleted = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), default=_utc_now)
    updated_at = Column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now)
    created_by = Column(Integer, nullable=True)


class TimeCapsuleNotification(Base):
    __tablename__ = "time_capsule_notifications"

    id = Column(Integer, primary_key=True, index=True)
    capsule_id = Column(Integer, ForeignKey("time_capsules.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    notification_type = Column(String(30), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)

    is_read = Column(Boolean, default=False, index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)

    is_push_sent = Column(Boolean, default=False)
    push_sent_at = Column(DateTime(timezone=True), nullable=True)

    is_site_message_sent = Column(Boolean, default=False)
    site_message_sent_at = Column(DateTime(timezone=True), nullable=True)

    extra_metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utc_now, index=True)

    capsule = relationship("TimeCapsule", backref="notifications")
    user = relationship("User", backref="capsule_notifications")


class UserCapsuleQuota(Base):
    __tablename__ = "user_capsule_quotas"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)

    total_used = Column(Integer, default=0)
    total_limit = Column(Integer, default=3)

    vip_extra_used = Column(Integer, default=0)
    vip_extra_limit = Column(Integer, default=0)

    premium_used = Column(Integer, default=0)
    premium_limit = Column(Integer, default=0)

    is_vip = Column(Boolean, default=False, index=True)
    vip_plan_type = Column(String(20), nullable=True)

    extra_metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utc_now)
    updated_at = Column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now)

    user = relationship("User", backref="capsule_quota", uselist=False)
