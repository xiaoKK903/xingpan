import logging
import json
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.models import (
    User,
    DailyCheckInReward,
    UserCheckInProgress,
    DailyCheckInRecord,
    UserCoupon,
    UserBenefit,
    UserCouponType,
    UserCouponStatus,
    UserBenefitType,
    CheckInRewardType,
    ProphecyTicket,
    UserVIP,
    VIPSubscription,
    VIPPlanType,
    StarDustTransaction,
    BlindBoxMatch
)

logger = logging.getLogger(__name__)


DEFAULT_CHECKIN_REWARDS = [
    {
        "day_number": 1,
        "reward_type": CheckInRewardType.STARDUST_FRAGMENT.value,
        "reward_amount": 10,
        "reward_name": "星元碎片 x10",
        "reward_description": "可用于兑换盲盒线索、购买特殊道具",
        "icon": "💎",
        "rarity": "common"
    },
    {
        "day_number": 2,
        "reward_type": CheckInRewardType.PROPHECY_TICKET.value,
        "reward_amount": 1,
        "reward_name": "预言券 x1",
        "reward_description": "可参与预言家礼堂竞猜活动",
        "icon": "🎫",
        "rarity": "uncommon"
    },
    {
        "day_number": 3,
        "reward_type": CheckInRewardType.COUPON.value,
        "reward_amount": 1,
        "reward_value": json.dumps({
            "coupon_type": UserCouponType.BLIND_BOX_DISCOUNT.value,
            "discount_type": "percentage",
            "discount_value": 0.5,
            "valid_days": 7
        }),
        "reward_name": "盲盒5折优惠券",
        "reward_description": "盲盒相关消费享受5折优惠，有效期7天",
        "icon": "🎁",
        "rarity": "rare"
    },
    {
        "day_number": 4,
        "reward_type": CheckInRewardType.STARDUST_FRAGMENT.value,
        "reward_amount": 20,
        "reward_name": "星元碎片 x20",
        "reward_description": "可用于兑换盲盒线索、购买特殊道具",
        "icon": "💎",
        "rarity": "uncommon"
    },
    {
        "day_number": 5,
        "reward_type": CheckInRewardType.BENEFIT.value,
        "reward_amount": 1,
        "reward_value": json.dumps({
            "benefit_type": UserBenefitType.SYNASTRY_FREE.value,
            "valid_days": 7
        }),
        "reward_name": "双人合盘深度解读免费权益",
        "reward_description": "可免费享受1次双人合盘深度解读服务，有效期7天",
        "icon": "💕",
        "rarity": "rare"
    },
    {
        "day_number": 6,
        "reward_type": CheckInRewardType.BLIND_BOX.value,
        "reward_amount": 1,
        "reward_name": "免费星图盲盒 x1",
        "reward_description": "可免费抽取1次星图盲盒",
        "icon": "📦",
        "rarity": "epic"
    },
    {
        "day_number": 7,
        "reward_type": CheckInRewardType.VIP_TRIAL.value,
        "reward_amount": 7,
        "reward_name": "VIP会员7天体验卡",
        "reward_description": "享受7天星钻会员全部特权",
        "icon": "⭐",
        "rarity": "legendary"
    }
]


