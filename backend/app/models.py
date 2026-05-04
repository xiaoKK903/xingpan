from enum import Enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float, UniqueConstraint, JSON, Numeric, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


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


class Chart(Base):
    __tablename__ = "charts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    name = Column(String(100), nullable=True)
    birth_date = Column(String(20), nullable=False)
    birth_time = Column(String(10), nullable=False)
    birth_place = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    house_system = Column(String(20), nullable=False, default="placidus")
    
    chart_data = Column(Text, nullable=False)
    
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="charts")


class SynastryRecord(Base):
    __tablename__ = "synastry_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    name = Column(String(100), nullable=True)
    
    person_a_name = Column(String(100), nullable=True)
    person_a_birth_date = Column(String(20), nullable=False)
    person_a_birth_time = Column(String(10), nullable=False)
    person_a_birth_place = Column(String(100), nullable=True)
    person_a_latitude = Column(Float, nullable=False)
    person_a_longitude = Column(Float, nullable=False)
    
    person_b_name = Column(String(100), nullable=True)
    person_b_birth_date = Column(String(20), nullable=False)
    person_b_birth_time = Column(String(10), nullable=False)
    person_b_birth_place = Column(String(100), nullable=True)
    person_b_latitude = Column(Float, nullable=False)
    person_b_longitude = Column(Float, nullable=False)
    
    synastry_data = Column(Text, nullable=False)
    analysis_data = Column(Text, nullable=True)
    share_code = Column(String(20), unique=True, index=True, nullable=True)
    
    total_score = Column(Integer, nullable=True)
    
    is_deleted = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GroupMatrix(Base):
    __tablename__ = "group_matrices"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    name = Column(String(200), nullable=False, default="未命名群组")
    description = Column(Text, nullable=True)
    group_type = Column(String(50), nullable=False, default="other")
    
    matrix_data = Column(Text, nullable=False)
    relationship_map = Column(Text, nullable=True)
    roles_data = Column(Text, nullable=True)
    scenario_simulations = Column(Text, nullable=True)
    
    is_deleted = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)
    share_code = Column(String(20), unique=True, index=True, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    members = relationship("GroupMember", back_populates="group_matrix", cascade="all, delete-orphan")


class GroupMember(Base):
    __tablename__ = "group_members"
    
    id = Column(Integer, primary_key=True, index=True)
    group_matrix_id = Column(Integer, ForeignKey("group_matrices.id"), nullable=False, index=True)
    
    name = Column(String(100), nullable=False)
    birth_date = Column(String(20), nullable=False)
    birth_time = Column(String(10), nullable=False)
    birth_place = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    is_core = Column(Boolean, default=False)
    weight = Column(Float, default=1.0)
    
    chart_data = Column(Text, nullable=True)
    role = Column(String(50), nullable=True)
    role_score = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    group_matrix = relationship("GroupMatrix", back_populates="members")


class OnlineUserPresence(Base):
    __tablename__ = "online_user_presence"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    session_id = Column(String(100), nullable=True, index=True)
    last_seen_at = Column(DateTime, default=datetime.utcnow, index=True)
    is_online = Column(Boolean, default=True, index=True)
    
    last_city = Column(String(100), nullable=True)
    last_latitude = Column(Float, nullable=True)
    last_longitude = Column(Float, nullable=True)
    
    primary_chart_id = Column(Integer, ForeignKey("charts.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CommunityEnergySnapshot(Base):
    __tablename__ = "community_energy_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    
    snapshot_type = Column(String(20), default="realtime", index=True)
    scope = Column(String(20), default="global", index=True)
    
    scope_city = Column(String(100), nullable=True)
    scope_latitude = Column(Float, nullable=True)
    scope_longitude = Column(Float, nullable=True)
    scope_radius_km = Column(Float, default=50.0)
    
    total_users = Column(Integer, default=0)
    online_users = Column(Integer, default=0)
    
    planet_distribution = Column(Text, nullable=True)
    aspect_distribution = Column(Text, nullable=True)
    
    overall_energy_score = Column(Float, default=50.0)
    overall_mood = Column(String(20), default="neutral")
    
    dimension_energies = Column(Text, nullable=True)
    
    dominant_planets = Column(Text, nullable=True)
    dominant_aspects = Column(Text, nullable=True)
    
    moon_phase = Column(String(50), nullable=True)
    mercury_status = Column(String(50), nullable=True)
    
    triggered_mission_ids = Column(Text, nullable=True)
    
    snapshot_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class EnergyMission(Base):
    __tablename__ = "energy_missions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    mission_type = Column(String(50), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    trigger_condition = Column(Text, nullable=True)
    trigger_aspect = Column(String(100), nullable=True)
    trigger_planet = Column(String(50), nullable=True)
    
    target_dimension = Column(String(50), nullable=True)
    
    difficulty = Column(String(20), default="medium")
    base_reward = Column(Integer, default=10)
    max_participants = Column(Integer, default=100)
    
    start_at = Column(DateTime, nullable=True, index=True)
    end_at = Column(DateTime, nullable=True, index=True)
    duration_minutes = Column(Integer, default=30)
    
    status = Column(String(20), default="pending", index=True)
    
    participant_count = Column(Integer, default=0)
    energy_contributed = Column(Float, default=0.0)
    
    mission_data = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MissionParticipation(Base):
    __tablename__ = "mission_participations"
    
    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(Integer, ForeignKey("energy_missions.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    status = Column(String(20), default="joined", index=True)
    
    energy_contributed = Column(Float, default=0.0)
    contribution_type = Column(String(50), nullable=True)
    
    reward_earned = Column(Integer, default=0)
    reward_claimed = Column(Boolean, default=False)
    
    joined_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    participation_data = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class EnergyContribution(Base):
    __tablename__ = "energy_contributions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    contribution_type = Column(String(50), nullable=False, index=True)
    
    planet_type = Column(String(50), nullable=True)
    planet_name = Column(String(50), nullable=True)
    
    energy_amount = Column(Float, default=0.0)
    energy_multiplier = Column(Float, default=1.0)
    
    target_scope = Column(String(20), default="global")
    target_dimension = Column(String(50), nullable=True)
    
    duration_minutes = Column(Integer, default=30)
    expires_at = Column(DateTime, nullable=True, index=True)
    
    is_active = Column(Boolean, default=True, index=True)
    
    cost_stardust = Column(Integer, default=0)
    
    contribution_data = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


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


class TransitEventMonitor(Base):
    __tablename__ = "transit_event_monitors"
    
    id = Column(Integer, primary_key=True, index=True)
    
    event_type = Column(String(50), nullable=False, index=True)
    event_name = Column(String(200), nullable=False)
    
    planet = Column(String(50), nullable=True)
    zodiac_sign = Column(String(20), nullable=True)
    aspect = Column(String(50), nullable=True)
    
    is_retrograde = Column(Boolean, default=False)
    is_major_event = Column(Boolean, default=False)
    
    trigger_action = Column(String(50), default="spawn_boss")
    boss_template_id = Column(Integer, ForeignKey("astro_bosses.id"), nullable=True)
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class ElementalCycle(Base):
    __tablename__ = "elemental_cycles"
    
    id = Column(Integer, primary_key=True, index=True)
    
    cycle_type = Column(String(50), nullable=False)
    dominant_element = Column(String(20), nullable=False)
    
    start_at = Column(DateTime, nullable=False, index=True)
    end_at = Column(DateTime, nullable=False, index=True)
    
    effect_multiplier = Column(Float, default=1.0)
    affected_elements = Column(Text, nullable=True)
    
    is_active = Column(Boolean, default=True, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class ResonancePoolSnapshot(Base):
    __tablename__ = "resonance_pool_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    
    total_energy = Column(Float, default=0.0)
    current_tier = Column(String(20), default="dormant", index=True)
    tier_progress = Column(Float, default=0.0)
    
    element_distribution = Column(Text, nullable=True)
    
    nebula_color = Column(String(20), default="#1F2937")
    nebula_intensity = Column(Float, default=0.1)
    
    active_effects = Column(Text, nullable=True)
    
    snapshot_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ResonanceContribution(Base):
    __tablename__ = "resonance_contributions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    element = Column(String(20), nullable=False, index=True)
    
    planet_name = Column(String(50), nullable=True)
    planet_sign = Column(String(50), nullable=True)
    
    fragment_cost = Column(Integer, default=0)
    base_energy = Column(Float, default=0.0)
    total_energy = Column(Float, default=0.0)
    energy_multiplier = Column(Float, default=1.0)
    
    dignity_score = Column(Integer, default=0)
    is_stellium = Column(Boolean, default=False)
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class ProphecyTicket(Base):
    __tablename__ = "prophecy_tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    ticket_type = Column(String(50), default="resonance_reward", index=True)
    source_snapshot_id = Column(Integer, ForeignKey("resonance_pool_snapshots.id"), nullable=True)
    
    is_used = Column(Boolean, default=False, index=True)
    used_at = Column(DateTime, nullable=True)
    used_for = Column(String(100), nullable=True)
    
    valid_from = Column(DateTime, nullable=True)
    valid_until = Column(DateTime, nullable=True, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class UserElementProfile(Base):
    __tablename__ = "user_element_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True, unique=True)
    chart_id = Column(Integer, ForeignKey("charts.id"), nullable=True, index=True)
    
    fire_score = Column(Float, default=0.0)
    earth_score = Column(Float, default=0.0)
    air_score = Column(Float, default=0.0)
    water_score = Column(Float, default=0.0)
    
    fire_level = Column(String(20), default="balanced")
    earth_level = Column(String(20), default="balanced")
    air_level = Column(String(20), default="balanced")
    water_level = Column(String(20), default="balanced")
    
    total_score = Column(Float, default=0.0)
    average_score = Column(Float, default=25.0)
    
    dominant_element = Column(String(20), nullable=True)
    secondary_dominant = Column(String(20), nullable=True)
    primary_deficiency = Column(String(20), nullable=True)
    
    has_deficiency = Column(Boolean, default=False)
    deficiency_count = Column(Integer, default=0)
    
    element_data = Column(Text, nullable=True)
    
    last_analyzed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserEnergyTag(Base):
    __tablename__ = "user_energy_tags"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    profile_id = Column(Integer, ForeignKey("user_element_profiles.id"), nullable=True, index=True)
    
    tag_key = Column(String(100), nullable=False, index=True)
    tag_name = Column(String(100), nullable=False)
    tag_category = Column(String(50), default="element", index=True)
    
    tag_score = Column(Float, default=1.0)
    description = Column(String(500), nullable=True)
    
    source_type = Column(String(50), default="analysis")
    source_reference = Column(String(200), nullable=True)
    
    is_active = Column(Boolean, default=True, index=True)
    
    first_seen_at = Column(DateTime, default=datetime.utcnow)
    last_seen_at = Column(DateTime, default=datetime.utcnow)
    occurrence_count = Column(Integer, default=1)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


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


class PhotocardRecord(Base):
    __tablename__ = "photocard_records"
    
    id = Column(Integer, primary_key=True, index=True)
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    synastry_record_id = Column(Integer, ForeignKey("synastry_records.id"), nullable=True)
    
    card_id = Column(String(100), unique=True, nullable=False)
    card_type = Column(String(50), default="default")
    card_name = Column(String(100), nullable=True)
    
    person_a_name = Column(String(100), nullable=True)
    person_b_name = Column(String(100), nullable=True)
    
    rarity = Column(String(20), default="common")
    is_limited_edition = Column(Boolean, default=False)
    
    card_design_data = Column(Text, nullable=True)
    card_svg = Column(Text, nullable=True)
    
    compatibility_score = Column(Integer, nullable=True)
    primary_highlight = Column(String(200), nullable=True)
    
    share_code = Column(String(50), unique=True, nullable=True, index=True)
    share_count = Column(Integer, default=0)
    
    is_saved = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", backref="photocards")
    synastry_record = relationship("SynastryRecord", backref="photocards")


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


def _utc_now():
    return datetime.now(timezone.utc)


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


class TimeCapsuleNotificationType(str, Enum):
    UNLOCK_REMINDER = "unlock_reminder"
    CAPSULE_UNLOCKED = "capsule_unlocked"
    CAPSULE_RECEIVED = "capsule_received"


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
