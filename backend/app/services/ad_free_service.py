import logging
import json
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import and_, func, or_

from app.models import (
    User,
    AdFreePlan,
    UserAdFreeSubscription,
    AdFreePlanType,
    VIPPlan,
    VIPPlanType,
    UserVIP,
    VIPSubscription,
    PaymentOrder,
    PaymentStatus,
    PaymentType,
)

logger = logging.getLogger(__name__)


DEFAULT_AD_FREE_PLANS = [
    {
        "plan_key": "ad_free_monthly",
        "plan_type": AdFreePlanType.MONTHLY.value,
        "name": "月度去广告",
        "description": "享受30天全站无广告体验",
        "short_description": "30天无广告",
        "price": 999,
        "original_price": 1499,
        "duration_days": 30,
        "icon": "🛡️",
        "badge_icon": "🛡️",
        "sort_order": 1,
        "is_included_in_vip": True,
        "vip_plan_types": ["monthly", "yearly"],
        "features": {
            "no_banner_ads": True,
            "no_interstitial_ads": True,
            "no_video_ads": True,
            "ad_free_badge": True,
        },
    },
    {
        "plan_key": "ad_free_quarterly",
        "plan_type": AdFreePlanType.QUARTERLY.value,
        "name": "季度去广告",
        "description": "享受90天全站无广告体验",
        "short_description": "90天无广告",
        "price": 2499,
        "original_price": 3999,
        "duration_days": 90,
        "icon": "🛡️",
        "badge_icon": "🛡️",
        "sort_order": 2,
        "is_included_in_vip": True,
        "vip_plan_types": ["monthly", "yearly"],
        "features": {
            "no_banner_ads": True,
            "no_interstitial_ads": True,
            "no_video_ads": True,
            "ad_free_badge": True,
            "extra_discount": 0.1,
        },
    },
    {
        "plan_key": "ad_free_yearly",
        "plan_type": AdFreePlanType.YEARLY.value,
        "name": "年度去广告",
        "description": "享受365天全站无广告体验",
        "short_description": "365天无广告",
        "price": 7999,
        "original_price": 11999,
        "duration_days": 365,
        "icon": "🛡️",
        "badge_icon": "🛡️",
        "sort_order": 3,
        "is_included_in_vip": True,
        "vip_plan_types": ["monthly", "yearly"],
        "features": {
            "no_banner_ads": True,
            "no_interstitial_ads": True,
            "no_video_ads": True,
            "ad_free_badge": True,
            "extra_discount": 0.2,
            "priority_support": True,
        },
    },
]


