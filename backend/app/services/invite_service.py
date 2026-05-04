import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError
import uuid
import json
import math
import secrets

from app.models import (
    User, InviteCode, InviteRelation, InviteReward, InviteShareLog,
    InviteRewardStage, UserVIP, VIPSubscription, VIPPlan,
    StarDustTransaction, Chart, ProphecyTicket, UserCoupon,
    PaymentOrder, PaymentStatus
)
from app.services.vip_service import get_or_create_user_vip, create_vip_subscription

logger = logging.getLogger(__name__)

SHARE_REWARD_FRAGMENTS = 50
REGISTER_COMPLETE_REWARD_TICKETS = 1
REGISTER_COMPLETE_VIP_DAYS = 3
FIRST_PAYMENT_REWARD_RATE = 0.20


def get_utc_now() -> datetime:
    return datetime.utcnow()


def generate_unique_no(prefix: str = "INV") -> str:
    timestamp = get_utc_now().strftime("%Y%m%d%H%M%S")
    random_part = uuid.uuid4().hex[:8].upper()
    return f"{prefix}{timestamp}{random_part}"


def generate_invite_code() -> str:
    return secrets.token_urlsafe(8)[:10].upper()


def get_or_create_invite_code(db: Session, user_id: int) -> InviteCode:
    invite_code = db.query(InviteCode).filter(InviteCode.user_id == user_id).first()
    if invite_code:
        return invite_code
    
    try:
        savepoint = db.begin_nested()
        
        code = generate_invite_code()
        attempts = 0
        while attempts < 10:
            existing = db.query(InviteCode).filter(InviteCode.invite_code == code).first()
            if not existing:
                break
            code = generate_invite_code()
            attempts += 1
        
        invite_code = InviteCode(
            user_id=user_id,
            invite_code=code,
            total_invites=0,
            valid_invites=0,
            paid_invites=0,
            total_rewards_earned=0,
            is_active=True
        )
        db.add(invite_code)
        savepoint.commit()
        db.commit()
        db.refresh(invite_code)
        
        logger.info(f"创建新用户邀请码: user_id={user_id}, code={code}")
        return invite_code
        
    except IntegrityError:
        savepoint.rollback()
        db.rollback()
        invite_code = db.query(InviteCode).filter(InviteCode.user_id == user_id).first()
        if invite_code:
            return invite_code
        raise


def get_invite_code_by_code(db: Session, code: str) -> Optional[InviteCode]:
    return db.query(InviteCode).filter(
        InviteCode.invite_code == code,
        InviteCode.is_active == True
    ).first()


def check_invite_relation_exists(db: Session, invitee_id: int) -> bool:
    return db.query(InviteRelation).filter(
        InviteRelation.invitee_id == invitee_id
    ).first() is not None


def get_invite_relation_by_invitee(db: Session, invitee_id: int) -> Optional[InviteRelation]:
    return db.query(InviteRelation).filter(
        InviteRelation.invitee_id == invitee_id
    ).first()


def check_anti_cheat(db: Session, ip: Optional[str], device: Optional[str], inviter_id: int) -> Tuple[bool, Optional[str]]:
    if not ip:
        return True, None
    
    recent_invites = db.query(InviteRelation).filter(
        InviteRelation.register_ip == ip,
        InviteRelation.created_at >= get_utc_now() - timedelta(hours=24)
    ).count()
    
    if recent_invites >= 5:
        return False, "同一IP地址24小时内邀请次数过多"
    
    same_ip_inviter = db.query(InviteRelation).filter(
        InviteRelation.register_ip == ip,
        InviteRelation.inviter_id == inviter_id,
        InviteRelation.created_at >= get_utc_now() - timedelta(hours=1)
    ).count()
    
    if same_ip_inviter >= 2:
        return False, "同一邀请人短时间内邀请次数异常"
    
    return True, None


