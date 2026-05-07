from enum import Enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float, UniqueConstraint, JSON, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class PlazaPostType(str, Enum):
    SYNASTRY_CARD = "synastry_card"
    DAILY_HOROSCOPE = "daily_horoscope"
    PAST_LIFE_STORY = "past_life_story"
    CARD_DRAW = "card_draw"


class PlazaPostStatus(str, Enum):
    PUBLISHED = "published"
    USER_DELETED = "user_deleted"
    HIDDEN = "hidden"
    REMOVED = "removed"
    PENDING_REVIEW = "pending_review"


class PlazaPost(Base):
    __tablename__ = "plaza_posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    post_type = Column(String(50), default=PlazaPostType.SYNASTRY_CARD, index=True)

    title = Column(String(200), nullable=True)
    content = Column(Text, nullable=True)

    image_urls = Column(Text, nullable=True)
    video_url = Column(String(500), nullable=True)

    related_data = Column(Text, nullable=True)

    synastry_record_id = Column(Integer, ForeignKey("synastry_records.id"), nullable=True, index=True)
    past_life_record_id = Column(Integer, ForeignKey("past_life_records.id"), nullable=True, index=True)
    photocard_record_id = Column(Integer, ForeignKey("photocard_records.id"), nullable=True, index=True)

    like_count = Column(Integer, default=0, index=True)
    flower_count = Column(Integer, default=0, index=True)
    mention_count = Column(Integer, default=0)

    status = Column(String(20), default=PlazaPostStatus.PUBLISHED, index=True)
    hide_reason = Column(String(500), nullable=True)
    hidden_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    is_vip = Column(Boolean, default=False, index=True)
    vip_border_style = Column(String(50), default="gold_gradient")

    publish_ip = Column(String(50), nullable=True)
    publish_device = Column(String(200), nullable=True)

    is_manual_reviewed = Column(Boolean, default=False)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    review_notes = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", foreign_keys=[user_id], backref="plaza_posts")


class PlazaLike(Base):
    __tablename__ = "plaza_likes"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("plaza_posts.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('post_id', 'user_id', name='uq_plaza_like_post_user'),
    )


class PlazaFlowerGift(Base):
    __tablename__ = "plaza_flower_gifts"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("plaza_posts.id"), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    gift_id = Column(Integer, ForeignKey("gifts.id"), nullable=True, index=True)
    gift_name = Column(String(100), nullable=True)
    gift_icon = Column(String(100), nullable=True)
    gift_rarity = Column(String(20), nullable=True)

    quantity = Column(Integer, default=1)

    message = Column(String(200), nullable=True)
    is_anonymous = Column(Boolean, default=False)

    cost_points = Column(Integer, default=0)
    cost_fragments = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class PlazaMention(Base):
    __tablename__ = "plaza_mentions"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("plaza_posts.id"), nullable=False, index=True)
    inviter_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    invitee_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    invitation_type = Column(String(50), default="synastry", index=True)

    message = Column(String(200), nullable=True)

    is_accepted = Column(Boolean, nullable=True)
    accepted_at = Column(DateTime, nullable=True)
    declined_at = Column(DateTime, nullable=True)
    decline_reason = Column(String(200), nullable=True)

    synastry_record_id = Column(Integer, ForeignKey("synastry_records.id"), nullable=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('post_id', 'inviter_id', 'invitee_id', name='uq_plaza_mention_post_users'),
    )


class PlazaPostReport(Base):
    __tablename__ = "plaza_post_reports"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("plaza_posts.id"), nullable=False, index=True)
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    report_category = Column(String(50), nullable=False, index=True)
    report_reason = Column(String(500), nullable=True)

    reporter_ip = Column(String(50), nullable=True)

    is_processed = Column(Boolean, default=False, index=True)
    processed_at = Column(DateTime, nullable=True)
    processed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    process_result = Column(String(20), nullable=True)
    process_notes = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class PlazaPostTag(Base):
    __tablename__ = "plaza_post_tags"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("plaza_posts.id"), nullable=False, index=True)

    tag_key = Column(String(100), nullable=False, index=True)
    tag_value = Column(String(500), nullable=True)
    tag_category = Column(String(50), nullable=True, index=True)

    is_auto_generated = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('post_id', 'tag_key', name='uq_plaza_post_tag_post_key'),
    )


class PlazaUserShareRecord(Base):
    __tablename__ = "plaza_user_share_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    post_id = Column(Integer, ForeignKey("plaza_posts.id"), nullable=True, index=True)

    share_platform = Column(String(50), nullable=True, index=True)
    share_type = Column(String(50), default="external", index=True)

    share_url = Column(String(500), nullable=True)
    share_text = Column(String(200), nullable=True)

    click_count = Column(Integer, default=0)
    redirect_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
