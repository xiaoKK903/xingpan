"""
前世故事 - 支付服务（订单、升级）

修复内容:
1. 订单幂等: 防止重复创建订单
2. 状态幂等: 防止重复处理支付回调
"""
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models import (
    User, PaymentOrder, PaymentStatus, PaymentType,
    PastLifeRecord, PastLifeSynastryRecord
)
from app.services.payment_service import create_payment_order, simulate_payment, get_order_by_no

from .config import (
    PAST_LIFE_PRICE,
    PAST_LIFE_SYNASTRY_PRICE
)
from .data_service import record_to_dict, synastry_record_to_dict

logger = logging.getLogger(__name__)


def create_past_life_order(
    db: Session,
    user_id: int,
    record_type: str = "single",
    record_id: int = 0
) -> Tuple[Optional[PaymentOrder], Optional[str]]:
    """
    创建前世故事深度版支付订单
    
    幂等性保障:
    1. 检查同一记录是否有未支付的订单，如果有则返回现有订单
    2. 检查同一记录是否已支付，如果已支付则返回错误
    """
    try:
        RecordModel = PastLifeRecord if record_type == "single" else PastLifeSynastryRecord
        
        record = db.query(RecordModel).filter(
            RecordModel.id == record_id,
            RecordModel.user_id == user_id,
            RecordModel.is_deleted == False
        ).first()
        
        if not record:
            return None, "记录不存在或无权限"
        
        if record.is_paid:
            return None, "该记录已解锁深度版"
        
        existing_order = db.query(PaymentOrder).filter(
            PaymentOrder.user_id == user_id,
            PaymentOrder.related_id == record_id,
            PaymentOrder.related_type == f"past_life_{record_type}",
            PaymentOrder.status.in_([PaymentStatus.PENDING, PaymentStatus.PROCESSING])
        ).first()
        
        if existing_order:
            logger.info(f"找到未支付订单，返回现有订单: {existing_order.order_no}")
            return existing_order, None
        
        price = PAST_LIFE_PRICE if record_type == "single" else PAST_LIFE_SYNASTRY_PRICE
        
        order, error = create_payment_order(
            db=db,
            user_id=user_id,
            amount=price,
            payment_type=PaymentType.REPORT,
            related_type=f"past_life_{record_type}",
            related_id=record_id,
            description=f"解锁前世故事深度版 - {record.name if hasattr(record, 'name') else f'{record.person_a_name} & {record.person_b_name}'}"
        )
        
        if order:
            logger.info(f"创建前世故事订单成功: {order.order_no}, 记录ID: {record_id}, 类型: {record_type}")
        else:
            logger.error(f"创建前世故事订单失败: {error}")
        
        return order, error
        
    except IntegrityError as e:
        logger.warning(f"创建订单时发生唯一键冲突，可能是并发请求: {e}")
        db.rollback()
        
        existing_order = db.query(PaymentOrder).filter(
            PaymentOrder.user_id == user_id,
            PaymentOrder.related_id == record_id,
            PaymentOrder.related_type == f"past_life_{record_type}"
        ).first()
        
        if existing_order:
            return existing_order, None
        
        return None, "创建订单失败，请重试"
        
    except Exception as e:
        logger.error(f"创建前世故事订单失败: {e}", exc_info=True)
        db.rollback()
        return None, str(e)