def create_invite_relation(
    db: Session,
    inviter_id: int,
    invitee_id: int,
    invite_code: str,
    ip: Optional[str] = None,
    device: Optional[str] = None
) -> Tuple[Optional[InviteRelation], Optional[str]]:
    try:
        if check_invite_relation_exists(db, invitee_id):
            return None, "该用户已有邀请关系"
        
        inviter = db.query(User).filter(User.id == inviter_id).first()
        if not inviter:
            return None, "邀请人不存在"
        
        if inviter_id == invitee_id:
            return None, "不能邀请自己"
        
        is_valid, reason = check_anti_cheat(db, ip, device, inviter_id)
        
        relation = InviteRelation(
            inviter_id=inviter_id,
            invitee_id=invitee_id,
            invite_code_used=invite_code,
            register_ip=ip,
            register_device=device,
            is_register_completed=False,
            has_first_payment=False,
            is_valid=is_valid,
            invalid_reason=reason if not is_valid else None
        )
        
        db.add(relation)
        
        invite_code_obj = db.query(InviteCode).filter(
            InviteCode.invite_code == invite_code
        ).first()
        if invite_code_obj:
            invite_code_obj.total_invites += 1
        
        db.commit()
        db.refresh(relation)
        
        logger.info(f"创建邀请关系: inviter_id={inviter_id}, invitee_id={invitee_id}, code={invite_code}, is_valid={is_valid}")
        
        return relation, None
        
    except Exception as e:
        db.rollback()
        logger.error(f"创建邀请关系失败: inviter_id={inviter_id}, invitee_id={invitee_id}, error={str(e)}")
        return None, f"创建邀请关系失败: {str(e)}"


def add_stardust_fragments(
    db: Session,
    user_id: int,
    amount: int,
    description: str,
    related_type: str = "invite_reward",
    related_id: Optional[int] = None
) -> Optional[StarDustTransaction]:
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        balance_before = user.stardust_fragment_balance or 0
        balance_after = balance_before + amount
        
        transaction = StarDustTransaction(
            user_id=user_id,
            transaction_type="reward",
            currency_type="fragment",
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            related_type=related_type,
            related_id=str(related_id) if related_id else None,
            description=description
        )
        
        db.add(transaction)
        
        user.stardust_fragment_balance = balance_after
        
        db.commit()
        db.refresh(transaction)
        
        logger.info(f"添加星元碎片: user_id={user_id}, amount={amount}, balance_before={balance_before}, balance_after={balance_after}")
        
        return transaction
        
    except Exception as e:
        db.rollback()
        logger.error(f"添加星元碎片失败: user_id={user_id}, error={str(e)}")
        return None


def add_prophecy_ticket(
    db: Session,
    user_id: int,
    source_type: str = "invite_reward",
    source_reference: Optional[str] = None
) -> Optional[ProphecyTicket]:
    try:
        ticket = ProphecyTicket(
            user_id=user_id,
            ticket_type="invite_reward",
            is_used=False,
            valid_from=get_utc_now(),
            valid_until=get_utc_now() + timedelta(days=30)
        )
        
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        
        logger.info(f"添加星图盲盒券: user_id={user_id}, ticket_id={ticket.id}")
        
        return ticket
        
    except Exception as e:
        db.rollback()
        logger.error(f"添加星图盲盒券失败: user_id={user_id}, error={str(e)}")
        return None