class CheckInService:
    """
    每日签到服务
    
    核心功能：
    - 签到状态查询
    - 执行签到
    - 连续签到进度管理
    - 奖励自动发放
    - 签到历史查询
    """
    
    _instance: Optional['CheckInService'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def initialize_default_rewards(self, db: Session) -> List[Dict[str, Any]]:
        """
        初始化默认签到奖励配置
        """
        try:
            created_rewards = []
            
            for reward_data in DEFAULT_CHECKIN_REWARDS:
                existing = db.query(DailyCheckInReward).filter(
                    DailyCheckInReward.day_number == reward_data["day_number"]
                ).first()
                
                if existing:
                    created_rewards.append(self._reward_to_dict(existing))
                    continue
                
                reward = DailyCheckInReward(
                    day_number=reward_data["day_number"],
                    reward_type=reward_data["reward_type"],
                    reward_amount=reward_data["reward_amount"],
                    reward_value=reward_data.get("reward_value"),
                    reward_name=reward_data["reward_name"],
                    reward_description=reward_data["reward_description"],
                    icon=reward_data.get("icon"),
                    rarity=reward_data.get("rarity", "common"),
                    is_active=True
                )
                
                db.add(reward)
                db.flush()
                
                created_rewards.append(self._reward_to_dict(reward))
                logger.info(f"创建签到奖励配置: 第{reward.day_number}天 - {reward.reward_name}")
            
            db.commit()
            return created_rewards
            
        except Exception as e:
            db.rollback()
            logger.error(f"初始化签到奖励配置异常: {str(e)}", exc_info=True)
            raise
    
    def get_checkin_status(self, db: Session, user_id: int) -> Dict[str, Any]:
        """
        获取用户签到状态
        """
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.warning(f"获取签到状态: 用户不存在, user_id={user_id}")
                return {
                    "success": False,
                    "error_code": "USER_NOT_FOUND",
                    "error": "用户不存在"
                }
            
            progress = self._get_or_create_progress(db, user_id)
            today = datetime.utcnow().strftime("%Y-%m-%d")
            
            has_checked_in_today = False
            if progress.last_checkin_date == today:
                has_checked_in_today = True
            
            rewards = self.get_active_rewards(db)
            
            today_reward = None
            tomorrow_reward = None
            
            next_streak_day = progress.current_streak + 1 if not has_checked_in_today else progress.current_streak
            if next_streak_day > 7:
                next_streak_day = 1
            
            for reward in rewards:
                if reward["day_number"] == next_streak_day:
                    tomorrow_reward = reward
                if has_checked_in_today and reward["day_number"] == progress.current_streak:
                    today_reward = reward
            
            recent_history = db.query(DailyCheckInRecord).filter(
                DailyCheckInRecord.user_id == user_id
            ).order_by(
                DailyCheckInRecord.checkin_at.desc()
            ).limit(7).all()
            
            logger.info(f"获取签到状态成功: user_id={user_id}, has_checked_in_today={has_checked_in_today}, current_streak={progress.current_streak}")
            
            return {
                "success": True,
                "data": {
                    "has_checked_in_today": has_checked_in_today,
                    "current_streak": progress.current_streak,
                    "best_streak": progress.best_streak,
                    "total_checkins": progress.total_checkins,
                    "last_checkin_at": progress.last_checkin_at.isoformat() if progress.last_checkin_at else None,
                    "next_reward": tomorrow_reward,
                    "today_reward": today_reward if has_checked_in_today else None,
                    "all_rewards": rewards,
                    "recent_history": [self._record_to_dict(r) for r in recent_history]
                }
            }
        except Exception as e:
            logger.error(f"获取签到状态异常: user_id={user_id}, error={str(e)}", exc_info=True)
            return {
                "success": False,
                "error_code": "CHECKIN_STATUS_ERROR",
                "error": f"获取签到状态失败: {str(e)}"
            }
    
    def perform_checkin(
        self, 
        db: Session, 
        user_id: int,
        ip_address: Optional[str] = None,
        device_info: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        执行签到
        
        逻辑：
        1. 检查今日是否已签到
        2. 计算连续签到天数（判断是否断签）
        3. 发放对应天数的奖励
        4. 更新签到进度
        5. 记录签到日志
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {
                "success": False,
                "error_code": "USER_NOT_FOUND",
                "error": "用户不存在"
            }
        
        progress = self._get_or_create_progress(db, user_id)
        today = datetime.utcnow().strftime("%Y-%m-%d")
        now = datetime.utcnow()
        
        if progress.last_checkin_date == today:
            return {
                "success": False,
                "error_code": "ALREADY_CHECKED_IN",
                "error": "今日已签到"
            }
        
        new_streak = self._calculate_new_streak(progress, today)
        
        reward_day = new_streak if new_streak <= 7 else 1
        
        reward = db.query(DailyCheckInReward).filter(
            DailyCheckInReward.day_number == reward_day,
            DailyCheckInReward.is_active == True
        ).first()
        
        if not reward:
            return {
                "success": False,
                "error_code": "REWARD_CONFIG_ERROR",
                "error": "签到奖励配置错误"
            }
        
        db.begin_nested()
        
        try:
            reward_result = self._grant_reward(db, user_id, reward)
            
            if not reward_result.get("success"):
                db.rollback()
                return reward_result
            
            record = DailyCheckInRecord(
                user_id=user_id,
                checkin_date=today,
                checkin_at=now,
                streak_day_number=reward_day,
                reward_claimed=True,
                reward_type=reward.reward_type,
                reward_amount=reward.reward_amount,
                reward_name=reward.reward_name,
                ip_address=ip_address,
                device_info=device_info
            )
            db.add(record)
            
            progress.current_streak = new_streak
            progress.last_checkin_at = now
            progress.last_checkin_date = today
            progress.total_checkins += 1
            progress.total_rewards_claimed += 1
            
            if new_streak > progress.best_streak:
                progress.best_streak = new_streak
            
            db.commit()
            db.refresh(progress)
            db.refresh(record)
            
            logger.info(f"用户 {user_id} 签到成功，连续签到 {new_streak} 天，获得奖励: {reward.reward_name}")
            
            return {
                "success": True,
                "message": "签到成功！",
                "data": {
                    "checkin_record": self._record_to_dict(record),
                    "current_streak": new_streak,
                    "best_streak": progress.best_streak,
                    "reward": self._reward_to_dict(reward),
                    "reward_result": reward_result.get("data")
                }
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"签到失败: {e}")
            return {
                "success": False,
                "error_code": "CHECKIN_FAILED",
                "error": str(e)
            }
    
    def get_active_rewards(self, db: Session) -> List[Dict[str, Any]]:
        """
        获取所有激活的签到奖励配置
        """
        rewards = db.query(DailyCheckInReward).filter(
            DailyCheckInReward.is_active == True
        ).order_by(
            DailyCheckInReward.day_number.asc()
        ).all()
        
        return [self._reward_to_dict(r) for r in rewards]
    
    def get_checkin_history(
        self, 
        db: Session, 
        user_id: int, 
        page: int = 1, 
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        获取签到历史记录
        """
        query = db.query(DailyCheckInRecord).filter(
            DailyCheckInRecord.user_id == user_id
        )
        
        total = query.count()
        
        records = query.order_by(
            DailyCheckInRecord.checkin_at.desc()
        ).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        return {
            "success": True,
            "data": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "records": [self._record_to_dict(r) for r in records]
            }
        }
    
    def _get_or_create_progress(self, db: Session, user_id: int) -> UserCheckInProgress:
        """
        获取或创建用户签到进度
        """
        try:
            progress = db.query(UserCheckInProgress).filter(
                UserCheckInProgress.user_id == user_id
            ).first()
            
            if not progress:
                progress = UserCheckInProgress(
                    user_id=user_id,
                    current_streak=0,
                    best_streak=0,
                    total_checkins=0,
                    total_rewards_claimed=0
                )
                db.add(progress)
                db.flush()
                logger.info(f"创建用户签到进度: user_id={user_id}")
            
            return progress
        except Exception as e:
            logger.error(f"获取或创建用户签到进度异常: user_id={user_id}, error={str(e)}", exc_info=True)
            raise
    
    def _calculate_new_streak(self, progress: UserCheckInProgress, today: str) -> int:
        """
        计算新的连续签到天数
        
        逻辑：
        - 如果昨天签到了，连续天数 +1
        - 如果断签了（超过1天），重置为1
        - 如果是第一次签到，从1开始
        """
        if not progress.last_checkin_date:
            return 1
        
        last_date = datetime.strptime(progress.last_checkin_date, "%Y-%m-%d").date()
        today_date = datetime.strptime(today, "%Y-%m-%d").date()
        
        days_diff = (today_date - last_date).days
        
        if days_diff == 1:
            return progress.current_streak + 1
        elif days_diff > 1:
            return 1
        else:
            return progress.current_streak
    
    def _grant_reward(
        self, 
        db: Session, 
        user_id: int, 
        reward: DailyCheckInReward
    ) -> Dict[str, Any]:
        """
        根据奖励类型发放奖励
        """
        reward_type = reward.reward_type
        amount = reward.reward_amount
        reward_value = {}
        
        if reward.reward_value:
            try:
                reward_value = json.loads(reward.reward_value)
            except:
                reward_value = {}
        
        user = db.query(User).filter(User.id == user_id).first()
        now = datetime.utcnow()
        
        if reward_type == CheckInRewardType.STARDUST_FRAGMENT.value:
            return self._grant_stardust_fragments(db, user, amount, reward.reward_name)
        
        elif reward_type == CheckInRewardType.PROPHECY_TICKET.value:
            return self._grant_prophecy_tickets(db, user_id, amount, reward.reward_name)
        
        elif reward_type == CheckInRewardType.COUPON.value:
            return self._grant_coupon(db, user_id, reward_value, reward.reward_name)
        
        elif reward_type == CheckInRewardType.BENEFIT.value:
            return self._grant_benefit(db, user_id, reward_value, reward.reward_name)
        
        elif reward_type == CheckInRewardType.BLIND_BOX.value:
            return self._grant_free_blind_box(db, user_id, amount, reward.reward_name)
        
        elif reward_type == CheckInRewardType.VIP_TRIAL.value:
            return self._grant_vip_trial(db, user_id, amount, reward.reward_name)
        
        else:
            return {
                "success": False,
                "error_code": "UNKNOWN_REWARD_TYPE",
                "error": f"未知的奖励类型: {reward_type}"
            }
    
    def _grant_stardust_fragments(
        self, 
        db: Session, 
        user: User, 
        amount: int, 
        reward_name: str
    ) -> Dict[str, Any]:
        """
        发放星元碎片
        """
        balance_before = user.stardust_fragment_balance or 0
        balance_after = balance_before + amount
        
        user.stardust_fragment_balance = balance_after
        
        transaction = StarDustTransaction(
            user_id=user.id,
            transaction_type="checkin_reward",
            currency_type="fragment",
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            related_type="checkin_reward",
            description=f"签到奖励: {reward_name}"
        )
        db.add(transaction)
        
        return {
            "success": True,
            "data": {
                "type": "stardust_fragment",
                "amount": amount,
                "balance_before": balance_before,
                "balance_after": balance_after
            }
        }
    
    def _grant_prophecy_tickets(
        self, 
        db: Session, 
        user_id: int, 
        amount: int, 
        reward_name: str
    ) -> Dict[str, Any]:
        """
        发放预言券
        """
        now = datetime.utcnow()
        valid_until = now + timedelta(days=30)
        
        created_tickets = []
        for _ in range(amount):
            ticket = ProphecyTicket(
                user_id=user_id,
                ticket_type="checkin_reward",
                is_used=False,
                valid_from=now,
                valid_until=valid_until
            )
            db.add(ticket)
            db.flush()
            created_tickets.append(ticket.id)
        
        return {
            "success": True,
            "data": {
                "type": "prophecy_ticket",
                "amount": amount,
                "ticket_ids": created_tickets,
                "valid_until": valid_until.isoformat()
            }
        }
    
    def _grant_coupon(
        self, 
        db: Session, 
        user_id: int, 
        reward_value: Dict, 
        reward_name: str
    ) -> Dict[str, Any]:
        """
        发放优惠券
        """
        now = datetime.utcnow()
        valid_days = reward_value.get("valid_days", 7)
        valid_until = now + timedelta(days=valid_days)
        
        coupon_no = f"CPN{now.strftime('%Y%m%d')}{uuid.uuid4().hex[:8].upper()}"
        
        coupon = UserCoupon(
            user_id=user_id,
            coupon_no=coupon_no,
            coupon_type=reward_value.get("coupon_type", UserCouponType.BLIND_BOX_DISCOUNT.value),
            coupon_name=reward_name,
            coupon_description=reward_value.get("description", ""),
            discount_type=reward_value.get("discount_type", "percentage"),
            discount_value=reward_value.get("discount_value", 0.5),
            discount_max_amount=reward_value.get("discount_max_amount"),
            min_spend_amount=reward_value.get("min_spend_amount", 0),
            source_type="checkin_reward",
            status=UserCouponStatus.ACTIVE.value,
            valid_from=now,
            valid_until=valid_until
        )
        
        db.add(coupon)
        db.flush()
        
        return {
            "success": True,
            "data": {
                "type": "coupon",
                "coupon_no": coupon_no,
                "coupon_type": coupon.coupon_type,
                "discount_type": coupon.discount_type,
                "discount_value": coupon.discount_value,
                "valid_until": valid_until.isoformat()
            }
        }
    
    def _grant_benefit(
        self, 
        db: Session, 
        user_id: int, 
        reward_value: Dict, 
        reward_name: str
    ) -> Dict[str, Any]:
        """
        发放权益
        """
        now = datetime.utcnow()
        valid_days = reward_value.get("valid_days", 7)
        valid_until = now + timedelta(days=valid_days)
        
        benefit = UserBenefit(
            user_id=user_id,
            benefit_type=reward_value.get("benefit_type", UserBenefitType.SYNASTRY_FREE.value),
            benefit_name=reward_name,
            benefit_description=reward_value.get("description", ""),
            total_count=1,
            used_count=0,
            remaining_count=1,
            source_type="checkin_reward",
            valid_from=now,
            valid_until=valid_until
        )
        
        db.add(benefit)
        db.flush()
        
        return {
            "success": True,
            "data": {
                "type": "benefit",
                "benefit_type": benefit.benefit_type,
                "benefit_name": benefit.benefit_name,
                "remaining_count": 1,
                "valid_until": valid_until.isoformat()
            }
        }
    
    def _grant_free_blind_box(
        self, 
        db: Session, 
        user_id: int, 
        amount: int, 
        reward_name: str
    ) -> Dict[str, Any]:
        """
        发放免费盲盒权益
        实际上是创建一个特殊的优惠券类型
        """
        now = datetime.utcnow()
        valid_until = now + timedelta(days=7)
        
        coupon_no = f"BOX{now.strftime('%Y%m%d')}{uuid.uuid4().hex[:8].upper()}"
        
        coupon = UserCoupon(
            user_id=user_id,
            coupon_no=coupon_no,
            coupon_type="blind_box_free",
            coupon_name=reward_name,
            coupon_description="免费抽取1次星图盲盒",
            discount_type="free",
            discount_value=1.0,
            min_spend_amount=0,
            source_type="checkin_reward",
            status=UserCouponStatus.ACTIVE.value,
            valid_from=now,
            valid_until=valid_until
        )
        
        db.add(coupon)
        db.flush()
        
        return {
            "success": True,
            "data": {
                "type": "blind_box_free",
                "coupon_no": coupon_no,
                "valid_until": valid_until.isoformat()
            }
        }
    
    def _grant_vip_trial(
        self, 
        db: Session, 
        user_id: int, 
        days: int, 
        reward_name: str
    ) -> Dict[str, Any]:
        """
        发放VIP体验卡
        """
        from app.services.vip_service import get_or_create_user_vip
        
        now = datetime.utcnow()
        
        user_vip = get_or_create_user_vip(db, user_id)
        
        if user_vip.is_vip and user_vip.expires_at and user_vip.expires_at > now:
            start_at = user_vip.expires_at
        else:
            start_at = now
        
        expires_at = start_at + timedelta(days=days)
        
        user_vip.is_vip = True
        user_vip.plan_type = "trial" if user_vip.plan_type is None else user_vip.plan_type
        user_vip.started_at = start_at
        user_vip.expires_at = expires_at
        
        subscription = VIPSubscription(
            user_id=user_id,
            subscription_no=f"VIP{now.strftime('%Y%m%d')}{uuid.uuid4().hex[:8].upper()}",
            plan_type="trial",
            price=0,
            discount_amount=0,
            duration_days=days,
            started_at=start_at,
            expires_at=expires_at,
            status="active",
            is_auto_renew=False
        )
        
        db.add(subscription)
        
        return {
            "success": True,
            "data": {
                "type": "vip_trial",
                "days": days,
                "started_at": start_at.isoformat(),
                "expires_at": expires_at.isoformat()
            }
        }
    
    def _reward_to_dict(self, reward: DailyCheckInReward) -> Dict[str, Any]:
        reward_value = {}
        if reward.reward_value:
            try:
                reward_value = json.loads(reward.reward_value)
            except:
                reward_value = {}
        
        return {
            "id": reward.id,
            "day_number": reward.day_number,
            "reward_type": reward.reward_type,
            "reward_amount": reward.reward_amount,
            "reward_value": reward_value,
            "reward_name": reward.reward_name,
            "reward_description": reward.reward_description,
            "icon": reward.icon,
            "rarity": reward.rarity,
            "is_active": reward.is_active
        }
    
    def _record_to_dict(self, record: DailyCheckInRecord) -> Dict[str, Any]:
        return {
            "id": record.id,
            "user_id": record.user_id,
            "checkin_date": record.checkin_date,
            "checkin_at": record.checkin_at.isoformat() if record.checkin_at else None,
            "streak_day_number": record.streak_day_number,
            "reward_claimed": record.reward_claimed,
            "reward_type": record.reward_type,
            "reward_amount": record.reward_amount,
            "reward_name": record.reward_name,
            "ip_address": record.ip_address,
            "created_at": record.created_at.isoformat() if record.created_at else None
        }


checkin_service = CheckInService()


def get_checkin_service() -> CheckInService:
    return checkin_service
