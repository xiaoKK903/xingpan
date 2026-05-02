import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
import uuid
import json

from app.models import (
    User, PaymentOrder, PaymentTransaction,
    PaymentStatus, PaymentType, VIPSubscription, UserVIP,
    VIPPlan
)
from app.services.vip_service import create_vip_subscription, get_vip_plan_by_type

logger = logging.getLogger(__name__)


def get_utc_now() -> datetime:
    return datetime.utcnow()


def generate_unique_no(prefix: str = "ORD") -> str:
    timestamp = get_utc_now().strftime("%Y%m%d%H%M%S")
    random_part = uuid.uuid4().hex[:8].upper()
    return f"{prefix}{timestamp}{random_part}"


def create_payment_order(
    db: Session,
    user_id: int,
    payment_type: str,
    amount: int,
    related_type: Optional[str] = None,
    related_id: Optional[int] = None,
    payment_method: Optional[str] = None,
    discount_amount: int = 0,
    is_sandbox: bool = True
) -> Tuple[Optional[PaymentOrder], Optional[str]]:
    if amount <= 0:
        return None, "支付金额必须大于0"
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None, "用户不存在"
    
    final_amount = max(0, amount - discount_amount)
    
    order = PaymentOrder(
        order_no=generate_unique_no("ORD"),
        user_id=user_id,
        payment_type=payment_type,
        related_type=related_type,
        related_id=related_id,
        amount=amount,
        currency="CNY",
        discount_amount=discount_amount,
        final_amount=final_amount,
        payment_method=payment_method,
        payment_platform="sandbox" if is_sandbox else None,
        status=PaymentStatus.PENDING.value,
        expired_at=get_utc_now() + timedelta(hours=24),
        is_sandbox=is_sandbox
    )
    
    db.add(order)
    db.commit()
    db.refresh(order)
    
    return order, None


def get_order_by_no(db: Session, order_no: str) -> Optional[PaymentOrder]:
    return db.query(PaymentOrder).filter(
        PaymentOrder.order_no == order_no
    ).first()


def get_order_by_id(db: Session, order_id: int, user_id: int) -> Optional[PaymentOrder]:
    return db.query(PaymentOrder).filter(
        PaymentOrder.id == order_id,
        PaymentOrder.user_id == user_id
    ).first()


def get_user_orders(
    db: Session,
    user_id: int,
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
) -> List[PaymentOrder]:
    query = db.query(PaymentOrder).filter(PaymentOrder.user_id == user_id)
    
    if status:
        query = query.filter(PaymentOrder.status == status)
    
    return query.order_by(desc(PaymentOrder.created_at)).offset(offset).limit(limit).all()


def simulate_payment(
    db: Session,
    order_no: str,
    success: bool = True,
    payment_method: str = "sandbox_alipay"
) -> Tuple[Optional[PaymentOrder], Optional[str]]:
    try:
        order = db.query(PaymentOrder).filter(
            PaymentOrder.order_no == order_no
        ).with_for_update(skip_locked=True).first()
        
        if not order:
            logger.warning(f"模拟支付失败: 订单不存在, order_no={order_no}")
            return None, "订单不存在"
        
        logger.info(f"开始模拟支付: order_no={order_no}, current_status={order.status}, success={success}")
        
        if order.status == PaymentStatus.PAID.value:
            logger.warning(f"幂等性校验通过: 订单已支付, order_no={order_no}")
            return order, None
        
        if order.status != PaymentStatus.PENDING.value:
            logger.warning(f"订单状态不允许支付: order_no={order_no}, status={order.status}")
            return None, f"订单状态不是待支付，当前状态: {order.status}"
        
        now = get_utc_now()
        if order.expired_at and order.expired_at < now:
            order.status = PaymentStatus.CANCELLED.value
            db.commit()
            logger.warning(f"订单已过期: order_no={order_no}")
            return None, "订单已过期"
        
        transaction = PaymentTransaction(
            transaction_no=generate_unique_no("TXN"),
            order_id=order.id,
            user_id=order.user_id,
            transaction_type="payment",
            amount=order.final_amount,
            currency=order.currency,
            platform_transaction_no=generate_unique_no("PAY"),
            status="pending"
        )
        
        db.add(transaction)
        db.flush()
        
        if success:
            order.status = PaymentStatus.PAID.value
            order.paid_at = now
            order.payment_method = payment_method
            order.payment_platform = "sandbox"
            
            transaction.status = "success"
            
            process_success, message = process_payment_success(db, order)
            if not process_success:
                db.rollback()
                logger.error(f"支付后处理失败: order_no={order_no}, error={message}")
                return None, message
            
            logger.info(f"模拟支付成功: order_no={order_no}, user_id={order.user_id}, amount={order.final_amount}")
        else:
            order.status = PaymentStatus.FAILED.value
            order.error_message = "模拟支付失败"
            transaction.status = "failed"
            transaction.error_message = "模拟支付失败"
            logger.info(f"模拟支付失败: order_no={order_no}, 主动模拟失败")
        
        db.commit()
        db.refresh(order)
        
        return order, None
        
    except Exception as e:
        db.rollback()
        logger.error(f"模拟支付异常: order_no={order_no}, error={str(e)}", exc_info=True)
        return None, f"支付处理异常: {str(e)}"


