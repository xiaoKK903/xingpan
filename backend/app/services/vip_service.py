import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError
import uuid
import json
import math

from app.models import (
    User, VIPPlan, VIPPrivilege, UserVIP, VIPSubscription,
    VIPPlanType, VIPPrivilegeType, PaymentOrder, PaymentStatus
)

logger = logging.getLogger(__name__)


MONTHLY_FREE_REPORTS_LIMIT = 3


def get_utc_now() -> datetime:
    return datetime.utcnow()


def generate_unique_no(prefix: str = "SUB") -> str:
    timestamp = get_utc_now().strftime("%Y%m%d%H%M%S")
    random_part = uuid.uuid4().hex[:8].upper()
    return f"{prefix}{timestamp}{random_part}"


def safe_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def ensure_user_vip_fields(user_vip: UserVIP):
    if user_vip.total_subscriptions is None:
        user_vip.total_subscriptions = 0
    if user_vip.total_paid is None:
        user_vip.total_paid = 0
    if user_vip.monthly_free_reports_used is None:
        user_vip.monthly_free_reports_used = 0
    if user_vip.auto_renew_enabled is None:
        user_vip.auto_renew_enabled = False
    if user_vip.is_vip is None:
        user_vip.is_vip = False


def is_vip_expired(user_vip: UserVIP, now: datetime) -> bool:
    if not user_vip.is_vip:
        return True
    if not user_vip.expires_at:
        return False
    return user_vip.expires_at <= now


def reset_vip_status(user_vip: UserVIP):
    user_vip.is_vip = False
    user_vip.plan_type = None
    user_vip.started_at = None
    user_vip.expires_at = None
    user_vip.auto_renew_enabled = False
    user_vip.monthly_free_reports_used = 0
    user_vip.monthly_free_reports_reset_at = None
    logger.info(f"VIP状态已重置: user_id={user_vip.user_id}")


def get_vip_days_remaining(user_vip: UserVIP) -> int:
    if not user_vip.is_vip or not user_vip.expires_at:
        return 0
    now = get_utc_now()
    if user_vip.expires_at <= now:
        return 0
    time_diff = user_vip.expires_at - now
    days_remaining = math.ceil(time_diff.total_seconds() / 86400)
    return max(0, days_remaining)


def init_vip_plans(db: Session):
    existing_plans = db.query(VIPPlan).count()
    if existing_plans > 0:
        return
    
    monthly_plan = VIPPlan(
        plan_type=VIPPlanType.MONTHLY.value,
        name="星钻会员月卡",
        description="开通星钻会员月卡，享受全部VIP特权，有效期30天",
        price=1900,
        original_price=2900,
        duration_days=30,
        is_active=True,
        sort_order=1
    )
    
    yearly_plan = VIPPlan(
        plan_type=VIPPlanType.YEARLY.value,
        name="星钻会员年卡",
        description="开通星钻会员年卡，享受全部VIP特权，有效期365天，比月卡省60元",
        price=16800,
        original_price=22800,
        duration_days=365,
        is_active=True,
        sort_order=2
    )
    
    db.add_all([monthly_plan, yearly_plan])
    db.commit()


