from enum import Enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


def _utc_now():
    return datetime.now(timezone.utc)


class TopicChallengeStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ENDED = "ended"
    ARCHIVED = "archived"


class RewardType(str, Enum):
    BLIND_BOX_TICKET = "blind_box_ticket"
    VIP_DURATION = "vip_duration"
    STARDUST_FRAGMENT = "stardust_fragment"
    STARDUST_POINT = "stardust_point"
    COUPON = "coupon"


class TopicChallenge(Base):
    __tablename__ = "topic_challenges"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    topic_tag = Column(String(100), nullable=False, index=True)

    banner_image_url = Column(String(500), nullable=True)
    cover_image_url = Column(String(500), nullable=True)

    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False, index=True)

    status = Column(String(20), default=TopicChallengeStatus.DRAFT.value, index=True)

    sort_order = Column(Integer, default=0, index=True)

    max_participants = Column(Integer, nullable=True)
    participant_count = Column(Integer, default=0)

    reward_config = Column(JSON, nullable=True)

    is_featured = Column(Boolean, default=False, index=True)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    posts = relationship("TopicParticipation", back_populates="topic", cascade="all, delete-orphan")


class TopicParticipation(Base):
    __tablename__ = "topic_participations"

    id = Column(Integer, primary_key=True, index=True)

    topic_id = Column(Integer, ForeignKey("topic_challenges.id"), nullable=False, index=True)
    post_id = Column(Integer, ForeignKey("plaza_posts.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    hot_score = Column(Integer, default=0, index=True)

    final_rank = Column(Integer, nullable=True, index=True)

    reward_claimed = Column(Boolean, default=False, index=True)
    reward_claimed_at = Column(DateTime, nullable=True)
    reward_type = Column(String(50), nullable=True)
    reward_amount = Column(Integer, default=0)

    participated_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index('ix_topic_participation_topic_user', 'topic_id', 'user_id'),
    )

    topic = relationship("TopicChallenge", back_populates="posts")


class TopicRewardClaim(Base):
    __tablename__ = "topic_reward_claims"

    id = Column(Integer, primary_key=True, index=True)

    topic_id = Column(Integer, ForeignKey("topic_challenges.id"), nullable=False, index=True)
    participation_id = Column(Integer, ForeignKey("topic_participations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    rank = Column(Integer, nullable=False)

    reward_type = Column(String(50), nullable=False)
    reward_amount = Column(Integer, default=0)
    reward_description = Column(String(200), nullable=True)

    transaction_id = Column(Integer, ForeignKey("stardust_transactions.id"), nullable=True)
    vip_subscription_id = Column(Integer, ForeignKey("vip_subscriptions.id"), nullable=True)

    claimed_at = Column(DateTime, default=datetime.utcnow, index=True)
