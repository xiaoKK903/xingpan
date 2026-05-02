from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
import uuid

from app.models import (
    User, Gift, GiftTransaction, UserGiftDisplay,
    GiftType, StarDustTransaction
)


def generate_unique_no(prefix: str = "GIFT") -> str:
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    random_part = uuid.uuid4().hex[:8].upper()
    return f"{prefix}{timestamp}{random_part}"


def init_default_gifts(db: Session):
    existing_gifts = db.query(Gift).count()
    if existing_gifts > 0:
        return
    
    gifts = [
        Gift(
            gift_key=GiftType.STARDUST_BOUQUET.value,
            name="星尘花束",
            description="一束由星尘凝聚而成的美丽花束，散发着柔和的光芒，适合表达心意",
            gift_type=GiftType.STARDUST_BOUQUET.value,
            price=50,
            currency_type="stardust_point",
            rarity="common",
            animation_effect="flower_bloom",
            is_active=True,
            is_limited=False,
            sort_order=1
        ),
        Gift(
            gift_key=GiftType.ENERGY_CRYSTAL.value,
            name="能量水晶",
            description="蕴含强大能量的神秘水晶，能够提升接收者的运势和能量",
            gift_type=GiftType.ENERGY_CRYSTAL.value,
            price=100,
            currency_type="stardust_point",
            rarity="rare",
            animation_effect="crystal_glow",
            is_active=True,
            is_limited=False,
            sort_order=2
        ),
        Gift(
            gift_key=GiftType.LIMITED_CARD_FRAME.value,
            name="限定合盘卡牌框",
            description="限时上架的珍稀合盘卡牌框，赠送后接收者可永久使用此卡牌框",
            gift_type=GiftType.LIMITED_CARD_FRAME.value,
            price=200,
            currency_type="stardust_point",
            rarity="legendary",
            animation_effect="card_frame_shine",
            is_active=True,
            is_limited=True,
            stock_remaining=1000,
            sort_order=3
        ),
    ]
    
    db.add_all(gifts)
    db.commit()


def get_active_gifts(db: Session) -> List[Gift]:
    now = datetime.utcnow()
    query = db.query(Gift).filter(Gift.is_active == True)
    
    query = query.filter(
        or_(
            Gift.available_from == None,
            Gift.available_from <= now
        ),
        or_(
            Gift.available_until == None,
            Gift.available_until >= now
        )
    )
    
    return query.order_by(Gift.sort_order).all()


def get_gift_by_id(db: Session, gift_id: int) -> Optional[Gift]:
    return db.query(Gift).filter(
        Gift.id == gift_id,
        Gift.is_active == True
    ).first()


def get_gift_by_key(db: Session, gift_key: str) -> Optional[Gift]:
    return db.query(Gift).filter(
        Gift.gift_key == gift_key,
        Gift.is_active == True
    ).first()


def send_gift(
    db: Session,
    sender_id: int,
    receiver_id: int,
    gift_id: int,
    quantity: int = 1,
    message: Optional[str] = None,
    is_anonymous: bool = False
) -> Tuple[Optional[GiftTransaction], Optional[str]]:
    if sender_id == receiver_id:
        return None, "不能给自己送礼物"
    
    gift = get_gift_by_id(db, gift_id)
    if not gift:
        return None, "礼物不存在或已下架"
    
    if gift.is_limited and gift.stock_remaining is not None:
        if gift.stock_remaining < quantity:
            return None, "礼物库存不足"
    
    sender = db.query(User).filter(User.id == sender_id).first()
    if not sender:
        return None, "发送者不存在"
    
    receiver = db.query(User).filter(User.id == receiver_id).first()
    if not receiver:
        return None, "接收者不存在"
    
    total_price = gift.price * quantity
    
    if gift.currency_type == "stardust_point":
        if sender.stardust_point_balance < total_price:
            return None, "星尘点数不足"
        sender.stardust_point_balance -= total_price
    elif gift.currency_type == "stardust_fragment":
        if sender.stardust_fragment_balance < total_price:
            return None, "星尘碎片不足"
        sender.stardust_fragment_balance -= total_price
    
    transaction = GiftTransaction(
        transaction_no=generate_unique_no("GIFT"),
        sender_id=sender_id,
        receiver_id=receiver_id,
        gift_id=gift_id,
        gift_name=gift.name,
        gift_key=gift.gift_key,
        quantity=quantity,
        price_per_unit=gift.price,
        total_price=total_price,
        currency_type=gift.currency_type,
        message=message,
        is_anonymous=is_anonymous,
        is_displayed=False
    )
    
    db.add(transaction)
    
    stardust_transaction = StarDustTransaction(
        user_id=sender_id,
        transaction_type="gift_send",
        currency_type=gift.currency_type,
        amount=-total_price,
        balance_before=(
            sender.stardust_point_balance + total_price 
            if gift.currency_type == "stardust_point" 
            else sender.stardust_fragment_balance + total_price
        ),
        balance_after=(
            sender.stardust_point_balance 
            if gift.currency_type == "stardust_point" 
            else sender.stardust_fragment_balance
        ),
        related_type="gift",
        related_id=str(transaction.id),
        description=f"赠送礼物: {gift.name} x{quantity} 给用户 {receiver_id}"
    )
    
    db.add(stardust_transaction)
    
    if gift.is_limited and gift.stock_remaining is not None:
        gift.stock_remaining -= quantity
    
    db.commit()
    db.refresh(transaction)
    
    return transaction, None