def init_vip_privileges(db: Session):
    existing_privileges = db.query(VIPPrivilege).count()
    if existing_privileges > 0:
        return
    
    privileges = [
        VIPPrivilege(
            privilege_key="no_ads",
            name="全站免广告",
            description="全站所有页面无广告打扰，享受纯净体验",
            privilege_type=VIPPrivilegeType.NO_ADS.value,
            value_data=json.dumps({"enabled": True}),
            icon="🛡️",
            is_active=True
        ),
        VIPPrivilege(
            privilege_key="blind_box_extra",
            name="盲盒额外抽取",
            description="每日盲盒匹配次数+3，VIP用户每日可额外抽取3次",
            privilege_type=VIPPrivilegeType.BLIND_BOX_EXTRA.value,
            value_data=json.dumps({"extra_count": 3}),
            icon="🎁",
            is_active=True
        ),
        VIPPrivilege(
            privilege_key="blind_box_discount",
            name="盲盒折扣",
            description="盲盒相关消费享受8折优惠",
            privilege_type=VIPPrivilegeType.BLIND_BOX_DISCOUNT.value,
            value_data=json.dumps({"discount_rate": 0.8}),
            icon="💰",
            is_active=True
        ),
        VIPPrivilege(
            privilege_key="unlimited_synastry",
            name="合盘无限制",
            description="双人合盘计算无次数限制，普通用户每日限5次",
            privilege_type=VIPPrivilegeType.UNLIMITED_SYNASTRY.value,
            value_data=json.dumps({"unlimited": True}),
            icon="💕",
            is_active=True
        ),
        VIPPrivilege(
            privilege_key="advanced_horoscope",
            name="7天星运超前看",
            description="可查看未来7天的详细运势预测，普通用户仅能查看当日",
            privilege_type=VIPPrivilegeType.ADVANCED_HOROSCOPE.value,
            value_data=json.dumps({"days_ahead": 7}),
            icon="🔮",
            is_active=True
        ),
        VIPPrivilege(
            privilege_key="exclusive_skin",
            name="专属皮肤挂件",
            description="解锁VIP专属头像框、聊天气泡和个人主页皮肤",
            privilege_type=VIPPrivilegeType.EXCLUSIVE_SKIN.value,
            value_data=json.dumps({"skins": ["vip_frame", "vip_bubble", "vip_theme"]}),
            icon="✨",
            is_active=True
        ),
        VIPPrivilege(
            privilege_key="social_weight",
            name="社交加权推荐",
            description="在社交匹配和推荐中获得更高权重，更容易被匹配到",
            privilege_type=VIPPrivilegeType.SOCIAL_WEIGHT.value,
            value_data=json.dumps({"weight_multiplier": 2.0}),
            icon="⭐",
            is_active=True
        ),
        VIPPrivilege(
            privilege_key="free_reports",
            name="每月免费报告",
            description="每月可免费获取3份付费星盘报告",
            privilege_type=VIPPrivilegeType.FREE_REPORTS.value,
            value_data=json.dumps({"monthly_limit": 3}),
            icon="📄",
            is_active=True
        ),
    ]
    
    db.add_all(privileges)
    db.commit()


def get_or_create_user_vip(db: Session, user_id: int) -> UserVIP:
    user_vip = db.query(UserVIP).filter(UserVIP.user_id == user_id).first()
    if not user_vip:
        try:
            savepoint = db.begin_nested()
            user_vip = UserVIP(
                user_id=user_id,
                is_vip=False,
                total_subscriptions=0,
                total_paid=0,
                auto_renew_enabled=False,
                monthly_free_reports_used=0
            )
            db.add(user_vip)
            savepoint.commit()
            db.commit()
            db.refresh(user_vip)
            logger.info(f"创建新用户VIP记录: user_id={user_id}")
        except IntegrityError:
            savepoint.rollback()
            db.rollback()
            user_vip = db.query(UserVIP).filter(UserVIP.user_id == user_id).first()
            if not user_vip:
                raise
    else:
        ensure_user_vip_fields(user_vip)
    return user_vip


def _check_and_update_vip_status_internal(db: Session, user_vip: UserVIP, now: datetime) -> Tuple[bool, bool]:
    needs_commit = False
    if is_vip_expired(user_vip, now):
        if user_vip.is_vip:
            reset_vip_status(user_vip)
            needs_commit = True
            logger.info(f"VIP已过期并重置状态: user_id={user_vip.user_id}")
        return False, needs_commit
    return True, needs_commit


def check_and_update_vip_status(db: Session, user_id: int) -> Tuple[bool, UserVIP]:
    user_vip = get_or_create_user_vip(db, user_id)
    now = get_utc_now()
    
    is_active, needs_commit = _check_and_update_vip_status_internal(db, user_vip, now)
    
    if needs_commit:
        try:
            savepoint = db.begin_nested()
            savepoint.commit()
            db.commit()
            logger.info(f"VIP过期状态已持久化: user_id={user_id}")
        except Exception as e:
            logger.error(f"提交VIP状态变更失败: user_id={user_id}, error={str(e)}")
            db.rollback()
    
    return is_active, user_vip


def get_active_vip_plans(db: Session) -> List[VIPPlan]:
    return db.query(VIPPlan).filter(
        VIPPlan.is_active == True
    ).order_by(VIPPlan.sort_order).all()


def get_active_vip_privileges(db: Session) -> List[VIPPrivilege]:
    return db.query(VIPPrivilege).filter(
        VIPPrivilege.is_active == True
    ).all()


