from enum import Enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float, UniqueConstraint, JSON, Numeric, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


def _utc_now():
    return datetime.now(timezone.utc)


class SessionType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    SPECIAL = "special"
    FESTIVAL = "festival"
    BRAND = "brand"


class RewardAssetType(str, Enum):
    FRAGMENT = "fragment"
    POINT = "point"
    TICKET = "ticket"


class OracleDataSource(str, Enum):
    WEATHER = "weather"
    RESONANCE_POOL = "resonance_pool"
    MANUAL = "manual"


class CollectivePrediction(Base):
    __tablename__ = "collective_predictions"

    id = Column(Integer, primary_key=True, index=True)

    prediction_date = Column(String(20), nullable=False, index=True)
    target_date = Column(String(20), nullable=False, index=True)

    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    prediction_type = Column(String(50), default="mood", index=True)
    session_type = Column(String(20), default=SessionType.DAILY, index=True)
    session_key = Column(String(100), nullable=True, index=True)

    theme_id = Column(Integer, ForeignKey("prediction_themes.id"), nullable=True, index=True)

    options = Column(Text, nullable=True)
    correct_option = Column(String(100), nullable=True)

    total_votes = Column(Integer, default=0)
    vote_distribution = Column(Text, nullable=True)

    status = Column(String(20), default="open", index=True)

    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)

    actual_result = Column(Text, nullable=True)
    accuracy_score = Column(Float, nullable=True)

    total_stardust_pool = Column(Integer, default=0)

    announced_at = Column(DateTime, nullable=True)
    voting_starts_at = Column(DateTime, nullable=True, index=True)
    voting_ends_at = Column(DateTime, nullable=True, index=True)

    max_votes_per_user = Column(Integer, default=1)
    base_vote_cost = Column(Integer, default=0)
    extra_vote_cost = Column(Integer, default=10)

    vip_multiplier = Column(Float, default=1.5)
    is_vip_enabled = Column(Boolean, default=False)

    ad_config = Column(Text, nullable=True)
    event_brand_info = Column(Text, nullable=True)

    reward_asset_type = Column(String(20), default=RewardAssetType.FRAGMENT, index=True)
    base_reward_amount = Column(Integer, default=10)
    bonus_reward_amount = Column(Integer, default=0)

    oracle_data_source = Column(String(20), default=OracleDataSource.MANUAL, index=True)
    resolution_evidence = Column(Text, nullable=True)
    is_manual_resolution = Column(Boolean, default=False)
    resolved_by_admin_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    resolution_audit_log = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    theme = relationship("PredictionTheme", back_populates="predictions")


class VoteAssetType(str, Enum):
    FRAGMENT = "fragment"
    POINT = "point"
    TICKET = "ticket"


