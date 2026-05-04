import logging
import json
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple, Type
from datetime import datetime, timedelta
from enum import Enum

from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_, func, or_

from app.models import (
    User,
    GrowthTask,
    UserGrowthTask,
    GrowthTaskLog,
    GrowthTaskType,
    GrowthTaskStatus,
    UserGrowthTaskStatus,
    FirstLoginPopup,
    Chart,
    SynastryRecord,
    GroupMatrix,
    DailyCheckInRecord,
    InviteShareLog,
    StarDustTransaction,
    ProphecyTicket,
    UserCoupon,
    UserCouponType,
    UserCouponStatus,
)

logger = logging.getLogger(__name__)


DEFAULT_GROWTH_TASKS = [
    {
        "task_key": "complete_chart",
        "task_type": GrowthTaskType.COMPLETE_CHART.value,
        "title": "完善个人星盘",
        "description": "创建您的个人星盘，解锁更多功能",
        "short_description": "创建个人星盘",
        "icon": "🌟",
        "rarity": "common",
        "sort_order": 1,
        "required_count": 1,
        "reward_type": "stardust_fragment",
        "reward_amount": 20,
        "reward_name": "星元碎片 x20",
        "is_auto_claim": True,
        "is_one_time": True,
        "is_new_user_only": True,
        "max_days_after_register": 30,
    },
    {
        "task_key": "complete_synastry",
        "task_type": GrowthTaskType.COMPLETE_SYNASTRY.value,
        "title": "完成双人合盘",
        "description": "与TA进行一次双人合盘分析",
        "short_description": "完成双人合盘",
        "icon": "💕",
        "rarity": "uncommon",
        "sort_order": 2,
        "required_count": 1,
        "reward_type": "prophecy_ticket",
        "reward_amount": 2,
        "reward_name": "预言券 x2",
        "is_auto_claim": True,
        "is_one_time": True,
        "is_new_user_only": True,
        "max_days_after_register": 30,
    },
    {
        "task_key": "join_group",
        "task_type": GrowthTaskType.JOIN_GROUP.value,
        "title": "加入群组",
        "description": "创建或加入一个星盘群组",
        "short_description": "加入群组",
        "icon": "👥",
        "rarity": "uncommon",
        "sort_order": 3,
        "required_count": 1,
        "reward_type": "stardust_fragment",
        "reward_amount": 30,
        "reward_name": "星元碎片 x30",
        "is_auto_claim": True,
        "is_one_time": True,
        "is_new_user_only": True,
        "max_days_after_register": 30,
    },
    {
        "task_key": "daily_checkin",
        "task_type": GrowthTaskType.DAILY_CHECKIN.value,
        "title": "每日签到",
        "description": "完成第一次每日签到",
        "short_description": "完成首次签到",
        "icon": "📅",
        "rarity": "common",
        "sort_order": 4,
        "required_count": 1,
        "reward_type": "stardust_fragment",
        "reward_amount": 10,
        "reward_name": "星元碎片 x10",
        "is_auto_claim": True,
        "is_one_time": True,
        "is_new_user_only": True,
        "max_days_after_register": 30,
    },
    {
        "task_key": "first_share",
        "task_type": GrowthTaskType.FIRST_SHARE.value,
        "title": "首次分享",
        "description": "分享您的星盘或合盘结果",
        "short_description": "首次分享",
        "icon": "📤",
        "rarity": "rare",
        "sort_order": 5,
        "required_count": 1,
        "reward_type": "coupon",
        "reward_amount": 1,
        "reward_value": {
            "coupon_type": UserCouponType.BLIND_BOX_DISCOUNT.value,
            "discount_type": "percentage",
            "discount_value": 0.5,
            "valid_days": 7
        },
        "reward_name": "盲盒5折优惠券",
        "is_auto_claim": True,
        "is_one_time": True,
        "is_new_user_only": True,
        "max_days_after_register": 30,
    },
]


class TaskErrorCode(str, Enum):
    USER_NOT_FOUND = "USER_NOT_FOUND"
    TASK_NOT_FOUND = "TASK_NOT_FOUND"
    TASK_CONFIG_NOT_FOUND = "TASK_CONFIG_NOT_FOUND"
    TASK_NOT_COMPLETED = "TASK_NOT_COMPLETED"
    TASK_NOT_AVAILABLE = "TASK_NOT_AVAILABLE"
    REWARD_ALREADY_CLAIMED = "REWARD_ALREADY_CLAIMED"
    UNKNOWN_REWARD_TYPE = "UNKNOWN_REWARD_TYPE"
    CHECK_COMPLETION_ERROR = "CHECK_COMPLETION_ERROR"
    CLAIM_REWARD_ERROR = "CLAIM_REWARD_ERROR"
    POPUP_ERROR = "POPUP_ERROR"
    TASK_OUT_OF_DATE = "TASK_OUT_OF_DATE"
    NOT_NEW_USER = "NOT_NEW_USER"
    CONCURRENT_CONFLICT = "CONCURRENT_CONFLICT"