class AdFreeService:
    """
    去广告权益服务
    
    核心功能：
    - 去广告套餐配置管理
    - 用户去广告订阅管理
    - VIP集成去广告权益
    - 去广告状态检查
    """
    
    _instance: Optional['AdFreeService'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def initialize_default_plans(self, db: Session) -> List[Dict[str, Any]]:
        """
        初始化默认去广告套餐配置
        """
        try:
            created_plans = []
            
            for plan_data in DEFAULT_AD_FREE_PLANS:
                existing = db.query(AdFreePlan).filter(
                    AdFreePlan.plan_key == plan_data["plan_key"]
                ).first()
                
                if existing:
                    created_plans.append(self._plan_to_dict(existing))
                    continue
                
                features_json = json.dumps(plan_data.get("features", {}), ensure_ascii=False)
                vip_plan_types_json = json.dumps(plan_data.get("vip_plan_types", []), ensure_ascii=False)
                
                plan = AdFreePlan(
                    plan_key=plan_data["plan_key"],
                    plan_type=plan_data["plan_type"],
                    name=plan_data["name"],
                    description=plan_data["description"],
                    short_description=plan_data.get("short_description"),
                    price=plan_data["price"],
                    original_price=plan_data.get("original_price"),
                    currency="CNY",
                    duration_days=plan_data["duration_days"],
                    features=features_json,
                    icon=plan_data.get("icon"),
                    badge_icon=plan_data.get("badge_icon"),
                    sort_order=plan_data.get("sort_order", 0),
                    is_included_in_vip=plan_data.get("is_included_in_vip", False),
                    vip_plan_types=vip_plan_types_json,
                    is_active=True,
                )
                
                db.add(plan)
                db.flush()
                
                created_plans.append(self._plan_to_dict(plan))
                logger.info(f"创建去广告套餐配置: {plan.plan_key} - {plan.name}")
            
            db.commit()
            return created_plans
            
        except Exception as e:
            db.rollback()
            logger.error(f"初始化去广告套餐配置异常: {str(e)}", exc_info=True)
            raise
    
    def get_active_plans(self, db: Session) -> List[Dict[str, Any]]:
        """
        获取所有激活的去广告套餐
        """
        plans = db.query(AdFreePlan).filter(
            AdFreePlan.is_active == True,
            AdFreePlan.is_deleted == False
        ).order_by(AdFreePlan.sort_order.asc()).all()
        
        return [self._plan_to_dict(p) for p in plans]
    
    def check_ad_free_status(self, db: Session, user_id: int) -> Dict[str, Any]:
        """
        检查用户的去广告状态
        
        检查优先级：
        1. 单独购买的去广告订阅
        2. VIP会员包含的去广告权益
        """
        now = datetime.utcnow()
        
        has_ad_free = False
        source_type = None
        expires_at = None
        subscription = None
        plan = None
        
        direct_sub = db.query(UserAdFreeSubscription).filter(
            UserAdFreeSubscription.user_id == user_id,
            UserAdFreeSubscription.is_active == True,
            UserAdFreeSubscription.is_cancelled == False,
            UserAdFreeSubscription.expires_at > now
        ).first()
        
        if direct_sub:
            has_ad_free = True
            source_type = "direct_purchase"
            expires_at = direct_sub.expires_at
            subscription = direct_sub
            if direct_sub.plan:
                plan = direct_sub.plan
        
        if not has_ad_free:
            from app.services.vip_service import check_and_update_vip_status
            
            is_vip, user_vip = check_and_update_vip_status(db, user_id)
            
            if is_vip and user_vip:
                vip_plan_type = user_vip.plan_type
                
                vip_included_plans = db.query(AdFreePlan).filter(
                    AdFreePlan.is_active == True,
                    AdFreePlan.is_deleted == False,
                    AdFreePlan.is_included_in_vip == True
                ).all()
                
                for vip_plan in vip_included_plans:
                    if vip_plan.vip_plan_types:
                        try:
                            vip_types = json.loads(vip_plan.vip_plan_types)
                            if vip_plan_type in vip_types:
                                has_ad_free = True
                                source_type = "vip_included"
                                expires_at = user_vip.expires_at
                                plan = vip_plan
                                break
                        except:
                            pass
        
        features = {}
        if plan and plan.features:
            try:
                features = json.loads(plan.features)
            except:
                features = {}
        
        return {
            "success": True,
            "data": {
                "has_ad_free": has_ad_free,
                "source_type": source_type,
                "expires_at": expires_at.isoformat() if expires_at else None,
                "plan": self._plan_to_dict(plan) if plan else None,
                "features": features,
            }
        }
    
    def get_user_subscriptions(
        self,
        db: Session,
        user_id: int,
        include_expired: bool = False
    ) -> List[Dict[str, Any]]:
        """
        获取用户的去广告订阅列表
        """
        now = datetime.utcnow()
        
        query = db.query(UserAdFreeSubscription).filter(
            UserAdFreeSubscription.user_id == user_id
        )
        
        if not include_expired:
            query = query.filter(
                UserAdFreeSubscription.expires_at > now
            )
        
        subscriptions = query.order_by(
            UserAdFreeSubscription.created_at.desc()
        ).all()
        
        return [self._subscription_to_dict(s) for s in subscriptions]
    
    def create_subscription_order(
        self,
        db: Session,
        user_id: int,
        plan_key: str
    ) -> Tuple[Optional[PaymentOrder], Optional[str]]:
        """
        创建设去广告订阅订单
        """
        try:
            plan = db.query(AdFreePlan).filter(
                AdFreePlan.plan_key == plan_key,
                AdFreePlan.is_active == True,
                AdFreePlan.is_deleted == False
            ).first()
            
            if not plan:
                logger.warning(f"创建设去广告订阅失败: 无效的套餐, user_id={user_id}, plan_key={plan_key}")
                return None, "无效的套餐"
            
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return None, "用户不存在"
            
            now = datetime.utcnow()
            
            order_no = self._generate_unique_no("ORD")
            
            order = PaymentOrder(
                order_no=order_no,
                user_id=user_id,
                payment_type=PaymentType.VIP_SUBSCRIPTION.value,
                related_type="ad_free_subscription",
                related_id=plan.id,
                amount=plan.price,
                currency="CNY",
                discount_amount=(plan.original_price or plan.price) - plan.price,
                final_amount=plan.price,
                status=PaymentStatus.PENDING.value,
                expired_at=now + timedelta(hours=24),
                is_sandbox=True
            )
            
            db.add(order)
            db.flush()
            
            logger.info(f"创建设去广告订单成功: user_id={user_id}, plan_key={plan_key}, order_no={order_no}")
            return order, None
            
        except Exception as e:
            db.rollback()
            logger.error(f"创建设去广告订单异常: user_id={user_id}, plan_key={plan_key}, error={str(e)}", exc_info=True)
            return None, f"创建订单失败: {str(e)}"
    
    def activate_subscription(
        self,
        db: Session,
        user_id: int,
        payment_order_id: int
    ) -> Tuple[Optional[UserAdFreeSubscription], Optional[str]]:
        """
        支付成功后激活去广告订阅
        """
        try:
            order = db.query(PaymentOrder).filter(
                PaymentOrder.id == payment_order_id,
                PaymentOrder.user_id == user_id,
                PaymentOrder.status == PaymentStatus.PAID.value
            ).first()
            
            if not order:
                return None, "订单不存在或未支付"
            
            plan = db.query(AdFreePlan).filter(
                AdFreePlan.id == order.related_id,
                AdFreePlan.is_active == True,
                AdFreePlan.is_deleted == False
            ).first()
            
            if not plan:
                return None, "套餐不存在"
            
            now = datetime.utcnow()
            
            existing_active = db.query(UserAdFreeSubscription).filter(
                UserAdFreeSubscription.user_id == user_id,
                UserAdFreeSubscription.is_active == True,
                UserAdFreeSubscription.is_cancelled == False,
                UserAdFreeSubscription.expires_at > now
            ).first()
            
            if existing_active and existing_active.expires_at > now:
                start_at = existing_active.expires_at
            else:
                start_at = now
            
            expires_at = start_at + timedelta(days=plan.duration_days)
            
            subscription_no = self._generate_unique_no("ADF")
            
            subscription = UserAdFreeSubscription(
                user_id=user_id,
                plan_id=plan.id,
                subscription_no=subscription_no,
                source_type="purchase",
                payment_order_id=payment_order_id,
                started_at=start_at,
                expires_at=expires_at,
                is_active=True,
                is_cancelled=False,
                is_auto_renew=False,
            )
            
            db.add(subscription)
            db.flush()
            
            db.commit()
            db.refresh(subscription)
            
            logger.info(f"激活动去广告订阅成功: user_id={user_id}, subscription_no={subscription_no}, expires_at={expires_at}")
            return subscription, None
            
        except Exception as e:
            db.rollback()
            logger.error(f"激活动去广告订阅异常: user_id={user_id}, payment_order_id={payment_order_id}, error={str(e)}", exc_info=True)
            return None, f"激活订阅失败: {str(e)}"
    
    def sync_vip_ad_free_benefit(
        self,
        db: Session,
        user_id: int,
        vip_subscription: VIPSubscription
    ) -> Optional[UserAdFreeSubscription]:
        """
        同步VIP会员的去广告权益
        
        当用户开通VIP时，自动添加去广告权益
        """
        try:
            plan = db.query(AdFreePlan).filter(
                AdFreePlan.is_active == True,
                AdFreePlan.is_deleted == False,
                AdFreePlan.is_included_in_vip == True
            ).order_by(AdFreePlan.sort_order.asc()).first()
            
            if not plan:
                logger.info(f"没有配置VIP包含的去广告套餐，跳过同步")
                return None
            
            now = datetime.utcnow()
            
            subscription_no = self._generate_unique_no("ADF")
            
            subscription = UserAdFreeSubscription(
                user_id=user_id,
                plan_id=plan.id,
                subscription_no=subscription_no,
                source_type="vip_included",
                is_vip_included=True,
                vip_subscription_id=vip_subscription.id,
                started_at=vip_subscription.started_at,
                expires_at=vip_subscription.expires_at,
                is_active=True,
                is_cancelled=False,
                is_auto_renew=vip_subscription.is_auto_renew,
            )
            
            db.add(subscription)
            db.flush()
            
            logger.info(f"同步VIP去广告权益成功: user_id={user_id}, subscription_no={subscription_no}")
            return subscription
            
        except Exception as e:
            logger.error(f"同步VIP去广告权益异常: user_id={user_id}, error={str(e)}", exc_info=True)
            return None
    
    def cancel_subscription(
        self,
        db: Session,
        user_id: int,
        subscription_id: int
    ) -> Tuple[bool, str]:
        """
        取消自动续费
        """
        try:
            subscription = db.query(UserAdFreeSubscription).filter(
                UserAdFreeSubscription.id == subscription_id,
                UserAdFreeSubscription.user_id == user_id
            ).first()
            
            if not subscription:
                return False, "订阅不存在"
            
            if not subscription.is_auto_renew:
                return False, "自动续费未开启"
            
            subscription.is_auto_renew = False
            
            db.commit()
            
            logger.info(f"取消自动续费成功: user_id={user_id}, subscription_id={subscription_id}")
            return True, "自动续费已取消"
            
        except Exception as e:
            db.rollback()
            logger.error(f"取消自动续费异常: user_id={user_id}, subscription_id={subscription_id}, error={str(e)}", exc_info=True)
            return False, f"操作失败: {str(e)}"
    
    def _generate_unique_no(self, prefix: str = "ADF") -> str:
        """生成唯一订单号/订阅号"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_part = uuid.uuid4().hex[:8].upper()
        return f"{prefix}{timestamp}{random_part}"
    
    def _plan_to_dict(self, plan: AdFreePlan) -> Dict[str, Any]:
        """将套餐配置转换为字典"""
        features = {}
        if plan.features:
            try:
                features = json.loads(plan.features)
            except:
                features = {}
        
        vip_plan_types = []
        if plan.vip_plan_types:
            try:
                vip_plan_types = json.loads(plan.vip_plan_types)
            except:
                vip_plan_types = []
        
        return {
            "id": plan.id,
            "plan_key": plan.plan_key,
            "plan_type": plan.plan_type,
            "name": plan.name,
            "description": plan.description,
            "short_description": plan.short_description,
            "price": plan.price,
            "original_price": plan.original_price,
            "currency": plan.currency,
            "duration_days": plan.duration_days,
            "features": features,
            "icon": plan.icon,
            "badge_icon": plan.badge_icon,
            "sort_order": plan.sort_order,
            "is_included_in_vip": plan.is_included_in_vip,
            "vip_plan_types": vip_plan_types,
            "is_active": plan.is_active,
            "created_at": plan.created_at.isoformat() if plan.created_at else None,
            "updated_at": plan.updated_at.isoformat() if plan.updated_at else None
        }
    
    def _subscription_to_dict(self, subscription: UserAdFreeSubscription) -> Dict[str, Any]:
        """将订阅记录转换为字典"""
        plan_dict = None
        if subscription.plan:
            plan_dict = self._plan_to_dict(subscription.plan)
        
        return {
            "id": subscription.id,
            "subscription_no": subscription.subscription_no,
            "user_id": subscription.user_id,
            "plan_id": subscription.plan_id,
            "plan": plan_dict,
            "source_type": subscription.source_type,
            "is_vip_included": subscription.is_vip_included,
            "started_at": subscription.started_at.isoformat() if subscription.started_at else None,
            "expires_at": subscription.expires_at.isoformat() if subscription.expires_at else None,
            "is_active": subscription.is_active,
            "is_cancelled": subscription.is_cancelled,
            "is_auto_renew": subscription.is_auto_renew,
            "cancelled_at": subscription.cancelled_at.isoformat() if subscription.cancelled_at else None,
            "created_at": subscription.created_at.isoformat() if subscription.created_at else None,
            "updated_at": subscription.updated_at.isoformat() if subscription.updated_at else None
        }


ad_free_service = AdFreeService()


def get_ad_free_service() -> AdFreeService:
    """获取去广告服务单例"""
    return ad_free_service