class PredictionVote(Base):
    __tablename__ = "prediction_votes"

    id = Column(Integer, primary_key=True, index=True)
    prediction_id = Column(Integer, ForeignKey("collective_predictions.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    vote_number = Column(Integer, default=1)

    selected_option = Column(String(100), nullable=False)
    confidence = Column(Integer, default=50)

    vote_asset_type = Column(String(20), default=VoteAssetType.FRAGMENT, index=True)
    vote_cost = Column(Integer, default=0)
    stardust_bet = Column(Integer, default=0)

    is_vip_bonus = Column(Boolean, default=False)
    applied_multiplier = Column(Float, default=1.0)

    is_correct = Column(Boolean, nullable=True)
    reward_earned = Column(Integer, default=0)
    reward_asset_type = Column(String(20), default=RewardAssetType.FRAGMENT, index=True)
    reward_claimed = Column(Boolean, default=False)
    reward_claimed_at = Column(DateTime, nullable=True)

    is_validated = Column(Boolean, default=True)
    validated_at = Column(DateTime, nullable=True)
    validation_notes = Column(String(500), nullable=True)

    vote_data = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class PredictionOptionStat(Base):
    __tablename__ = "prediction_option_stats"

    id = Column(Integer, primary_key=True, index=True)

    prediction_id = Column(Integer, ForeignKey("collective_predictions.id"), nullable=False, index=True)
    option_value = Column(String(100), nullable=False, index=True)

    vote_count = Column(Integer, default=0)
    total_amount = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RewardClaimRecord(Base):
    __tablename__ = "reward_claim_records"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    prediction_id = Column(Integer, ForeignKey("collective_predictions.id"), nullable=False, index=True)
    vote_id = Column(Integer, ForeignKey("prediction_votes.id"), nullable=False, unique=True, index=True)

    asset_type = Column(String(20), nullable=False, index=True)
    amount = Column(Integer, default=0)

    claimed_at = Column(DateTime, default=datetime.utcnow, index=True)
    claim_ip = Column(String(50), nullable=True)
    claim_session = Column(String(100), nullable=True)

    audit_note = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class VoteAssetLock(Base):
    __tablename__ = "vote_asset_locks"

    id = Column(Integer, primary_key=True, index=True)

    lock_key = Column(String(100), unique=True, nullable=False, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    prediction_id = Column(Integer, ForeignKey("collective_predictions.id"), nullable=False, index=True)
    vote_number = Column(Integer, default=1)

    asset_type = Column(String(20), nullable=False)
    amount = Column(Integer, default=0)

    is_processed = Column(Boolean, default=False, index=True)
    processed_at = Column(DateTime, nullable=True)

    expires_at = Column(DateTime, nullable=False, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class RateLimitRecord(Base):
    __tablename__ = "rate_limit_records"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    ip_address = Column(String(50), nullable=True, index=True)

    action_type = Column(String(50), nullable=False, index=True)
    action_count = Column(Integer, default=0)

    window_start = Column(DateTime, nullable=False, index=True)
    window_end = Column(DateTime, nullable=False, index=True)

    is_blocked = Column(Boolean, default=False, index=True)
    blocked_reason = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AbnormalBehaviorLog(Base):
    __tablename__ = "abnormal_behavior_logs"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    ip_address = Column(String(50), nullable=True, index=True)
    session_id = Column(String(100), nullable=True, index=True)

    behavior_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), default="low", index=True)

    request_data = Column(Text, nullable=True)
    request_path = Column(String(200), nullable=True)
    request_method = Column(String(20), nullable=True)

    detection_rule = Column(String(100), nullable=True)
    risk_score = Column(Float, default=0.0)

    is_manual_reviewed = Column(Boolean, default=False)
    review_result = Column(String(20), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    action_taken = Column(String(50), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class TieredVoteCost(Base):
    __tablename__ = "tiered_vote_costs"

    id = Column(Integer, primary_key=True, index=True)

    prediction_id = Column(Integer, ForeignKey("collective_predictions.id"), nullable=False, index=True)

    vote_tier = Column(Integer, default=1)

    allowed_asset_types = Column(String(200), default="fragment")

    cost_fragment = Column(Integer, default=0)
    cost_point = Column(Integer, default=0)
    cost_ticket = Column(Integer, default=0)

    reward_multiplier = Column(Float, default=1.0)

    is_active = Column(Boolean, default=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PredictionTheme(Base):
    __tablename__ = "prediction_themes"

    id = Column(Integer, primary_key=True, index=True)

    theme_key = Column(String(100), unique=True, nullable=False, index=True)
    theme_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    theme_category = Column(String(50), default="general", index=True)

    default_options = Column(Text, nullable=True)
    default_session_type = Column(String(20), default=SessionType.DAILY)
    default_max_votes = Column(Integer, default=1)
    default_base_cost = Column(Integer, default=0)
    default_reward_type = Column(String(20), default=RewardAssetType.FRAGMENT)
    default_reward_amount = Column(Integer, default=10)

    oracle_source = Column(String(20), default=OracleDataSource.MANUAL)
    resolution_rule = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True, index=True)
    is_permanent = Column(Boolean, default=False)

    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)

    ad_config = Column(Text, nullable=True)
    brand_info = Column(Text, nullable=True)

    sort_order = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    predictions = relationship("CollectivePrediction", back_populates="theme")


class ResolutionEvidence(Base):
    __tablename__ = "resolution_evidences"

    id = Column(Integer, primary_key=True, index=True)

    prediction_id = Column(Integer, ForeignKey("collective_predictions.id"), nullable=False, index=True)

    evidence_type = Column(String(50), nullable=False, index=True)
    evidence_source = Column(String(100), nullable=True)

    evidence_data = Column(Text, nullable=False)
    evidence_summary = Column(String(500), nullable=True)

    snapshot_at = Column(DateTime, nullable=True, index=True)

    is_used_for_resolution = Column(Boolean, default=False)
    resolution_outcome = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


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
    extra_metadata = Column(JSON, nullable=True)

    is_deleted = Column(Boolean, default=False, index=True)

    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)
    created_by = Column(Integer, nullable=True)

    benefits = relationship("ActivityBenefit", back_populates="activity")
    user_participations = relationship("ActivityParticipation", back_populates="activity")

    __table_args__ = (
        Index('idx_activities_status_time', 'status', 'start_time', 'end_time'),
        Index('idx_activities_start_time', 'start_time'),
        Index('idx_activities_end_time', 'end_time'),
        Index('idx_activities_type', 'activity_type'),
    )


class ActivityBenefit(Base):
    __tablename__ = "activity_benefits"

    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=False, index=True)

    benefit_type = Column(String(100), nullable=False)
    benefit_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    multiplier = Column(Numeric(precision=10, scale=2), default=1.0)
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

    is_deleted = Column(Boolean, default=False)

    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)

    activity = relationship("Activity", back_populates="benefits")


class ActivityParticipation(Base):
    __tablename__ = "activity_participations"

    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    joined_at = Column(DateTime, default=_utc_now)
    last_active_at = Column(DateTime, default=_utc_now)

    synastry_count = Column(Integer, default=0)
    blind_box_count = Column(Integer, default=0)
    stardust_earned = Column(Integer, default=0)
    items_claimed = Column(JSON, nullable=True)

    daily_benefit_usage = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)

    activity = relationship("Activity", back_populates="user_participations")

    __table_args__ = (
        UniqueConstraint('activity_id', 'user_id', name='uq_activity_participation'),
    )


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


class GrowthTaskType(str, Enum):
    COMPLETE_CHART = "complete_chart"
    COMPLETE_SYNASTRY = "complete_synastry"
    JOIN_GROUP = "join_group"
    DAILY_CHECKIN = "daily_checkin"
    FIRST_SHARE = "first_share"


class GrowthTaskStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"


class UserGrowthTaskStatus(str, Enum):
    LOCKED = "locked"
    AVAILABLE = "available"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CLAIMED = "claimed"


class GrowthTask(Base):
    __tablename__ = "growth_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_key = Column(String(100), unique=True, index=True, nullable=False)
    task_type = Column(String(50), nullable=False, index=True)

    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    short_description = Column(String(500), nullable=True)

    icon = Column(String(200), nullable=True)
    rarity = Column(String(20), default="common")

    sort_order = Column(Integer, default=0)
    required_count = Column(Integer, default=1)

    trigger_condition = Column(JSON, nullable=True)
    completion_verifier = Column(JSON, nullable=True)

    reward_type = Column(String(50), default="stardust_fragment")
    reward_amount = Column(Integer, default=10)
    reward_value = Column(JSON, nullable=True)
    reward_name = Column(String(200), nullable=True)

    is_auto_claim = Column(Boolean, default=True)
    is_one_time = Column(Boolean, default=True)

    status = Column(String(50), default=GrowthTaskStatus.ACTIVE, index=True)
    start_at = Column(DateTime, nullable=True)
    end_at = Column(DateTime, nullable=True)

    is_new_user_only = Column(Boolean, default=True)
    max_days_after_register = Column(Integer, nullable=True)

    extra_metadata = Column(JSON, nullable=True)
    is_deleted = Column(Boolean, default=False, index=True)

    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)
    created_by = Column(Integer, nullable=True)

    user_progress = relationship("UserGrowthTask", back_populates="task")

    __table_args__ = (
        Index('idx_growth_tasks_status_type', 'status', 'task_type'),
        Index('idx_growth_tasks_sort', 'sort_order'),
    )


class UserGrowthTask(Base):
    __tablename__ = "user_growth_tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    task_id = Column(Integer, ForeignKey("growth_tasks.id"), nullable=False, index=True)

    status = Column(String(50), default=UserGrowthTaskStatus.AVAILABLE, index=True)

    progress_current = Column(Integer, default=0)
    progress_target = Column(Integer, default=1)

    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True, index=True)
    claimed_at = Column(DateTime, nullable=True)

    progress_data = Column(JSON, nullable=True)
    completion_proof = Column(JSON, nullable=True)

    reward_claimed = Column(Boolean, default=False)
    reward_transaction_id = Column(Integer, ForeignKey("stardust_transactions.id"), nullable=True)
    reward_coupon_id = Column(Integer, ForeignKey("user_coupons.id"), nullable=True)
    reward_ticket_id = Column(Integer, ForeignKey("prophecy_tickets.id"), nullable=True)

    is_deleted = Column(Boolean, default=False)

    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)

    user = relationship("User", backref="growth_tasks")
    task = relationship("GrowthTask", back_populates="user_progress")

    __table_args__ = (
        UniqueConstraint('user_id', 'task_id', name='uq_user_growth_task'),
        Index('idx_user_growth_tasks_status', 'user_id', 'status'),
    )


class GrowthTaskLog(Base):
    __tablename__ = "growth_task_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    task_id = Column(Integer, ForeignKey("growth_tasks.id"), nullable=False, index=True)
    user_task_id = Column(Integer, ForeignKey("user_growth_tasks.id"), nullable=True, index=True)

    action_type = Column(String(50), nullable=False, index=True)
    action_description = Column(String(500), nullable=True)

    progress_before = Column(Integer, nullable=True)
    progress_after = Column(Integer, nullable=True)

    ip_address = Column(String(50), nullable=True)
    device_info = Column(String(500), nullable=True)

    extra_metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=_utc_now, index=True)

    user = relationship("User", backref="growth_task_logs")
    task = relationship("GrowthTask")
    user_task = relationship("UserGrowthTask")


class LeaderboardType(str, Enum):
    WEEKLY_ENERGY = "weekly_energy"
    PREDICTION_HIT = "prediction_hit"
    FRIEND_NETWORK = "friend_network"
    WEEKLY_PK = "weekly_pk"


class LeaderboardCycle(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    SEASONAL = "seasonal"


class LeaderboardConfig(Base):
    __tablename__ = "leaderboard_configs"

    id = Column(Integer, primary_key=True, index=True)
    board_key = Column(String(100), unique=True, index=True, nullable=False)
    board_type = Column(String(50), nullable=False, index=True)

    name = Column(String(200), nullable=False)
    display_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    cycle_type = Column(String(30), default=LeaderboardCycle.WEEKLY, index=True)
    rank_count = Column(Integer, default=100)
    display_count = Column(Integer, default=20)

    scoring_rules = Column(JSON, nullable=True)
    eligibility_rules = Column(JSON, nullable=True)

    is_active = Column(Boolean, default=True, index=True)
    sort_order = Column(Integer, default=0)

    icon = Column(String(200), nullable=True)
    banner_url = Column(String(500), nullable=True)

    extra_metadata = Column(JSON, nullable=True)
    is_deleted = Column(Boolean, default=False, index=True)

    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)
    created_by = Column(Integer, nullable=True)

    rewards = relationship("LeaderboardReward", back_populates="config")
    entries = relationship("LeaderboardEntry", back_populates="config")

    __table_args__ = (
        Index('idx_leaderboard_configs_type_cycle', 'board_type', 'cycle_type'),
    )


