from enum import Enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class InviteRewardStage(str, Enum):
    SHARE = "share"
    REGISTER_COMPLETE = "register_complete"
    FIRST_PAYMENT = "first_payment"


class InviteCode(Base):
    __tablename__ = "invite_codes"
    
    id = Column(Integer, primary_key=True, index=True)
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    invite_code = Column(String(20), unique=True, nullable=False, index=True)
    
    total_invites = Column(Integer, default=0)
    valid_invites = Column(Integer, default=0)
    paid_invites = Column(Integer, default=0)
    
    total_rewards_earned = Column(Integer, default=0)
    
    is_active = Column(Boolean, default=True, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", backref="invite_code", uselist=False)


class InviteRelation(Base):
    __tablename__ = "invite_relations"
    
    id = Column(Integer, primary_key=True, index=True)
    
    inviter_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    invitee_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    invite_code_used = Column(String(20), nullable=False, index=True)
    
    register_ip = Column(String(50), nullable=True)
    register_device = Column(String(500), nullable=True)
    
    is_register_completed = Column(Boolean, default=False)
    register_completed_at = Column(DateTime, nullable=True, index=True)
    
    has_first_payment = Column(Boolean, default=False)
    first_payment_at = Column(DateTime, nullable=True, index=True)
    first_payment_amount = Column(Integer, default=0)
    
    is_valid = Column(Boolean, default=True, index=True)
    invalid_reason = Column(String(200), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    inviter = relationship("User", foreign_keys=[inviter_id], backref="invitees")
    invitee = relationship("User", foreign_keys=[invitee_id], backref="inviter_relation", uselist=False)
    
    __table_args__ = (
        UniqueConstraint('invitee_id', name='uq_invitee_relation'),
    )


class InviteReward(Base):
    __tablename__ = "invite_rewards"
    
    id = Column(Integer, primary_key=True, index=True)
    
    reward_no = Column(String(50), unique=True, nullable=False, index=True)
    
    invite_relation_id = Column(Integer, ForeignKey("invite_relations.id"), nullable=False, index=True)
    
    inviter_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    invitee_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    reward_stage = Column(String(30), nullable=False, index=True)
    
    reward_type = Column(String(30), nullable=False, index=True)
    reward_amount = Column(Integer, default=0)
    reward_value = Column(String(500), nullable=True)
    
    reward_name = Column(String(200), nullable=False)
    reward_description = Column(Text, nullable=True)
    
    is_claimed = Column(Boolean, default=True)
    claimed_at = Column(DateTime, default=datetime.utcnow)
    
    transaction_id = Column(Integer, ForeignKey("stardust_transactions.id"), nullable=True)
    vip_subscription_id = Column(Integer, ForeignKey("vip_subscriptions.id"), nullable=True)
    coupon_id = Column(Integer, ForeignKey("user_coupons.id"), nullable=True)
    prophecy_ticket_id = Column(Integer, ForeignKey("prophecy_tickets.id"), nullable=True)
    
    status = Column(String(20), default="completed", index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    invite_relation = relationship("InviteRelation", backref="rewards")
    inviter = relationship("User", foreign_keys=[inviter_id], backref="invite_rewards_given")
    invitee = relationship("User", foreign_keys=[invitee_id], backref="invite_rewards_received")


class InviteShareLog(Base):
    __tablename__ = "invite_share_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    share_type = Column(String(30), nullable=False, index=True)
    share_platform = Column(String(30), nullable=True)
    
    share_content = Column(Text, nullable=True)
    invite_code = Column(String(20), nullable=True, index=True)
    
    synastry_record_id = Column(Integer, ForeignKey("synastry_records.id"), nullable=True)
    
    share_ip = Column(String(50), nullable=True)
    share_device = Column(String(500), nullable=True)
    
    click_count = Column(Integer, default=0)
    register_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    user = relationship("User", backref="invite_share_logs")
    synastry_record = relationship("SynastryRecord", backref="share_logs")