def get_vip_plan_by_type(db: Session, plan_type: str) -> Optional[VIPPlan]:
    return db.query(VIPPlan).filter(
        VIPPlan.plan_type == plan_type,
        VIPPlan.is_active == True
    ).first()


def calculate_subscription_times(user_vip: UserVIP, plan: VIPPlan) -> Tuple[datetime, datetime]:
    now = get_utc_now()
    
    if user_vip.is_vip and user_vip.expires_at and user_vip.expires_at > now:
        start_at = user_vip.expires_at
    else:
        start_at = now
    
    expires_at = start_at + timedelta(days=plan.duration_days)
    
    return start_at, expires_at


def check_existing_subscription(db: Session, payment_order_id: Optional[int]) -> Optional[VIPSubscription]:
    if not payment_order_id:
        return None
    
    return db.query(VIPSubscription).filter(
        VIPSubscription.payment_order_id == payment_order_id
    ).first()


def update_user_vip_from_subscription(
    user_vip: UserVIP,
    plan: VIPPlan,
    start_at: datetime,
    expires_at: datetime,
    is_auto_renew: bool
):
    now = get_utc_now()
    user_vip.is_vip = True
    user_vip.plan_type = plan.plan_type
    user_vip.started_at = start_at
    user_vip.expires_at = expires_at
    user_vip.total_subscriptions = safe_int(user_vip.total_subscriptions) + 1
    user_vip.total_paid = safe_int(user_vip.total_paid) + plan.price
    user_vip.auto_renew_enabled = is_auto_renew
    user_vip.last_renewed_at = now


def create_vip_subscription(
    db: Session,
    user_id: int,
    plan_type: str,
    payment_order_id: Optional[int] = None,
    is_auto_renew: bool = False
) -> Tuple[Optional[VIPSubscription], Optional[str]]:
    try:
        plan = get_vip_plan_by_type(db, plan_type)
        if not plan:
            logger.warning(f"创建VIP订阅失败: 无效的会员套餐, user_id={user_id}, plan_type={plan_type}")
            return None, "无效的会员套餐"
        
        existing_sub = check_existing_subscription(db, payment_order_id)
        if existing_sub:
            logger.warning(f"重复创建VIP订阅请求，已存在订阅: payment_order_id={payment_order_id}")
            return existing_sub, None
        
        user_vip = get_or_create_user_vip(db, user_id)
        
        start_at, expires_at = calculate_subscription_times(user_vip, plan)
        
        subscription = VIPSubscription(
            user_id=user_id,
            subscription_no=generate_unique_no("SUB"),
            plan_type=plan_type,
            price=plan.price,
            discount_amount=(plan.original_price or plan.price) - plan.price,
            duration_days=plan.duration_days,
            started_at=start_at,
            expires_at=expires_at,
            payment_order_id=payment_order_id,
            status="active",
            is_auto_renew=is_auto_renew
        )
        
        db.add(subscription)
        db.flush()
        
        update_user_vip_from_subscription(user_vip, plan, start_at, expires_at, is_auto_renew)
        
        db.commit()
        db.refresh(subscription)
        db.refresh(user_vip)
        
        logger.info(f"创建VIP订阅成功: user_id={user_id}, plan_type={plan_type}, duration_days={plan.duration_days}")
        return subscription, None
        
    except Exception as e:
        db.rollback()
        logger.error(f"创建VIP订阅异常: user_id={user_id}, error={str(e)}", exc_info=True)
        return None, f"创建订阅失败: {str(e)}"


def cancel_auto_renew(db: Session, user_id: int) -> Tuple[bool, str]:
    try:
        user_vip = get_or_create_user_vip(db, user_id)
        
        if not user_vip.auto_renew_enabled:
            return False, "自动续费未开启"
        
        user_vip.auto_renew_enabled = False
        
        active_subscription = db.query(VIPSubscription).filter(
            VIPSubscription.user_id == user_id,
            VIPSubscription.status == "active",
            VIPSubscription.is_auto_renew == True
        ).first()
        
        if active_subscription:
            active_subscription.is_auto_renew = False
        
        db.commit()
        
        logger.info(f"取消自动续费成功: user_id={user_id}")
        return True, "自动续费已取消"
        
    except Exception as e:
        db.rollback()
        logger.error(f"取消自动续费异常: user_id={user_id}, error={str(e)}", exc_info=True)
        return False, f"操作失败: {str(e)}"