class TaskVerifierStrategy(ABC):
    """任务验证策略接口"""
    
    @abstractmethod
    def get_task_type(self) -> str:
        """获取支持的任务类型"""
        pass
    
    @abstractmethod
    def verify(self, db: Session, user_id: int, task: GrowthTask, **kwargs) -> Tuple[bool, int]:
        """
        验证任务是否完成
        
        Returns:
            Tuple[bool, int]: (是否完成, 当前进度)
        """
        pass


class CompleteChartVerifier(TaskVerifierStrategy):
    """完善星盘任务验证器"""
    
    def get_task_type(self) -> str:
        return GrowthTaskType.COMPLETE_CHART.value
    
    def verify(self, db: Session, user_id: int, task: GrowthTask, **kwargs) -> Tuple[bool, int]:
        chart_id = kwargs.get("chart_id")
        
        if chart_id:
            chart = db.query(Chart).filter(
                Chart.id == chart_id,
                Chart.user_id == user_id,
                Chart.is_deleted == False
            ).first()
            current_count = 1 if chart else 0
        else:
            current_count = db.query(Chart).filter(
                Chart.user_id == user_id,
                Chart.is_deleted == False
            ).count()
        
        required_count = task.required_count or 1
        is_complete = current_count >= required_count
        
        return is_complete, current_count


class CompleteSynastryVerifier(TaskVerifierStrategy):
    """双人合盘任务验证器"""
    
    def get_task_type(self) -> str:
        return GrowthTaskType.COMPLETE_SYNASTRY.value
    
    def verify(self, db: Session, user_id: int, task: GrowthTask, **kwargs) -> Tuple[bool, int]:
        record_id = kwargs.get("synastry_record_id")
        
        if record_id:
            record = db.query(SynastryRecord).filter(
                SynastryRecord.id == record_id,
                SynastryRecord.user_id == user_id,
                SynastryRecord.is_deleted == False
            ).first()
            current_count = 1 if record else 0
        else:
            current_count = db.query(SynastryRecord).filter(
                SynastryRecord.user_id == user_id,
                SynastryRecord.is_deleted == False
            ).count()
        
        required_count = task.required_count or 1
        is_complete = current_count >= required_count
        
        return is_complete, current_count


class JoinGroupVerifier(TaskVerifierStrategy):
    """加入群组任务验证器"""
    
    def get_task_type(self) -> str:
        return GrowthTaskType.JOIN_GROUP.value
    
    def verify(self, db: Session, user_id: int, task: GrowthTask, **kwargs) -> Tuple[bool, int]:
        matrix_id = kwargs.get("group_matrix_id")
        
        if matrix_id:
            matrix = db.query(GroupMatrix).filter(
                GroupMatrix.id == matrix_id,
                GroupMatrix.user_id == user_id,
                GroupMatrix.is_deleted == False
            ).first()
            current_count = 1 if matrix else 0
        else:
            current_count = db.query(GroupMatrix).filter(
                GroupMatrix.user_id == user_id,
                GroupMatrix.is_deleted == False
            ).count()
        
        required_count = task.required_count or 1
        is_complete = current_count >= required_count
        
        return is_complete, current_count


class DailyCheckinVerifier(TaskVerifierStrategy):
    """每日签到任务验证器"""
    
    def get_task_type(self) -> str:
        return GrowthTaskType.DAILY_CHECKIN.value
    
    def verify(self, db: Session, user_id: int, task: GrowthTask, **kwargs) -> Tuple[bool, int]:
        current_count = db.query(DailyCheckInRecord).filter(
            DailyCheckInRecord.user_id == user_id
        ).count()
        
        required_count = task.required_count or 1
        is_complete = current_count >= required_count
        
        return is_complete, current_count


class FirstShareVerifier(TaskVerifierStrategy):
    """首次分享任务验证器"""
    
    def get_task_type(self) -> str:
        return GrowthTaskType.FIRST_SHARE.value
    
    def verify(self, db: Session, user_id: int, task: GrowthTask, **kwargs) -> Tuple[bool, int]:
        share_log_id = kwargs.get("share_log_id")
        
        if share_log_id:
            log = db.query(InviteShareLog).filter(
                InviteShareLog.id == share_log_id,
                InviteShareLog.user_id == user_id
            ).first()
            current_count = 1 if log else 0
        else:
            current_count = db.query(InviteShareLog).filter(
                InviteShareLog.user_id == user_id
            ).count()
        
        required_count = task.required_count or 1
        is_complete = current_count >= required_count
        
        return is_complete, current_count