class LeaderboardReward(Base):
    __tablename__ = "leaderboard_rewards"

    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(Integer, ForeignKey("leaderboard_configs.id"), nullable=False, index=True)

    rank_start = Column(Integer, nullable=False)
    rank_end = Column(Integer, nullable=False)

    reward_type = Column(String(50), default="badge")
    reward_amount = Column(Integer, default=1)
    reward_value = Column(JSON, nullable=True)
    reward_name = Column(String(200), nullable=False)
    reward_description = Column(Text, nullable=True)

    badge_key = Column(String(100), nullable=True)
    badge_name = Column(String(200), nullable=True)
    badge_icon = Column(String(200), nullable=True)
    badge_animation = Column(String(200), nullable=True)

    title_key = Column(String(100), nullable=True)
    title_name = Column(String(200), nullable=True)
    title_color = Column(String(20), nullable=True)

    card_key = Column(String(100), nullable=True)
    card_name = Column(String(200), nullable=True)
    card_rarity = Column(String(20), default="limited")

    is_auto_distribute = Column(Boolean, default=True)
    valid_days = Column(Integer, nullable=True)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)

    config = relationship("LeaderboardConfig", back_populates="rewards")


class LeaderboardEntry(Base):
    __tablename__ = "leaderboard_entries"

    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(Integer, ForeignKey("leaderboard_configs.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    cycle_key = Column(String(50), nullable=False, index=True)
    cycle_start = Column(DateTime, nullable=True)
    cycle_end = Column(DateTime, nullable=True)

    rank = Column(Integer, nullable=True, index=True)
    previous_rank = Column(Integer, nullable=True)

    score = Column(Float, default=0.0, index=True)
    score_display = Column(String(100), nullable=True)
    score_detail = Column(JSON, nullable=True)

    is_eligible = Column(Boolean, default=True)
    ineligibility_reason = Column(String(200), nullable=True)

    reward_claimed = Column(Boolean, default=False)
    reward_claimed_at = Column(DateTime, nullable=True)
    reward_transaction_id = Column(Integer, ForeignKey("stardust_transactions.id"), nullable=True)

    extra_metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)

    config = relationship("LeaderboardConfig", back_populates="entries")
    user = relationship("User", backref="leaderboard_entries")

    __table_args__ = (
        UniqueConstraint('config_id', 'user_id', 'cycle_key', name='uq_leaderboard_entry'),
        Index('idx_leaderboard_entries_cycle_score', 'config_id', 'cycle_key', 'score'),
        Index('idx_leaderboard_entries_cycle_rank', 'config_id', 'cycle_key', 'rank'),
    )


class UserBadge(Base):
    __tablename__ = "user_badges"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    badge_key = Column(String(100), nullable=False, index=True)
    badge_name = Column(String(200), nullable=False)
    badge_description = Column(Text, nullable=True)

    badge_icon = Column(String(200), nullable=True)
    badge_animation = Column(String(200), nullable=True)
    badge_rarity = Column(String(20), default="common")

    source_type = Column(String(50), default="leaderboard")
    source_reference = Column(String(200), nullable=True)

    is_equipped = Column(Boolean, default=False)
    equipped_at = Column(DateTime, nullable=True)

    is_limited = Column(Boolean, default=False)
    valid_from = Column(DateTime, nullable=True)
    valid_until = Column(DateTime, nullable=True, index=True)

    extra_metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)

    user = relationship("User", backref="badges")


class UserTitle(Base):
    __tablename__ = "user_titles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    title_key = Column(String(100), nullable=False, index=True)
    title_name = Column(String(200), nullable=False)
    title_description = Column(Text, nullable=True)

    title_color = Column(String(20), nullable=True)
    title_effect = Column(String(200), nullable=True)

    source_type = Column(String(50), default="leaderboard")
    source_reference = Column(String(200), nullable=True)

    is_equipped = Column(Boolean, default=False)
    equipped_at = Column(DateTime, nullable=True)

    is_limited = Column(Boolean, default=False)
    valid_from = Column(DateTime, nullable=True)
    valid_until = Column(DateTime, nullable=True, index=True)

    extra_metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)

    user = relationship("User", backref="titles")


