from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    charts = relationship("Chart", back_populates="user", cascade="all, delete-orphan")


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


class CollectivePrediction(Base):
    __tablename__ = "collective_predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    prediction_date = Column(String(20), nullable=False, index=True)
    target_date = Column(String(20), nullable=False, index=True)
    
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    prediction_type = Column(String(50), default="mood", index=True)
    
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
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PredictionVote(Base):
    __tablename__ = "prediction_votes"
    
    id = Column(Integer, primary_key=True, index=True)
    prediction_id = Column(Integer, ForeignKey("collective_predictions.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    selected_option = Column(String(100), nullable=False)
    confidence = Column(Integer, default=50)
    
    stardust_bet = Column(Integer, default=0)
    
    is_correct = Column(Boolean, nullable=True)
    reward_earned = Column(Integer, default=0)
    reward_claimed = Column(Boolean, default=False)
    
    vote_data = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        dict(extend_existing=True),
    )


class StarDustTransaction(Base):
    __tablename__ = "stardust_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    transaction_type = Column(String(50), nullable=False, index=True)
    
    amount = Column(Integer, default=0)
    balance_before = Column(Integer, default=0)
    balance_after = Column(Integer, default=0)
    
    related_type = Column(String(50), nullable=True)
    related_id = Column(Integer, nullable=True)
    
    description = Column(String(500), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