def check_privilege(db: Session, user_id: int, privilege_key: str) -> Tuple[bool, Optional[Dict]]:
    is_vip, user_vip = check_and_update_vip_status(db, user_id)
    
    if not is_vip:
        return False, None
    
    privilege = db.query(VIPPrivilege).filter(
        VIPPrivilege.privilege_key == privilege_key,
        VIPPrivilege.is_active == True
    ).first()
    
    if not privilege:
        return False, None
    
    value_data = {}
    if privilege.value_data:
        try:
            value_data = json.loads(privilege.value_data)
        except:
            value_data = {}
    
    return True, value_data


def get_next_month_reset_time(now: datetime) -> datetime:
    if now.month == 12:
        return datetime(now.year + 1, 1, 1)
    else:
        return datetime(now.year, now.month + 1, 1)


def is_monthly_reset_needed(user_vip: UserVIP, now: datetime) -> bool:
    reset_at = user_vip.monthly_free_reports_reset_at
    if reset_at is None:
        return True
    return reset_at <= now


def _get_free_reports_remaining_internal(
    db: Session, 
    user_vip: UserVIP, 
    is_vip: bool, 
    now: datetime
) -> Tuple[int, bool]:
    if not is_vip:
        return 0, False
    
    needs_commit = False
    
    if is_monthly_reset_needed(user_vip, now):
        user_vip.monthly_free_reports_used = 0
        user_vip.monthly_free_reports_reset_at = get_next_month_reset_time(now)
        needs_commit = True
        logger.info(f"重置用户免费报告额度: user_id={user_vip.user_id}, next_reset={user_vip.monthly_free_reports_reset_at}")
    
    used = safe_int(user_vip.monthly_free_reports_used)
    return max(0, MONTHLY_FREE_REPORTS_LIMIT - used), needs_commit


def check_free_reports_remaining(db: Session, user_id: int) -> int:
    user_vip = get_or_create_user_vip(db, user_id)
    now = get_utc_now()
    
    is_vip, needs_commit_vip = _check_and_update_vip_status_internal(db, user_vip, now)
    
    remaining, needs_commit_free = _get_free_reports_remaining_internal(db, user_vip, is_vip, now)
    
    needs_commit = needs_commit_vip or needs_commit_free
    if needs_commit:
        try:
            savepoint = db.begin_nested()
            savepoint.commit()
            db.commit()
        except Exception as e:
            logger.error(f"提交免费报告状态变更失败: user_id={user_id}, error={str(e)}")
            db.rollback()
    
    return remaining


def use_free_report(db: Session, user_id: int) -> Tuple[bool, str]:
    try:
        user_vip = get_or_create_user_vip(db, user_id)
        now = get_utc_now()
        
        is_vip, needs_commit_vip = _check_and_update_vip_status_internal(db, user_vip, now)
        
        if not is_vip:
            return False, "不是VIP会员"
        
        remaining, needs_commit_free = _get_free_reports_remaining_internal(db, user_vip, is_vip, now)
        
        if remaining <= 0:
            return False, "本月免费报告额度已用完"
        
        user_vip.monthly_free_reports_used = safe_int(user_vip.monthly_free_reports_used) + 1
        
        db.commit()
        
        logger.info(f"使用免费报告: user_id={user_id}, remaining={remaining - 1}")
        return True, "免费报告已使用"
        
    except Exception as e:
        db.rollback()
        logger.error(f"使用免费报告异常: user_id={user_id}, error={str(e)}", exc_info=True)
        return False, f"操作失败: {str(e)}"


def get_user_subscriptions(db: Session, user_id: int, limit: int = 20) -> List[VIPSubscription]:
    return db.query(VIPSubscription).filter(
        VIPSubscription.user_id == user_id
    ).order_by(VIPSubscription.created_at.desc()).limit(limit).all()


def process_single_expired_vip(db: Session, user_vip: UserVIP):
    try:
        savepoint = db.begin_nested()
        
        reset_vip_status(user_vip)
        
        active_subscriptions = db.query(VIPSubscription).filter(
            VIPSubscription.user_id == user_vip.user_id,
            VIPSubscription.status == "active"
        ).all()
        
        for sub in active_subscriptions:
            sub.status = "expired"
        
        savepoint.commit()
        logger.info(f"处理过期VIP成功: user_id={user_vip.user_id}")
        return True
        
    except Exception as e:
        savepoint.rollback()
        logger.error(f"处理过期VIP失败: user_id={user_vip.user_id}, error={str(e)}", exc_info=True)
        return False


