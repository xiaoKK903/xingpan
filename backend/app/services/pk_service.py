import logging
import json
import uuid
import random
import secrets
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import and_, func, or_

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


class PKEnergyEngine:
    """
    PK能量计算引擎
    负责计算用户当日能量值，基于：
    1. 每日星运分值
    2. 日常任务完成度
    """

    def __init__(self, config: Dict = None):
        self.config = config or DEFAULT_CONFIG

    def get_user_horoscope_score(
        self,
        db: Session,
        user_id: int,
        date_str: str = None
    ) -> Tuple[int, Dict[str, Any]]:
        """
        获取用户当日星运分值
        模拟基于星座的运势分数，范围 0-100
        """
        if date_str is None:
            date_str = get_today_str()

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return 50, {}

        charts = db.query(Chart).filter(
            Chart.user_id == user_id,
            Chart.is_deleted == False
        ).order_by(Chart.created_at.desc()).first()

        sun_sign = None
        if charts:
            try:
                chart_data = json.loads(charts.chart_data)
                sun_sign = chart_data.get('sun_sign', {}).get('sign')
            except Exception:
                pass

        seed = self._generate_seed(user_id, date_str, sun_sign)

        base_score = 50 + self._pseudo_random(seed, -20, 20, 0)

        checkin = db.query(DailyCheckInRecord).filter(
            DailyCheckInRecord.user_id == user_id,
            DailyCheckInRecord.checkin_date == date_str
        ).first()
        if checkin:
            base_score += 10

        final_score = max(0, min(100, base_score))

        detail = {
            "base_score": base_score,
            "checkin_bonus": 10 if checkin else 0,
            "sun_sign_used": sun_sign is not None,
            "date": date_str
        }

        return final_score, detail

    def get_user_task_completion_score(
        self,
        db: Session,
        user_id: int,
        date_str: str = None
    ) -> Tuple[int, Dict[str, Any]]:
        """
        获取用户日常任务完成度分数
        基于今日完成的任务数量计算，范围 0-100
        """
        if date_str is None:
            date_str = get_today_str()

        today = datetime.utcnow().date()
        day_start = datetime(today.year, today.month, today.day)
        day_end = day_start + timedelta(days=1)

        task_count = db.query(UserGrowthTask).filter(
            UserGrowthTask.user_id == user_id,
            UserGrowthTask.status == UserGrowthTaskStatus.COMPLETED.value,
            UserGrowthTask.completed_at >= day_start,
            UserGrowthTask.completed_at < day_end
        ).count()

        today_checkin = db.query(DailyCheckInRecord).filter(
            DailyCheckInRecord.user_id == user_id,
            DailyCheckInRecord.checkin_date == date_str
        ).first()

        checkin_done = today_checkin is not None

        base_score = min(100, task_count * 25)

        if checkin_done:
            base_score = min(100, base_score + 15)

        detail = {
            "tasks_completed_today": task_count,
            "checkin_done": checkin_done,
            "base_score": base_score,
            "date": date_str
        }

        return base_score, detail

    def calculate_total_energy(
        self,
        horoscope_score: float,
        task_score: float,
        boost_multiplier: float = 1.0
    ) -> Dict[str, Any]:
        """
        计算综合能量值
        使用加权平均：星运权重0.6，任务权重0.4
        """
        horoscope_weight = self.config.get("horoscope_weight", 0.6)
        task_weight = self.config.get("task_weight", 0.4)

        weighted_score = (
            horoscope_score * horoscope_weight +
            task_score * task_weight
        )

        boosted_score = weighted_score * boost_multiplier

        final_score = min(100.0, boosted_score)

        return {
            "weighted_score": round(weighted_score, 1),
            "boost_multiplier": boost_multiplier,
            "boosted_score": round(boosted_score, 1),
            "final_score": round(final_score, 1),
            "horoscope_score": round(horoscope_score, 1),
            "task_score": round(task_score, 1),
            "horoscope_weight": horoscope_weight,
            "task_weight": task_weight
        }

    def get_or_create_energy_snapshot(
        self,
        db: Session,
        user_id: int,
        date_str: str = None,
        force_refresh: bool = False
    ) -> UserEnergySnapshot:
        """
        获取或创建用户能量快照
        """
        if date_str is None:
            date_str = get_today_str()

        snapshot = db.query(UserEnergySnapshot).filter(
            UserEnergySnapshot.user_id == user_id,
            UserEnergySnapshot.snapshot_date == date_str
        ).first()

        if snapshot and not force_refresh:
            return snapshot

        horoscope_score, horoscope_detail = self.get_user_horoscope_score(
            db, user_id, date_str
        )

        task_score, task_detail = self.get_user_task_completion_score(
            db, user_id, date_str
        )

        boost = self._get_active_boost(db, user_id)
        boost_multiplier = boost.energy_multiplier if boost else 1.0

        energy_result = self.calculate_total_energy(
            horoscope_score, task_score, boost_multiplier
        )

        if snapshot:
            snapshot.daily_horoscope_score = horoscope_score
            snapshot.daily_horoscope_detail = json.dumps(horoscope_detail, ensure_ascii=False)
            snapshot.task_completion_score = task_score
            snapshot.task_completion_detail = json.dumps(task_detail, ensure_ascii=False)
            snapshot.total_energy_score = energy_result["final_score"]
            snapshot.energy_boost_applied = boost_multiplier
        else:
            snapshot = UserEnergySnapshot(
                user_id=user_id,
                snapshot_date=date_str,
                daily_horoscope_score=horoscope_score,
                daily_horoscope_detail=json.dumps(horoscope_detail, ensure_ascii=False),
                task_completion_score=task_score,
                task_completion_detail=json.dumps(task_detail, ensure_ascii=False),
                total_energy_score=energy_result["final_score"],
                energy_boost_applied=boost_multiplier,
                pk_matches_count=0,
                pk_wins=0
            )
            db.add(snapshot)

        db.commit()
        db.refresh(snapshot)

        return snapshot

    def _get_active_boost(
        self,
        db: Session,
        user_id: int
    ) -> Optional[EnergyBoost]:
        """获取用户当前激活的能量Buff"""
        now = datetime.utcnow()
        return db.query(EnergyBoost).filter(
            EnergyBoost.user_id == user_id,
            EnergyBoost.is_active == True,
            EnergyBoost.valid_from <= now,
            EnergyBoost.valid_until > now
        ).order_by(EnergyBoost.created_at.desc()).first()

    def _generate_seed(self, user_id: int, date_str: str, sun_sign: str = None) -> int:
        """生成随机种子"""
        seed_str = f"{user_id}_{date_str}"
        if sun_sign:
            seed_str += f"_{sun_sign}"
        return hash(seed_str)

    def _pseudo_random(self, seed: int, min_val: int, max_val: int, offset: int = 0) -> int:
        """伪随机数生成"""
        a = 1103515245
        c = 12345
        m = 2**31
        seed = (a * (seed + offset) + c) % m
        return min_val + (seed % (max_val - min_val + 1))


