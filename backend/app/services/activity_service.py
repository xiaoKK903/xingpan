import logging
import json
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta, timezone
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import and_, func, or_

from app.models import (
    Activity,
    ActivityBenefit,
    ActivityParticipation,
    ActivityType,
    ActivityStatus,
    BenefitType,
    ZodiacSign,
    User,
    StarDustTransaction,
    UserCoupon,
    UserCouponStatus,
    UserBenefit,
    UserBenefitStatus,
)

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


ZODIAC_DATE_RANGES = [
    (3, 21, 4, 19, ZodiacSign.ARIES),
    (4, 20, 5, 20, ZodiacSign.TAURUS),
    (5, 21, 6, 20, ZodiacSign.GEMINI),
    (6, 21, 7, 22, ZodiacSign.CANCER),
    (7, 23, 8, 22, ZodiacSign.LEO),
    (8, 23, 9, 22, ZodiacSign.VIRGO),
    (9, 23, 10, 22, ZodiacSign.LIBRA),
    (10, 23, 11, 21, ZodiacSign.SCORPIO),
    (11, 22, 12, 21, ZodiacSign.SAGITTARIUS),
    (12, 22, 12, 31, ZodiacSign.CAPRICORN),
    (1, 1, 1, 19, ZodiacSign.CAPRICORN),
    (1, 20, 2, 18, ZodiacSign.AQUARIUS),
    (2, 19, 3, 20, ZodiacSign.PISCES),
]


def get_zodiac_sign_by_date(month: int, day: int) -> Optional[ZodiacSign]:
    for start_month, start_day, end_month, end_day, sign in ZODIAC_DATE_RANGES:
        if start_month == end_month:
            if month == start_month and start_day <= day <= end_day:
                return sign
        else:
            if (month == start_month and day >= start_day) or \
               (month == end_month and day <= end_day):
                return sign
    return None


def is_zodiac_match(user_zodiac: str, target_zodiac: str) -> bool:
    if not user_zodiac or not target_zodiac:
        return False
    return user_zodiac.lower() == target_zodiac.lower()

ZODIAC_DISPLAY_NAMES = {
    ZodiacSign.ARIES: "白羊座",
    ZodiacSign.TAURUS: "金牛座",
    ZodiacSign.GEMINI: "双子座",
    ZodiacSign.CANCER: "巨蟹座",
    ZodiacSign.LEO: "狮子座",
    ZodiacSign.VIRGO: "处女座",
    ZodiacSign.LIBRA: "天秤座",
    ZodiacSign.SCORPIO: "天蝎座",
    ZodiacSign.SAGITTARIUS: "射手座",
    ZodiacSign.CAPRICORN: "摩羯座",
    ZodiacSign.AQUARIUS: "水瓶座",
    ZodiacSign.PISCES: "双鱼座",
}

ACTIVITY_TYPE_DISPLAY_NAMES = {
    ActivityType.FESTIVAL: "节日活动",
    ActivityType.ZODIAC_MONTH: "星座月",
    ActivityType.WEEKEND_DUNGEON: "周末副本",
    ActivityType.BRAND_COLLAB: "品牌联名",
}