class VIPPlanType(str, Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"


class VIPPlan(Base):
    __tablename__ = "vip_plans"

    id = Column(Integer, primary_key=True, index=True)
    plan_type = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    price = Column(Integer, nullable=False)
    original_price = Column(Integer, nullable=True)
    duration_days = Column(Integer, nullable=False)

    is_active = Column(Boolean, default=True, index=True)
    sort_order = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class VIPPrivilegeType(str, Enum):
    NO_ADS = "no_ads"
    BLIND_BOX_EXTRA = "blind_box_extra"
    BLIND_BOX_DISCOUNT = "blind_box_discount"
    UNLIMITED_SYNASTRY = "unlimited_synastry"
    ADVANCED_HOROSCOPE = "advanced_horoscope"
    EXCLUSIVE_SKIN = "exclusive_skin"
    SOCIAL_WEIGHT = "social_weight"
    FREE_REPORTS = "free_reports"


class VIPPrivilege(Base):
    __tablename__ = "vip_privileges"

    id = Column(Integer, primary_key=True, index=True)
    privilege_key = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    privilege_type = Column(String(50), nullable=False, index=True)
    value_data = Column(Text, nullable=True)

    icon = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserVIP(Base):
    __tablename__ = "user_vips"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)

    is_vip = Column(Boolean, default=False, index=True)
    plan_type = Column(String(20), nullable=True)

    started_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True, index=True)

    total_subscriptions = Column(Integer, default=0)
    total_paid = Column(Integer, default=0)

    auto_renew_enabled = Column(Boolean, default=False)
    last_renewed_at = Column(DateTime, nullable=True)

    monthly_free_reports_used = Column(Integer, default=0)
    monthly_free_reports_reset_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", backref="vip_status", uselist=False)


class VIPSubscription(Base):
    __tablename__ = "vip_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    subscription_no = Column(String(50), unique=True, nullable=False, index=True)
    plan_type = Column(String(20), nullable=False)

    price = Column(Integer, nullable=False)
    discount_amount = Column(Integer, default=0)

    duration_days = Column(Integer, nullable=False)
    started_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)

    payment_order_id = Column(Integer, ForeignKey("payment_orders.id"), nullable=True)

    status = Column(String(20), default="active", index=True)
    is_auto_renew = Column(Boolean, default=False)

    cancelled_at = Column(DateTime, nullable=True)
    cancel_reason = Column(String(200), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", backref="subscriptions")


class GiftType(str, Enum):
    STARDUST_BOUQUET = "stardust_bouquet"
    ENERGY_CRYSTAL = "energy_crystal"
    LIMITED_CARD_FRAME = "limited_card_frame"


class Gift(Base):
    __tablename__ = "gifts"

    id = Column(Integer, primary_key=True, index=True)
    gift_key = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    gift_type = Column(String(50), nullable=False, index=True)
    price = Column(Integer, nullable=False)
    currency_type = Column(String(20), default="stardust_point")

    rarity = Column(String(20), default="common")
    animation_effect = Column(String(200), nullable=True)
    icon_url = Column(String(500), nullable=True)

    is_active = Column(Boolean, default=True, index=True)
    is_limited = Column(Boolean, default=False)

    stock_remaining = Column(Integer, nullable=True)
    available_from = Column(DateTime, nullable=True)
    available_until = Column(DateTime, nullable=True)

    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GiftTransaction(Base):
    __tablename__ = "gift_transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_no = Column(String(50), unique=True, nullable=False, index=True)

    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    gift_id = Column(Integer, ForeignKey("gifts.id"), nullable=False)
    gift_name = Column(String(100), nullable=False)
    gift_key = Column(String(50), nullable=False)

    quantity = Column(Integer, default=1)
    price_per_unit = Column(Integer, nullable=False)
    total_price = Column(Integer, nullable=False)
    currency_type = Column(String(20), default="stardust_point")

    message = Column(String(500), nullable=True)
    is_anonymous = Column(Boolean, default=False)

    is_displayed = Column(Boolean, default=False)
    displayed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    sender = relationship("User", foreign_keys=[sender_id], backref="gifts_sent")
    receiver = relationship("User", foreign_keys=[receiver_id], backref="gifts_received")
    gift = relationship("Gift", backref="transactions")


class UserGiftDisplay(Base):
    __tablename__ = "user_gift_displays"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    gift_transaction_id = Column(Integer, ForeignKey("gift_transactions.id"), nullable=False)

    gift_key = Column(String(50), nullable=False)
    gift_name = Column(String(100), nullable=False)
    sender_name = Column(String(100), nullable=True)

    is_featured = Column(Boolean, default=False)
    display_order = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="displayed_gifts")


class ReportProductType(str, Enum):
    DEEP_SINGLE = "deep_single"
    SYNASTRY_INTERPRETATION = "synastry_interpretation"
    YEARLY_PREDICTION = "yearly_prediction"
    GROUP_ENERGY = "group_energy"