class PKMatchService:
    """
    PK匹配服务
    负责随机匹配和好友对战
    """

    def __init__(self, config: Dict = None, energy_engine: PKEnergyEngine = None):
        self.config = config or DEFAULT_CONFIG
        self.energy_engine = energy_engine or PKEnergyEngine(self.config)

    def get_or_create_daily_pk(
        self,
        db: Session,
        user_id: int,
        date_str: str = None
    ) -> UserDailyPK:
        """获取或创建用户每日PK记录"""
        if date_str is None:
            date_str = get_today_str()

        daily_pk = db.query(UserDailyPK).filter(
            UserDailyPK.user_id == user_id,
            UserDailyPK.battle_date == date_str
        ).first()

        if not daily_pk:
            daily_pk = UserDailyPK(
                user_id=user_id,
                battle_date=date_str,
                free_challenges_total=self.config.get("free_challenges_per_day", 3),
                free_challenges_used=0,
                paid_challenges_purchased=0,
                paid_challenges_used=0
            )
            db.add(daily_pk)
            db.commit()
            db.refresh(daily_pk)

        return daily_pk

    def can_challenge(
        self,
        db: Session,
        user_id: int
    ) -> Tuple[bool, Optional[PKBattleErrorCode], Dict[str, Any]]:
        """检查用户是否可以进行PK挑战"""
        daily_pk = self.get_or_create_daily_pk(db, user_id)

        if not daily_pk.can_challenge:
            return False, PKBattleErrorCode.NO_CHALLENGES_LEFT, {
                "free_remaining": max(0, daily_pk.free_challenges_total - daily_pk.free_challenges_used),
                "paid_remaining": max(0, daily_pk.paid_challenges_purchased - daily_pk.paid_challenges_used),
                "total_available": daily_pk.total_challenges_available
            }

        return True, None, {
            "free_remaining": max(0, daily_pk.free_challenges_total - daily_pk.free_challenges_used),
            "paid_remaining": max(0, daily_pk.paid_challenges_purchased - daily_pk.paid_challenges_used),
            "total_available": daily_pk.total_challenges_available
        }

    def check_wager_valid(
        self,
        db: Session,
        user_id: int,
        wager_fragments: int
    ) -> Tuple[bool, Optional[PKBattleErrorCode]]:
        """检查赌注是否有效"""
        min_wager = self.config.get("wager_min_fragments", 10)
        max_wager = self.config.get("wager_max_fragments", 500)

        if wager_fragments < min_wager or wager_fragments > max_wager:
            return False, PKBattleErrorCode.INVALID_WAGER

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, PKBattleErrorCode.USER_NOT_FOUND

        if user.stardust_fragment_balance < wager_fragments:
            return False, PKBattleErrorCode.INSUFFICIENT_FRAGMENTS

        return True, None

    def start_random_match(
        self,
        db: Session,
        user_id: int,
        wager_fragments: int = 10
    ) -> Tuple[Optional[PKMatch], Optional[PKBattleErrorCode], str]:
        """
        开始随机匹配
        1. 检查是否可以挑战
        2. 检查赌注有效性
        3. 查找或创建匹配
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None, PKBattleErrorCode.USER_NOT_FOUND, "用户不存在"

        can_challenge, err_code, err_detail = self.can_challenge(db, user_id)
        if not can_challenge:
            return None, err_code, "今日挑战次数已用完"

        wager_valid, wager_err = self.check_wager_valid(db, user_id, wager_fragments)
        if not wager_valid:
            return None, wager_err, "赌注无效或碎片不足"

        waiting_matches = db.query(PKMatch).filter(
            PKMatch.match_type == PKMatchType.RANDOM.value,
            PKMatch.status == PKMatchStatus.WAITING.value,
            PKMatch.challenger_id != user_id,
            PKMatch.wager_fragments == wager_fragments,
            PKMatch.expires_at > datetime.utcnow()
        ).order_by(PKMatch.created_at.asc()).all()

        for waiting_match in waiting_matches:
            try:
                return self._match_with_opponent(db, user_id, waiting_match, wager_fragments)
            except Exception as e:
                logger.warning(f"匹配失败: {e}")
                continue

        return self._create_waiting_match(db, user_id, wager_fragments)

    def _create_waiting_match(
        self,
        db: Session,
        user_id: int,
        wager_fragments: int
    ) -> Tuple[PKMatch, Optional[PKBattleErrorCode], str]:
        """创建等待中的匹配"""
        match_no = generate_unique_no("PKM")

        energy_snapshot = self.energy_engine.get_or_create_energy_snapshot(db, user_id)

        active_boost = db.query(EnergyBoost).filter(
            EnergyBoost.user_id == user_id,
            EnergyBoost.is_active == True,
            EnergyBoost.valid_from <= datetime.utcnow(),
            EnergyBoost.valid_until > datetime.utcnow()
        ).order_by(EnergyBoost.created_at.desc()).first()

        match = PKMatch(
            match_no=match_no,
            match_type=PKMatchType.RANDOM.value,
            status=PKMatchStatus.WAITING.value,
            challenger_id=user_id,
            challenger_energy=energy_snapshot.total_energy_score,
            challenger_boost_id=active_boost.id if active_boost else None,
            wager_fragments=wager_fragments,
            expires_at=datetime.utcnow() + timedelta(
                seconds=self.config.get("match_waiting_timeout_seconds", 60)
            )
        )

        db.add(match)
        db.commit()
        db.refresh(match)

        return match, None, "已加入匹配池，等待对手..."

    def _match_with_opponent(
        self,
        db: Session,
        user_id: int,
        waiting_match: PKMatch,
        wager_fragments: int
    ) -> Tuple[PKMatch, Optional[PKBattleErrorCode], str]:
        """与等待中的对手匹配"""
        opponent_id = waiting_match.challenger_id

        if opponent_id == user_id:
            return None, PKBattleErrorCode.CANNOT_INVITE_SELF, "不能与自己匹配"

        user_energy = self.energy_engine.get_or_create_energy_snapshot(db, user_id)

        user_boost = db.query(EnergyBoost).filter(
            EnergyBoost.user_id == user_id,
            EnergyBoost.is_active == True,
            EnergyBoost.valid_from <= datetime.utcnow(),
            EnergyBoost.valid_until > datetime.utcnow()
        ).order_by(EnergyBoost.created_at.desc()).first()

        waiting_match.defender_id = user_id
        waiting_match.defender_energy = user_energy.total_energy_score
        waiting_match.defender_boost_id = user_boost.id if user_boost else None
        waiting_match.status = PKMatchStatus.MATCHED.value
        waiting_match.match_started_at = datetime.utcnow()

        db.commit()
        db.refresh(waiting_match)

        return waiting_match, None, "匹配成功！"

    def create_friend_invite(
        self,
        db: Session,
        inviter_id: int,
        invitee_id: int,
        wager_fragments: int = 10
    ) -> Tuple[Optional[PKMatchInvite], Optional[PKBattleErrorCode], str]:
        """创建好友对战邀请"""
        inviter = db.query(User).filter(User.id == inviter_id).first()
        if not inviter:
            return None, PKBattleErrorCode.USER_NOT_FOUND, "邀请人不存在"

        invitee = db.query(User).filter(User.id == invitee_id).first()
        if not invitee:
            return None, PKBattleErrorCode.OPPONENT_NOT_FOUND, "被邀请人不存在"

        if inviter_id == invitee_id:
            return None, PKBattleErrorCode.CANNOT_INVITE_SELF, "不能邀请自己"

        can_challenge, err_code, _ = self.can_challenge(db, inviter_id)
        if not can_challenge:
            return None, err_code, "今日挑战次数已用完"

        wager_valid, wager_err = self.check_wager_valid(db, inviter_id, wager_fragments)
        if not wager_valid:
            return None, wager_err, "赌注无效或碎片不足"

        invite_code = generate_invite_code()

        existing_invite = db.query(PKMatchInvite).filter(
            PKMatchInvite.inviter_id == inviter_id,
            PKMatchInvite.invitee_id == invitee_id,
            PKMatchInvite.status == PKInviteStatus.PENDING.value,
            PKMatchInvite.expires_at > datetime.utcnow()
        ).first()

        if existing_invite:
            return None, PKBattleErrorCode.INVITE_ALREADY_ACCEPTED, "已有未处理的邀请"

        invite = PKMatchInvite(
            invite_code=invite_code,
            inviter_id=inviter_id,
            invitee_id=invitee_id,
            wager_fragments=wager_fragments,
            expires_at=datetime.utcnow() + timedelta(
                minutes=self.config.get("invite_expiry_minutes", 10)
            )
        )

        db.add(invite)
        db.commit()
        db.refresh(invite)

        return invite, None, f"邀请已发送！邀请码: {invite_code}"

    def accept_invite(
        self,
        db: Session,
        invitee_id: int,
        invite_code: str
    ) -> Tuple[Optional[PKMatch], Optional[PKBattleErrorCode], str]:
        """接受好友对战邀请（带行锁和幂等检查）"""
        try:
            invite = db.query(PKMatchInvite).filter(
                PKMatchInvite.invite_code == invite_code
            ).with_for_update().first()

            if not invite:
                db.rollback()
                return None, PKBattleErrorCode.INVITE_NOT_FOUND, "邀请不存在"

            if invite.invitee_id != invitee_id:
                db.rollback()
                return None, PKBattleErrorCode.INVITE_NOT_FOUND, "无权接受此邀请"

            if invite.status == PKInviteStatus.ACCEPTED.value:
                db.rollback()
                return None, PKBattleErrorCode.INVITE_ALREADY_ACCEPTED, "邀请已被接受"

            if invite.status in [PKInviteStatus.DECLINED.value, PKInviteStatus.EXPIRED.value, PKInviteStatus.CANCELLED.value]:
                db.rollback()
                return None, PKBattleErrorCode.INVITE_EXPIRED, "邀请已过期或被拒绝"

            if invite.expires_at < datetime.utcnow():
                invite.status = PKInviteStatus.EXPIRED.value
                db.commit()
                return None, PKBattleErrorCode.INVITE_EXPIRED, "邀请已过期"

            can_challenge, err_code, _ = self.can_challenge(db, invitee_id)
            if not can_challenge:
                db.rollback()
                return None, err_code, "今日挑战次数已用完"

            wager_valid, wager_err = self.check_wager_valid(db, invitee_id, invite.wager_fragments)
            if not wager_valid:
                db.rollback()
                return None, wager_err, "碎片不足，无法接受挑战"

            inviter_energy = self.energy_engine.get_or_create_energy_snapshot(db, invite.inviter_id)
            invitee_energy = self.energy_engine.get_or_create_energy_snapshot(db, invitee_id)

            inviter_boost = db.query(EnergyBoost).filter(
                EnergyBoost.user_id == invite.inviter_id,
                EnergyBoost.is_active == True,
                EnergyBoost.valid_from <= datetime.utcnow(),
                EnergyBoost.valid_until > datetime.utcnow()
            ).order_by(EnergyBoost.created_at.desc()).first()

            invitee_boost = db.query(EnergyBoost).filter(
                EnergyBoost.user_id == invitee_id,
                EnergyBoost.is_active == True,
                EnergyBoost.valid_from <= datetime.utcnow(),
                EnergyBoost.valid_until > datetime.utcnow()
            ).order_by(EnergyBoost.created_at.desc()).first()

            match_no = generate_unique_no("PKF")
            match = PKMatch(
                match_no=match_no,
                match_type=PKMatchType.FRIEND.value,
                status=PKMatchStatus.MATCHED.value,
                challenger_id=invite.inviter_id,
                defender_id=invitee_id,
                challenger_energy=inviter_energy.total_energy_score,
                defender_energy=invitee_energy.total_energy_score,
                challenger_boost_id=inviter_boost.id if inviter_boost else None,
                defender_boost_id=invitee_boost.id if invitee_boost else None,
                wager_fragments=invite.wager_fragments,
                match_started_at=datetime.utcnow()
            )

            db.add(match)
            db.flush()

            invite.status = PKInviteStatus.ACCEPTED.value
            invite.accepted_at = datetime.utcnow()
            invite.match_id = match.id

            db.commit()
            db.refresh(match)
            db.refresh(invite)

            return match, None, "邀请已接受，对战开始！"

        except Exception as e:
            logger.error(f"接受邀请异常: invite_code={invite_code}, error={str(e)}", exc_info=True)
            db.rollback()
            return None, PKBattleErrorCode.PURCHASE_FAILED, f"接受邀请失败: {str(e)}"

    def decline_invite(
        self,
        db: Session,
        invitee_id: int,
        invite_code: str
    ) -> Tuple[bool, Optional[PKBattleErrorCode], str]:
        """拒绝好友对战邀请（带行锁和幂等检查）"""
        try:
            invite = db.query(PKMatchInvite).filter(
                PKMatchInvite.invite_code == invite_code
            ).with_for_update().first()

            if not invite:
                db.rollback()
                return False, PKBattleErrorCode.INVITE_NOT_FOUND, "邀请不存在"

            if invite.invitee_id != invitee_id:
                db.rollback()
                return False, PKBattleErrorCode.INVITE_NOT_FOUND, "无权拒绝此邀请"

            if invite.status == PKInviteStatus.ACCEPTED.value:
                db.rollback()
                return False, PKBattleErrorCode.INVITE_ALREADY_ACCEPTED, "邀请已被接受"

            if invite.status in [PKInviteStatus.DECLINED.value, PKInviteStatus.EXPIRED.value, PKInviteStatus.CANCELLED.value]:
                db.rollback()
                return False, PKBattleErrorCode.INVITE_EXPIRED, "邀请已过期或被拒绝"

            invite.status = PKInviteStatus.DECLINED.value
            invite.declined_at = datetime.utcnow()
            db.commit()

            return True, None, "已拒绝邀请"

        except Exception as e:
            logger.error(f"拒绝邀请异常: invite_code={invite_code}, error={str(e)}", exc_info=True)
            db.rollback()
            return False, PKBattleErrorCode.PURCHASE_FAILED, f"拒绝邀请失败: {str(e)}"


class PKBattleEngine:
    """
    PK战斗引擎
    负责胜负判定和碎片掠夺
    """

    def __init__(self, config: Dict = None, energy_engine: PKEnergyEngine = None):
        self.config = config or DEFAULT_CONFIG
        self.energy_engine = energy_engine or PKEnergyEngine(self.config)

    def execute_battle(
        self,
        db: Session,
        match_id: int
    ) -> Tuple[Optional[PKMatch], Optional[PKBattleErrorCode], str]:
        """
        执行战斗（带行锁、幂等检查、完整事务）
        1. 加行锁检查匹配状态
        2. 幂等检查：已完成则直接返回结果
        3. 消耗双方挑战次数（加行锁）
        4. 计算胜负（基于能量值 + 随机因素）
        5. 进行碎片转移（原子更新）
        6. 更新统计
        """
        try:
            match = db.query(PKMatch).filter(
                PKMatch.id == match_id
            ).with_for_update().first()

            if not match:
                db.rollback()
                return None, PKBattleErrorCode.MATCH_NOT_FOUND, "匹配不存在"

            if match.status == PKMatchStatus.COMPLETED.value:
                db.rollback()
                result_msg = self._generate_result_message(match, match.winner_id)
                return match, None, result_msg

            if match.status not in [PKMatchStatus.MATCHED.value, PKMatchStatus.IN_PROGRESS.value]:
                db.rollback()
                return None, PKBattleErrorCode.MATCH_NOT_IN_PROGRESS, "匹配不在进行中"

            challenger = db.query(User).filter(
                User.id == match.challenger_id
            ).with_for_update().first()
            
            defender = db.query(User).filter(
                User.id == match.defender_id
            ).with_for_update().first()

            if not challenger or not defender:
                db.rollback()
                return None, PKBattleErrorCode.OPPONENT_NOT_FOUND, "对手不存在"

            if not self._use_challenge_atomic(db, match.challenger_id):
                db.rollback()
                return None, PKBattleErrorCode.NO_CHALLENGES_LEFT, "挑战者挑战次数不足"

            if not self._use_challenge_atomic(db, match.defender_id):
                db.rollback()
                return None, PKBattleErrorCode.NO_CHALLENGES_LEFT, "防御者挑战次数不足"

            match.status = PKMatchStatus.IN_PROGRESS.value
            db.flush()

            challenger_boost = db.query(EnergyBoost).filter(
                EnergyBoost.id == match.challenger_boost_id
            ).first() if match.challenger_boost_id else None

            defender_boost = db.query(EnergyBoost).filter(
                EnergyBoost.id == match.defender_boost_id
            ).first() if match.defender_boost_id else None

            challenger_final_energy, challenger_critical = self._calculate_battle_energy(
                match.challenger_energy, challenger_boost
            )
            defender_final_energy, defender_critical = self._calculate_battle_energy(
                match.defender_energy, defender_boost
            )

            is_challenger_critical = challenger_critical and challenger_final_energy > defender_final_energy
            is_defender_critical = defender_critical and defender_final_energy > challenger_final_energy

            winner_id, loser_id, is_draw = self._determine_winner(
                match.challenger_id, match.defender_id,
                challenger_final_energy, defender_final_energy
            )

            fragments_transferred = 0
            result_detail = {
                "challenger_energy": match.challenger_energy,
                "defender_energy": match.defender_energy,
                "challenger_final_energy": challenger_final_energy,
                "defender_final_energy": defender_final_energy,
                "is_challenger_critical": is_challenger_critical,
                "is_defender_critical": is_defender_critical,
                "wager_fragments": match.wager_fragments
            }

            if not is_draw:
                fragments_transferred = self._transfer_fragments_atomic(
                    db, winner_id, loser_id, match.wager_fragments,
                    is_challenger_critical or is_defender_critical, match
                )

                result_detail["fragments_transferred"] = fragments_transferred

                self._update_daily_pk_results(db, winner_id, loser_id, fragments_transferred)

                self._update_pk_stats(db, winner_id, loser_id, fragments_transferred)

                self._update_energy_snapshots(db, match.challenger_id, match.defender_id, winner_id)

            match.winner_id = winner_id
            match.loser_id = loser_id
            match.is_draw = is_draw
            match.is_challenger_critical = is_challenger_critical
            match.is_defender_critical = is_defender_critical
            match.fragments_transferred = fragments_transferred
            match.result = PKBattleResult.WIN.value if not is_draw and winner_id == match.challenger_id else \
                PKBattleResult.LOSE.value if not is_draw and winner_id == match.defender_id else \
                PKBattleResult.DRAW.value
            match.result_detail = json.dumps(result_detail, ensure_ascii=False)
            match.status = PKMatchStatus.COMPLETED.value
            match.match_completed_at = datetime.utcnow()

            db.commit()
            db.refresh(match)

            result_msg = self._generate_result_message(match, winner_id)

            return match, None, result_msg

        except Exception as e:
            logger.error(f"执行战斗异常: match_id={match_id}, error={str(e)}", exc_info=True)
            db.rollback()
            return None, PKBattleErrorCode.PURCHASE_FAILED, f"执行战斗失败: {str(e)}"

    def _use_challenge_atomic(
        self,
        db: Session,
        user_id: int
    ) -> bool:
        """
        原子扣减挑战次数（加行锁）
        """
        date_str = get_today_str()
        
        daily_pk = db.query(UserDailyPK).filter(
            UserDailyPK.user_id == user_id,
            UserDailyPK.battle_date == date_str
        ).with_for_update().first()

        if not daily_pk:
            daily_pk = UserDailyPK(
                user_id=user_id,
                battle_date=date_str,
                free_challenges_total=self.config.get("free_challenges_per_day", 3),
                free_challenges_used=0,
                paid_challenges_purchased=0,
                paid_challenges_used=0
            )
            db.add(daily_pk)
            db.flush()
            
            daily_pk = db.query(UserDailyPK).filter(
                UserDailyPK.user_id == user_id,
                UserDailyPK.battle_date == date_str
            ).with_for_update().first()

        if not daily_pk:
            return False

        free_remaining = max(0, daily_pk.free_challenges_total - daily_pk.free_challenges_used)
        paid_remaining = max(0, daily_pk.paid_challenges_purchased - daily_pk.paid_challenges_used)
        
        if free_remaining > 0:
            daily_pk.free_challenges_used += 1
        elif paid_remaining > 0:
            daily_pk.paid_challenges_used += 1
        else:
            return False

        db.flush()
        return True

    def _transfer_fragments_atomic(
        self,
        db: Session,
        winner_id: int,
        loser_id: int,
        wager_fragments: int,
        is_critical: bool,
        match: PKMatch
    ) -> int:
        """
        原子转移碎片（加行锁 + 原子更新）
        """
        winner = db.query(User).filter(
            User.id == winner_id
        ).with_for_update().first()
        
        loser = db.query(User).filter(
            User.id == loser_id
        ).with_for_update().first()

        if not winner or not loser:
            return 0

        winner_rate = self.config.get("winner_fraction_rate", 0.8)
        base_winnings = int(wager_fragments * winner_rate)

        if is_critical:
            base_winnings = int(base_winnings * self.config.get("critical_hit_multiplier", 1.5))

        winner_balance_before = winner.stardust_fragment_balance
        loser_balance_before = loser.stardust_fragment_balance

        actual_wager = min(wager_fragments, loser_balance_before)
        
        db.query(User).filter(User.id == loser_id).update(
            {"stardust_fragment_balance": User.stardust_fragment_balance - actual_wager}
        )
        
        db.query(User).filter(User.id == winner_id).update(
            {"stardust_fragment_balance": User.stardust_fragment_balance + base_winnings}
        )

        db.flush()

        winner_transaction = StarDustTransaction(
            user_id=winner_id,
            transaction_type="pk_win",
            currency_type="fragment",
            amount=base_winnings,
            balance_before=winner_balance_before,
            balance_after=winner_balance_before + base_winnings,
            related_type="pk_match",
            related_id=str(match.id),
            description=f"PK对战胜利获得 {base_winnings} 星元碎片"
        )
        db.add(winner_transaction)

        loser_transaction = StarDustTransaction(
            user_id=loser_id,
            transaction_type="pk_lose",
            currency_type="fragment",
            amount=-actual_wager,
            balance_before=loser_balance_before,
            balance_after=max(0, loser_balance_before - actual_wager),
            related_type="pk_match",
            related_id=str(match.id),
            description=f"PK对战失败失去 {actual_wager} 星元碎片"
        )
        db.add(loser_transaction)

        pk_transaction_winner = PKTransaction(
            transaction_no=generate_unique_no("PKT"),
            user_id=winner_id,
            match_id=match.id,
            transaction_type="pk_winnings",
            currency_type="fragment",
            amount=base_winnings,
            balance_before=winner_balance_before,
            balance_after=winner_balance_before + base_winnings,
            related_match_no=match.match_no,
            related_opponent_id=loser_id,
            is_winnings=True,
            description=f"PK胜利 - 获得 {base_winnings} 星元碎片"
        )
        db.add(pk_transaction_winner)

        pk_transaction_loser = PKTransaction(
            transaction_no=generate_unique_no("PKT"),
            user_id=loser_id,
            match_id=match.id,
            transaction_type="pk_loss",
            currency_type="fragment",
            amount=-actual_wager,
            balance_before=loser_balance_before,
            balance_after=max(0, loser_balance_before - actual_wager),
            related_match_no=match.match_no,
            related_opponent_id=winner_id,
            is_loss=True,
            description=f"PK失败 - 失去 {actual_wager} 星元碎片"
        )
        db.add(pk_transaction_loser)

        db.flush()

        return base_winnings

    def _calculate_battle_energy(
        self,
        base_energy: float,
        boost: Optional[EnergyBoost]
    ) -> Tuple[float, bool]:
        """
        计算战斗时的最终能量值
        包含：能量Buff加成、暴击判定
        """
        final_energy = base_energy
        is_critical = False

        if boost:
            final_energy = base_energy * boost.energy_multiplier

        random_factor = random.uniform(-5, 5)
        final_energy += random_factor

        critical_chance = self.config.get("critical_hit_base_chance", 0.05)
        if boost and boost.critical_hit_chance > 0:
            critical_chance += boost.critical_hit_chance

        if random.random() < critical_chance:
            is_critical = True
            critical_multiplier = self.config.get("critical_hit_multiplier", 1.5)
            final_energy *= critical_multiplier

        final_energy = max(0, final_energy)

        return final_energy, is_critical

    def _determine_winner(
        self,
        challenger_id: int,
        defender_id: int,
        challenger_energy: float,
        defender_energy: float
    ) -> Tuple[int, int, bool]:
        """
        判定胜负
        基于能量值差异，加入一定的随机性
        """
        energy_diff = challenger_energy - defender_energy

        if abs(energy_diff) < 5:
            if random.random() < 0.5:
                return challenger_id, defender_id, False
            else:
                return defender_id, challenger_id, False

        win_probability = 0.5 + (energy_diff / 100) * 0.4
        win_probability = max(0.1, min(0.9, win_probability))

        if random.random() < win_probability:
            return challenger_id, defender_id, False
        else:
            return defender_id, challenger_id, False

    def _transfer_fragments(
        self,
        db: Session,
        winner_id: int,
        loser_id: int,
        wager_fragments: int,
        is_critical: bool,
        match: PKMatch
    ) -> int:
        """
        转移碎片
        赢家获得失败者的赌注，但扣除一定比例的"手续费"
        暴击时获得额外奖励
        """
        winner = db.query(User).filter(User.id == winner_id).first()
        loser = db.query(User).filter(User.id == loser_id).first()

        if not winner or not loser:
            return 0

        winner_rate = self.config.get("winner_fraction_rate", 0.8)

        base_winnings = int(wager_fragments * winner_rate)

        if is_critical:
            base_winnings = int(base_winnings * self.config.get("critical_hit_multiplier", 1.5))

        winner_balance_before = winner.stardust_fragment_balance
        loser_balance_before = loser.stardust_fragment_balance

        loser.stardust_fragment_balance = max(0, loser_balance_before - wager_fragments)
        winner.stardust_fragment_balance = winner_balance_before + base_winnings

        winner_transaction = StarDustTransaction(
            user_id=winner_id,
            transaction_type="pk_win",
            currency_type="fragment",
            amount=base_winnings,
            balance_before=winner_balance_before,
            balance_after=winner_balance_before + base_winnings,
            related_type="pk_match",
            related_id=str(match.id),
            description=f"PK对战胜利获得 {base_winnings} 星元碎片"
        )
        db.add(winner_transaction)

        loser_transaction = StarDustTransaction(
            user_id=loser_id,
            transaction_type="pk_lose",
            currency_type="fragment",
            amount=-wager_fragments,
            balance_before=loser_balance_before,
            balance_after=max(0, loser_balance_before - wager_fragments),
            related_type="pk_match",
            related_id=str(match.id),
            description=f"PK对战失败失去 {wager_fragments} 星元碎片"
        )
        db.add(loser_transaction)

        pk_transaction_winner = PKTransaction(
            transaction_no=generate_unique_no("PKT"),
            user_id=winner_id,
            match_id=match.id,
            transaction_type="pk_winnings",
            currency_type="fragment",
            amount=base_winnings,
            balance_before=winner_balance_before,
            balance_after=winner_balance_before + base_winnings,
            related_match_no=match.match_no,
            related_opponent_id=loser_id,
            is_winnings=True,
            description=f"PK胜利 - 获得 {base_winnings} 星元碎片"
        )
        db.add(pk_transaction_winner)

        pk_transaction_loser = PKTransaction(
            transaction_no=generate_unique_no("PKT"),
            user_id=loser_id,
            match_id=match.id,
            transaction_type="pk_loss",
            currency_type="fragment",
            amount=-wager_fragments,
            balance_before=loser_balance_before,
            balance_after=max(0, loser_balance_before - wager_fragments),
            related_match_no=match.match_no,
            related_opponent_id=winner_id,
            is_loss=True,
            description=f"PK失败 - 失去 {wager_fragments} 星元碎片"
        )
        db.add(pk_transaction_loser)

        db.flush()

        return base_winnings

    def _update_daily_pk_results(
        self,
        db: Session,
        winner_id: int,
        loser_id: int,
        fragments_earned: int
    ):
        """更新每日PK结果统计"""
        today = get_today_str()

        winner_daily = db.query(UserDailyPK).filter(
            UserDailyPK.user_id == winner_id,
            UserDailyPK.battle_date == today
        ).first()
        if winner_daily:
            winner_daily.daily_wins += 1
            winner_daily.fragments_earned += fragments_earned

        loser_daily = db.query(UserDailyPK).filter(
            UserDailyPK.user_id == loser_id,
            UserDailyPK.battle_date == today
        ).first()
        if loser_daily:
            loser_daily.daily_losses += 1

        db.flush()

    def _update_pk_stats(
        self,
        db: Session,
        winner_id: int,
        loser_id: int,
        fragments_transferred: int
    ):
        """更新用户PK总统计"""
        winner_stats = db.query(UserPKStats).filter(
            UserPKStats.user_id == winner_id
        ).first()

        if not winner_stats:
            winner_stats = UserPKStats(user_id=winner_id)
            db.add(winner_stats)

        winner_stats.total_matches += 1
        winner_stats.total_wins += 1
        winner_stats.total_fragments_won += fragments_transferred
        winner_stats.current_win_streak += 1
        winner_stats.best_win_streak = max(winner_stats.best_win_streak, winner_stats.current_win_streak)
        winner_stats.net_fragments += fragments_transferred
        winner_stats.last_match_at = datetime.utcnow()

        loser_stats = db.query(UserPKStats).filter(
            UserPKStats.user_id == loser_id
        ).first()

        if not loser_stats:
            loser_stats = UserPKStats(user_id=loser_id)
            db.add(loser_stats)

        loser_stats.total_matches += 1
        loser_stats.total_losses += 1
        loser_stats.total_fragments_lost += fragments_transferred
        loser_stats.current_win_streak = 0
        loser_stats.net_fragments -= fragments_transferred
        loser_stats.last_match_at = datetime.utcnow()

        db.flush()

    def _update_energy_snapshots(
        self,
        db: Session,
        challenger_id: int,
        defender_id: int,
        winner_id: int
    ):
        """更新能量快照中的PK统计"""
        today = get_today_str()

        for user_id in [challenger_id, defender_id]:
            snapshot = db.query(UserEnergySnapshot).filter(
                UserEnergySnapshot.user_id == user_id,
                UserEnergySnapshot.snapshot_date == today
            ).first()

            if snapshot:
                snapshot.pk_matches_count += 1
                if user_id == winner_id:
                    snapshot.pk_wins += 1

        db.flush()

    def _generate_result_message(
        self,
        match: PKMatch,
        winner_id: int
    ) -> str:
        """生成战斗结果消息"""
        if match.is_draw:
            return "平局！双方能量势均力敌。"

        is_challenger_win = winner_id == match.challenger_id

        if match.is_challenger_critical or match.is_defender_critical:
            critical_side = "挑战者" if is_challenger_win else "防御者"
            return f"暴击！{critical_side}以强大能量获得胜利！获得 {match.fragments_transferred} 星元碎片！"

        winner_side = "挑战者" if is_challenger_win else "防御者"
        return f"{winner_side}获胜！获得 {match.fragments_transferred} 星元碎片！"


class PKShopService:
    """
    PK商店服务
    负责购买挑战次数和能量Buff
    """

    def __init__(self, config: Dict = None):
        self.config = config or DEFAULT_CONFIG

    def purchase_challenges(
        self,
        db: Session,
        user_id: int,
        count: int = 1
    ) -> Tuple[Optional[PKChallengePurchase], Optional[PKBattleErrorCode], str]:
        """
        购买额外PK挑战次数（带行锁和事务）
        使用星元点数购买
        """
        try:
            user = db.query(User).filter(
                User.id == user_id
            ).with_for_update().first()
            
            if not user:
                db.rollback()
                return None, PKBattleErrorCode.USER_NOT_FOUND, "用户不存在"

            price_per_challenge = self.config.get("challenge_purchase_price_points", 50)
            total_price = price_per_challenge * count

            if user.stardust_point_balance < total_price:
                db.rollback()
                return None, PKBattleErrorCode.INSUFFICIENT_POINTS, f"点数不足，需要 {total_price} 星元点数"

            balance_before = user.stardust_point_balance
            
            db.query(User).filter(User.id == user_id).update(
                {"stardust_point_balance": User.stardust_point_balance - total_price}
            )

            purchase = PKChallengePurchase(
                purchase_no=generate_unique_no("PKP"),
                user_id=user_id,
                challenges_purchased=count,
                price_per_challenge=price_per_challenge,
                total_price=total_price,
                currency_type="point",
                is_paid=True,
                paid_at=datetime.utcnow(),
                purchase_date=get_today_str()
            )
            db.add(purchase)
            db.flush()

            daily_pk = db.query(UserDailyPK).filter(
                UserDailyPK.user_id == user_id,
                UserDailyPK.battle_date == get_today_str()
            ).first()

            if not daily_pk:
                daily_pk = UserDailyPK(
                    user_id=user_id,
                    battle_date=get_today_str(),
                    free_challenges_total=self.config.get("free_challenges_per_day", 3),
                    free_challenges_used=0,
                    paid_challenges_purchased=count,
                    paid_challenges_used=0
                )
                db.add(daily_pk)
            else:
                daily_pk.paid_challenges_purchased += count

            transaction = StarDustTransaction(
                user_id=user_id,
                transaction_type="pk_challenge_purchase",
                currency_type="point",
                amount=-total_price,
                balance_before=balance_before,
                balance_after=balance_before - total_price,
                related_type="pk_purchase",
                related_id=str(purchase.id),
                description=f"购买PK挑战次数 x{count}"
            )
            db.add(transaction)

            db.commit()
            db.refresh(purchase)

            return purchase, None, f"成功购买 {count} 次PK挑战次数！"

        except Exception as e:
            logger.error(f"购买挑战次数异常: user_id={user_id}, count={count}, error={str(e)}", exc_info=True)
            db.rollback()
            return None, PKBattleErrorCode.PURCHASE_FAILED, f"购买失败: {str(e)}"

    def purchase_double_energy_boost(
        self,
        db: Session,
        user_id: int
    ) -> Tuple[Optional[EnergyBoost], Optional[PKBattleErrorCode], str]:
        """
        购买当日能量翻倍Buff（带行锁和事务）
        """
        try:
            user = db.query(User).filter(
                User.id == user_id
            ).with_for_update().first()
            
            if not user:
                db.rollback()
                return None, PKBattleErrorCode.USER_NOT_FOUND, "用户不存在"

            price = self.config.get("double_energy_price_points", 100)

            if user.stardust_point_balance < price:
                db.rollback()
                return None, PKBattleErrorCode.INSUFFICIENT_POINTS, f"点数不足，需要 {price} 星元点数"

            now = datetime.utcnow()
            today_end = datetime(now.year, now.month, now.day, 23, 59, 59)

            existing_boost = db.query(EnergyBoost).filter(
                EnergyBoost.user_id == user_id,
                EnergyBoost.boost_type == EnergyBoostType.DOUBLE_ENERGY.value,
                EnergyBoost.is_active == True,
                EnergyBoost.valid_until > now
            ).first()

            if existing_boost:
                db.rollback()
                return existing_boost, None, "您已有激活的能量翻倍Buff！"

            balance_before = user.stardust_point_balance
            
            db.query(User).filter(User.id == user_id).update(
                {"stardust_point_balance": User.stardust_point_balance - price}
            )

            boost = EnergyBoost(
                user_id=user_id,
                boost_type=EnergyBoostType.DOUBLE_ENERGY.value,
                boost_name="能量翻倍Buff",
                boost_description="当日所有PK对战能量值翻倍",
                energy_multiplier=2.0,
                critical_hit_chance=0.0,
                protection_rate=0.0,
                is_active=True,
                valid_from=now,
                valid_until=today_end
            )
            db.add(boost)
            db.flush()

            transaction = StarDustTransaction(
                user_id=user_id,
                transaction_type="energy_boost_purchase",
                currency_type="point",
                amount=-price,
                balance_before=balance_before,
                balance_after=balance_before - price,
                related_type="energy_boost",
                related_id=str(boost.id),
                description="购买能量翻倍Buff"
            )
            db.add(transaction)

            db.commit()
            db.refresh(boost)

            return boost, None, "成功购买能量翻倍Buff！今日所有PK对战能量值翻倍！"

        except Exception as e:
            logger.error(f"购买能量Buff异常: user_id={user_id}, error={str(e)}", exc_info=True)
            db.rollback()
            return None, PKBattleErrorCode.PURCHASE_FAILED, f"购买失败: {str(e)}"

    def get_user_active_boosts(
        self,
        db: Session,
        user_id: int
    ) -> List[EnergyBoost]:
        """获取用户当前激活的所有Buff"""
        now = datetime.utcnow()
        return db.query(EnergyBoost).filter(
            EnergyBoost.user_id == user_id,
            EnergyBoost.is_active == True,
            EnergyBoost.valid_from <= now,
            EnergyBoost.valid_until > now
        ).order_by(EnergyBoost.created_at.desc()).all()


class PKService:
    """
    PK综合服务
    整合所有PK相关功能
    """

    _instance: Optional['PKService'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_services()
        return cls._instance

    def _init_services(self):
        self.config = DEFAULT_CONFIG
        self.energy_engine = PKEnergyEngine(self.config)
        self.match_service = PKMatchService(self.config, self.energy_engine)
        self.battle_engine = PKBattleEngine(self.config, self.energy_engine)
        self.shop_service = PKShopService(self.config)

    def get_user_pk_status(
        self,
        db: Session,
        user_id: int
    ) -> Dict[str, Any]:
        """获取用户PK状态"""
        daily_pk = self.match_service.get_or_create_daily_pk(db, user_id)
        energy_snapshot = self.energy_engine.get_or_create_energy_snapshot(db, user_id)

        active_boosts = self.shop_service.get_user_active_boosts(db, user_id)

        stats = db.query(UserPKStats).filter(UserPKStats.user_id == user_id).first()

        recent_matches = db.query(PKMatch).filter(
            or_(
                PKMatch.challenger_id == user_id,
                PKMatch.defender_id == user_id
            )
        ).order_by(PKMatch.created_at.desc()).limit(10).all()

        return {
            "daily_status": {
                "battle_date": daily_pk.battle_date,
                "free_challenges_used": daily_pk.free_challenges_used,
                "free_challenges_total": daily_pk.free_challenges_total,
                "free_remaining": max(0, daily_pk.free_challenges_total - daily_pk.free_challenges_used),
                "paid_challenges_used": daily_pk.paid_challenges_used,
                "paid_challenges_purchased": daily_pk.paid_challenges_purchased,
                "paid_remaining": max(0, daily_pk.paid_challenges_purchased - daily_pk.paid_challenges_used),
                "total_available": daily_pk.total_challenges_available,
                "can_challenge": daily_pk.can_challenge,
                "daily_wins": daily_pk.daily_wins,
                "daily_losses": daily_pk.daily_losses,
                "daily_draws": daily_pk.daily_draws,
                "fragments_earned": daily_pk.fragments_earned,
                "fragments_lost": daily_pk.fragments_lost,
            },
            "energy_snapshot": {
                "snapshot_date": energy_snapshot.snapshot_date,
                "daily_horoscope_score": energy_snapshot.daily_horoscope_score,
                "task_completion_score": energy_snapshot.task_completion_score,
                "total_energy_score": energy_snapshot.total_energy_score,
                "energy_boost_applied": energy_snapshot.energy_boost_applied,
                "pk_matches_count": energy_snapshot.pk_matches_count,
                "pk_wins": energy_snapshot.pk_wins,
            },
            "active_boosts": [
                {
                    "id": boost.id,
                    "boost_type": boost.boost_type,
                    "boost_name": boost.boost_name,
                    "energy_multiplier": boost.energy_multiplier,
                    "critical_hit_chance": boost.critical_hit_chance,
                    "valid_from": boost.valid_from.isoformat() if boost.valid_from else None,
                    "valid_until": boost.valid_until.isoformat() if boost.valid_until else None,
                }
                for boost in active_boosts
            ],
            "total_stats": {
                "total_matches": stats.total_matches if stats else 0,
                "total_wins": stats.total_wins if stats else 0,
                "total_losses": stats.total_losses if stats else 0,
                "total_draws": stats.total_draws if stats else 0,
                "win_rate": stats.win_rate if stats else 0.0,
                "net_fragments": stats.net_fragments if stats else 0,
                "current_win_streak": stats.current_win_streak if stats else 0,
                "best_win_streak": stats.best_win_streak if stats else 0,
            } if stats else None,
            "recent_matches": [self._match_to_dict(m, user_id) for m in recent_matches]
        }

    def get_match_detail(
        self,
        db: Session,
        match_id: int,
        user_id: int
    ) -> Optional[Dict[str, Any]]:
        """获取对战详情"""
        match = db.query(PKMatch).filter(PKMatch.id == match_id).first()

        if not match:
            return None

        if match.challenger_id != user_id and match.defender_id != user_id:
            return None

        return self._match_to_dict(match, user_id, include_detail=True)

    def _match_to_dict(
        self,
        match: PKMatch,
        user_id: int,
        include_detail: bool = False
    ) -> Dict[str, Any]:
        """将匹配记录转换为字典"""
        is_challenger = match.challenger_id == user_id

        result_detail = {}
        if match.result_detail and include_detail:
            try:
                result_detail = json.loads(match.result_detail)
            except Exception:
                pass

        return {
            "id": match.id,
            "match_no": match.match_no,
            "match_type": match.match_type,
            "status": match.status,

            "is_challenger": is_challenger,
            "opponent_id": match.defender_id if is_challenger else match.challenger_id,

            "my_energy": match.challenger_energy if is_challenger else match.defender_energy,
            "opponent_energy": match.defender_energy if is_challenger else match.challenger_energy,

            "wager_fragments": match.wager_fragments,
            "fragments_transferred": match.fragments_transferred,

            "result": match.result,
            "is_draw": match.is_draw,
            "is_critical_hit": match.is_challenger_critical if is_challenger else match.is_defender_critical,

            "result_detail": result_detail,

            "created_at": match.created_at.isoformat() if match.created_at else None,
            "match_started_at": match.match_started_at.isoformat() if match.match_started_at else None,
            "match_completed_at": match.match_completed_at.isoformat() if match.match_completed_at else None,
        }

    def get_pending_invites(
        self,
        db: Session,
        user_id: int
    ) -> List[Dict[str, Any]]:
        """获取待处理的邀请"""
        now = datetime.utcnow()

        invites = db.query(PKMatchInvite).filter(
            PKMatchInvite.invitee_id == user_id,
            PKMatchInvite.status == PKInviteStatus.PENDING.value,
            PKMatchInvite.expires_at > now
        ).order_by(PKMatchInvite.created_at.desc()).all()

        return [
            {
                "id": invite.id,
                "invite_code": invite.invite_code,
                "inviter_id": invite.inviter_id,
                "wager_fragments": invite.wager_fragments,
                "status": invite.status,
                "expires_at": invite.expires_at.isoformat() if invite.expires_at else None,
                "created_at": invite.created_at.isoformat() if invite.created_at else None,
            }
            for invite in invites
        ]

    def get_sent_invites(
        self,
        db: Session,
        user_id: int
    ) -> List[Dict[str, Any]]:
        """获取已发送的邀请"""
        invites = db.query(PKMatchInvite).filter(
            PKMatchInvite.inviter_id == user_id
        ).order_by(PKMatchInvite.created_at.desc()).limit(20).all()

        return [
            {
                "id": invite.id,
                "invite_code": invite.invite_code,
                "invitee_id": invite.invitee_id,
                "wager_fragments": invite.wager_fragments,
                "status": invite.status,
                "expires_at": invite.expires_at.isoformat() if invite.expires_at else None,
                "created_at": invite.created_at.isoformat() if invite.created_at else None,
                "accepted_at": invite.accepted_at.isoformat() if invite.accepted_at else None,
            }
            for invite in invites
        ]

    def get_waiting_matches(
        self,
        db: Session,
        user_id: int
    ) -> List[Dict[str, Any]]:
        """获取用户等待中的匹配"""
        now = datetime.utcnow()

        matches = db.query(PKMatch).filter(
            PKMatch.challenger_id == user_id,
            PKMatch.status == PKMatchStatus.WAITING.value,
            PKMatch.expires_at > now
        ).order_by(PKMatch.created_at.desc()).all()

        return [
            {
                "id": match.id,
                "match_no": match.match_no,
                "match_type": match.match_type,
                "wager_fragments": match.wager_fragments,
                "created_at": match.created_at.isoformat() if match.created_at else None,
                "expires_at": match.expires_at.isoformat() if match.expires_at else None,
            }
            for match in matches
        ]

    def cancel_waiting_match(
        self,
        db: Session,
        match_id: int,
        user_id: int
    ) -> Tuple[bool, Optional[PKBattleErrorCode], str]:
        """取消等待中的匹配"""
        match = db.query(PKMatch).filter(PKMatch.id == match_id).first()

        if not match:
            return False, PKBattleErrorCode.MATCH_NOT_FOUND, "匹配不存在"

        if match.challenger_id != user_id:
            return False, PKBattleErrorCode.MATCH_NOT_FOUND, "无权取消此匹配"

        if match.status != PKMatchStatus.WAITING.value:
            return False, PKBattleErrorCode.MATCH_NOT_IN_PROGRESS, "匹配不在等待状态"

        match.status = PKMatchStatus.CANCELLED.value
        db.commit()

        return True, None, "匹配已取消"


pk_service = PKService()


def get_pk_service() -> PKService:
    """获取PK服务单例"""
    return pk_service