class RewardGrantStrategy(ABC):
    """奖励发放策略接口"""
    
    @abstractmethod
    def get_reward_type(self) -> str:
        """获取支持的奖励类型"""
        pass
    
    @abstractmethod
    def grant(
        self,
        db: Session,
        user: User,
        user_task: UserGrowthTask,
        task: GrowthTask
    ) -> Dict[str, Any]:
        """
        发放奖励
        
        Returns:
            Dict[str, Any]: 发放结果
        """
        pass


class StardustFragmentReward(RewardGrantStrategy):
    """星元碎片奖励"""
    
    def get_reward_type(self) -> str:
        return "stardust_fragment"
    
    def grant(
        self,
        db: Session,
        user: User,
        user_task: UserGrowthTask,
        task: GrowthTask
    ) -> Dict[str, Any]:
        amount = task.reward_amount or 10
        balance_before = user.stardust_fragment_balance or 0
        balance_after = balance_before + amount
        
        user.stardust_fragment_balance = balance_after
        
        transaction = StarDustTransaction(
            user_id=user.id,
            transaction_type="growth_task_reward",
            currency_type="fragment",
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            related_type="growth_task",
            related_id=str(task.id),
            description=f"成长任务奖励: {task.title}"
        )
        db.add(transaction)
        db.flush()
        
        user_task.reward_claimed = True
        user_task.reward_transaction_id = transaction.id
        user_task.status = UserGrowthTaskStatus.CLAIMED.value
        user_task.claimed_at = datetime.utcnow()
        
        return {
            "success": True,
            "data": {
                "type": "stardust_fragment",
                "amount": amount,
                "balance_before": balance_before,
                "balance_after": balance_after,
                "reward_name": task.reward_name
            }
        }


class StardustPointReward(RewardGrantStrategy):
    """星元点数奖励"""
    
    def get_reward_type(self) -> str:
        return "stardust_point"
    
    def grant(
        self,
        db: Session,
        user: User,
        user_task: UserGrowthTask,
        task: GrowthTask
    ) -> Dict[str, Any]:
        amount = task.reward_amount or 10
        balance_before = user.stardust_point_balance or 0
        balance_after = balance_before + amount
        
        user.stardust_point_balance = balance_after
        
        transaction = StarDustTransaction(
            user_id=user.id,
            transaction_type="growth_task_reward",
            currency_type="point",
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            related_type="growth_task",
            related_id=str(task.id),
            description=f"成长任务奖励: {task.title}"
        )
        db.add(transaction)
        db.flush()
        
        user_task.reward_claimed = True
        user_task.reward_transaction_id = transaction.id
        user_task.status = UserGrowthTaskStatus.CLAIMED.value
        user_task.claimed_at = datetime.utcnow()
        
        return {
            "success": True,
            "data": {
                "type": "stardust_point",
                "amount": amount,
                "balance_before": balance_before,
                "balance_after": balance_after,
                "reward_name": task.reward_name
            }
        }


class ProphecyTicketReward(RewardGrantStrategy):
    """预言券奖励"""
    
    def get_reward_type(self) -> str:
        return "prophecy_ticket"
    
    def grant(
        self,
        db: Session,
        user: User,
        user_task: UserGrowthTask,
        task: GrowthTask
    ) -> Dict[str, Any]:
        amount = task.reward_amount or 1
        now = datetime.utcnow()
        valid_until = now + timedelta(days=30)
        
        created_tickets = []
        for _ in range(amount):
            ticket = ProphecyTicket(
                user_id=user.id,
                ticket_type="growth_task_reward",
                is_used=False,
                valid_from=now,
                valid_until=valid_until
            )
            db.add(ticket)
            db.flush()
            created_tickets.append(ticket.id)
        
        if created_tickets:
            user_task.reward_claimed = True
            user_task.reward_ticket_id = created_tickets[0]
            user_task.status = UserGrowthTaskStatus.CLAIMED.value
            user_task.claimed_at = datetime.utcnow()
        
        return {
            "success": True,
            "data": {
                "type": "prophecy_ticket",
                "amount": amount,
                "ticket_ids": created_tickets,
                "valid_until": valid_until.isoformat(),
                "reward_name": task.reward_name
            }
        }