def process_expired_vips(db: Session) -> int:
    now = get_utc_now()
    
    expired_vips = db.query(UserVIP).filter(
        UserVIP.is_vip == True,
        UserVIP.expires_at <= now
    ).with_for_update(skip_locked=True).all()
    
    processed_count = 0
    
    for user_vip in expired_vips:
        try:
            if process_single_expired_vip(db, user_vip):
                processed_count += 1
        except Exception as e:
            logger.error(f"处理过期VIP循环异常: user_id={user_vip.user_id}, error={str(e)}", exc_info=True)
            continue
    
    try:
        db.commit()
        logger.info(f"批量处理过期VIP完成: 总数={len(expired_vips)}, 成功={processed_count}")
    except Exception as e:
        db.rollback()
        logger.error(f"提交过期VIP处理结果失败: error={str(e)}", exc_info=True)
        processed_count = 0
    
    return processed_count


def should_create_auto_renew_order(db: Session, sub: VIPSubscription, user_vip: UserVIP, plan: Optional[VIPPlan]) -> bool:
    if not user_vip.auto_renew_enabled:
        return False
    
    if not plan:
        return False
    
    existing_pending = db.query(PaymentOrder).filter(
        PaymentOrder.user_id == sub.user_id,
        PaymentOrder.payment_type == "vip_subscription",
        PaymentOrder.related_type == "auto_renew",
        PaymentOrder.status == "pending"
    ).first()
    
    if existing_pending:
        return False
    
    return True


def create_auto_renew_order(db: Session, sub: VIPSubscription, plan: VIPPlan) -> PaymentOrder:
    now = get_utc_now()
    
    order = PaymentOrder(
        order_no=generate_unique_no("ORD"),
        user_id=sub.user_id,
        payment_type="vip_subscription",
        related_type="auto_renew",
        related_id=sub.id,
        amount=plan.price,
        currency="CNY",
        discount_amount=0,
        final_amount=plan.price,
        status="pending",
        expired_at=now + timedelta(hours=24),
        is_sandbox=True
    )
    
    db.add(order)
    logger.info(f"创建自动续费订单: user_id={sub.user_id}, subscription_id={sub.id}")
    return order


def process_auto_renew(db: Session) -> int:
    now = get_utc_now()
    renew_window = now + timedelta(days=3)
    
    auto_renew_subscriptions = db.query(VIPSubscription).filter(
        VIPSubscription.status == "active",
        VIPSubscription.is_auto_renew == True,
        VIPSubscription.expires_at <= renew_window,
        VIPSubscription.expires_at > now
    ).with_for_update(skip_locked=True).all()
    
    renewed_count = 0
    
    for sub in auto_renew_subscriptions:
        savepoint = None
        try:
            savepoint = db.begin_nested()
            
            user_vip = get_or_create_user_vip(db, sub.user_id)
            plan = get_vip_plan_by_type(db, sub.plan_type)
            
            if should_create_auto_renew_order(db, sub, user_vip, plan):
                create_auto_renew_order(db, sub, plan)
                renewed_count += 1
                savepoint.commit()
                logger.info(f"创建自动续费订单成功: subscription_id={sub.id}")
            elif not user_vip.auto_renew_enabled:
                sub.is_auto_renew = False
                savepoint.commit()
                logger.info(f"自动续费已禁用，更新订阅状态: subscription_id={sub.id}")
            else:
                savepoint.rollback()
                
        except Exception as e:
            if savepoint:
                savepoint.rollback()
            logger.error(f"处理自动续费失败: subscription_id={sub.id}, error={str(e)}", exc_info=True)
            continue
    
    try:
        db.commit()
        logger.info(f"批量创建自动续费订单完成: count={renewed_count}")
    except Exception as e:
        db.rollback()
        logger.error(f"提交自动续费处理结果失败: error={str(e)}", exc_info=True)
        renewed_count = 0
    
    return renewed_count


check_vip_status = check_and_update_vip_status
get_free_reports_remaining = check_free_reports_remaining
