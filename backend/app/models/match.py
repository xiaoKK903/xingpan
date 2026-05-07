from enum import Enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float, UniqueConstraint, JSON, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
from app.utils.datetime_utils import utc_now as _utc_now


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False, default="新会话")
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")


class BlindBoxMatch(Base):
    __tablename__ = "blind_box_matches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    matched_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    blind_box_id = Column(String(50), unique=True, nullable=False, index=True)

    complement_score = Column(Float, default=0.0)
    match_type = Column(String(20), default="partial")

    clues_data = Column(Text, nullable=True)
    complement_details = Column(Text, nullable=True)
    completeness_data = Column(Text, nullable=True)

    is_revealed = Column(Boolean, default=False)
    revealed_at = Column(DateTime, nullable=True)

    is_claimed = Column(Boolean, default=False)
    claimed_at = Column(DateTime, nullable=True)
    reward_earned = Column(Integer, default=0)

    status = Column(String(20), default="active", index=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class QuestLog(Base):
    __tablename__ = "quest_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    quest_date = Column(String(20), nullable=False, index=True)
    quest_type = Column(String(50), default="blind_box_match", index=True)

    blind_box_match_id = Column(Integer, ForeignKey("blind_box_matches.id"), nullable=True, index=True)

    quest_status = Column(String(20), default="completed", index=True)

    reward_earned = Column(Integer, default=0)
    reward_type = Column(String(20), default="fragment")

    meta_data = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class DailyQuestLimit(Base):
    __tablename__ = "daily_quest_limits"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    limit_date = Column(String(20), nullable=False, index=True)
    quest_type = Column(String(50), default="blind_box_match", index=True)

    used_count = Column(Integer, default=0)
    max_count = Column(Integer, default=3)

    is_vip = Column(Boolean, default=False)
    vip_extra_count = Column(Integer, default=0)

    refresh_count = Column(Integer, default=0)
    max_refresh = Column(Integer, default=1)

    meta_data = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ClueRevealHistory(Base):
    __tablename__ = "clue_reveal_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    blind_box_match_id = Column(Integer, ForeignKey("blind_box_matches.id"), nullable=False, index=True)

    clue_index = Column(Integer, default=0)
    clue_content = Column(String(500), nullable=True)
    hint_level = Column(String(20), default="subtle")

    cost_fragment = Column(Integer, default=0)
    cost_point = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)


class UserPrivateChat(Base):
    __tablename__ = "user_private_chats"

    id = Column(Integer, primary_key=True, index=True)

    user_a_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user_b_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    chat_identifier = Column(String(100), unique=True, nullable=False, index=True)

    last_message_at = Column(DateTime, nullable=True)
    last_message_content = Column(String(500), nullable=True)
    last_message_sender_id = Column(Integer, nullable=True)

    unread_count_a = Column(Integer, default=0)
    unread_count_b = Column(Integer, default=0)

    match_source = Column(String(50), nullable=True)
    match_source_id = Column(Integer, nullable=True)

    match_compatibility_score = Column(Integer, nullable=True)
    match_type = Column(String(50), nullable=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('user_a_id', 'user_b_id', name='uq_private_chat_users'),
    )


class PrivateChatMessage(Base):
    __tablename__ = "private_chat_messages"

    id = Column(Integer, primary_key=True, index=True)

    chat_id = Column(Integer, ForeignKey("user_private_chats.id"), nullable=False, index=True)

    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    content = Column(Text, nullable=False)
    message_type = Column(String(20), default="text")

    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    chat = relationship("UserPrivateChat", backref="messages")