class CouponReward(RewardGrantStrategy):
    """优惠券奖励"""
    
    def get_reward_type(self) -> str:
        return "coupon"
    
    def grant(
        self,
        db: Session,
        user: User,
        user_task: UserGrowthTask,
        task: GrowthTask
    ) -> Dict[str, Any]:
        reward_value = {}
        if task.reward_value:
            try:
                reward_value = json.loads(task.reward_value)
            except (json.JSONDecodeError, TypeError):
                reward_value = {}
        
        now = datetime.utcnow()
        valid_days = reward_value.get("valid_days", 7)
        valid_until = now + timedelta(days=valid_days)
        
        coupon_no = f"GT{now.strftime('%Y%m%d')}{uuid.uuid4().hex[:8].upper()}"
        
        coupon = UserCoupon(
            user_id=user.id,
            coupon_no=coupon_no,
            coupon_type=reward_value.get("coupon_type", UserCouponType.BLIND_BOX_DISCOUNT.value),
            coupon_name=task.reward_name or "成长任务优惠券",
            coupon_description=f"成长任务奖励: {task.title}",
            discount_type=reward_value.get("discount_type", "percentage"),
            discount_value=reward_value.get("discount_value", 0.5),
            discount_max_amount=reward_value.get("discount_max_amount"),
            min_spend_amount=reward_value.get("min_spend_amount", 0),
            source_type="growth_task",
            source_reference=str(task.id),
            status=UserCouponStatus.ACTIVE.value,
            valid_from=now,
            valid_until=valid_until
        )
        
        db.add(coupon)
        db.flush()
        
        user_task.reward_claimed = True
        user_task.reward_coupon_id = coupon.id
        user_task.status = UserGrowthTaskStatus.CLAIMED.value
        user_task.claimed_at = datetime.utcnow()
        
        return {
            "success": True,
            "data": {
                "type": "coupon",
                "coupon_no": coupon_no,
                "coupon_type": coupon.coupon_type,
                "discount_type": coupon.discount_type,
                "discount_value": coupon.discount_value,
                "valid_until": valid_until.isoformat(),
                "reward_name": task.reward_name
            }
        }


