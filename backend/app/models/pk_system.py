from enum import Enum
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float, UniqueConstraint, JSON, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base


def _utc_now():
    return datetime.now(timezone.utc)


class PKMatchType(str, Enum):
    RANDOM = "random"
    FRIEND = "friend"


class PKMatchStatus(str, Enum):
    WAITING = "waiting"
    MATCHED = "matched"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class PKBattleResult(str, Enum):
    WIN = "win"
    LOSE = "lose"
    DRAW = "draw"


class EnergyBoostType(str, Enum):
    DOUBLE_ENERGY = "double_energy"
    CRITICAL_HIT = "critical_hit"
    LUCKY_BLESSING = "lucky_blessing"


class PKInviteStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class UserDailyPK(Base):
    __tablename__ = "user_daily_pk"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    battle_date = Column(String(20), nullable=False, index=True)

    free_challenges_used = Column(Integer, default=0)
    free_challenges_total = Column(Integer, default=3)

    paid_challenges_used = Column(Integer, default=0)
    paid_challenges_purchased = Column(Integer, default=0)

    daily_wins = Column(Integer, default=0)
    daily_losses = Column(Integer, default=0)
    daily_draws = Column(Integer, default=0)

    fragments_earned = Column(Integer, default=0)
    fragments_lost = Column(Integer, default=0)

    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)

    user = relationship("User", backref="daily_pk_records")

    __table_args__ = (
        UniqueConstraint('user_id', 'battle_date', name='uq_user_daily_pk'),
        Index('idx_user_daily_pk_date', 'user_id', 'battle_date'),
    )

    @property
    def total_challenges_available(self) -> int:
        free_remaining = max(0, self.free_challenges_total - self.free_challenges_used)
        paid_remaining = max(0, self.paid_challenges_purchased - self.paid_challenges_used)
        return free_remaining + paid_remaining

    @property
    def can_challenge(self) -> bool:
        return self.total_challenges_available > 0

    def use_challenge(self) -> bool:
        if not self.can_challenge:
            return False

        free_remaining = max(0, self.free_challenges_total - self.free_challenges_used)
        if free_remaining > 0:
            self.free_challenges_used += 1
        else:
            self.paid_challenges_used += 1
        return True


class EnergyBoost(Base):
    __tablename__ = "energy_boosts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    boost_type = Column(String(50), nullable=False, index=True)
    boost_name = Column(String(100), nullable=False)
    boost_description = Column(Text, nullable=True)

    energy_multiplier = Column(Float, default=1.0)
    critical_hit_chance = Column(Float, default=0.0)
    protection_rate = Column(Float, default=0.0)

    is_active = Column(Boolean, default=True, index=True)
    valid_from = Column(DateTime, nullable=False, default=_utc_now)
    valid_until = Column(DateTime, nullable=False, index=True)

    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)

    user = relationship("User", backref="energy_boosts")

    __table_args__ = (
        Index('idx_active_boosts', 'user_id', 'is_active', 'valid_until'),
    )


class PKMatchInvite(Base):
    __tablename__ = "pk_match_invites"

    id = Column(Integer, primary_key=True, index=True)
    invite_code = Column(String(20), unique=True, nullable=False, index=True)

    inviter_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    invitee_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    match_id = Column(Integer, ForeignKey("pk_matches.id"), nullable=True)

    wager_fragments = Column(Integer, default=10)
    
    status = Column(String(30), default=PKInviteStatus.PENDING.value, index=True)

    accepted_at = Column(DateTime, nullable=True)
    declined_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False, index=True)

    created_at = Column(DateTime, default=_utc_now, index=True)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)

    inviter = relationship("User", foreign_keys=[inviter_id], backref="pk_invites_sent")
    invitee = relationship("User", foreign_keys=[invitee_id], backref="pk_invites_received")
    match = relationship("PKMatch", backref="invite_record")

    __table_args__ = (
        Index('idx_pending_invites', 'inviter_id', 'status', 'expires_at'),
        Index('idx_invitee_invites', 'invitee_id', 'status'),
    )
    
    @property
    def is_accepted(self) -> bool:
        return self.status == PKInviteStatus.ACCEPTED.value
    
    @property
    def is_declined(self) -> bool:
        return self.status == PKInviteStatus.DECLINED.value
    
    @property
    def is_expired(self) -> bool:
        return self.status == PKInviteStatus.EXPIRED.value


