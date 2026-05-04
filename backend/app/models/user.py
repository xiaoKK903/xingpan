from enum import Enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float, UniqueConstraint, JSON, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


def _utc_now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

    stardust_fragment_balance = Column(Integer, default=0)
    stardust_point_balance = Column(Integer, default=0)

    blind_box_tickets = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    charts = relationship("Chart", back_populates="user", cascade="all, delete-orphan")
    stardust_transactions = relationship("StarDustTransaction", back_populates="user", cascade="all, delete-orphan")
    mission_completions = relationship("MissionCompletion", back_populates="user", cascade="all, delete-orphan")


class StarDustTransaction(Base):
    __tablename__ = "stardust_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    transaction_type = Column(String(50), nullable=False, index=True)
    currency_type = Column(String(20), default="fragment")

    amount = Column(Integer, default=0)
    balance_before = Column(Integer, default=0)
    balance_after = Column(Integer, default=0)

    related_type = Column(String(50), nullable=True)
    related_id = Column(String(100), nullable=True)
    related_ref = Column(String(200), nullable=True)

    description = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="stardust_transactions")


class MissionCompletion(Base):
    __tablename__ = "mission_completions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    mission_id = Column(String(100), nullable=False, index=True)
    mission_type = Column(String(50), nullable=True)
    mission_title = Column(String(200), nullable=True)

    completion_key = Column(String(200), unique=True, index=True, nullable=False)

    reward_amount = Column(Integer, default=0)
    currency_type = Column(String(20), default="fragment")

    transaction_id = Column(Integer, ForeignKey("stardust_transactions.id"), nullable=True)

    proof_text = Column(Text, nullable=True)
    completion_data = Column(Text, nullable=True)

    is_bonus = Column(Boolean, default=False)
    bonus_reason = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="mission_completions")


class UserTag(Base):
    __tablename__ = "user_tags"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    tag_category = Column(String(50), nullable=False, index=True)
    tag_key = Column(String(100), nullable=False, index=True)
    tag_value = Column(String(500), nullable=True)

    tag_score = Column(Float, default=1.0)
    confidence = Column(Float, default=0.5)

    source_type = Column(String(50), default="inference", index=True)
    source_reference = Column(String(200), nullable=True)

    is_manual = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True, index=True)

    first_seen_at = Column(DateTime, default=datetime.utcnow)
    last_seen_at = Column(DateTime, default=datetime.utcnow)
    occurrence_count = Column(Integer, default=1)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TagCategory(str, Enum):
    EMOTION = "emotion"
    CONSTELLATION_BEHAVIOR = "constellation_behavior"
    VOTING_PREFERENCE = "voting_preference"
    ELEMENT_PREFERENCE = "element_preference"
    PLANET_PREFERENCE = "planet_preference"
    ACTIVITY_PATTERN = "activity_pattern"
    SPENDING_HABIT = "spending_habit"


class UserTagInferenceLog(Base):
    __tablename__ = "user_tag_inference_logs"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    inference_type = Column(String(50), nullable=False)
    inference_source = Column(String(100), nullable=True)

    tags_inferred = Column(Text, nullable=True)
    tags_updated = Column(Text, nullable=True)

    context_data = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class ExclusiveItem(Base):
    __tablename__ = "exclusive_items"

    id = Column(Integer, primary_key=True, index=True)

    item_key = Column(String(100), unique=True, nullable=False, index=True)
    item_name = Column(String(200), nullable=False)
    item_type = Column(String(50), default="pendant", index=True)

    description = Column(Text, nullable=True)
    rarity = Column(String(20), default="common", index=True)

    cost_points = Column(Integer, default=100)
    cost_fragments = Column(Integer, default=0)

    effect_type = Column(String(50), default="cosmetic", index=True)
    effect_data = Column(Text, nullable=True)

    energy_weight_bonus = Column(Float, default=0.0)

    is_active = Column(Boolean, default=True, index=True)
    is_limited = Column(Boolean, default=False)

    stock_remaining = Column(Integer, nullable=True)
    max_per_user = Column(Integer, default=1)

    available_from = Column(DateTime, nullable=True)
    available_until = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserInventory(Base):
    __tablename__ = "user_inventories"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("exclusive_items.id"), nullable=False, index=True)

    quantity = Column(Integer, default=1)

    is_equipped = Column(Boolean, default=False)
    equipped_at = Column(DateTime, nullable=True)

    acquired_at = Column(DateTime, default=datetime.utcnow)
    acquired_source = Column(String(50), default="purchase")

    cost_points_spent = Column(Integer, default=0)
    cost_fragments_spent = Column(Integer, default=0)

    expires_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Avatar(Base):
    __tablename__ = "avatars"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    chart_id = Column(Integer, ForeignKey("charts.id"), nullable=True)

    name = Column(String(100), nullable=False, default="无名星者")
    title = Column(String(100), nullable=True)
    avatar_type = Column(String(50), nullable=False, default="default")
    avatar_image = Column(String(500), nullable=True)

    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)
    experience_needed = Column(Integer, default=100)

    primary_element = Column(String(20), nullable=False, default="fire")
    secondary_element = Column(String(20), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    stats = relationship("CharacterStats", back_populates="avatar", uselist=False, cascade="all, delete-orphan")
    inventory = relationship("AvatarInventory", back_populates="avatar", cascade="all, delete-orphan")


class CharacterStats(Base):
    __tablename__ = "character_stats"

    id = Column(Integer, primary_key=True, index=True)
    avatar_id = Column(Integer, ForeignKey("avatars.id"), nullable=False, unique=True, index=True)

    combat_power = Column(Integer, default=50)
    inspiration = Column(Integer, default=50)
    emotion_resonance = Column(Integer, default=50)
    intuition = Column(Integer, default=50)
    creativity = Column(Integer, default=50)
    resilience = Column(Integer, default=50)
    charisma = Column(Integer, default=50)
    luck = Column(Integer, default=50)

    fire_power = Column(Integer, default=0)
    earth_power = Column(Integer, default=0)
    air_power = Column(Integer, default=0)
    water_power = Column(Integer, default=0)

    sun_strength = Column(Integer, default=50)
    moon_strength = Column(Integer, default=50)
    mercury_strength = Column(Integer, default=50)
    venus_strength = Column(Integer, default=50)
    mars_strength = Column(Integer, default=50)
    jupiter_strength = Column(Integer, default=50)
    saturn_strength = Column(Integer, default=50)
    uranus_strength = Column(Integer, default=50)
    neptune_strength = Column(Integer, default=50)
    pluto_strength = Column(Integer, default=50)

    zodiac_archetype = Column(String(50), nullable=True)
    planetary_dominant = Column(String(50), nullable=True)

    stats_data = Column(Text, nullable=True)

    avatar = relationship("Avatar", back_populates="stats")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AvatarInventory(Base):
    __tablename__ = "avatar_inventory"

    id = Column(Integer, primary_key=True, index=True)
    avatar_id = Column(Integer, ForeignKey("avatars.id"), nullable=False, index=True)

    item_name = Column(String(100), nullable=False)
    item_type = Column(String(50), nullable=False)
    item_rarity = Column(String(20), default="common")
    item_description = Column(Text, nullable=True)

    power_bonus = Column(Integer, default=0)
    element_bonus = Column(String(20), nullable=True)
    special_effect = Column(Text, nullable=True)

    is_equipped = Column(Boolean, default=False)
    slot = Column(String(50), nullable=True)

    avatar = relationship("Avatar", back_populates="inventory")
    created_at = Column(DateTime, default=datetime.utcnow)