class NetworkConnection(Base):
    __tablename__ = "network_connections"

    id = Column(Integer, primary_key=True, index=True)

    from_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    to_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    connection_type = Column(String(50), nullable=True)
    connection_strength = Column(String(20), default="medium")

    compatibility_score = Column(Integer, nullable=True)
    match_type = Column(String(50), nullable=True)

    shared_aspects = Column(Text, nullable=True)
    highlights_summary = Column(Text, nullable=True)

    is_mutual = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    private_chat_id = Column(Integer, ForeignKey("user_private_chats.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('from_user_id', 'to_user_id', name='uq_network_connection'),
    )


class DailyCPMatchStatus(str, Enum):
    PENDING = "pending"
    MATCHED = "matched"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class DailyCPMatch(Base):
    __tablename__ = "daily_cp_matches"

    id = Column(Integer, primary_key=True, index=True)
    match_date = Column(String(20), nullable=False, index=True)
    match_batch_id = Column(String(50), nullable=True, index=True)

    user_a_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user_b_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    user_a_chart_id = Column(Integer, ForeignKey("charts.id"), nullable=True)
    user_b_chart_id = Column(Integer, ForeignKey("charts.id"), nullable=True)

    compatibility_score = Column(Integer, default=50)
    match_type = Column(String(50), default="random")
    target_zodiac_sign = Column(String(50), nullable=True)

    synastry_aspects = Column(Text, nullable=True)
    highlights_summary = Column(Text, nullable=True)
    interpretation_text = Column(Text, nullable=True)

    user_a_status = Column(String(20), default=DailyCPMatchStatus.PENDING, index=True)
    user_b_status = Column(String(20), default=DailyCPMatchStatus.PENDING, index=True)

    user_a_accepted_at = Column(DateTime, nullable=True)
    user_b_accepted_at = Column(DateTime, nullable=True)

    is_mutual_accepted = Column(Boolean, default=False, index=True)
    mutual_accepted_at = Column(DateTime, nullable=True)

    session_id = Column(Integer, ForeignKey("time_limited_sessions.id"), nullable=True)

    user_a_profile_unlocked = Column(Boolean, default=False)
    user_a_profile_unlocked_at = Column(DateTime, nullable=True)
    user_a_profile_unlock_order_id = Column(Integer, ForeignKey("payment_orders.id"), nullable=True)

    user_b_profile_unlocked = Column(Boolean, default=False)
    user_b_profile_unlocked_at = Column(DateTime, nullable=True)
    user_b_profile_unlock_order_id = Column(Integer, ForeignKey("payment_orders.id"), nullable=True)

    match_source = Column(String(50), default="daily_scheduled")
    is_vip_targeted_match = Column(Boolean, default=False)

    status = Column(String(20), default="active", index=True)
    expired_at = Column(DateTime, nullable=True, index=True)

    created_at = Column(DateTime, default=_utc_now, index=True)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)

    user_a = relationship("User", foreign_keys=[user_a_id], backref="cp_matches_as_a")
    user_b = relationship("User", foreign_keys=[user_b_id], backref="cp_matches_as_b")
    session = relationship("TimeLimitedSession", foreign_keys=[session_id], backref="match", uselist=False)

    __table_args__ = (
        UniqueConstraint('match_date', 'user_a_id', 'user_b_id', name='uq_daily_cp_match_users'),
        Index('idx_daily_cp_matches_date_status', 'match_date', 'status'),
        Index('idx_daily_cp_matches_mutual', 'is_mutual_accepted', 'status'),
    )


class DailyMatchLimit(Base):
    __tablename__ = "daily_match_limits"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    limit_date = Column(String(20), nullable=False, index=True)

    free_match_count = Column(Integer, default=0)
    free_match_max = Column(Integer, default=1)

    vip_extra_match_count = Column(Integer, default=0)
    vip_extra_match_max = Column(Integer, default=0)

    paid_match_count = Column(Integer, default=0)
    paid_match_max = Column(Integer, default=10)

    targeted_match_count = Column(Integer, default=0)
    targeted_match_max = Column(Integer, default=0)

    is_vip = Column(Boolean, default=False, index=True)
    vip_plan_type = Column(String(20), nullable=True)

    extra_metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=_utc_now, index=True)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)

    user = relationship("User", backref="daily_match_limits")

    __table_args__ = (
        UniqueConstraint('user_id', 'limit_date', name='uq_daily_match_limit_user_date'),
    )


