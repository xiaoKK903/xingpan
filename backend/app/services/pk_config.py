import logging
import json
import uuid
import random
import secrets
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum

from app.models import (
    User, UserDailyPK, EnergyBoost, PKMatchInvite, PKMatch,
    UserEnergySnapshot, PKTransaction, PKChallengePurchase, UserPKStats,
    PKMatchType, PKMatchStatus, PKBattleResult, EnergyBoostType, PKInviteStatus,
    DailyCheckInRecord, UserGrowthTask, GrowthTask, UserGrowthTaskStatus,
    Chart, StarDustTransaction, LeaderboardType, LeaderboardCycle
)

from app.services.leaderboard_service import leaderboard_service

logger = logging.getLogger(__name__)


DEFAULT_CONFIG = {
    "free_challenges_per_day": 3,
    "wager_min_fragments": 10,
    "wager_max_fragments": 500,
    "winner_fraction_rate": 0.8,
    "invite_expiry_minutes": 10,
    "match_waiting_timeout_seconds": 60,
    "horoscope_weight": 0.6,
    "task_weight": 0.4,
    "critical_hit_base_chance": 0.05,
    "critical_hit_multiplier": 1.5,
    "challenge_purchase_price_points": 50,
    "double_energy_price_points": 100,
}


class PKBattleErrorCode(str, Enum):
    USER_NOT_FOUND = "USER_NOT_FOUND"
    NO_CHALLENGES_LEFT = "NO_CHALLENGES_LEFT"
    INSUFFICIENT_FRAGMENTS = "INSUFFICIENT_FRAGMENTS"
    INVALID_WAGER = "INVALID_WAGER"
    MATCH_NOT_FOUND = "MATCH_NOT_FOUND"
    MATCH_NOT_IN_PROGRESS = "MATCH_NOT_IN_PROGRESS"
    OPPONENT_NOT_FOUND = "OPPONENT_NOT_FOUND"
    INVITE_NOT_FOUND = "INVITE_NOT_FOUND"
    INVITE_EXPIRED = "INVITE_EXPIRED"
    INVITE_ALREADY_ACCEPTED = "INVITE_ALREADY_ACCEPTED"
    CANNOT_INVITE_SELF = "CANNOT_INVITE_SELF"
    NO_MATCHES_AVAILABLE = "NO_MATCHES_AVAILABLE"
    MATCH_ALREADY_COMPLETED = "MATCH_ALREADY_COMPLETED"
    BOOST_NOT_FOUND = "BOOST_NOT_FOUND"
    BOOST_EXPIRED = "BOOST_EXPIRED"
    INSUFFICIENT_POINTS = "INSUFFICIENT_POINTS"
    PURCHASE_FAILED = "PURCHASE_FAILED"


def generate_unique_no(prefix: str = "PK") -> str:
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    random_part = uuid.uuid4().hex[:8].upper()
    return f"{prefix}{timestamp}{random_part}"


def generate_invite_code() -> str:
    return secrets.token_urlsafe(6)[:10].upper()


def get_today_str() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")