class PKMatch(Base):
    __tablename__ = "pk_matches"

    id = Column(Integer, primary_key=True, index=True)
    match_no = Column(String(50), unique=True, nullable=False, index=True)

    match_type = Column(String(20), default=PKMatchType.RANDOM.value, index=True)
    status = Column(String(30), default=PKMatchStatus.WAITING.value, index=True)

    challenger_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    defender_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    challenger_energy = Column(Float, default=0.0)
    defender_energy = Column(Float, default=0.0)

    challenger_boost_id = Column(Integer, ForeignKey("energy_boosts.id"), nullable=True)
    defender_boost_id = Column(Integer, ForeignKey("energy_boosts.id"), nullable=True)

    wager_fragments = Column(Integer, default=10)
    winner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    loser_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    result = Column(String(20), nullable=True)
    fragments_transferred = Column(Integer, default=0)

    is_draw = Column(Boolean, default=False)
    is_challenger_critical = Column(Boolean, default=False)
    is_defender_critical = Column(Boolean, default=False)

    match_started_at = Column(DateTime, nullable=True)
    match_completed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True, index=True)

    match_data = Column(JSON, nullable=True)
    result_detail = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=_utc_now, index=True)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)

    challenger = relationship("User", foreign_keys=[challenger_id], backref="pk_matches_as_challenger")
    defender = relationship("User", foreign_keys=[defender_id], backref="pk_matches_as_defender")
    winner = relationship("User", foreign_keys=[winner_id], backref="pk_wins")
    loser = relationship("User", foreign_keys=[loser_id], backref="pk_losses")

    challenger_boost = relationship("EnergyBoost", foreign_keys=[challenger_boost_id])
    defender_boost = relationship("EnergyBoost", foreign_keys=[defender_boost_id])

    __table_args__ = (
        Index('idx_pk_matches_challenger', 'challenger_id', 'status', 'created_at'),
        Index('idx_pk_matches_defender', 'defender_id', 'status', 'created_at'),
        Index('idx_pk_matches_status', 'status', 'created_at'),
        Index('idx_pk_matches_expires', 'status', 'expires_at'),
    )


class UserEnergySnapshot(Base):
    __tablename__ = "user_energy_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    snapshot_date = Column(String(20), nullable=False, index=True)

    daily_horoscope_score = Column(Integer, default=0)
    daily_horoscope_detail = Column(JSON, nullable=True)

    task_completion_score = Column(Integer, default=0)
    task_completion_detail = Column(JSON, nullable=True)

    total_energy_score = Column(Float, default=0.0)
    energy_boost_applied = Column(Float, default=1.0)

    pk_matches_count = Column(Integer, default=0)
    pk_wins = Column(Integer, default=0)

    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)

    user = relationship("User", backref="energy_snapshots")

    __table_args__ = (
        UniqueConstraint('user_id', 'snapshot_date', name='uq_user_energy_snapshot'),
        Index('idx_energy_snapshot_date', 'user_id', 'snapshot_date'),
    )


class PKTransaction(Base):
    __tablename__ = "pk_transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_no = Column(String(50), unique=True, nullable=False, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    match_id = Column(Integer, ForeignKey("pk_matches.id"), nullable=True)

    transaction_type = Column(String(50), nullable=False, index=True)
    transaction_subtype = Column(String(50), nullable=True)

    currency_type = Column(String(20), default="fragment")
    amount = Column(Integer, default=0)

    balance_before = Column(Integer, default=0)
    balance_after = Column(Integer, default=0)

    related_match_no = Column(String(50), nullable=True)
    related_opponent_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    is_wager = Column(Boolean, default=False)
    is_winnings = Column(Boolean, default=False)
    is_loss = Column(Boolean, default=False)

    description = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=_utc_now, index=True)

    user = relationship("User", primaryjoin="PKTransaction.user_id == User.id", backref="pk_transactions")
    match = relationship("PKMatch", backref="transactions")
    opponent = relationship("User", primaryjoin="PKTransaction.related_opponent_id == User.id")

    __table_args__ = (
        Index('idx_pk_transactions_user', 'user_id', 'created_at'),
        Index('idx_pk_transactions_match', 'match_id'),
    )


class PKChallengePurchase(Base):
    __tablename__ = "pk_challenge_purchases"

    id = Column(Integer, primary_key=True, index=True)
    purchase_no = Column(String(50), unique=True, nullable=False, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    challenges_purchased = Column(Integer, default=1)
    price_per_challenge = Column(Integer, default=0)
    total_price = Column(Integer, default=0)

    currency_type = Column(String(20), default="point")

    payment_order_id = Column(Integer, ForeignKey("payment_orders.id"), nullable=True)
    is_paid = Column(Boolean, default=False)
    paid_at = Column(DateTime, nullable=True)

    purchase_date = Column(String(20), nullable=False, index=True)

    created_at = Column(DateTime, default=_utc_now, index=True)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)

    user = relationship("User", backref="pk_challenge_purchases")

    __table_args__ = (
        Index('idx_pk_purchases_user', 'user_id', 'purchase_date'),
    )


class UserPKStats(Base):
    __tablename__ = "user_pk_stats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)

    total_matches = Column(Integer, default=0)
    total_wins = Column(Integer, default=0)
    total_losses = Column(Integer, default=0)
    total_draws = Column(Integer, default=0)

    total_fragments_won = Column(Integer, default=0)
    total_fragments_lost = Column(Integer, default=0)
    net_fragments = Column(Integer, default=0)

    current_win_streak = Column(Integer, default=0)
    best_win_streak = Column(Integer, default=0)

    highest_energy_used = Column(Float, default=0.0)
    highest_wager_won = Column(Integer, default=0)

    random_match_count = Column(Integer, default=0)
    friend_match_count = Column(Integer, default=0)

    last_match_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)

    user = relationship("User", backref="pk_stats", uselist=False)

    @property
    def win_rate(self) -> float:
        if self.total_matches == 0:
            return 0.0
        return round(self.total_wins / self.total_matches * 100, 2)

    @property
    def total_played(self) -> int:
        return self.total_wins + self.total_losses + self.total_draws
