import logging
import json
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import and_, func, text, update, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.models import (
    User,
    CollectivePrediction,
    PredictionVote,
    PredictionOptionStat,
    RewardClaimRecord,
    VoteAssetLock,
    RateLimitRecord,
    AbnormalBehaviorLog,
    TieredVoteCost,
    ProphecyTicket,
    StarDustTransaction,
    SessionType,
    RewardAssetType,
    OracleDataSource,
    VoteAssetType
)

logger = logging.getLogger(__name__)


class RateLimitConfig:
    VOTE_PER_MINUTE = 5
    VOTE_PER_HOUR = 20
    VOTE_PER_DAY = 50
    
    SUSPICIOUS_INTERVAL_SECONDS = 1
    SUSPICIOUS_CONSECUTIVE_VOTES = 3


class VoteErrorCode(str, Enum):
    PREDICTION_NOT_FOUND = "PREDICTION_NOT_FOUND"
    VOTING_NOT_STARTED = "VOTING_NOT_STARTED"
    VOTING_ENDED = "VOTING_ENDED"
    ALREADY_RESOLVED = "ALREADY_RESOLVED"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    MAX_VOTES_EXCEEDED = "MAX_VOTES_EXCEEDED"
    INSUFFICIENT_ASSETS = "INSUFFICIENT_ASSETS"
    INVALID_OPTION = "INVALID_OPTION"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    SUSPICIOUS_ACTIVITY = "SUSPICIOUS_ACTIVITY"
    ASSET_LOCK_FAILED = "ASSET_LOCK_FAILED"
    CONCURRENT_CONFLICT = "CONCURRENT_CONFLICT"
    INVALID_ASSET_TYPE = "INVALID_ASSET_TYPE"
    TIER_NOT_CONFIGURED = "TIER_NOT_CONFIGURED"


@dataclass
class SecureVoteResult:
    success: bool
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    vote_id: Optional[int] = None
    vote_number: Optional[int] = None
    prediction_id: Optional[int] = None
    user_id: Optional[int] = None
    selected_option: Optional[str] = None
    cost_amount: int = 0
    cost_asset_type: Optional[str] = None
    reward_multiplier: float = 1.0


@dataclass
class RateLimitCheckResult:
    allowed: bool
    remaining: int
    reset_time: Optional[datetime] = None
    block_reason: Optional[str] = None
    risk_score: float = 0.0