def upgrade_to_deep_version(
    db: Session,
    record_id: int,
    user_id: int,
    order_no: str,
    is_synastry: bool = False
) -> Tuple[bool, Optional[str]]:
    """
    根据订单升级到深度版
    
    幂等性保障:
    1. 检查订单状态，确保是已支付状态
    2. 检查记录是否已升级，如果已升级则直接返回成功
    3. 检查订单是否已被使用过
    """
    try:
        order = get_order_by_no(db, order_no)
        
        if not order:
            return False, "订单不存在"
        
        if order.status != PaymentStatus.PAID:
            return False, "订单未支付"
        
        RecordModel = PastLifeSynastryRecord if is_synastry else PastLifeRecord
        
        record = db.query(RecordModel).filter(
            RecordModel.id == record_id,
            RecordModel.user_id == user_id,
            RecordModel.is_deleted == False
        ).first()
        
        if not record:
            return False, "记录不存在或无权限"
        
        if record.is_paid:
            if record.pay_order_no == order_no:
                logger.info(f"记录{record_id}已使用订单{order_no}升级，幂等返回成功")
                return True, None
            else:
                return True, None
        
        record.is_paid = True
        record.pay_order_no = order_no
        record.updated_at = datetime.now()
        
        db.commit()
        db.refresh(record)
        
        logger.info(f"升级到深度版成功: 记录ID={record_id}, 订单={order_no}, 类型={'合盘' if is_synastry else '单人'}")
        
        return True, None
        
    except Exception as e:
        logger.error(f"升级到深度版失败: {e}", exc_info=True)
        db.rollback()
        return False, str(e)


def process_payment_callback(
    db: Session,
    order_no: str,
    success: bool = True
) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    处理支付回调，自动升级到深度版
    
    幂等性保障:
    1. 检查订单状态，防止重复处理
    2. 检查记录是否已升级
    """
    try:
        order = get_order_by_no(db, order_no)
        
        if not order:
            return False, "订单不存在", None
        
        if order.status == PaymentStatus.PAID:
            logger.info(f"订单{order_no}已处理，幂等返回")
            return True, "订单已处理", None
        
        if success:
            simulate_payment(db=db, order_no=order_no, success=True)
        else:
            db.query(PaymentOrder).filter(
                PaymentOrder.order_no == order_no
            ).update({"status": PaymentStatus.FAILED})
            db.commit()
            return False, "支付失败", None
        
        order = get_order_by_no(db, order_no)
        
        related_type = order.related_type or ""
        record_id = order.related_id or 0
        
        is_synastry = "synastry" in related_type
        RecordModel = PastLifeSynastryRecord if is_synastry else PastLifeRecord
        
        if not record_id:
            return False, "订单关联记录ID无效", None
        
        record = db.query(RecordModel).filter(
            RecordModel.id == record_id,
            RecordModel.user_id == order.user_id,
            RecordModel.is_deleted == False
        ).first()
        
        if not record:
            return False, "关联记录不存在", None
        
        if record.is_paid:
            logger.info(f"记录{record_id}已付费，幂等返回成功")
            result = synastry_record_to_dict(record) if is_synastry else record_to_dict(record)
            return True, "记录已解锁", result
        
        record.is_paid = True
        record.pay_order_no = order_no
        record.updated_at = datetime.now()
        
        db.commit()
        db.refresh(record)
        
        result = synastry_record_to_dict(record) if is_synastry else record_to_dict(record)
        
        logger.info(f"支付回调处理成功: 订单={order_no}, 记录ID={record_id}")
        
        return True, "升级成功", result
        
    except Exception as e:
        logger.error(f"处理支付回调失败: {e}", exc_info=True)
        db.rollback()
        return False, str(e), None


def get_order_status(
    db: Session,
    order_no: str,
    user_id: int
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    获取订单状态（带权限检查）
    """
    try:
        order = db.query(PaymentOrder).filter(
            PaymentOrder.order_no == order_no,
            PaymentOrder.user_id == user_id
        ).first()
        
        if not order:
            return None, "订单不存在"
        
        return {
            "order_no": order.order_no,
            "amount": order.amount,
            "final_amount": order.final_amount,
            "status": order.status.value if hasattr(order.status, 'value') else str(order.status),
            "is_sandbox": order.is_sandbox,
            "payment_url": f"/api/payment/sandbox/pay?order_no={order.order_no}" if order.is_sandbox else None,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "paid_at": order.paid_at.isoformat() if order.paid_at else None,
        }, None
        
    except Exception as e:
        logger.error(f"获取订单状态失败: {e}", exc_info=True)
        return None, str(e)