def get_user_received_gifts(
    db: Session,
    user_id: int,
    limit: int = 50,
    offset: int = 0
) -> List[GiftTransaction]:
    return db.query(GiftTransaction).filter(
        GiftTransaction.receiver_id == user_id
    ).order_by(desc(GiftTransaction.created_at)).offset(offset).limit(limit).all()


def get_user_sent_gifts(
    db: Session,
    user_id: int,
    limit: int = 50,
    offset: int = 0
) -> List[GiftTransaction]:
    return db.query(GiftTransaction).filter(
        GiftTransaction.sender_id == user_id
    ).order_by(desc(GiftTransaction.created_at)).offset(offset).limit(limit).all()


def get_gift_transaction_by_id(
    db: Session,
    transaction_id: int
) -> Optional[GiftTransaction]:
    return db.query(GiftTransaction).filter(
        GiftTransaction.id == transaction_id
    ).first()


def display_gift_on_profile(
    db: Session,
    user_id: int,
    gift_transaction_id: int,
    is_featured: bool = False
) -> Tuple[Optional[UserGiftDisplay], Optional[str]]:
    transaction = get_gift_transaction_by_id(db, gift_transaction_id)
    
    if not transaction:
        return None, "礼物交易记录不存在"
    
    if transaction.receiver_id != user_id:
        return None, "无权展示此礼物"
    
    existing_display = db.query(UserGiftDisplay).filter(
        UserGiftDisplay.gift_transaction_id == gift_transaction_id
    ).first()
    
    if existing_display:
        return None, "该礼物已在展示中"
    
    display_count = db.query(UserGiftDisplay).filter(
        UserGiftDisplay.user_id == user_id
    ).count()
    
    if display_count >= 10:
        return None, "展示位已满，最多展示10个礼物"
    
    gift_display = UserGiftDisplay(
        user_id=user_id,
        gift_transaction_id=gift_transaction_id,
        gift_key=transaction.gift_key,
        gift_name=transaction.gift_name,
        sender_name=None if transaction.is_anonymous else (
            db.query(User).filter(User.id == transaction.sender_id).first().username
            if db.query(User).filter(User.id == transaction.sender_id).first()
            else None
        ),
        is_featured=is_featured,
        display_order=display_count
    )
    
    db.add(gift_display)
    
    transaction.is_displayed = True
    transaction.displayed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(gift_display)
    
    return gift_display, None


def remove_gift_from_display(
    db: Session,
    user_id: int,
    display_id: int
) -> Tuple[bool, str]:
    display = db.query(UserGiftDisplay).filter(
        UserGiftDisplay.id == display_id,
        UserGiftDisplay.user_id == user_id
    ).first()
    
    if not display:
        return False, "展示记录不存在或无权操作"
    
    transaction = db.query(GiftTransaction).filter(
        GiftTransaction.id == display.gift_transaction_id
    ).first()
    
    if transaction:
        transaction.is_displayed = False
    
    db.delete(display)
    db.commit()
    
    return True, "已从展示中移除"


def get_user_displayed_gifts(
    db: Session,
    user_id: int
) -> List[UserGiftDisplay]:
    return db.query(UserGiftDisplay).filter(
        UserGiftDisplay.user_id == user_id
    ).order_by(
        desc(UserGiftDisplay.is_featured),
        UserGiftDisplay.display_order
    ).all()


def set_gift_featured(
    db: Session,
    user_id: int,
    display_id: int,
    is_featured: bool
) -> Tuple[bool, str]:
    display = db.query(UserGiftDisplay).filter(
        UserGiftDisplay.id == display_id,
        UserGiftDisplay.user_id == user_id
    ).first()
    
    if not display:
        return False, "展示记录不存在或无权操作"
    
    display.is_featured = is_featured
    db.commit()
    
    return True, "设置成功"


def get_gift_statistics(db: Session, user_id: int) -> Dict:
    received_count = db.query(GiftTransaction).filter(
        GiftTransaction.receiver_id == user_id
    ).count()
    
    sent_count = db.query(GiftTransaction).filter(
        GiftTransaction.sender_id == user_id
    ).count()
    
    displayed_count = db.query(UserGiftDisplay).filter(
        UserGiftDisplay.user_id == user_id
    ).count()
    
    gift_types = db.query(GiftTransaction.gift_key).filter(
        GiftTransaction.receiver_id == user_id
    ).distinct().count()
    
    return {
        "received_count": received_count,
        "sent_count": sent_count,
        "displayed_count": displayed_count,
        "gift_types_received": gift_types
    }


def get_recent_gifts_for_feed(
    db: Session,
    user_id: int,
    limit: int = 20
) -> List[GiftTransaction]:
    return db.query(GiftTransaction).filter(
        GiftTransaction.receiver_id == user_id,
        GiftTransaction.is_anonymous == False
    ).order_by(desc(GiftTransaction.created_at)).limit(limit).all()