class GrowthTaskService:
    """
    成长任务服务
    
    重构说明：
    1. 使用策略模式替代大量 if/elif
    2. 添加并发控制（数据库行锁）
    3. 优化 N+1 查询（使用 selectinload）
    4. 规范异常处理（统一错误码，不暴露内部错误）
    5. 补全业务规则（新用户限定、时间范围、进度累积）
    """
    
    _instance: Optional['GrowthTaskService'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_strategies()
        return cls._instance
    
    def _init_strategies(self):
        """初始化策略"""
        self._task_verifiers: Dict[str, TaskVerifierStrategy] = {}
        self._reward_granters: Dict[str, RewardGrantStrategy] = {}
        
        verifiers = [
            CompleteChartVerifier(),
            CompleteSynastryVerifier(),
            JoinGroupVerifier(),
            DailyCheckinVerifier(),
            FirstShareVerifier(),
        ]
        for v in verifiers:
            self._task_verifiers[v.get_task_type()] = v
        
        granters = [
            StardustFragmentReward(),
            StardustPointReward(),
            ProphecyTicketReward(),
            CouponReward(),
        ]
        for g in granters:
            self._reward_granters[g.get_reward_type()] = g
    
    def initialize_default_tasks(self, db: Session) -> List[Dict[str, Any]]:
        """初始化默认成长任务配置"""
        try:
            created_tasks = []
            
            for task_data in DEFAULT_GROWTH_TASKS:
                existing = db.query(GrowthTask).filter(
                    GrowthTask.task_key == task_data["task_key"]
                ).first()
                
                if existing:
                    created_tasks.append(self._task_to_dict(existing))
                    continue
                
                reward_value = task_data.get("reward_value")
                reward_value_json = json.dumps(reward_value, ensure_ascii=False) if reward_value else None
                
                task = GrowthTask(
                    task_key=task_data["task_key"],
                    task_type=task_data["task_type"],
                    title=task_data["title"],
                    description=task_data["description"],
                    short_description=task_data.get("short_description"),
                    icon=task_data.get("icon"),
                    rarity=task_data.get("rarity", "common"),
                    sort_order=task_data.get("sort_order", 0),
                    required_count=task_data.get("required_count", 1),
                    reward_type=task_data["reward_type"],
                    reward_amount=task_data["reward_amount"],
                    reward_value=reward_value_json,
                    reward_name=task_data["reward_name"],
                    is_auto_claim=task_data.get("is_auto_claim", True),
                    is_one_time=task_data.get("is_one_time", True),
                    status=GrowthTaskStatus.ACTIVE.value,
                    is_new_user_only=task_data.get("is_new_user_only", True),
                    max_days_after_register=task_data.get("max_days_after_register"),
                )
                
                db.add(task)
                db.flush()
                
                created_tasks.append(self._task_to_dict(task))
                logger.info(f"创建成长任务配置: {task.task_key} - {task.title}")
            
            db.commit()
            return created_tasks
            
        except Exception as e:
            db.rollback()
            logger.error(f"初始化成长任务配置异常: {str(e)}", exc_info=True)
            raise
    
    def _is_task_available_for_user(
        self,
        db: Session,
        user: User,
        task: GrowthTask
    ) -> Tuple[bool, Optional[TaskErrorCode]]:
        """
        检查任务对用户是否可用
        
        业务规则：
        1. 新用户限定：is_new_user_only 且 max_days_after_register 限制
        2. 时间范围：start_at 到 end_at 之间
        3. 一次性任务：已完成则不可用
        """
        now = datetime.utcnow()
        
        if task.start_at and now < task.start_at:
            return False, TaskErrorCode.TASK_OUT_OF_DATE
        
        if task.end_at and now > task.end_at:
            return False, TaskErrorCode.TASK_OUT_OF_DATE
        
        if task.is_new_user_only and user.created_at:
            max_days = task.max_days_after_register or 30
            days_since_register = (now - user.created_at.replace(tzinfo=None)).days
            
            if days_since_register > max_days:
                return False, TaskErrorCode.NOT_NEW_USER
        
        return True, None
    
    def get_active_tasks(
        self,
        db: Session,
        user: Optional[User] = None
    ) -> List[Dict[str, Any]]:
        """获取所有激活的成长任务（可选过滤用户可用）"""
        now = datetime.utcnow()
        
        query = db.query(GrowthTask).filter(
            GrowthTask.status == GrowthTaskStatus.ACTIVE.value,
            GrowthTask.is_deleted == False,
            or_(GrowthTask.start_at == None, GrowthTask.start_at <= now),
            or_(GrowthTask.end_at == None, GrowthTask.end_at >= now)
        ).order_by(GrowthTask.sort_order.asc())
        
        tasks = query.all()
        
        result = []
        for t in tasks:
            if user:
                available, _ = self._is_task_available_for_user(db, user, t)
                if not available:
                    continue
            result.append(self._task_to_dict(t))
        
        return result
    
    def get_user_tasks(
        self, 
        db: Session, 
        user_id: int,
        include_completed: bool = True
    ) -> List[Dict[str, Any]]:
        """
        获取用户的任务进度列表
        
        优化：使用 selectinload 预加载 task，避免 N+1 查询
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return []
        
        self._ensure_user_tasks(db, user_id)
        
        user_tasks = db.query(UserGrowthTask).options(
            selectinload(UserGrowthTask.task)
        ).filter(
            UserGrowthTask.user_id == user_id,
            UserGrowthTask.is_deleted == False
        ).order_by(
            UserGrowthTask.status.asc()
        ).all()
        
        result = []
        for ut in user_tasks:
            if not include_completed and ut.status in [
                UserGrowthTaskStatus.COMPLETED.value,
                UserGrowthTaskStatus.CLAIMED.value
            ]:
                continue
            
            if ut.task:
                available, _ = self._is_task_available_for_user(db, user, ut.task)
                if not available:
                    continue
            
            task_dict = self._user_task_to_dict(ut)
            result.append(task_dict)
        
        return result
    
    def check_task_completion(
        self,
        db: Session,
        user_id: int,
        task_type: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        检测任务完成情况并自动发放奖励
        
        并发控制：
        1. 使用 with_for_update 对 UserGrowthTask 加行锁（等待锁，不跳过）
        2. 检查 reward_claimed 状态防止重复发放
        3. 锁超时返回"稍后重试"
        """
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {
                    "success": False, 
                    "error": "用户不存在", 
                    "code": TaskErrorCode.USER_NOT_FOUND.value
                }
            
            self._ensure_user_tasks(db, user_id)
            
            verifier = self._task_verifiers.get(task_type)
            if not verifier:
                return {
                    "success": True,
                    "data": {"message": f"不支持的任务类型: {task_type}", "completed_count": 0}
                }
            
            tasks = db.query(GrowthTask).filter(
                GrowthTask.task_type == task_type,
                GrowthTask.status == GrowthTaskStatus.ACTIVE.value,
                GrowthTask.is_deleted == False
            ).all()
            
            if not tasks:
                return {
                    "success": True,
                    "data": {"message": "没有匹配的任务", "completed_count": 0}
                }
            
            completed_count = 0
            rewards_earned = []
            
            for task in tasks:
                available, error_code = self._is_task_available_for_user(db, user, task)
                if not available:
                    logger.info(f"任务 {task.task_key} 对用户 {user_id} 不可用: {error_code}")
                    continue
                
                try:
                    user_task = db.query(UserGrowthTask).filter(
                        UserGrowthTask.user_id == user_id,
                        UserGrowthTask.task_id == task.id,
                        UserGrowthTask.is_deleted == False
                    ).with_for_update().first()
                except Exception as lock_error:
                    logger.warning(f"获取任务锁失败: user_id={user_id}, task_id={task.id}, error={str(lock_error)}")
                    return {
                        "success": False,
                        "error": "系统繁忙，请稍后重试",
                        "code": TaskErrorCode.CONCURRENT_CONFLICT.value
                    }
                
                if not user_task:
                    continue
                
                if user_task.reward_claimed:
                    continue
                
                if user_task.status == UserGrowthTaskStatus.CLAIMED.value:
                    continue
                
                is_complete, current_progress = verifier.verify(db, user_id, task, **kwargs)
                
                old_progress = user_task.progress_current
                progress_changed = False
                
                if old_progress != current_progress:
                    user_task.progress_current = current_progress
                    user_task.progress_target = task.required_count
                    progress_changed = True
                
                if is_complete and user_task.status != UserGrowthTaskStatus.COMPLETED.value and user_task.status != UserGrowthTaskStatus.CLAIMED.value:
                    user_task.status = UserGrowthTaskStatus.COMPLETED.value
                    user_task.completed_at = datetime.utcnow()
                    user_task.completion_proof = json.dumps({
                        "task_type": task_type,
                        "verified_at": datetime.utcnow().isoformat(),
                        "current_progress": current_progress,
                        **kwargs
                    }, ensure_ascii=False)
                    
                    self._log_task_action(
                        db, user_id, task.id, user_task.id,
                        "completed", f"任务完成: {task.title}",
                        progress_before=old_progress,
                        progress_after=current_progress
                    )
                    
                    if task.is_auto_claim:
                        reward_result = self._claim_reward_with_lock(db, user, user_task, task)
                        if reward_result.get("success"):
                            rewards_earned.append(reward_result.get("data"))
                    
                    completed_count += 1
                    logger.info(f"用户 {user_id} 完成任务: {task.task_key} - {task.title}")
                elif progress_changed:
                    self._log_task_action(
                        db, user_id, task.id, user_task.id,
                        "progress_updated", f"任务进度更新: {task.title}",
                        progress_before=old_progress,
                        progress_after=current_progress
                    )
            
            db.commit()
            
            return {
                "success": True,
                "data": {
                    "completed_count": completed_count,
                    "rewards_earned": rewards_earned
                }
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"检测任务完成异常: user_id={user_id}, task_type={task_type}, error={str(e)}", exc_info=True)
            return {
                "success": False, 
                "error": "任务检测失败，请稍后重试", 
                "code": TaskErrorCode.CHECK_COMPLETION_ERROR.value
            }
    
    def claim_task_reward(
        self,
        db: Session,
        user_id: int,
        task_id: int
    ) -> Dict[str, Any]:
        """
        用户手动领取任务奖励
        
        并发控制：
        1. 使用 with_for_update 加行锁（等待锁，不跳过）
        2. 检查 reward_claimed 状态
        3. 锁超时返回"稍后重试"
        """
        try:
            try:
                user_task = db.query(UserGrowthTask).filter(
                    UserGrowthTask.user_id == user_id,
                    UserGrowthTask.task_id == task_id,
                    UserGrowthTask.is_deleted == False
                ).with_for_update().first()
            except Exception as lock_error:
                logger.warning(f"获取任务奖励锁失败: user_id={user_id}, task_id={task_id}, error={str(lock_error)}")
                return {
                    "success": False,
                    "error": "系统繁忙，请稍后重试",
                    "code": TaskErrorCode.CONCURRENT_CONFLICT.value
                }
            
            if not user_task:
                return {
                    "success": False, 
                    "error": "任务不存在", 
                    "code": TaskErrorCode.TASK_NOT_FOUND.value
                }
            
            if user_task.reward_claimed:
                return {
                    "success": False, 
                    "error": "奖励已领取", 
                    "code": TaskErrorCode.REWARD_ALREADY_CLAIMED.value
                }
            
            if user_task.status == UserGrowthTaskStatus.CLAIMED.value:
                return {
                    "success": False, 
                    "error": "奖励已领取", 
                    "code": TaskErrorCode.REWARD_ALREADY_CLAIMED.value
                }
            
            if user_task.status != UserGrowthTaskStatus.COMPLETED.value:
                return {
                    "success": False, 
                    "error": "任务未完成，无法领取奖励", 
                    "code": TaskErrorCode.TASK_NOT_COMPLETED.value
                }
            
            task = db.query(GrowthTask).filter(
                GrowthTask.id == task_id,
                GrowthTask.is_deleted == False
            ).first()
            
            if not task:
                return {
                    "success": False, 
                    "error": "任务配置不存在", 
                    "code": TaskErrorCode.TASK_CONFIG_NOT_FOUND.value
                }
            
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {
                    "success": False, 
                    "error": "用户不存在", 
                    "code": TaskErrorCode.USER_NOT_FOUND.value
                }
            
            result = self._claim_reward_with_lock(db, user, user_task, task)
            
            if result.get("success"):
                db.commit()
                logger.info(f"用户 {user_id} 手动领取任务奖励成功, task_id={task_id}")
            
            return result
            
        except Exception as e:
            db.rollback()
            logger.error(f"领取任务奖励异常: user_id={user_id}, task_id={task_id}, error={str(e)}", exc_info=True)
            return {
                "success": False, 
                "error": "领取奖励失败，请稍后重试", 
                "code": TaskErrorCode.CLAIM_REWARD_ERROR.value
            }
    
    def _claim_reward_with_lock(
        self,
        db: Session,
        user: User,
        user_task: UserGrowthTask,
        task: GrowthTask
    ) -> Dict[str, Any]:
        """
        发放奖励（已在事务中，且已加锁）
        """
        if user_task.reward_claimed:
            return {
                "success": False, 
                "error": "奖励已领取", 
                "code": TaskErrorCode.REWARD_ALREADY_CLAIMED.value
            }
        
        reward_type = task.reward_type
        granter = self._reward_granters.get(reward_type)
        
        if not granter:
            logger.warning(f"未知的奖励类型: {reward_type}, task_id={task.id}")
            return {
                "success": False, 
                "error": f"不支持的奖励类型", 
                "code": TaskErrorCode.UNKNOWN_REWARD_TYPE.value
            }
        
        result = granter.grant(db, user, user_task, task)
        
        self._log_task_action(
            db, user.id, task.id, user_task.id,
            "reward_claimed", f"领取奖励: {task.reward_name}"
        )
        
        return result
    
    def check_first_login_popup(
        self,
        db: Session,
        user_id: int
    ) -> Dict[str, Any]:
        """
        检查是否需要显示首次登录弹窗
        
        修复逻辑：
        1. 新用户第一次访问时自动创建弹窗记录
        2. 确保 should_show 逻辑正确
        3. 预加载用户任务数据
        """
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {
                    "success": False, 
                    "error": "用户不存在", 
                    "code": TaskErrorCode.USER_NOT_FOUND.value
                }
            
            popup = db.query(FirstLoginPopup).filter(
                FirstLoginPopup.user_id == user_id
            ).first()
            
            if not popup:
                self._ensure_user_tasks(db, user_id)
                
                popup = FirstLoginPopup(
                    user_id=user_id,
                    has_seen=False,
                    should_show_again=True,
                    popup_type="growth_task"
                )
                db.add(popup)
                db.commit()
                db.refresh(popup)
            
            should_show = (not popup.has_seen) and popup.should_show_again
            
            user_tasks = self.get_user_tasks(db, user_id, include_completed=True)
            completed_count = sum(1 for t in user_tasks if t.get("status") in ["completed", "claimed"])
            
            return {
                "success": True,
                "data": {
                    "should_show": should_show,
                    "has_seen": popup.has_seen,
                    "seen_at": popup.seen_at.isoformat() if popup.seen_at else None,
                    "dismiss_count": popup.dismiss_count or 0,
                    "tasks": user_tasks,
                    "completed_count": completed_count,
                    "total_count": len(user_tasks)
                }
            }
            
        except Exception as e:
            logger.error(f"检查首次登录弹窗异常: user_id={user_id}, error={str(e)}", exc_info=True)
            return {
                "success": False, 
                "error": "获取弹窗状态失败，请稍后重试", 
                "code": TaskErrorCode.POPUP_ERROR.value
            }
    
    def mark_popup_seen(
        self,
        db: Session,
        user_id: int,
        is_dismissed: bool = False,
        interaction_data: Dict = None
    ) -> Dict[str, Any]:
        """标记弹窗已显示
        
        并发控制：
        1. 使用 with_for_update 加行锁（等待锁，不跳过）
        2. 锁超时返回"稍后重试"
        """
        try:
            try:
                popup = db.query(FirstLoginPopup).filter(
                    FirstLoginPopup.user_id == user_id
                ).with_for_update().first()
            except Exception as lock_error:
                logger.warning(f"获取弹窗锁失败: user_id={user_id}, error={str(lock_error)}")
                return {
                    "success": False,
                    "error": "系统繁忙，请稍后重试",
                    "code": TaskErrorCode.CONCURRENT_CONFLICT.value
                }
            
            if not popup:
                popup = FirstLoginPopup(
                    user_id=user_id,
                    popup_type="growth_task"
                )
                db.add(popup)
            
            popup.has_seen = True
            popup.seen_at = datetime.utcnow()
            
            if is_dismissed:
                popup.dismiss_count = (popup.dismiss_count or 0) + 1
                popup.last_dismissed_at = datetime.utcnow()
                
                if popup.dismiss_count >= 3:
                    popup.should_show_again = False
            
            if interaction_data:
                popup.interaction_data = json.dumps(interaction_data, ensure_ascii=False)
            
            db.commit()
            
            return {
                "success": True,
                "data": {
                    "has_seen": popup.has_seen,
                    "seen_at": popup.seen_at.isoformat() if popup.seen_at else None,
                    "dismiss_count": popup.dismiss_count or 0,
                    "should_show_again": popup.should_show_again
                }
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"标记弹窗已显示异常: user_id={user_id}, error={str(e)}", exc_info=True)
            return {
                "success": False, 
                "error": "操作失败，请稍后重试", 
                "code": TaskErrorCode.POPUP_ERROR.value
            }
    
    def _ensure_user_tasks(self, db: Session, user_id: int):
        """
        确保用户有所有激活任务的进度记录
        
        优化：批量处理，减少循环查询
        """
        now = datetime.utcnow()
        
        active_tasks = db.query(GrowthTask).filter(
            GrowthTask.status == GrowthTaskStatus.ACTIVE.value,
            GrowthTask.is_deleted == False,
            or_(GrowthTask.start_at == None, GrowthTask.start_at <= now),
            or_(GrowthTask.end_at == None, GrowthTask.end_at >= now)
        ).all()
        
        if not active_tasks:
            return
        
        active_task_ids = [t.id for t in active_tasks]
        
        existing_user_tasks = db.query(UserGrowthTask).filter(
            UserGrowthTask.user_id == user_id,
            UserGrowthTask.task_id.in_(active_task_ids)
        ).all()
        
        existing_task_ids = {ut.task_id for ut in existing_user_tasks}
        
        for task in active_tasks:
            if task.id not in existing_task_ids:
                user_task = UserGrowthTask(
                    user_id=user_id,
                    task_id=task.id,
                    status=UserGrowthTaskStatus.AVAILABLE.value,
                    progress_current=0,
                    progress_target=task.required_count
                )
                db.add(user_task)
                
                self._log_task_action(
                    db, user_id, task.id, None,
                    "created", f"用户任务初始化: {task.title}"
                )
        
        db.flush()
    
    def _log_task_action(
        self,
        db: Session,
        user_id: int,
        task_id: int,
        user_task_id: Optional[int],
        action_type: str,
        action_description: str,
        progress_before: Optional[int] = None,
        progress_after: Optional[int] = None
    ):
        """记录任务操作日志"""
        log = GrowthTaskLog(
            user_id=user_id,
            task_id=task_id,
            user_task_id=user_task_id,
            action_type=action_type,
            action_description=action_description,
            progress_before=progress_before,
            progress_after=progress_after
        )
        db.add(log)
    
    def _task_to_dict(self, task: GrowthTask) -> Dict[str, Any]:
        """将任务配置转换为字典"""
        reward_value = {}
        if task.reward_value:
            try:
                reward_value = json.loads(task.reward_value)
            except (json.JSONDecodeError, TypeError):
                reward_value = {}
        
        return {
            "id": task.id,
            "task_key": task.task_key,
            "task_type": task.task_type,
            "title": task.title,
            "description": task.description,
            "short_description": task.short_description,
            "icon": task.icon,
            "rarity": task.rarity,
            "sort_order": task.sort_order,
            "required_count": task.required_count,
            "reward_type": task.reward_type,
            "reward_amount": task.reward_amount,
            "reward_value": reward_value,
            "reward_name": task.reward_name,
            "is_auto_claim": task.is_auto_claim,
            "is_one_time": task.is_one_time,
            "status": task.status,
            "is_new_user_only": task.is_new_user_only,
            "max_days_after_register": task.max_days_after_register,
            "start_at": task.start_at.isoformat() if task.start_at else None,
            "end_at": task.end_at.isoformat() if task.end_at else None,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None
        }
    
    def _user_task_to_dict(self, user_task: UserGrowthTask) -> Dict[str, Any]:
        """将用户任务进度转换为字典"""
        task_dict = self._task_to_dict(user_task.task) if user_task.task else {}
        
        progress_data = {}
        if user_task.progress_data:
            try:
                progress_data = json.loads(user_task.progress_data)
            except (json.JSONDecodeError, TypeError):
                progress_data = {}
        
        completion_proof = {}
        if user_task.completion_proof:
            try:
                completion_proof = json.loads(user_task.completion_proof)
            except (json.JSONDecodeError, TypeError):
                completion_proof = {}
        
        progress_percent = 0
        if user_task.progress_target and user_task.progress_target > 0:
            progress_percent = round((user_task.progress_current / user_task.progress_target) * 100, 1)
        
        return {
            **task_dict,
            "user_task_id": user_task.id,
            "status": user_task.status,
            "progress_current": user_task.progress_current,
            "progress_target": user_task.progress_target,
            "progress_percent": progress_percent,
            "started_at": user_task.started_at.isoformat() if user_task.started_at else None,
            "completed_at": user_task.completed_at.isoformat() if user_task.completed_at else None,
            "claimed_at": user_task.claimed_at.isoformat() if user_task.claimed_at else None,
            "progress_data": progress_data,
            "completion_proof": completion_proof,
            "reward_claimed": user_task.reward_claimed
        }


growth_task_service = GrowthTaskService()


def get_growth_task_service() -> GrowthTaskService:
    """获取成长任务服务单例"""
    return growth_task_service
