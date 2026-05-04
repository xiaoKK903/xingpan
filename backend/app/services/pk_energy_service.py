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


pk_energy_engine = PKEnergyEngine()


def get_energy_engine() -> PKEnergyEngine:
    """获取能量计算引擎单例"""
    return pk_energy_engine