class ReportProduct(Base):
    __tablename__ = "report_products"

    id = Column(Integer, primary_key=True, index=True)
    product_key = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    product_type = Column(String(50), nullable=False, index=True)

    price = Column(Integer, nullable=False)
    original_price = Column(Integer, nullable=True)
    currency_type = Column(String(20), default="stardust_point")

    report_template = Column(String(100), nullable=True)
    sections_included = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True, index=True)
    sort_order = Column(Integer, default=0)

    icon_url = Column(String(500), nullable=True)
    preview_image_url = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserReportPurchase(Base):
    __tablename__ = "user_report_purchases"

    id = Column(Integer, primary_key=True, index=True)
    purchase_no = Column(String(50), unique=True, nullable=False, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("report_products.id"), nullable=False)

    product_key = Column(String(50), nullable=False)
    product_name = Column(String(200), nullable=False)

    price_paid = Column(Integer, nullable=False)
    currency_type = Column(String(20), default="stardust_point")

    is_free_vip = Column(Boolean, default=False)

    chart_id = Column(Integer, ForeignKey("charts.id"), nullable=True)
    synastry_record_id = Column(Integer, ForeignKey("synastry_records.id"), nullable=True)
    group_matrix_id = Column(Integer, ForeignKey("group_matrices.id"), nullable=True)

    report_data = Column(Text, nullable=True)
    report_pdf_url = Column(String(500), nullable=True)

    view_count = Column(Integer, default=0)
    last_viewed_at = Column(DateTime, nullable=True)

    payment_order_id = Column(Integer, ForeignKey("payment_orders.id"), nullable=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", backref="report_purchases")
    product = relationship("ReportProduct", backref="purchases")


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentType(str, Enum):
    VIP_SUBSCRIPTION = "vip_subscription"
    GIFT_PURCHASE = "gift_purchase"
    REPORT_PURCHASE = "report_purchase"
    STARDUST_RECHARGE = "stardust_recharge"


class PaymentOrder(Base):
    __tablename__ = "payment_orders"

    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String(50), unique=True, nullable=False, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    payment_type = Column(String(50), nullable=False, index=True)
    related_type = Column(String(50), nullable=True)
    related_id = Column(Integer, nullable=True)

    amount = Column(Integer, nullable=False)
    currency = Column(String(10), default="CNY")

    discount_amount = Column(Integer, default=0)
    final_amount = Column(Integer, nullable=False)

    payment_method = Column(String(20), nullable=True)
    payment_platform = Column(String(20), nullable=True)
    platform_order_no = Column(String(100), nullable=True)

    status = Column(String(20), default="pending", index=True)

    paid_at = Column(DateTime, nullable=True)
    expired_at = Column(DateTime, nullable=True, index=True)

    callback_data = Column(Text, nullable=True)
    error_message = Column(String(500), nullable=True)

    is_sandbox = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", backref="payment_orders")


class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_no = Column(String(50), unique=True, nullable=False, index=True)

    order_id = Column(Integer, ForeignKey("payment_orders.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    transaction_type = Column(String(20), nullable=False)

    amount = Column(Integer, nullable=False)
    currency = Column(String(10), default="CNY")

    platform_transaction_no = Column(String(100), nullable=True)

    status = Column(String(20), default="pending", index=True)

    transaction_data = Column(Text, nullable=True)
    error_message = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    order = relationship("PaymentOrder", backref="transactions")


class CheckInRewardType(str, Enum):
    STARDUST_FRAGMENT = "stardust_fragment"
    PROPHECY_TICKET = "prophecy_ticket"
    COUPON = "coupon"
    BENEFIT = "benefit"
    BLIND_BOX = "blind_box"
    VIP_TRIAL = "vip_trial"


class DailyCheckInReward(Base):
    __tablename__ = "daily_checkin_rewards"

    id = Column(Integer, primary_key=True, index=True)

    day_number = Column(Integer, nullable=False, unique=True, index=True)

    reward_type = Column(String(50), nullable=False, index=True)
    reward_amount = Column(Integer, default=1)
    reward_value = Column(String(500), nullable=True)

    reward_name = Column(String(100), nullable=False)
    reward_description = Column(Text, nullable=True)

    icon = Column(String(200), nullable=True)
    rarity = Column(String(20), default="common")

    is_active = Column(Boolean, default=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserCheckInProgress(Base):
    __tablename__ = "user_checkin_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)

    current_streak = Column(Integer, default=0)
    best_streak = Column(Integer, default=0)

    last_checkin_at = Column(DateTime, nullable=True, index=True)
    last_checkin_date = Column(String(20), nullable=True, index=True)

    total_checkins = Column(Integer, default=0)
    total_rewards_claimed = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", backref="checkin_progress", uselist=False)


class DailyCheckInRecord(Base):
    __tablename__ = "daily_checkin_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    checkin_date = Column(String(20), nullable=False, index=True)
    checkin_at = Column(DateTime, default=datetime.utcnow, index=True)

    streak_day_number = Column(Integer, default=1)

    reward_claimed = Column(Boolean, default=True)
    reward_type = Column(String(50), nullable=True)
    reward_amount = Column(Integer, default=0)
    reward_name = Column(String(100), nullable=True)

    ip_address = Column(String(50), nullable=True)
    device_info = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="checkin_records")


class UserCouponType(str, Enum):
    BLIND_BOX_DISCOUNT = "blind_box_discount"
    REPORT_DISCOUNT = "report_discount"
    SYNASTRY_DISCOUNT = "synastry_discount"


class UserCouponStatus(str, Enum):
    ACTIVE = "active"
    USED = "used"
    EXPIRED = "expired"


class UserCoupon(Base):
    __tablename__ = "user_coupons"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    coupon_no = Column(String(50), unique=True, nullable=False, index=True)
    coupon_type = Column(String(50), nullable=False, index=True)

    coupon_name = Column(String(100), nullable=False)
    coupon_description = Column(Text, nullable=True)

    discount_type = Column(String(20), default="percentage")
    discount_value = Column(Float, default=0.5)
    discount_max_amount = Column(Integer, nullable=True)

    min_spend_amount = Column(Integer, default=0)

    source_type = Column(String(50), default="checkin_reward")
    source_reference = Column(String(100), nullable=True)

    status = Column(String(20), default="active", index=True)

    valid_from = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime, nullable=True, index=True)

    used_at = Column(DateTime, nullable=True)
    used_for_type = Column(String(50), nullable=True)
    used_for_id = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", backref="coupons")


class UserBenefitType(str, Enum):
    SYNASTRY_FREE = "synastry_free"
    REPORT_FREE = "report_free"
    CHART_EXPORT_FREE = "chart_export_free"


class UserBenefitStatus(str, Enum):
    ACTIVE = "active"
    USED = "used"
    EXPIRED = "expired"


class UserBenefit(Base):
    __tablename__ = "user_benefits"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    benefit_type = Column(String(50), nullable=False, index=True)
    benefit_name = Column(String(100), nullable=False)
    benefit_description = Column(Text, nullable=True)

    total_count = Column(Integer, default=1)
    used_count = Column(Integer, default=0)
    remaining_count = Column(Integer, default=1)

    source_type = Column(String(50), default="checkin_reward")
    source_reference = Column(String(100), nullable=True)

    valid_from = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime, nullable=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", backref="benefits")


class AdFreePlanType(str, Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class AdFreePlan(Base):
    __tablename__ = "ad_free_plans"

    id = Column(Integer, primary_key=True, index=True)
    plan_key = Column(String(100), unique=True, index=True, nullable=False)
    plan_type = Column(String(50), nullable=False, index=True)

    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    short_description = Column(String(500), nullable=True)

    price = Column(Integer, nullable=False)
    original_price = Column(Integer, nullable=True)
    currency = Column(String(10), default="CNY")

    duration_days = Column(Integer, nullable=False)

    features = Column(JSON, nullable=True)
    restrictions = Column(JSON, nullable=True)

    is_active = Column(Boolean, default=True, index=True)
    sort_order = Column(Integer, default=0)

    icon = Column(String(200), nullable=True)
    badge_icon = Column(String(200), nullable=True)

    is_included_in_vip = Column(Boolean, default=False)
    vip_plan_types = Column(JSON, nullable=True)

    extra_metadata = Column(JSON, nullable=True)
    is_deleted = Column(Boolean, default=False, index=True)

    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)
    created_by = Column(Integer, nullable=True)

    subscriptions = relationship("UserAdFreeSubscription", back_populates="plan")


class UserAdFreeSubscription(Base):
    __tablename__ = "user_ad_free_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    plan_id = Column(Integer, ForeignKey("ad_free_plans.id"), nullable=True, index=True)

    subscription_no = Column(String(50), unique=True, index=True, nullable=False)

    source_type = Column(String(50), default="purchase")
    source_reference = Column(String(200), nullable=True)

    is_vip_included = Column(Boolean, default=False)
    vip_subscription_id = Column(Integer, ForeignKey("vip_subscriptions.id"), nullable=True)

    payment_order_id = Column(Integer, ForeignKey("payment_orders.id"), nullable=True)

    started_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)

    is_active = Column(Boolean, default=True, index=True)
    is_cancelled = Column(Boolean, default=False)
    cancelled_at = Column(DateTime, nullable=True)
    cancel_reason = Column(String(200), nullable=True)

    is_auto_renew = Column(Boolean, default=False)

    extra_metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)

    user = relationship("User", backref="ad_free_subscriptions")
    plan = relationship("AdFreePlan", back_populates="subscriptions")
    vip_subscription = relationship("VIPSubscription")
    payment_order = relationship("PaymentOrder")


