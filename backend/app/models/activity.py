from enum import Enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class ActivityType(str, Enum):
    FESTIVAL = "festival"
    ZODIAC_MONTH = "zodiac_month"
    WEEKEND_DUNGEON = "weekend_dungeon"
    BRAND_COLLAB = "brand_collab"


class ActivityStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    ENDED = "ended"
    ARCHIVED = "archived"


class BenefitType(str, Enum):
    SYNASTRY_DOUBLE_REWARD = "synastry_double_reward"
    SYNASTRY_FREE = "synastry_free"
    BLIND_BOX_DISCOUNT = "blind_box_discount"
    BLIND_BOX_RATE_UP = "blind_box_rate_up"
    STARDUST_DOUBLE = "stardust_double"
    LIMITED_CARD = "limited_card"
    BRAND_COUPON = "brand_coupon"
    LIMITED_ITEM = "limited_item"


class ZodiacSign(str, Enum):
    ARIES = "aries"
    TAURUS = "taurus"
    GEMINI = "gemini"
    CANCER = "cancer"
    LEO = "leo"
    VIRGO = "virgo"
    LIBRA = "libra"
    SCORPIO = "scorpio"
    SAGITTARIUS = "sagittarius"
    CAPRICORN = "capricorn"
    AQUARIUS = "aquarius"
    PISCES = "pisces"


ZODIAC_MONTH_MAP = {
    1: ZodiacSign.CAPRICORN,
    2: ZodiacSign.AQUARIUS,
    3: ZodiacSign.PISCES,
    4: ZodiacSign.ARIES,
    5: ZodiacSign.TAURUS,
    6: ZodiacSign.GEMINI,
    7: ZodiacSign.CANCER,
    8: ZodiacSign.LEO,
    9: ZodiacSign.VIRGO,
    10: ZodiacSign.LIBRA,
    11: ZodiacSign.SCORPIO,
    12: ZodiacSign.SAGITTARIUS,
}


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    activity_key = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    display_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    activity_type = Column(String(50), nullable=False, default=ActivityType.FESTIVAL)
    status = Column(String(50), nullable=False, default=ActivityStatus.DRAFT)

    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)

    target_zodiac_sign = Column(String(50), nullable=True)
    brand_name = Column(String(200), nullable=True)
    brand_logo_url = Column(String(500), nullable=True)

    rules_text = Column(Text, nullable=True)
    display_image_url = Column(String(500), nullable=True)
    banner_image_url = Column(String(500), nullable=True)

    is_auto_activated = Column(Boolean, default=True)
    priority = Column(Integer, default=0)
    metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, nullable=True)

    benefits = relationship("ActivityBenefit", back_populates="activity", cascade="all, delete-orphan")
    user_participations = relationship("ActivityParticipation", back_populates="activity", cascade="all, delete-orphan")


class ActivityBenefit(Base):
    __tablename__ = "activity_benefits"

    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=False, index=True)

    benefit_type = Column(String(100), nullable=False)
    benefit_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    multiplier = Column(Float, default=1.0)
    discount_percent = Column(Integer, nullable=True)
    rate_up_percent = Column(Integer, nullable=True)
    free_count = Column(Integer, default=0)
    item_id = Column(Integer, nullable=True)
    item_quantity = Column(Integer, default=1)

    target_module = Column(String(100), nullable=True)
    eligibility_filter = Column(JSON, nullable=True)

    is_active = Column(Boolean, default=True)
    daily_limit = Column(Integer, nullable=True)
    total_limit = Column(Integer, nullable=True)
    sort_order = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    activity = relationship("Activity", back_populates="benefits")


class ActivityParticipation(Base):
    __tablename__ = "activity_participations"

    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    joined_at = Column(DateTime, default=datetime.utcnow)
    last_active_at = Column(DateTime, default=datetime.utcnow)

    synastry_count = Column(Integer, default=0)
    blind_box_count = Column(Integer, default=0)
    stardust_earned = Column(Integer, default=0)
    items_claimed = Column(JSON, nullable=True)

    daily_benefit_usage = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    activity = relationship("Activity", back_populates="user_participations")

    __table_args__ = (
        UniqueConstraint('activity_id', 'user_id', name='uq_activity_participation'),
    )
