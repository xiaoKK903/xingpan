import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models import (
    User, UserDailyPK, EnergyBoost, PKMatchInvite, PKMatch,
    UserEnergySnapshot, PKTransaction, PKChallengePurchase, UserPKStats,
    PKMatchType, PKMatchStatus, PKBattleResult, EnergyBoostType, PKInviteStatus,
    DailyCheckInRecord, UserGrowthTask, GrowthTask, UserGrowthTaskStatus,
    Chart, StarDustTransaction, LeaderboardType, LeaderboardCycle
)

from app.services.pk_config import (
    DEFAULT_CONFIG,
    PKBattleErrorCode,
    generate_unique_no,
    generate_invite_code,
    get_today_str,
    logger
)

from app.services.pk_energy_service import PKEnergyEngine, get_energy_engine


class PKMatchService:
    """
    PK匹配服务
    负责随机匹配和好友对战
    """

    def __init__(self, config: Dict = None, energy_engine: PKEnergyEngine = None):
        self.config = config or DEFAULT_CONFIG
        self.energy_engine = energy_engine or get_energy_engine()

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


pk_match_service = PKMatchService()


def get_match_service() -> PKMatchService:
    """获取匹配服务单例"""
    return pk_match_service
