from enum import Enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


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


class PastLifeTheme(str, Enum):
    WARRIOR = "warrior"
    SCHOLAR = "scholar"
    ARTIST = "artist"
    ROYAL = "royal"
    MONK = "monk"
    MERCHANT = "merchant"
    HEALER = "healer"
    ADVENTURER = "adventurer"


class PastLifeRelationshipType(str, Enum):
    LOVERS = "lovers"
    MENTOR = "mentor"
    RIVAL = "rival"
    SOULMATE = "soulmate"
    FAMILY = "family"
    COMRADE = "comrade"
    STRANGER = "stranger"


class PastLifeRecord(Base):
    __tablename__ = "past_life_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    chart_id = Column(Integer, ForeignKey("charts.id"), nullable=True, index=True)

    name = Column(String(100), nullable=True)
    theme = Column(String(50), nullable=True)
    theme_name = Column(String(100), nullable=True)

    core_planet = Column(String(50), nullable=True)
    core_sign = Column(String(50), nullable=True)
    core_house = Column(Integer, nullable=True)

    basic_story = Column(Text, nullable=True)
    basic_story_short = Column(String(500), nullable=True)

    deep_story = Column(Text, nullable=True)
    deep_story_details = Column(Text, nullable=True)

    is_paid = Column(Boolean, default=False)
    payment_order_id = Column(Integer, nullable=True)

    share_code = Column(String(20), unique=True, index=True, nullable=True)
    share_count = Column(Integer, default=0)

    story_metadata = Column(Text, nullable=True)

    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", backref="past_lives")


class PastLifeSynastryRecord(Base):
    __tablename__ = "past_life_synastry_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    synastry_record_id = Column(Integer, ForeignKey("synastry_records.id"), nullable=True, index=True)

    person_a_name = Column(String(100), nullable=True)
    person_b_name = Column(String(100), nullable=True)

    relationship_type = Column(String(50), nullable=True)
    relationship_name = Column(String(100), nullable=True)

    key_aspect = Column(String(200), nullable=True)
    dominant_element = Column(String(20), nullable=True)

    basic_story = Column(Text, nullable=True)
    basic_story_short = Column(String(500), nullable=True)

    deep_story = Column(Text, nullable=True)
    deep_story_details = Column(Text, nullable=True)

    is_paid = Column(Boolean, default=False)
    payment_order_id = Column(Integer, nullable=True)

    share_code = Column(String(20), unique=True, index=True, nullable=True)
    share_count = Column(Integer, default=0)

    story_metadata = Column(Text, nullable=True)

    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", backref="past_life_synastries")


class StoryCardRarity(str, Enum):
    COMMON = "common"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class StoryCardTemplate(str, Enum):
    SOULMATE_KNIGHT = "soulmate_knight"
    CONFIDANT = "confidant"
    RIVAL_TURNS_FRIEND = "rival_turns_friend"
    STAR_CROSSED_LOVERS = "star_crossed_lovers"
    MENTOR_STUDENT = "mentor_student"
    COMRADES_IN_ARMS = "comrades_in_arms"
    FAMILIAR_STRANGERS = "familiar_strangers"
    MYSTIC_BOND = "mystic_bond"


class StoryCard(Base):
    __tablename__ = "story_cards"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    synastry_record_id = Column(Integer, ForeignKey("synastry_records.id"), nullable=True, index=True)
    past_life_synastry_id = Column(Integer, ForeignKey("past_life_synastry_records.id"), nullable=True, index=True)

    card_template = Column(String(50), nullable=False, default=StoryCardTemplate.SOULMATE_KNIGHT)
    template_name = Column(String(100), nullable=True)

    person_a_name = Column(String(100), nullable=True)
    person_b_name = Column(String(100), nullable=True)
    target_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    headline = Column(String(200), nullable=False)
    subheadline = Column(String(300), nullable=True)
    story_content = Column(Text, nullable=False)
    story_short = Column(String(500), nullable=True)

    compatibility_score = Column(Integer, nullable=True)
    match_type = Column(String(50), nullable=True)
    dominant_element = Column(String(20), nullable=True)
    key_aspect = Column(String(200), nullable=True)

    rarity = Column(String(20), default=StoryCardRarity.COMMON, index=True)
    rarity_name = Column(String(50), nullable=True)

    is_mounted = Column(Boolean, default=False, index=True)
    mounted_at = Column(DateTime, nullable=True)

    is_public = Column(Boolean, default=False, index=True)
    share_code = Column(String(20), unique=True, index=True, nullable=True)
    share_count = Column(Integer, default=0)

    card_metadata = Column(Text, nullable=True)

    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", foreign_keys=[user_id], backref="story_cards")
    target_user = relationship("User", foreign_keys=[target_user_id])
    synastry_record = relationship("SynastryRecord", backref="story_cards")
    past_life_synastry = relationship("PastLifeSynastryRecord", backref="story_cards")