def grant_vip_trial(
    db: Session,
    user_id: int,
    days: int = REGISTER_COMPLETE_VIP_DAYS
) -> Tuple[Optional[VIPSubscription], Optional[str]]:
    try:
        user_vip = get_or_create_user_vip(db, user_id)
        now = get_utc_now()
        
        if user_vip.is_vip and user_vip.expires_at and user_vip.expires_at > now:
            start_at = user_vip.expires_at
        else:
            start_at = now
        
        expires_at = start_at + timedelta(days=days)
        
        user_vip.is_vip = True
        user_vip.plan_type = "trial"
        user_vip.started_at = start_at
        user_vip.expires_at = expires_at
        
        subscription = VIPSubscription(
            user_id=user_id,
            subscription_no=generate_unique_no("SUB"),
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
        db.commit()
        db.refresh(subscription)
        db.refresh(user_vip)
        
        logger.info(f"授予VIP试用: user_id={user_id}, days={days}, expires_at={expires_at}")
        
        return subscription, None
        
    except Exception as e:
        db.rollback()
        logger.error(f"授予VIP试用失败: user_id={user_id}, error={str(e)}")
        return None, f"授予VIP试用失败: {str(e)}"


def create_invite_reward(
    db: Session,
    invite_relation_id: int,
    inviter_id: int,
    invitee_id: int,
    reward_stage: str,
    reward_type: str,
    reward_amount: int,
    reward_name: str,
    reward_description: str,
    transaction_id: Optional[int] = None,
    vip_subscription_id: Optional[int] = None,
    coupon_id: Optional[int] = None,
    prophecy_ticket_id: Optional[int] = None
) -> Optional[InviteReward]:
    try:
        reward = InviteReward(
            reward_no=generate_unique_no("REW"),
            invite_relation_id=invite_relation_id,
            inviter_id=inviter_id,
            invitee_id=invitee_id,
            reward_stage=reward_stage,
            reward_type=reward_type,
            reward_amount=reward_amount,
            reward_name=reward_name,
            reward_description=reward_description,
            is_claimed=True,
            claimed_at=get_utc_now(),
            transaction_id=transaction_id,
            vip_subscription_id=vip_subscription_id,
            coupon_id=coupon_id,
            prophecy_ticket_id=prophecy_ticket_id,
            status="completed"
        )
        
        db.add(reward)
        db.commit()
        db.refresh(reward)
        
        logger.info(f"创建邀请奖励: reward_no={reward.reward_no}, stage={reward_stage}, inviter_id={inviter_id}, invitee_id={invitee_id}")
        
        return reward
        
    except Exception as e:
        db.rollback()
        logger.error(f"创建邀请奖励失败: error={str(e)}")
        return None


def process_share_reward(
    db: Session,
    invite_relation: InviteRelation
) -> Tuple[bool, Optional[str]]:
    if not invite_relation.is_valid:
        return False, "邀请关系无效，无法发放奖励"
    
    inviter_transaction = add_stardust_fragments(
        db=db,
        user_id=invite_relation.inviter_id,
        amount=SHARE_REWARD_FRAGMENTS,
        description=f"邀请好友注册奖励 - 邀请人获得 {SHARE_REWARD_FRAGMENTS} 星元碎片",
        related_type="invite_reward",
        related_id=invite_relation.id
    )
    
    invitee_transaction = add_stardust_fragments(
        db=db,
        user_id=invite_relation.invitee_id,
        amount=SHARE_REWARD_FRAGMENTS,
        description=f"通过邀请注册奖励 - 获得 {SHARE_REWARD_FRAGMENTS} 星元碎片",
        related_type="invite_reward",
        related_id=invite_relation.id
    )
    
    if inviter_transaction:
        create_invite_reward(
            db=db,
            invite_relation_id=invite_relation.id,
            inviter_id=invite_relation.inviter_id,
            invitee_id=invite_relation.invitee_id,
            reward_stage=InviteRewardStage.SHARE.value,
            reward_type="fragment",
            reward_amount=SHARE_REWARD_FRAGMENTS,
            reward_name="邀请注册奖励",
            reward_description=f"邀请好友注册成功，获得 {SHARE_REWARD_FRAGMENTS} 星元碎片",
            transaction_id=inviter_transaction.id
        )
    
    if invitee_transaction:
        create_invite_reward(
            db=db,
            invite_relation_id=invite_relation.id,
            inviter_id=invite_relation.inviter_id,
            invitee_id=invite_relation.invitee_id,
            reward_stage=InviteRewardStage.SHARE.value,
            reward_type="fragment",
            reward_amount=SHARE_REWARD_FRAGMENTS,
            reward_name="被邀请注册奖励",
            reward_description=f"通过好友邀请注册成功，获得 {SHARE_REWARD_FRAGMENTS} 星元碎片",
            transaction_id=invitee_transaction.id
        )
    
    invite_code_obj = db.query(InviteCode).filter(
        InviteCode.user_id == invite_relation.inviter_id
    ).first()
    if invite_code_obj:
        invite_code_obj.total_rewards_earned += SHARE_REWARD_FRAGMENTS
        db.commit()
    
    logger.info(f"处理分享奖励完成: relation_id={invite_relation.id}")
    return True, None


def process_register_complete_reward(
    db: Session,
    invite_relation: InviteRelation
) -> Tuple[bool, Optional[str]]:
    if not invite_relation.is_valid:
        return False, "邀请关系无效，无法发放奖励"
    
    if invite_relation.is_register_completed:
        return False, "该阶段奖励已发放"
    
    ticket = add_prophecy_ticket(
        db=db,
        user_id=invite_relation.inviter_id,
        source_type="invite_reward",
        source_reference=f"invitee_{invite_relation.invitee_id}"
    )
    
    if ticket:
        create_invite_reward(
            db=db,
            invite_relation_id=invite_relation.id,
            inviter_id=invite_relation.inviter_id,
            invitee_id=invite_relation.invitee_id,
            reward_stage=InviteRewardStage.REGISTER_COMPLETE.value,
            reward_type="ticket",
            reward_amount=REGISTER_COMPLETE_REWARD_TICKETS,
            reward_name="邀请完成星盘奖励",
            reward_description=f"好友完成个人星盘，获得 {REGISTER_COMPLETE_REWARD_TICKETS} 张星图盲盒券",
            prophecy_ticket_id=ticket.id
        )
    
    vip_subscription, vip_error = grant_vip_trial(
        db=db,
        user_id=invite_relation.invitee_id,
        days=REGISTER_COMPLETE_VIP_DAYS
    )
    
    if vip_subscription:
        create_invite_reward(
            db=db,
            invite_relation_id=invite_relation.id,
            inviter_id=invite_relation.inviter_id,
            invitee_id=invite_relation.invitee_id,
            reward_stage=InviteRewardStage.REGISTER_COMPLETE.value,
            reward_type="vip_trial",
            reward_amount=REGISTER_COMPLETE_VIP_DAYS,
            reward_name="新用户VIP体验",
            reward_description=f"完成个人星盘，获得 {REGISTER_COMPLETE_VIP_DAYS} 天VIP会员体验",
            vip_subscription_id=vip_subscription.id
        )
    
    invite_relation.is_register_completed = True
    invite_relation.register_completed_at = get_utc_now()
    
    invite_code_obj = db.query(InviteCode).filter(
        InviteCode.user_id == invite_relation.inviter_id
    ).first()
    if invite_code_obj:
        invite_code_obj.valid_invites += 1
        db.commit()
    
    db.commit()
    
    logger.info(f"处理注册完成奖励完成: relation_id={invite_relation.id}")
    return True, None


def process_first_payment_reward(
    db: Session,
    invite_relation: InviteRelation,
    payment_amount: int
) -> Tuple[bool, Optional[str]]:
    if not invite_relation.is_valid:
        return False, "邀请关系无效，无法发放奖励"
    
    if invite_relation.has_first_payment:
        return False, "首次付费奖励已发放"
    
    reward_amount = int(payment_amount * FIRST_PAYMENT_REWARD_RATE)
    
    if reward_amount <= 0:
        return False, "返利金额为0，无需发放奖励"
    
    transaction = add_stardust_fragments(
        db=db,
        user_id=invite_relation.inviter_id,
        amount=reward_amount,
        description=f"好友首次付费返利 - 付费金额 {payment_amount/100:.2f}元，返利 {reward_amount} 星元碎片（{FIRST_PAYMENT_REWARD_RATE*100}%）",
        related_type="invite_reward",
        related_id=invite_relation.id
    )
    
    if transaction:
        create_invite_reward(
            db=db,
            invite_relation_id=invite_relation.id,
            inviter_id=invite_relation.inviter_id,
            invitee_id=invite_relation.invitee_id,
            reward_stage=InviteRewardStage.FIRST_PAYMENT.value,
            reward_type="fragment",
            reward_amount=reward_amount,
            reward_name="好友首次付费返利",
            reward_description=f"好友首次付费金额 {payment_amount/100:.2f}元，获得 {FIRST_PAYMENT_REWARD_RATE*100}% 返利，共 {reward_amount} 星元碎片",
            transaction_id=transaction.id
        )
    
    invite_relation.has_first_payment = True
    invite_relation.first_payment_at = get_utc_now()
    invite_relation.first_payment_amount = payment_amount
    
    invite_code_obj = db.query(InviteCode).filter(
        InviteCode.user_id == invite_relation.inviter_id
    ).first()
    if invite_code_obj:
        invite_code_obj.paid_invites += 1
        invite_code_obj.total_rewards_earned += reward_amount
        db.commit()
    
    db.commit()
    
    logger.info(f"处理首次付费奖励完成: relation_id={invite_relation.id}, payment_amount={payment_amount}, reward_amount={reward_amount}")
    return True, None


def check_user_has_chart(db: Session, user_id: int) -> bool:
    return db.query(Chart).filter(
        Chart.user_id == user_id,
        Chart.is_deleted == False
    ).first() is not None


def on_user_chart_created(db: Session, user_id: int):
    relation = get_invite_relation_by_invitee(db, user_id)
    if not relation:
        return
    
    if relation.is_register_completed:
        return
    
    if not relation.is_valid:
        logger.info(f"邀请关系无效，跳过注册完成奖励: invitee_id={user_id}")
        return
    
    process_register_complete_reward(db, relation)


def on_payment_completed(db: Session, order: PaymentOrder):
    if order.status != PaymentStatus.PAID.value:
        return
    
    relation = get_invite_relation_by_invitee(db, order.user_id)
    if not relation:
        return
    
    if relation.has_first_payment:
        return
    
    if not relation.is_valid:
        logger.info(f"邀请关系无效，跳过高付费返利: invitee_id={order.user_id}")
        return
    
    process_first_payment_reward(db, relation, order.final_amount)


def log_invite_share(
    db: Session,
    user_id: int,
    share_type: str,
    share_platform: Optional[str] = None,
    share_content: Optional[str] = None,
    invite_code: Optional[str] = None,
    synastry_record_id: Optional[int] = None,
    share_ip: Optional[str] = None,
    share_device: Optional[str] = None
) -> Optional[InviteShareLog]:
    try:
        log = InviteShareLog(
            user_id=user_id,
            share_type=share_type,
            share_platform=share_platform,
            share_content=share_content,
            invite_code=invite_code,
            synastry_record_id=synastry_record_id,
            share_ip=share_ip,
            share_device=share_device,
            click_count=0,
            register_count=0
        )
        
        db.add(log)
        db.commit()
        db.refresh(log)
        
        logger.info(f"记录邀请分享: user_id={user_id}, type={share_type}, code={invite_code}")
        
        return log
        
    except Exception as e:
        db.rollback()
        logger.error(f"记录邀请分享失败: error={str(e)}")
        return None


def get_user_invite_stats(db: Session, user_id: int) -> Dict[str, Any]:
    invite_code = get_or_create_invite_code(db, user_id)
    
    invite_relations = db.query(InviteRelation).filter(
        InviteRelation.inviter_id == user_id
    ).all()
    
    total_invites = len(invite_relations)
    valid_invites = sum(1 for r in invite_relations if r.is_valid)
    completed_invites = sum(1 for r in invite_relations if r.is_register_completed)
    paid_invites = sum(1 for r in invite_relations if r.has_first_payment)
    
    rewards = db.query(InviteReward).filter(
        InviteReward.inviter_id == user_id
    ).all()
    
    total_rewards_value = sum(r.reward_amount for r in rewards)
    
    recent_invitees = []
    for relation in invite_relations[:10]:
        invitee = db.query(User).filter(User.id == relation.invitee_id).first()
        if invitee:
            recent_invitees.append({
                "user_id": invitee.id,
                "username": invitee.username,
                "invited_at": relation.created_at.isoformat() if relation.created_at else None,
                "is_register_completed": relation.is_register_completed,
                "has_first_payment": relation.has_first_payment,
                "is_valid": relation.is_valid
            })
    
    return {
        "invite_code": invite_code.invite_code,
        "total_invites": total_invites,
        "valid_invites": valid_invites,
        "completed_invites": completed_invites,
        "paid_invites": paid_invites,
        "total_rewards_earned": invite_code.total_rewards_earned,
        "total_rewards_value": total_rewards_value,
        "share_reward_fragments": SHARE_REWARD_FRAGMENTS,
        "register_complete_reward_tickets": REGISTER_COMPLETE_REWARD_TICKETS,
        "register_complete_vip_days": REGISTER_COMPLETE_VIP_DAYS,
        "first_payment_reward_rate": FIRST_PAYMENT_REWARD_RATE,
        "recent_invitees": recent_invitees
    }


def get_invite_rewards_list(
    db: Session,
    user_id: int,
    limit: int = 20,
    offset: int = 0
) -> Dict[str, Any]:
    query = db.query(InviteReward).filter(
        or_(
            InviteReward.inviter_id == user_id,
            InviteReward.invitee_id == user_id
        )
    )
    
    total = query.count()
    
    rewards = query.order_by(
        InviteReward.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    reward_list = []
    for reward in rewards:
        is_inviter = reward.inviter_id == user_id
        other_user_id = reward.invitee_id if is_inviter else reward.inviter_id
        other_user = db.query(User).filter(User.id == other_user_id).first()
        
        reward_list.append({
            "reward_no": reward.reward_no,
            "reward_stage": reward.reward_stage,
            "reward_type": reward.reward_type,
            "reward_amount": reward.reward_amount,
            "reward_name": reward.reward_name,
            "reward_description": reward.reward_description,
            "is_inviter": is_inviter,
            "other_user": {
                "user_id": other_user.id,
                "username": other_user.username
            } if other_user else None,
            "claimed_at": reward.claimed_at.isoformat() if reward.claimed_at else None,
            "created_at": reward.created_at.isoformat() if reward.created_at else None
        })
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "rewards": reward_list
    }