class FirstLoginPopup(Base):
    __tablename__ = "first_login_popups"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)

    has_seen = Column(Boolean, default=False, index=True)
    seen_at = Column(DateTime, nullable=True)

    popup_type = Column(String(50), default="growth_task")
    popup_version = Column(String(20), nullable=True)

    dismiss_count = Column(Integer, default=0)
    last_dismissed_at = Column(DateTime, nullable=True)

    should_show_again = Column(Boolean, default=True)

    interaction_data = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)

    user = relationship("User", backref="first_login_popup", uselist=False)


class DungeonTemplate(Base):
    __tablename__ = "dungeon_templates"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(200), nullable=False)
    theme = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    story_intro = Column(Text, nullable=True)

    difficulty = Column(String(20), default="normal")
    min_level = Column(Integer, default=1)
    max_level = Column(Integer, default=100)

    required_elements = Column(Text, nullable=True)

    rewards = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True)
    weight = Column(Integer, default=10)

    created_at = Column(DateTime, default=datetime.utcnow)


class DungeonInstance(Base):
    __tablename__ = "dungeon_instances"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("dungeon_templates.id"), nullable=True)

    name = Column(String(200), nullable=False)
    theme = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    story_content = Column(Text, nullable=True)

    difficulty = Column(String(20), default="normal")

    start_at = Column(DateTime, nullable=False, index=True)
    end_at = Column(DateTime, nullable=False, index=True)

    status = Column(String(20), default="active")

    participant_count = Column(Integer, default=0)
    completion_count = Column(Integer, default=0)

    dungeon_data = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class DungeonParticipation(Base):
    __tablename__ = "dungeon_participations"

    id = Column(Integer, primary_key=True, index=True)
    dungeon_id = Column(Integer, ForeignKey("dungeon_instances.id"), nullable=False, index=True)
    avatar_id = Column(Integer, ForeignKey("avatars.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    status = Column(String(20), default="joined")
    progress = Column(Integer, default=0)

    score = Column(Integer, default=0)
    rewards_earned = Column(Text, nullable=True)

    story_progress = Column(Text, nullable=True)
    choices_made = Column(Text, nullable=True)

    joined_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class EncounterSquare(Base):
    __tablename__ = "encounter_squares"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    area_type = Column(String(50), default="plaza")

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class AvatarPresence(Base):
    __tablename__ = "avatar_presence"

    id = Column(Integer, primary_key=True, index=True)
    avatar_id = Column(Integer, ForeignKey("avatars.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    square_id = Column(Integer, ForeignKey("encounter_squares.id"), nullable=True)

    is_online = Column(Boolean, default=True, index=True)
    is_roaming = Column(Boolean, default=False)

    current_position_x = Column(Float, default=0.0)
    current_position_y = Column(Float, default=0.0)

    last_encounter_at = Column(DateTime, nullable=True)
    last_seen_at = Column(DateTime, default=datetime.utcnow, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EncounterEvent(Base):
    __tablename__ = "encounter_events"

    id = Column(Integer, primary_key=True, index=True)

    avatar_a_id = Column(Integer, ForeignKey("avatars.id"), nullable=False, index=True)
    avatar_b_id = Column(Integer, ForeignKey("avatars.id"), nullable=False, index=True)

    square_id = Column(Integer, ForeignKey("encounter_squares.id"), nullable=True)

    encounter_type = Column(String(50), default="random")

    aspect_relation = Column(String(100), nullable=True)
    zodiac_relation = Column(String(100), nullable=True)
    element_relation = Column(String(50), nullable=True)

    relation_score = Column(Integer, default=50)
    relation_tone = Column(String(20), default="neutral")

    dialogue_content = Column(Text, nullable=True)
    ai_story = Column(Text, nullable=True)

    avatar_a_reaction = Column(String(20), nullable=True)
    avatar_b_reaction = Column(String(20), nullable=True)

    experience_gained = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class AstroBoss(Base):
    __tablename__ = "astro_bosses"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(200), nullable=False)
    title = Column(String(200), nullable=True)

    boss_type = Column(String(50), nullable=False)
    trigger_event = Column(String(100), nullable=False)

    planet_involved = Column(String(50), nullable=True)
    zodiac_sign = Column(String(20), nullable=True)

    description = Column(Text, nullable=True)
    lore = Column(Text, nullable=True)

    base_health = Column(Integer, default=1000)
    base_power = Column(Integer, default=100)

    weakness_element = Column(String(20), nullable=True)
    resistance_element = Column(String(20), nullable=True)

    special_abilities = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class BossFightInstance(Base):
    __tablename__ = "boss_fight_instances"

    id = Column(Integer, primary_key=True, index=True)
    boss_id = Column(Integer, ForeignKey("astro_bosses.id"), nullable=False)

    boss_name = Column(String(200), nullable=False)
    boss_title = Column(String(200), nullable=True)

    trigger_event = Column(String(100), nullable=False)
    planet_involved = Column(String(50), nullable=True)

    current_health = Column(Integer, default=1000)
    max_health = Column(Integer, default=1000)
    current_power = Column(Integer, default=100)

    status = Column(String(20), default="spawned")

    start_at = Column(DateTime, nullable=False, index=True)
    end_at = Column(DateTime, nullable=True)

    required_elements = Column(Text, nullable=True)

    total_damage_dealt = Column(Integer, default=0)
    participant_count = Column(Integer, default=0)

    fight_data = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BossTeam(Base):
    __tablename__ = "boss_teams"

    id = Column(Integer, primary_key=True, index=True)
    fight_id = Column(Integer, ForeignKey("boss_fight_instances.id"), nullable=False, index=True)
    leader_id = Column(Integer, ForeignKey("avatars.id"), nullable=False)

    team_name = Column(String(100), nullable=False, default="星之队")

    fire_member_id = Column(Integer, ForeignKey("avatars.id"), nullable=True)
    earth_member_id = Column(Integer, ForeignKey("avatars.id"), nullable=True)
    air_member_id = Column(Integer, ForeignKey("avatars.id"), nullable=True)
    water_member_id = Column(Integer, ForeignKey("avatars.id"), nullable=True)

    has_fire = Column(Boolean, default=False)
    has_earth = Column(Boolean, default=False)
    has_air = Column(Boolean, default=False)
    has_water = Column(Boolean, default=False)

    status = Column(String(20), default="recruiting")

    damage_contributed = Column(Integer, default=0)
    rewards_earned = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BossFightLog(Base):
    __tablename__ = "boss_fight_logs"

    id = Column(Integer, primary_key=True, index=True)
    fight_id = Column(Integer, ForeignKey("boss_fight_instances.id"), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("boss_teams.id"), nullable=True)
    avatar_id = Column(Integer, ForeignKey("avatars.id"), nullable=False)

    action_type = Column(String(50), nullable=False)
    element_used = Column(String(20), nullable=True)

    damage_dealt = Column(Integer, default=0)
    is_critical = Column(Boolean, default=False)

    description = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