def process_payment_success(
    db: Session,
    order: PaymentOrder
) -> Tuple[bool, str]:
    if order.payment_type == PaymentType.VIP_SUBSCRIPTION.value:
        return process_vip_subscription_payment(db, order)
    
    return True, "支付成功"


def process_vip_subscription_payment(
    db: Session,
    order: PaymentOrder
) -> Tuple[bool, str]:
    plan_type = order.related_type
    
    if not plan_type:
        return False, "缺少会员套餐类型信息"
    
    plan = get_vip_plan_by_type(db, plan_type)
    if not plan:
        return False, "无效的会员套餐"
    
    subscription, error = create_vip_subscription(
        db=db,
        user_id=order.user_id,
        plan_type=plan_type,
        payment_order_id=order.id,
        is_auto_renew=False
    )
    
    if not subscription:
        return False, error or "创建订阅失败"
    
    return True, "订阅成功"


def cancel_order(
    db: Session,
    order_no: str,
    user_id: int,
    reason: str = "用户取消"
) -> Tuple[bool, str]:
    order = get_order_by_no(db, order_no)
    
    if not order:
        return False, "订单不存在"
    
    if order.user_id != user_id:
        return False, "无权操作此订单"
    
    if order.status != PaymentStatus.PENDING.value:
        return False, f"订单状态不允许取消，当前状态: {order.status}"
    
    order.status = PaymentStatus.CANCELLED.value
    order.error_message = reason
    
    db.commit()
    
    return True, "订单已取消"


def refund_order(
    db: Session,
    order_no: str,
    reason: str = "用户申请退款"
) -> Tuple[bool, str]:
    order = get_order_by_no(db, order_no)
    
    if not order:
        return False, "订单不存在"
    
    if order.status != PaymentStatus.PAID.value:
        return False, f"只有已支付订单可以退款，当前状态: {order.status}"
    
    order.status = PaymentStatus.REFUNDED.value
    order.error_message = reason
    
    transaction = PaymentTransaction(
        transaction_no=generate_unique_no("TXN"),
        order_id=order.id,
        user_id=order.user_id,
        transaction_type="refund",
        amount=order.final_amount,
        currency=order.currency,
        platform_transaction_no=generate_unique_no("REF"),
        status="success"
    )
    
    db.add(transaction)
    
    if order.payment_type == PaymentType.VIP_SUBSCRIPTION.value:
        user_vip = db.query(UserVIP).filter(UserVIP.user_id == order.user_id).first()
        if user_vip:
            subscription = db.query(VIPSubscription).filter(
                VIPSubscription.payment_order_id == order.id
            ).first()
            if subscription:
                subscription.status = "refunded"
                subscription.cancelled_at = get_utc_now()
                subscription.cancel_reason = reason
    
    db.commit()
    
    return True, "退款已处理"


def process_expired_orders(db: Session):
    now = get_utc_now()
    
    expired_orders = db.query(PaymentOrder).filter(
        PaymentOrder.status == PaymentStatus.PENDING.value,
        PaymentOrder.expired_at < now
    ).all()
    
    for order in expired_orders:
        order.status = PaymentStatus.CANCELLED.value
        order.error_message = "订单超时未支付"
    
    db.commit()
    
    return len(expired_orders)


def get_order_payment_info(
    db: Session,
    order_no: str
) -> Optional[Dict]:
    order = get_order_by_no(db, order_no)
    
    if not order:
        return None
    
    return {
        "order_no": order.order_no,
        "amount": order.amount,
        "final_amount": order.final_amount,
        "currency": order.currency,
        "status": order.status,
        "payment_type": order.payment_type,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "expired_at": order.expired_at.isoformat() if order.expired_at else None,
        "is_sandbox": order.is_sandbox,
        "payment_url": f"/api/payment/sandbox/pay?order_no={order.order_no}" if order.is_sandbox else None
    }


def create_vip_subscription_order(
    db: Session,
    user_id: int,
    plan_type: str,
    is_auto_renew: bool = False
) -> Tuple[Optional[PaymentOrder], Optional[str]]:
    plan = get_vip_plan_by_type(db, plan_type)
    
    if not plan:
        return None, "无效的会员套餐"
    
    order, error = create_payment_order(
        db=db,
        user_id=user_id,
        payment_type=PaymentType.VIP_SUBSCRIPTION.value,
        amount=plan.price,
        related_type=plan_type,
        is_sandbox=True
    )
    
    return order, error


def get_payment_statistics(db: Session, user_id: int) -> Dict:
    total_orders = db.query(PaymentOrder).filter(
        PaymentOrder.user_id == user_id
    ).count()
    
    paid_orders = db.query(PaymentOrder).filter(
        PaymentOrder.user_id == user_id,
        PaymentOrder.status == PaymentStatus.PAID.value
    ).count()
    
    total_spent = db.query(PaymentOrder).filter(
        PaymentOrder.user_id == user_id,
        PaymentOrder.status == PaymentStatus.PAID.value
    ).with_entities(PaymentOrder.final_amount).all()
    
    total_spent_amount = sum(amount[0] for amount in total_spent)
    
    return {
        "total_orders": total_orders,
        "paid_orders": paid_orders,
        "total_spent": total_spent_amount
    }