class ActivityService:
    """
    活动系统服务
    
    核心功能：
    - 活动 CRUD 操作
    - 活动状态管理（自动启停）
    - 活动权益计算与发放
    - 用户参与记录管理
    - 活动列表查询（进行中、即将开始、已结束）
    """
    
    _instance: Optional['ActivityService'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_activity_list(
        self, 
        db: Session,
        status_filter: Optional[str] = None,
        activity_type: Optional[str] = None,
        include_archived: bool = False
    ) -> List[Dict[str, Any]]:
        """
        获取活动列表
        
        Args:
            status_filter: 状态过滤，可选值：active, upcoming, ended
            activity_type: 活动类型过滤
            include_archived: 是否包含已归档活动
        """
        now = _utc_now()
        
        query = db.query(Activity).filter(Activity.is_deleted == False)
        
        if not include_archived:
            query = query.filter(Activity.status != ActivityStatus.ARCHIVED)
        
        if activity_type:
            query = query.filter(Activity.activity_type == activity_type)
        
        if status_filter == "active":
            query = query.filter(
                Activity.status == ActivityStatus.ACTIVE,
                Activity.start_time <= now,
                Activity.end_time > now
            )
        elif status_filter == "upcoming":
            query = query.filter(
                Activity.status == ActivityStatus.SCHEDULED,
                Activity.start_time > now
            )
        elif status_filter == "ended":
            query = query.filter(
                Activity.status == ActivityStatus.ENDED,
                Activity.end_time <= now
            )
        
        query = query.order_by(Activity.priority.desc(), Activity.start_time.desc())
        
        activities = query.all()
        
        return [self._activity_to_dict(act, include_benefits=True) for act in activities]
    
    def get_activity_by_id(self, db: Session, activity_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID获取活动详情
        """
        activity = db.query(Activity).filter(Activity.id == activity_id, Activity.is_deleted == False).first()
        if not activity:
            return None
        return self._activity_to_dict(activity, include_benefits=True)
    
    def get_activity_by_key(self, db: Session, activity_key: str) -> Optional[Dict[str, Any]]:
        """
        根据KEY获取活动详情
        """
        activity = db.query(Activity).filter(Activity.activity_key == activity_key, Activity.is_deleted == False).first()
        if not activity:
            return None
        return self._activity_to_dict(activity, include_benefits=True)
    
    def create_activity(
        self, 
        db: Session,
        activity_data: Dict[str, Any],
        created_by: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        创建活动
        
        Args:
            activity_data: 活动数据
            created_by: 创建者用户ID
        """
        now = _utc_now()
        
        activity_key = activity_data.get("activity_key")
        if not activity_key:
            activity_key = f"ACT_{now.strftime('%Y%m%d')}_{uuid.uuid4().hex[:8].upper()}"
        
        existing = db.query(Activity).filter(Activity.activity_key == activity_key).first()
        if existing:
            return {
                "success": False,
                "error_code": "DUPLICATE_ACTIVITY_KEY",
                "error": f"活动KEY已存在: {activity_key}"
            }
        
        start_time = activity_data.get("start_time")
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        
        end_time = activity_data.get("end_time")
        if isinstance(end_time, str):
            end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        
        status = activity_data.get("status", ActivityStatus.DRAFT)
        if status == ActivityStatus.SCHEDULED:
            if start_time and start_time <= now and end_time and end_time > now:
                status = ActivityStatus.ACTIVE
            elif end_time and end_time <= now:
                status = ActivityStatus.ENDED
        
        activity = Activity(
            activity_key=activity_key,
            name=activity_data.get("name", ""),
            display_name=activity_data.get("display_name", activity_data.get("name", "")),
            description=activity_data.get("description"),
            activity_type=activity_data.get("activity_type", ActivityType.FESTIVAL),
            status=status,
            start_time=start_time,
            end_time=end_time,
            target_zodiac_sign=activity_data.get("target_zodiac_sign"),
            brand_name=activity_data.get("brand_name"),
            brand_logo_url=activity_data.get("brand_logo_url"),
            rules_text=activity_data.get("rules_text"),
            display_image_url=activity_data.get("display_image_url"),
            banner_image_url=activity_data.get("banner_image_url"),
            is_auto_activated=activity_data.get("is_auto_activated", True),
            priority=activity_data.get("priority", 0),
            extra_metadata=json.dumps(activity_data.get("metadata", {}) if activity_data.get("metadata") else activity_data.get("extra_metadata", {})) if (activity_data.get("metadata") or activity_data.get("extra_metadata")) else None,
            created_by=created_by
        )
        
        db.add(activity)
        db.flush()
        
        benefits_data = activity_data.get("benefits", [])
        for benefit_data in benefits_data:
            benefit = ActivityBenefit(
                activity_id=activity.id,
                benefit_type=benefit_data.get("benefit_type"),
                benefit_name=benefit_data.get("benefit_name"),
                description=benefit_data.get("description"),
                multiplier=benefit_data.get("multiplier", 1.0),
                discount_percent=benefit_data.get("discount_percent"),
                rate_up_percent=benefit_data.get("rate_up_percent"),
                free_count=benefit_data.get("free_count", 0),
                item_id=benefit_data.get("item_id"),
                item_quantity=benefit_data.get("item_quantity", 1),
                target_module=benefit_data.get("target_module"),
                eligibility_filter=json.dumps(benefit_data.get("eligibility_filter", {})) if benefit_data.get("eligibility_filter") else None,
                is_active=benefit_data.get("is_active", True),
                daily_limit=benefit_data.get("daily_limit"),
                total_limit=benefit_data.get("total_limit"),
                sort_order=benefit_data.get("sort_order", 0)
            )
            db.add(benefit)
        
        db.commit()
        db.refresh(activity)
        
        logger.info(f"创建活动成功: {activity.activity_key} - {activity.name}")
        
        return {
            "success": True,
            "data": self._activity_to_dict(activity, include_benefits=True)
        }
    
    def update_activity(
        self,
        db: Session,
        activity_id: int,
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        更新活动
        """
        activity = db.query(Activity).filter(Activity.id == activity_id).first()
        if not activity:
            return {
                "success": False,
                "error_code": "ACTIVITY_NOT_FOUND",
                "error": "活动不存在"
            }
        
        updatable_fields = [
            "name", "display_name", "description", "activity_type", "status",
            "start_time", "end_time", "target_zodiac_sign", "brand_name",
            "brand_logo_url", "rules_text", "display_image_url", "banner_image_url",
            "is_auto_activated", "priority", "extra_metadata"
        ]
        
        for field in updatable_fields:
            if field in update_data:
                if field in ["start_time", "end_time"] and isinstance(update_data[field], str):
                    setattr(activity, field, datetime.fromisoformat(update_data[field].replace('Z', '+00:00')))
                elif field == "extra_metadata" and update_data[field]:
                    setattr(activity, field, json.dumps(update_data[field]))
                else:
                    setattr(activity, field, update_data[field])
        
        if "metadata" in update_data and update_data["metadata"]:
            setattr(activity, "extra_metadata", json.dumps(update_data["metadata"]))
        
        now = _utc_now()
        if activity.is_auto_activated:
            if activity.start_time <= now and activity.end_time > now:
                if activity.status == ActivityStatus.SCHEDULED:
                    activity.status = ActivityStatus.ACTIVE
            elif activity.end_time <= now:
                if activity.status == ActivityStatus.ACTIVE:
                    activity.status = ActivityStatus.ENDED
        
        db.commit()
        db.refresh(activity)
        
        logger.info(f"更新活动成功: {activity.activity_key}")
        
        return {
            "success": True,
            "data": self._activity_to_dict(activity, include_benefits=True)
        }
    
    def update_activity_status(
        self,
        db: Session,
        activity_id: int,
        new_status: str
    ) -> Dict[str, Any]:
        """
        更新活动状态
        """
        activity = db.query(Activity).filter(Activity.id == activity_id).first()
        if not activity:
            return {
                "success": False,
                "error_code": "ACTIVITY_NOT_FOUND",
                "error": "活动不存在"
            }
        
        activity.status = new_status
        db.commit()
        db.refresh(activity)
        
        logger.info(f"更新活动状态: {activity.activity_key} -> {new_status}")
        
        return {
            "success": True,
            "data": self._activity_to_dict(activity, include_benefits=False)
        }
    
    def delete_activity(self, db: Session, activity_id: int) -> Dict[str, Any]:
        """
        删除活动（软删除，设置 is_deleted=True）
        """
        activity = db.query(Activity).filter(Activity.id == activity_id, Activity.is_deleted == False).first()
        if not activity:
            return {
                "success": False,
                "error_code": "ACTIVITY_NOT_FOUND",
                "error": "活动不存在或已删除"
            }
        
        activity.is_deleted = True
        activity.status = ActivityStatus.ARCHIVED
        db.commit()
        
        logger.info(f"软删除活动: {activity.activity_key}")
        
        return {
            "success": True,
            "message": "活动已软删除"
        }
    
    def get_active_benefits(
        self,
        db: Session,
        user_id: Optional[int] = None,
        module_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取当前生效的活动权益
        
        Args:
            user_id: 用户ID，用于检查用户特定的权益
            module_type: 模块类型，如 synastry, blind_box, stardust 等
        """
        now = _utc_now()
        
        query = db.query(ActivityBenefit).join(Activity).filter(
            Activity.status == ActivityStatus.ACTIVE,
            Activity.start_time <= now,
            Activity.end_time > now,
            Activity.is_deleted == False,
            ActivityBenefit.is_active == True
        )
        
        if module_type:
            query = query.filter(
                or_(
                    ActivityBenefit.target_module == module_type,
                    ActivityBenefit.target_module == None
                )
            )
        
        query = query.order_by(Activity.priority.desc(), ActivityBenefit.sort_order.asc())
        
        benefits = query.all()
        
        result = []
        for benefit in benefits:
            benefit_dict = self._benefit_to_dict(benefit)
            benefit_dict["activity"] = {
                "id": benefit.activity.id,
                "activity_key": benefit.activity.activity_key,
                "name": benefit.activity.name,
                "display_name": benefit.activity.display_name,
                "activity_type": benefit.activity.activity_type,
                "start_time": benefit.activity.start_time.isoformat() if benefit.activity.start_time else None,
                "end_time": benefit.activity.end_time.isoformat() if benefit.activity.end_time else None,
            }
            result.append(benefit_dict)
        
        return result
    
    def get_user_activity_participation(
        self,
        db: Session,
        user_id: int,
        activity_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取用户的活动参与记录
        """
        query = db.query(ActivityParticipation).filter(
            ActivityParticipation.user_id == user_id
        )
        
        if activity_id:
            query = query.filter(ActivityParticipation.activity_id == activity_id)
        
        participations = query.all()
        
        return [self._participation_to_dict(p) for p in participations]
    
    def record_user_participation(
        self,
        db: Session,
        user_id: int,
        activity_id: int,
        action_type: str,
        action_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        记录用户活动参与
        
        Args:
            action_type: 操作类型，如 synastry, blind_box, stardust 等
        """
        participation = db.query(ActivityParticipation).filter(
            ActivityParticipation.user_id == user_id,
            ActivityParticipation.activity_id == activity_id
        ).first()
        
        now = _utc_now()
        
        if not participation:
            participation = ActivityParticipation(
                user_id=user_id,
                activity_id=activity_id,
                joined_at=now,
                last_active_at=now,
                synastry_count=0,
                blind_box_count=0,
                stardust_earned=0
            )
            db.add(participation)
        
        participation.last_active_at = now
        
        if action_type == "synastry":
            participation.synastry_count = (participation.synastry_count or 0) + 1
        elif action_type == "blind_box":
            participation.blind_box_count = (participation.blind_box_count or 0) + 1
        elif action_type == "stardust" and action_data:
            amount = action_data.get("amount", 0)
            participation.stardust_earned = (participation.stardust_earned or 0) + amount
        
        db.commit()
        db.refresh(participation)
        
        return {
            "success": True,
            "data": self._participation_to_dict(participation)
        }
    
    def calculate_benefit_multiplier(
        self,
        db: Session,
        module_type: str,
        user_id: Optional[int] = None,
        user_zodiac_sign: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        计算活动权益倍率
        
        Args:
            module_type: 模块类型：synastry, blind_box, stardust
            user_id: 用户ID
            user_zodiac_sign: 用户星座，用于星座月活动判断
        
        Returns:
            包含 multiplier, discount_percent, rate_up_percent, free_count 等信息
        """
        benefits = self.get_active_benefits(db, user_id, module_type)
        
        result = {
            "multiplier": 1.0,
            "discount_percent": 0,
            "rate_up_percent": 0,
            "free_count": 0,
            "active_activities": [],
            "applied_benefits": []
        }
        
        now = _utc_now()
        
        for benefit in benefits:
            activity = benefit.get("activity", {})
            activity_type = activity.get("activity_type")
            
            is_eligible = True
            
            if activity_type == ActivityType.ZODIAC_MONTH:
                target_zodiac = activity.get("target_zodiac_sign")
                if target_zodiac and user_zodiac_sign:
                    if not is_zodiac_match(user_zodiac_sign, target_zodiac):
                        is_eligible = False
            
            if not is_eligible:
                continue
            
            if module_type == "synastry":
                if benefit["benefit_type"] == BenefitType.SYNASTRY_DOUBLE_REWARD:
                    if benefit["multiplier"] > result["multiplier"]:
                        result["multiplier"] = benefit["multiplier"]
                        result["applied_benefits"].append(benefit)
                elif benefit["benefit_type"] == BenefitType.SYNASTRY_FREE:
                    result["free_count"] += benefit.get("free_count", 0)
                    result["applied_benefits"].append(benefit)
            
            elif module_type == "blind_box":
                if benefit["benefit_type"] == BenefitType.BLIND_BOX_DISCOUNT:
                    discount = benefit.get("discount_percent", 0)
                    if discount > result["discount_percent"]:
                        result["discount_percent"] = discount
                        result["applied_benefits"].append(benefit)
                elif benefit["benefit_type"] == BenefitType.BLIND_BOX_RATE_UP:
                    rate_up = benefit.get("rate_up_percent", 0)
                    if rate_up > result["rate_up_percent"]:
                        result["rate_up_percent"] = rate_up
                        result["applied_benefits"].append(benefit)
            
            elif module_type == "stardust":
                if benefit["benefit_type"] == BenefitType.STARDUST_DOUBLE:
                    if benefit["multiplier"] > result["multiplier"]:
                        result["multiplier"] = benefit["multiplier"]
                        result["applied_benefits"].append(benefit)
            
            if activity not in result["active_activities"]:
                result["active_activities"].append(activity)
        
        return result
    
    def check_and_update_activity_statuses(self, db: Session) -> Dict[str, Any]:
        """
        检查并更新所有活动的状态（自动启停）
        
        此方法应该定期调用（如定时任务）
        """
        now = _utc_now()
        
        scheduled_activities = db.query(Activity).filter(
            Activity.status == ActivityStatus.SCHEDULED,
            Activity.is_auto_activated == True,
            Activity.is_deleted == False,
            Activity.start_time <= now,
            Activity.end_time > now
        ).all()
        
        activated_count = 0
        for activity in scheduled_activities:
            activity.status = ActivityStatus.ACTIVE
            activated_count += 1
            logger.info(f"自动激活活动: {activity.activity_key}")
        
        active_activities = db.query(Activity).filter(
            Activity.status == ActivityStatus.ACTIVE,
            Activity.is_auto_activated == True,
            Activity.is_deleted == False,
            Activity.end_time <= now
        ).all()
        
        ended_count = 0
        for activity in active_activities:
            activity.status = ActivityStatus.ENDED
            ended_count += 1
            logger.info(f"自动结束活动: {activity.activity_key}")
        
        db.commit()
        
        return {
            "success": True,
            "data": {
                "activated_count": activated_count,
                "ended_count": ended_count
            }
        }
    
    def get_hall_activities(self, db: Session) -> Dict[str, Any]:
        """
        获取副本大厅展示的活动列表
        
        返回进行中、即将开始、已结束的活动
        """
        now = _utc_now()
        
        active_activities = db.query(Activity).filter(
            Activity.status == ActivityStatus.ACTIVE,
            Activity.is_deleted == False,
            Activity.start_time <= now,
            Activity.end_time > now
        ).order_by(Activity.priority.desc(), Activity.start_time.asc()).all()
        
        upcoming_activities = db.query(Activity).filter(
            Activity.status == ActivityStatus.SCHEDULED,
            Activity.is_deleted == False,
            Activity.start_time > now
        ).order_by(Activity.start_time.asc()).limit(5).all()
        
        ended_activities = db.query(Activity).filter(
            Activity.status == ActivityStatus.ENDED,
            Activity.is_deleted == False,
            Activity.end_time <= now
        ).order_by(Activity.end_time.desc()).limit(3).all()
        
        return {
            "success": True,
            "data": {
                "active": [self._activity_to_dict(a, include_benefits=True) for a in active_activities],
                "upcoming": [self._activity_to_dict(a, include_benefits=False) for a in upcoming_activities],
                "ended": [self._activity_to_dict(a, include_benefits=False) for a in ended_activities],
                "current_time": now.isoformat()
            }
        }
    
    def _activity_to_dict(self, activity: Activity, include_benefits: bool = False) -> Dict[str, Any]:
        """
        将活动对象转换为字典
        """
        extra_metadata = {}
        if activity.extra_metadata:
            try:
                extra_metadata = json.loads(activity.extra_metadata)
            except:
                pass
        
        result = {
            "id": activity.id,
            "activity_key": activity.activity_key,
            "name": activity.name,
            "display_name": activity.display_name,
            "description": activity.description,
            "activity_type": activity.activity_type,
            "activity_type_display": ACTIVITY_TYPE_DISPLAY_NAMES.get(activity.activity_type, activity.activity_type),
            "status": activity.status,
            "start_time": activity.start_time.isoformat() if activity.start_time else None,
            "end_time": activity.end_time.isoformat() if activity.end_time else None,
            "target_zodiac_sign": activity.target_zodiac_sign,
            "target_zodiac_display": ZODIAC_DISPLAY_NAMES.get(activity.target_zodiac_sign) if activity.target_zodiac_sign else None,
            "brand_name": activity.brand_name,
            "brand_logo_url": activity.brand_logo_url,
            "rules_text": activity.rules_text,
            "display_image_url": activity.display_image_url,
            "banner_image_url": activity.banner_image_url,
            "is_auto_activated": activity.is_auto_activated,
            "priority": activity.priority,
            "is_deleted": activity.is_deleted,
            "extra_metadata": extra_metadata,
            "metadata": extra_metadata,
            "created_by": activity.created_by,
            "created_at": activity.created_at.isoformat() if activity.created_at else None,
            "updated_at": activity.updated_at.isoformat() if activity.updated_at else None,
        }
        
        if include_benefits:
            result["benefits"] = [self._benefit_to_dict(b) for b in activity.benefits]
        
        return result
    
    def _benefit_to_dict(self, benefit: ActivityBenefit) -> Dict[str, Any]:
        """
        将权益对象转换为字典
        """
        eligibility_filter = {}
        if benefit.eligibility_filter:
            try:
                eligibility_filter = json.loads(benefit.eligibility_filter)
            except:
                pass
        
        return {
            "id": benefit.id,
            "activity_id": benefit.activity_id,
            "benefit_type": benefit.benefit_type,
            "benefit_name": benefit.benefit_name,
            "description": benefit.description,
            "multiplier": benefit.multiplier,
            "discount_percent": benefit.discount_percent,
            "rate_up_percent": benefit.rate_up_percent,
            "free_count": benefit.free_count,
            "item_id": benefit.item_id,
            "item_quantity": benefit.item_quantity,
            "target_module": benefit.target_module,
            "eligibility_filter": eligibility_filter,
            "is_active": benefit.is_active,
            "daily_limit": benefit.daily_limit,
            "total_limit": benefit.total_limit,
            "sort_order": benefit.sort_order,
        }
    
    def _participation_to_dict(self, participation: ActivityParticipation) -> Dict[str, Any]:
        """
        将参与记录转换为字典
        """
        items_claimed = []
        if participation.items_claimed:
            try:
                items_claimed = json.loads(participation.items_claimed)
            except:
                pass
        
        daily_benefit_usage = {}
        if participation.daily_benefit_usage:
            try:
                daily_benefit_usage = json.loads(participation.daily_benefit_usage)
            except:
                pass
        
        return {
            "id": participation.id,
            "activity_id": participation.activity_id,
            "user_id": participation.user_id,
            "joined_at": participation.joined_at.isoformat() if participation.joined_at else None,
            "last_active_at": participation.last_active_at.isoformat() if participation.last_active_at else None,
            "synastry_count": participation.synastry_count,
            "blind_box_count": participation.blind_box_count,
            "stardust_earned": participation.stardust_earned,
            "items_claimed": items_claimed,
            "daily_benefit_usage": daily_benefit_usage,
        }


activity_service = ActivityService()


def get_activity_service() -> ActivityService:
    return activity_service