class TimeLimitedSession(Base):
    __tablename__ = "time_limited_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_key = Column(String(100), unique=True, nullable=False, index=True)

    user_a_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user_b_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    match_id = Column(Integer, ForeignKey("daily_cp_matches.id"), nullable=False, index=True)

    base_duration_hours = Column(Integer, default=24)
    extended_duration_hours = Column(Integer, default=0)
    total_duration_hours = Column(Integer, default=24)

    started_at = Column(DateTime, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)

    is_extended = Column(Boolean, default=False)
    extension_count = Column(Integer, default=0)

    private_chat_id = Column(Integer, ForeignKey("user_private_chats.id"), nullable=True)

    is_active = Column(Boolean, default=True, index=True)
    closed_at = Column(DateTime, nullable=True)
    close_reason = Column(String(50), nullable=True)

    message_count = Column(Integer, default=0)
    last_message_at = Column(DateTime, nullable=True)

    extra_metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=_utc_now, index=True)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)

    user_a = relationship("User", foreign_keys=[user_a_id], backref="sessions_as_a")
    user_b = relationship("User", foreign_keys=[user_b_id], backref="sessions_as_b")
    private_chat = relationship("UserPrivateChat", backref="time_limited_session", uselist=False)

    __table_args__ = (
        Index('idx_time_limited_sessions_expires', 'expires_at', 'is_active'),
        Index('idx_time_limited_sessions_users', 'user_a_id', 'user_b_id'),
    )


class SessionExtension(Base):
    __tablename__ = "session_extensions"

    id = Column(Integer, primary_key=True, index=True)
    extension_no = Column(String(50), unique=True, nullable=False, index=True)

    session_id = Column(Integer, ForeignKey("time_limited_sessions.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    extension_type = Column(String(50), default="7_days")
    extension_hours = Column(Integer, default=168)

    price = Column(Integer, default=0)
    currency_type = Column(String(20), default="stardust_point")

    payment_order_id = Column(Integer, ForeignKey("payment_orders.id"), nullable=True)
    is_vip_free = Column(Boolean, default=False)

    applied_at = Column(DateTime, nullable=True, index=True)
    new_expires_at = Column(DateTime, nullable=True)

    status = Column(String(20), default="pending", index=True)

    created_at = Column(DateTime, default=_utc_now, index=True)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)

    session = relationship("TimeLimitedSession", backref="extensions")
    user = relationship("User", backref="session_extensions")
    payment_order = relationship("PaymentOrder")


class ProfileUnlock(Base):
    __tablename__ = "profile_unlocks"

    id = Column(Integer, primary_key=True, index=True)
    unlock_no = Column(String(50), unique=True, nullable=False, index=True)

    match_id = Column(Integer, ForeignKey("daily_cp_matches.id"), nullable=False, index=True)
    buyer_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    target_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    price = Column(Integer, default=0)
    currency_type = Column(String(20), default="stardust_point")

    payment_order_id = Column(Integer, ForeignKey("payment_orders.id"), nullable=True)
    is_vip_free = Column(Boolean, default=False)

    unlocked_at = Column(DateTime, nullable=True, index=True)
    expires_at = Column(DateTime, nullable=True, index=True)

    is_permanent = Column(Boolean, default=False)

    status = Column(String(20), default="pending", index=True)

    created_at = Column(DateTime, default=_utc_now, index=True)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)

    match = relationship("DailyCPMatch", backref="profile_unlocks")
    buyer = relationship("User", foreign_keys=[buyer_user_id], backref="profile_unlocks_bought")
    target = relationship("User", foreign_keys=[target_user_id], backref="profile_unlocks_received")
    payment_order = relationship("PaymentOrder")


class MatchPreference(Base):
    __tablename__ = "match_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)

    preferred_zodiac_signs = Column(JSON, nullable=True)
    excluded_zodiac_signs = Column(JSON, nullable=True)

    min_age = Column(Integer, nullable=True)
    max_age = Column(Integer, nullable=True)

    preferred_element = Column(String(20), nullable=True)
    preferred_match_type = Column(String(20), default="all")

    search_radius_km = Column(Float, default=50.0)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=_utc_now, index=True)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)

    user = relationship("User", backref="match_preference", uselist=False)