class SecurePredictionService:
    """
    安全的并发投票服务
    
    核心特性：
    1. 行级锁 + 事务确保数据一致性
    2. 独立统计表替代JSON，支持原子累加
    3. 资产锁定机制防止重复扣资
    4. 阶梯式付费规则
    5. 接口限流 + 异常行为检测
    6. 防重复领取机制
    7. 统一时区处理
    """
    
    _instance: Optional['SecurePredictionService'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def _get_current_time(self) -> datetime:
        return datetime.utcnow()
    
    def check_rate_limit(
        self,
        db: Session,
        user_id: int,
        action_type: str = "vote",
        ip_address: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> RateLimitCheckResult:
        """
        检查接口限流
        
        规则：
        - 每分钟最多 N 次
        - 每小时最多 N 次
        - 每天最多 N 次
        - 检测异常快速投票
        """
        now = self._get_current_time()
        
        window_minute_start = now.replace(second=0, microsecond=0)
        window_minute_end = window_minute_start + timedelta(minutes=1)
        
        window_hour_start = now.replace(minute=0, second=0, microsecond=0)
        window_hour_end = window_hour_start + timedelta(hours=1)
        
        window_day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        window_day_end = window_day_start + timedelta(days=1)
        
        blocked_record = db.query(RateLimitRecord).filter(
            RateLimitRecord.user_id == user_id,
            RateLimitRecord.action_type == action_type,
            RateLimitRecord.is_blocked == True,
            RateLimitRecord.window_end > now
        ).first()
        
        if blocked_record:
            return RateLimitCheckResult(
                allowed=False,
                remaining=0,
                reset_time=blocked_record.window_end,
                block_reason=blocked_record.blocked_reason,
                risk_score=1.0
            )
        
        def get_or_create_record(window_start: datetime, window_end: datetime) -> RateLimitRecord:
            record = db.query(RateLimitRecord).filter(
                RateLimitRecord.user_id == user_id,
                RateLimitRecord.action_type == action_type,
                RateLimitRecord.window_start == window_start
            ).with_for_update().first()
            
            if not record:
                record = RateLimitRecord(
                    user_id=user_id,
                    ip_address=ip_address,
                    action_type=action_type,
                    action_count=0,
                    window_start=window_start,
                    window_end=window_end,
                    is_blocked=False
                )
                db.add(record)
                db.flush()
            
            return record
        
        minute_record = get_or_create_record(window_minute_start, window_minute_end)
        hour_record = get_or_create_record(window_hour_start, window_hour_end)
        day_record = get_or_create_record(window_day_start, window_day_end)
        
        risk_score = 0.0
        block_reason = None
        
        if minute_record.action_count >= RateLimitConfig.VOTE_PER_MINUTE:
            risk_score = 0.9
            block_reason = f"分钟级限流: {RateLimitConfig.VOTE_PER_MINUTE}次/分钟"
        
        elif hour_record.action_count >= RateLimitConfig.VOTE_PER_HOUR:
            risk_score = 0.8
            block_reason = f"小时级限流: {RateLimitConfig.VOTE_PER_HOUR}次/小时"
        
        elif day_record.action_count >= RateLimitConfig.VOTE_PER_DAY:
            risk_score = 0.7
            block_reason = f"每日限流: {RateLimitConfig.VOTE_PER_DAY}次/天"
        
        recent_votes = db.query(PredictionVote).filter(
            PredictionVote.user_id == user_id,
            PredictionVote.created_at >= now - timedelta(seconds=10)
        ).order_by(PredictionVote.created_at.desc()).limit(5).all()
        
        if len(recent_votes) >= RateLimitConfig.SUSPICIOUS_CONSECUTIVE_VOTES:
            intervals = []
            for i in range(len(recent_votes) - 1):
                if recent_votes[i].created_at and recent_votes[i + 1].created_at:
                    interval = (recent_votes[i].created_at - recent_votes[i + 1].created_at).total_seconds()
                    intervals.append(interval)
            
            if intervals and all(i < RateLimitConfig.SUSPICIOUS_INTERVAL_SECONDS for i in intervals):
                risk_score = 0.95
                block_reason = "异常快速投票，疑似脚本刷票"
                
                self._log_abnormal_behavior(
                    db, user_id, ip_address, session_id,
                    "suspicious_rapid_voting", "high",
                    risk_score, "连续快速投票检测"
                )
        
        if block_reason:
            minute_record.is_blocked = True
            minute_record.blocked_reason = block_reason
            minute_record.risk_score = risk_score
            db.commit()
            
            return RateLimitCheckResult(
                allowed=False,
                remaining=0,
                reset_time=window_minute_end,
                block_reason=block_reason,
                risk_score=risk_score
            )
        
        minute_record.action_count += 1
        hour_record.action_count += 1
        day_record.action_count += 1
        minute_record.risk_score = risk_score
        db.commit()
        
        remaining = min(
            RateLimitConfig.VOTE_PER_MINUTE - minute_record.action_count,
            RateLimitConfig.VOTE_PER_HOUR - hour_record.action_count,
            RateLimitConfig.VOTE_PER_DAY - day_record.action_count
        )
        
        return RateLimitCheckResult(
            allowed=True,
            remaining=remaining,
            reset_time=window_minute_end,
            risk_score=risk_score
        )
    
    def _log_abnormal_behavior(
        self,
        db: Session,
        user_id: int,
        ip_address: Optional[str],
        session_id: Optional[str],
        behavior_type: str,
        severity: str,
        risk_score: float,
        detection_rule: str,
        request_path: Optional[str] = None,
        request_method: Optional[str] = None,
        request_data: Optional[Dict] = None
    ):
        """
        记录异常行为日志
        """
        log = AbnormalBehaviorLog(
            user_id=user_id,
            ip_address=ip_address,
            session_id=session_id,
            behavior_type=behavior_type,
            severity=severity,
            request_data=json.dumps(request_data, ensure_ascii=False) if request_data else None,
            request_path=request_path,
            request_method=request_method,
            detection_rule=detection_rule,
            risk_score=risk_score,
            is_manual_reviewed=False,
            created_at=self._get_current_time()
        )
        db.add(log)
        db.commit()
        
        logger.warning(
            f"[异常行为检测] user={user_id}, type={behavior_type}, "
            f"severity={severity}, risk={risk_score}, rule={detection_rule}"
        )
    
    def get_tiered_cost(
        self,
        db: Session,
        prediction_id: int,
        vote_number: int
    ) -> Optional[Dict[str, Any]]:
        """
        获取阶梯式投票费用
        
        阶梯规则：
        - 第1票：基础费用（通常免费或低价）
        - 第2票：中等费用
        - 第3票及以上：高费用
        """
        prediction = db.query(CollectivePrediction).filter(
            CollectivePrediction.id == prediction_id
        ).first()
        
        if not prediction:
            return None
        
        tiered_costs = db.query(TieredVoteCost).filter(
            TieredVoteCost.prediction_id == prediction_id,
            TieredVoteCost.is_active == True
        ).order_by(TieredVoteCost.vote_tier.asc()).all()
        
        if not tiered_costs:
            max_votes = prediction.max_votes_per_user or 1
            
            for tier in range(1, max_votes + 1):
                if tier == 1:
                    cost = TieredVoteCost(
                        prediction_id=prediction_id,
                        vote_tier=tier,
                        allowed_asset_types="fragment,point,ticket",
                        cost_fragment=prediction.base_vote_cost or 0,
                        cost_point=0,
                        cost_ticket=0,
                        reward_multiplier=1.0,
                        is_active=True
                    )
                elif tier == 2:
                    cost = TieredVoteCost(
                        prediction_id=prediction_id,
                        vote_tier=tier,
                        allowed_asset_types="fragment,point",
                        cost_fragment=prediction.extra_vote_cost or 20,
                        cost_point=5,
                        cost_ticket=0,
                        reward_multiplier=1.2,
                        is_active=True
                    )
                else:
                    cost = TieredVoteCost(
                        prediction_id=prediction_id,
                        vote_tier=tier,
                        allowed_asset_types="point,ticket",
                        cost_fragment=0,
                        cost_point=10 * (tier - 1),
                        cost_ticket=1 * (tier - 2) if tier > 2 else 0,
                        reward_multiplier=1.0 + (tier - 1) * 0.1,
                        is_active=True
                    )
                db.add(cost)
                tiered_costs.append(cost)
            
            db.commit()
        
        for cost in tiered_costs:
            if cost.vote_tier == vote_number:
                return {
                    "vote_tier": cost.vote_tier,
                    "allowed_asset_types": cost.allowed_asset_types.split(","),
                    "cost_fragment": cost.cost_fragment,
                    "cost_point": cost.cost_point,
                    "cost_ticket": cost.cost_ticket,
                    "reward_multiplier": cost.reward_multiplier
                }
        
        if tiered_costs:
            highest_tier = max(tiered_costs, key=lambda x: x.vote_tier)
            return {
                "vote_tier": highest_tier.vote_tier,
                "allowed_asset_types": highest_tier.allowed_asset_types.split(","),
                "cost_fragment": highest_tier.cost_fragment,
                "cost_point": highest_tier.cost_point,
                "cost_ticket": highest_tier.cost_ticket,
                "reward_multiplier": highest_tier.reward_multiplier
            }
        
        return None
    
    def cast_vote_secure(
        self,
        db: Session,
        user_id: int,
        prediction_id: int,
        selected_option: str,
        use_asset_type: str = "fragment",
        confidence: int = 50,
        is_vip: bool = False,
        ip_address: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> SecureVoteResult:
        """
        安全投票（并发安全）
        
        完整流程：
        1. 限流检查
        2. 场次状态验证
        3. 投票次数和资产验证
        4. 资产锁定（防重复扣资）
        5. 创建投票记录
        6. 原子更新统计
        7. 提交事务
        """
        rate_limit = self.check_rate_limit(
            db, user_id, "vote", ip_address, session_id
        )
        
        if not rate_limit.allowed:
            return SecureVoteResult(
                success=False,
                error_code=VoteErrorCode.RATE_LIMIT_EXCEEDED,
                error_message=rate_limit.block_reason or "请求过于频繁"
            )
        
        if rate_limit.risk_score > 0.5:
            logger.warning(
                f"高风险投票请求: user={user_id}, risk={rate_limit.risk_score}"
            )
        
        try:
            db.begin_nested()
            
            prediction = db.query(CollectivePrediction).filter(
                CollectivePrediction.id == prediction_id
            ).with_for_update().first()
            
            if not prediction:
                db.rollback()
                return SecureVoteResult(
                    success=False,
                    error_code=VoteErrorCode.PREDICTION_NOT_FOUND,
                    error_message="预测场次不存在"
                )
            
            now = self._get_current_time()
            
            if prediction.voting_starts_at and prediction.voting_starts_at > now:
                db.rollback()
                return SecureVoteResult(
                    success=False,
                    error_code=VoteErrorCode.VOTING_NOT_STARTED,
                    error_message=f"投票尚未开始，开始时间: {prediction.voting_starts_at}"
                )
            
            if prediction.voting_ends_at and prediction.voting_ends_at <= now:
                db.rollback()
                return SecureVoteResult(
                    success=False,
                    error_code=VoteErrorCode.VOTING_ENDED,
                    error_message="投票已结束"
                )
            
            if prediction.is_resolved:
                db.rollback()
                return SecureVoteResult(
                    success=False,
                    error_code=VoteErrorCode.ALREADY_RESOLVED,
                    error_message="场次已结算"
                )
            
            user = db.query(User).filter(
                User.id == user_id
            ).with_for_update().first()
            
            if not user:
                db.rollback()
                return SecureVoteResult(
                    success=False,
                    error_code=VoteErrorCode.USER_NOT_FOUND,
                    error_message="用户不存在"
                )
            
            user_vote_count = db.query(func.count(PredictionVote.id)).filter(
                PredictionVote.prediction_id == prediction_id,
                PredictionVote.user_id == user_id
            ).scalar() or 0
            
            max_votes = prediction.max_votes_per_user or 1
            
            if user_vote_count >= max_votes:
                db.rollback()
                return SecureVoteResult(
                    success=False,
                    error_code=VoteErrorCode.MAX_VOTES_EXCEEDED,
                    error_message=f"已达到最大投票次数 ({max_votes}次)"
                )
            
            vote_number = user_vote_count + 1
            
            tier_config = self.get_tiered_cost(db, prediction_id, vote_number)
            
            if not tier_config:
                db.rollback()
                return SecureVoteResult(
                    success=False,
                    error_code=VoteErrorCode.TIER_NOT_CONFIGURED,
                    error_message="投票阶梯未配置"
                )
            
            allowed_assets = tier_config["allowed_asset_types"]
            if use_asset_type not in allowed_assets:
                db.rollback()
                return SecureVoteResult(
                    success=False,
                    error_code=VoteErrorCode.INVALID_ASSET_TYPE,
                    error_message=f"该场次第{vote_number}票不支持使用{use_asset_type}"
                )
            
            cost_amount = 0
            if use_asset_type == "fragment":
                cost_amount = tier_config["cost_fragment"]
            elif use_asset_type == "point":
                cost_amount = tier_config["cost_point"]
            elif use_asset_type == "ticket":
                cost_amount = tier_config["cost_ticket"]
            
            options = json.loads(prediction.options) if prediction.options else {}
            option_values = options.get("values", [])
            
            if selected_option not in option_values:
                db.rollback()
                return SecureVoteResult(
                    success=False,
                    error_code=VoteErrorCode.INVALID_OPTION,
                    error_message="无效的投票选项"
                )
            
            balance_sufficient = False
            
            if use_asset_type == "fragment":
                balance = user.stardust_fragment_balance or 0
                if balance >= cost_amount:
                    balance_sufficient = True
            
            elif use_asset_type == "point":
                balance = user.stardust_point_balance or 0
                if balance >= cost_amount:
                    balance_sufficient = True
            
            elif use_asset_type == "ticket":
                valid_tickets = db.query(func.count(ProphecyTicket.id)).filter(
                    ProphecyTicket.user_id == user_id,
                    ProphecyTicket.is_used == False,
                    ProphecyTicket.valid_until > now
                ).scalar() or 0
                if valid_tickets >= cost_amount:
                    balance_sufficient = True
            
            if not balance_sufficient:
                db.rollback()
                asset_name = {
                    "fragment": "星元碎片",
                    "point": "高阶星尘",
                    "ticket": "预言券"
                }.get(use_asset_type, use_asset_type)
                return SecureVoteResult(
                    success=False,
                    error_code=VoteErrorCode.INSUFFICIENT_ASSETS,
                    error_message=f"{asset_name}不足，需要 {cost_amount}"
                )
            
            lock_key = f"vote_{user_id}_{prediction_id}_{vote_number}_{int(now.timestamp() * 1000000)}"
            
            try:
                asset_lock = VoteAssetLock(
                    lock_key=lock_key,
                    user_id=user_id,
                    prediction_id=prediction_id,
                    vote_number=vote_number,
                    asset_type=use_asset_type,
                    amount=cost_amount,
                    is_processed=False,
                    expires_at=now + timedelta(minutes=5),
                    created_at=now
                )
                db.add(asset_lock)
                db.flush()
                
            except IntegrityError:
                db.rollback()
                return SecureVoteResult(
                    success=False,
                    error_code=VoteErrorCode.ASSET_LOCK_FAILED,
                    error_message="资产锁定失败，请勿重复提交"
                )
            
            if cost_amount > 0:
                self._deduct_asset_secure(
                    db, user, use_asset_type, cost_amount,
                    f"第{vote_number}票 - {prediction.title}",
                    prediction_id
                )
            
            reward_multiplier = tier_config["reward_multiplier"]
            
            if is_vip and prediction.is_vip_enabled:
                reward_multiplier *= (prediction.vip_multiplier or 1.5)
            
            vote_asset_enum = {
                "fragment": VoteAssetType.FRAGMENT,
                "point": VoteAssetType.POINT,
                "ticket": VoteAssetType.TICKET
            }.get(use_asset_type, VoteAssetType.FRAGMENT)
            
            vote = PredictionVote(
                prediction_id=prediction_id,
                user_id=user_id,
                vote_number=vote_number,
                selected_option=selected_option,
                confidence=max(0, min(100, confidence)),
                vote_asset_type=vote_asset_enum,
                vote_cost=cost_amount,
                stardust_bet=0,
                is_vip_bonus=is_vip and prediction.is_vip_enabled,
                applied_multiplier=reward_multiplier,
                is_correct=None,
                reward_earned=0,
                reward_asset_type=prediction.reward_asset_type,
                reward_claimed=False,
                is_validated=True,
                validated_at=now,
                created_at=now
            )
            
            db.add(vote)
            db.flush()
            
            asset_lock.is_processed = True
            asset_lock.processed_at = now
            
            self._update_option_stat_atomic(
                db, prediction_id, selected_option, cost_amount
            )
            
            prediction.total_votes = (prediction.total_votes or 0) + 1
            prediction.updated_at = now
            
            db.commit()
            
            logger.info(
                f"[安全投票成功] user={user_id}, prediction={prediction_id}, "
                f"vote_number={vote_number}, option={selected_option}, "
                f"asset={use_asset_type}, cost={cost_amount}"
            )
            
            return SecureVoteResult(
                success=True,
                vote_id=vote.id,
                vote_number=vote_number,
                prediction_id=prediction_id,
                user_id=user_id,
                selected_option=selected_option,
                cost_amount=cost_amount,
                cost_asset_type=use_asset_type,
                reward_multiplier=reward_multiplier
            )
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"[安全投票失败] 数据库错误: {e}")
            return SecureVoteResult(
                success=False,
                error_code=VoteErrorCode.CONCURRENT_CONFLICT,
                error_message=f"投票失败，请重试: {str(e)}"
            )
        
        except Exception as e:
            db.rollback()
            logger.error(f"[安全投票失败] 未知错误: {e}")
            return SecureVoteResult(
                success=False,
                error_code=VoteErrorCode.CONCURRENT_CONFLICT,
                error_message=f"投票失败: {str(e)}"
            )
    
    def _deduct_asset_secure(
        self,
        db: Session,
        user: User,
        asset_type: str,
        amount: int,
        description: str,
        prediction_id: int
    ) -> bool:
        """
        安全扣除资产（使用行级锁）
        """
        now = self._get_current_time()
        
        if asset_type == "fragment":
            balance_before = user.stardust_fragment_balance or 0
            if balance_before < amount:
                raise ValueError("星元碎片不足")
            
            user.stardust_fragment_balance = balance_before - amount
            currency_type = "fragment"
            
        elif asset_type == "point":
            balance_before = user.stardust_point_balance or 0
            if balance_before < amount:
                raise ValueError("高阶星尘不足")
            
            user.stardust_point_balance = balance_before - amount
            currency_type = "point"
            
        elif asset_type == "ticket":
            valid_tickets = db.query(ProphecyTicket).filter(
                ProphecyTicket.user_id == user.id,
                ProphecyTicket.is_used == False,
                ProphecyTicket.valid_until > now
            ).order_by(ProphecyTicket.valid_until.asc()).limit(amount).with_for_update().all()
            
            if len(valid_tickets) < amount:
                raise ValueError("预言券不足")
            
            for ticket in valid_tickets:
                ticket.is_used = True
                ticket.used_at = now
                ticket.used_for = f"prediction_{prediction_id}"
            
            return True
        
        else:
            raise ValueError(f"不支持的资产类型: {asset_type}")
        
        transaction = StarDustTransaction(
            user_id=user.id,
            transaction_type="prediction_vote_cost",
            currency_type=currency_type,
            amount=-amount,
            balance_before=balance_before,
            balance_after=balance_before - amount,
            related_type="prediction",
            related_id=str(prediction_id),
            description=description,
            created_at=now
        )
        
        db.add(transaction)
        
        return True
    
    def _update_option_stat_atomic(
        self,
        db: Session,
        prediction_id: int,
        option_value: str,
        amount: int
    ) -> bool:
        """
        原子更新选项统计
        
        使用独立的统计表替代JSON字段，支持原子累加
        """
        now = self._get_current_time()
        
        stat = db.query(PredictionOptionStat).filter(
            PredictionOptionStat.prediction_id == prediction_id,
            PredictionOptionStat.option_value == option_value
        ).with_for_update().first()
        
        if stat:
            stat.vote_count = stat.vote_count + 1
            stat.total_amount = stat.total_amount + amount
            stat.updated_at = now
        else:
            stat = PredictionOptionStat(
                prediction_id=prediction_id,
                option_value=option_value,
                vote_count=1,
                total_amount=amount,
                created_at=now,
                updated_at=now
            )
            db.add(stat)
        
        db.flush()
        
        return True
    
    def claim_reward_secure(
        self,
        db: Session,
        user_id: int,
        vote_id: int,
        ip_address: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        安全领取奖励（防重复领取）
        """
        now = self._get_current_time()
        
        try:
            db.begin_nested()
            
            existing_claim = db.query(RewardClaimRecord).filter(
                RewardClaimRecord.vote_id == vote_id
            ).with_for_update().first()
            
            if existing_claim:
                db.rollback()
                return {
                    "success": False,
                    "error_code": "ALREADY_CLAIMED",
                    "error": "奖励已领取"
                }
            
            vote = db.query(PredictionVote).filter(
                PredictionVote.id == vote_id,
                PredictionVote.user_id == user_id
            ).with_for_update().first()
            
            if not vote:
                db.rollback()
                return {
                    "success": False,
                    "error_code": "VOTE_NOT_FOUND",
                    "error": "投票记录不存在"
                }
            
            if vote.is_correct != True:
                db.rollback()
                return {
                    "success": False,
                    "error_code": "NOT_CORRECT",
                    "error": "未猜中，无法领取奖励"
                }
            
            if vote.reward_claimed:
                db.rollback()
                return {
                    "success": False,
                    "error_code": "ALREADY_CLAIMED",
                    "error": "奖励已领取"
                }
            
            prediction = db.query(CollectivePrediction).filter(
                CollectivePrediction.id == vote.prediction_id
            ).first()
            
            if not prediction or not prediction.is_resolved:
                db.rollback()
                return {
                    "success": False,
                    "error_code": "NOT_RESOLVED",
                    "error": "场次尚未结算"
                }
            
            base_reward = vote.reward_earned or prediction.base_reward_amount or 10
            
            if vote.applied_multiplier and vote.applied_multiplier > 1:
                base_reward = int(base_reward * vote.applied_multiplier)
            
            confidence = vote.confidence or 50
            if confidence >= 80:
                base_reward = int(base_reward * 1.5)
            elif confidence >= 50:
                base_reward = int(base_reward * 1.2)
            
            user = db.query(User).filter(
                User.id == user_id
            ).with_for_update().first()
            
            asset_type = vote.reward_asset_type or RewardAssetType.FRAGMENT
            
            self._grant_reward_secure(
                db, user, asset_type, base_reward,
                f"竞猜奖励 - {prediction.title}",
                prediction.id
            )
            
            claim_record = RewardClaimRecord(
                user_id=user_id,
                prediction_id=prediction.id,
                vote_id=vote_id,
                asset_type=asset_type,
                amount=base_reward,
                claimed_at=now,
                claim_ip=ip_address,
                claim_session=session_id,
                audit_note=f"成功领取奖励，金额={base_reward}",
                created_at=now
            )
            db.add(claim_record)
            
            vote.reward_claimed = True
            vote.reward_claimed_at = now
            vote.reward_earned = base_reward
            
            db.commit()
            
            logger.info(
                f"[奖励领取成功] user={user_id}, vote={vote_id}, "
                f"asset={asset_type}, amount={base_reward}"
            )
            
            return {
                "success": True,
                "message": "奖励领取成功",
                "reward_amount": base_reward,
                "reward_asset_type": asset_type,
                "claimed_at": now.isoformat()
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"[奖励领取失败] {e}")
            return {
                "success": False,
                "error_code": "CLAIM_FAILED",
                "error": str(e)
            }
    
    def _grant_reward_secure(
        self,
        db: Session,
        user: User,
        asset_type: str,
        amount: int,
        description: str,
        prediction_id: int
    ) -> bool:
        """
        安全发放奖励（使用行级锁）
        """
        now = self._get_current_time()
        
        if asset_type == RewardAssetType.FRAGMENT:
            balance_before = user.stardust_fragment_balance or 0
            user.stardust_fragment_balance = balance_before + amount
            currency_type = "fragment"
            
        elif asset_type == RewardAssetType.POINT:
            balance_before = user.stardust_point_balance or 0
            user.stardust_point_balance = balance_before + amount
            currency_type = "point"
            
        elif asset_type == RewardAssetType.TICKET:
            for _ in range(amount):
                ticket = ProphecyTicket(
                    user_id=user.id,
                    ticket_type="prediction_reward",
                    source_snapshot_id=None,
                    is_used=False,
                    valid_from=now,
                    valid_until=now + timedelta(days=30),
                    created_at=now
                )
                db.add(ticket)
            return True
        
        else:
            raise ValueError(f"不支持的奖励资产类型: {asset_type}")
        
        transaction = StarDustTransaction(
            user_id=user.id,
            transaction_type="prediction_reward",
            currency_type=currency_type,
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_before + amount,
            related_type="prediction",
            related_id=str(prediction_id),
            description=description,
            created_at=now
        )
        
        db.add(transaction)
        
        return True
    
    def get_prediction_detail_optimized(
        self,
        db: Session,
        prediction_id: int,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        优化的场次详情查询（消除N+1问题）
        
        使用 JOIN 和预加载减少数据库查询次数
        """
        from sqlalchemy.orm import joinedload
        
        prediction = db.query(CollectivePrediction).options(
            joinedload(CollectivePrediction.theme)
        ).filter(
            CollectivePrediction.id == prediction_id
        ).first()
        
        if not prediction:
            return {"error": "预测场次不存在"}
        
        stats = db.query(PredictionOptionStat).filter(
            PredictionOptionStat.prediction_id == prediction_id
        ).all()
        
        vote_distribution = {}
        for stat in stats:
            vote_distribution[stat.option_value] = stat.vote_count
        
        options = json.loads(prediction.options) if prediction.options else {}
        
        result = {
            "id": prediction.id,
            "prediction_date": prediction.prediction_date,
            "target_date": prediction.target_date,
            "title": prediction.title,
            "description": prediction.description,
            "prediction_type": prediction.prediction_type,
            "session_type": prediction.session_type,
            "session_key": prediction.session_key,
            
            "options": options.get("labels", []),
            "option_values": options.get("values", []),
            "option_icons": options.get("icons", []),
            
            "total_votes": prediction.total_votes or 0,
            "vote_distribution": vote_distribution,
            
            "status": prediction.status,
            "is_resolved": prediction.is_resolved,
            "resolved_at": prediction.resolved_at.isoformat() if prediction.resolved_at else None,
            "correct_option": prediction.correct_option,
            "accuracy_score": prediction.accuracy_score,
            
            "voting_starts_at": prediction.voting_starts_at.isoformat() if prediction.voting_starts_at else None,
            "voting_ends_at": prediction.voting_ends_at.isoformat() if prediction.voting_ends_at else None,
            
            "max_votes_per_user": prediction.max_votes_per_user or 1,
            "is_vip_enabled": prediction.is_vip_enabled,
            "vip_multiplier": prediction.vip_multiplier,
            
            "reward_asset_type": prediction.reward_asset_type,
            "base_reward_amount": prediction.base_reward_amount,
            
            "oracle_data_source": prediction.oracle_data_source,
            "resolution_evidence": prediction.resolution_evidence
        }
        
        if user_id:
            user_votes = db.query(PredictionVote).filter(
                PredictionVote.prediction_id == prediction_id,
                PredictionVote.user_id == user_id
            ).order_by(PredictionVote.vote_number.asc()).all()
            
            result["user_votes"] = [
                {
                    "id": v.id,
                    "vote_number": v.vote_number,
                    "selected_option": v.selected_option,
                    "confidence": v.confidence,
                    "is_correct": v.is_correct,
                    "reward_earned": v.reward_earned,
                    "reward_claimed": v.reward_claimed,
                    "cost_asset_type": v.vote_asset_type,
                    "vote_cost": v.vote_cost,
                    "created_at": v.created_at.isoformat() if v.created_at else None
                }
                for v in user_votes
            ]
            result["user_vote_count"] = len(user_votes)
            
            tiered_costs = db.query(TieredVoteCost).filter(
                TieredVoteCost.prediction_id == prediction_id,
                TieredVoteCost.is_active == True
            ).order_by(TieredVoteCost.vote_tier.asc()).all()
            
            result["tiered_costs"] = [
                {
                    "vote_tier": tc.vote_tier,
                    "allowed_asset_types": tc.allowed_asset_types.split(","),
                    "cost_fragment": tc.cost_fragment,
                    "cost_point": tc.cost_point,
                    "cost_ticket": tc.cost_ticket,
                    "reward_multiplier": tc.reward_multiplier
                }
                for tc in tiered_costs
            ]
        
        return result


secure_prediction_service = SecurePredictionService()


def get_secure_prediction_service() -> SecurePredictionService:
    return secure_prediction_service
