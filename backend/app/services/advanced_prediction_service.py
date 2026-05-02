import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import and_, func, or_

from app.models import (
    CollectivePrediction,
    PredictionVote,
    StarDustTransaction,
    User,
    PredictionTheme,
    UserTag,
    UserTagInferenceLog,
    ResolutionEvidence,
    ExclusiveItem,
    UserInventory,
    ProphecyTicket,
    SessionType,
    RewardAssetType,
    OracleDataSource,
    VoteAssetType,
    TagCategory
)
from app.services.energy_weather_service import (
    get_energy_weather_service,
    EnergyWeatherService
)
from app.services.star_resonance_service import (
    get_star_resonance_service,
    StarResonanceService
)

logger = logging.getLogger(__name__)

FIXED_THEMES_CONFIG = {
    "daily_element_dominance": {
        "theme_key": "daily_element_dominance",
        "theme_name": "今日主导元素",
        "description": "预测今日能量场中占主导地位的元素",
        "theme_category": "element",
        "default_options": [
            {"value": "fire", "label": "🔥 火象主导", "icon": "🔥"},
            {"value": "earth", "label": "🌍 土象主导", "icon": "🌍"},
            {"value": "air", "label": "💨 风象主导", "icon": "💨"},
            {"value": "water", "label": "💧 水象主导", "icon": "💧"}
        ],
        "oracle_source": OracleDataSource.RESONANCE_POOL,
        "resolution_rule": "根据星能共鸣池快照中的元素分布，选择能量最高的元素",
        "default_session_type": SessionType.DAILY,
        "default_max_votes": 1,
        "default_base_cost": 0,
        "default_reward_type": RewardAssetType.FRAGMENT,
        "default_reward_amount": 15
    },
    "daily_weather_forecast": {
        "theme_key": "daily_weather_forecast",
        "theme_name": "能量天气预报",
        "description": "预测今日能量气象站的天气状况",
        "theme_category": "weather",
        "default_options": [
            {"value": "clear", "label": "☀️ 晴朗", "icon": "☀️"},
            {"value": "mild", "label": "⛅ 多云", "icon": "⛅"},
            {"value": "moderate", "label": "🌥️ 阴天", "icon": "🌥️"},
            {"value": "severe", "label": "⛈️ 雷雨", "icon": "⛈️"},
            {"value": "critical", "label": "🚨 红色预警", "icon": "🚨"}
        ],
        "oracle_source": OracleDataSource.WEATHER,
        "resolution_rule": "根据能量气象站的实际天气状况进行结算",
        "default_session_type": SessionType.DAILY,
        "default_max_votes": 1,
        "default_base_cost": 0,
        "default_reward_type": RewardAssetType.FRAGMENT,
        "default_reward_amount": 20
    },
    "weekly_lucky_sign": {
        "theme_key": "weekly_lucky_sign",
        "theme_name": "本周幸运星座",
        "description": "预测本周运势最佳的星座",
        "theme_category": "zodiac",
        "default_options": [
            {"value": "aries", "label": "♈ 白羊座", "icon": "♈"},
            {"value": "taurus", "label": "♉ 金牛座", "icon": "♉"},
            {"value": "gemini", "label": "♊ 双子座", "icon": "♊"},
            {"value": "cancer", "label": "♋ 巨蟹座", "icon": "♋"},
            {"value": "leo", "label": "♌ 狮子座", "icon": "♌"},
            {"value": "virgo", "label": "♍ 处女座", "icon": "♍"},
            {"value": "libra", "label": "♎ 天秤座", "icon": "♎"},
            {"value": "scorpio", "label": "♏ 天蝎座", "icon": "♏"},
            {"value": "sagittarius", "label": "♐ 射手座", "icon": "♐"},
            {"value": "capricorn", "label": "♑ 摩羯座", "icon": "♑"},
            {"value": "aquarius", "label": "♒ 水瓶座", "icon": "♒"},
            {"value": "pisces", "label": "♓ 双鱼座", "icon": "♓"}
        ],
        "oracle_source": OracleDataSource.RESONANCE_POOL,
        "resolution_rule": "根据本周星能共鸣池中各星座的能量贡献统计",
        "default_session_type": SessionType.WEEKLY,
        "default_max_votes": 3,
        "default_base_cost": 0,
        "default_reward_type": RewardAssetType.POINT,
        "default_reward_amount": 50
    },
    "monthly_dominant_planet": {
        "theme_key": "monthly_dominant_planet",
        "theme_name": "本月主导行星",
        "description": "预测本月影响力最大的行星",
        "theme_category": "planet",
        "default_options": [
            {"value": "sun", "label": "☉ 太阳", "icon": "☉"},
            {"value": "moon", "label": "☽ 月亮", "icon": "☽"},
            {"value": "mercury", "label": "☿ 水星", "icon": "☿"},
            {"value": "venus", "label": "♀ 金星", "icon": "♀"},
            {"value": "mars", "label": "♂ 火星", "icon": "♂"},
            {"value": "jupiter", "label": "♃ 木星", "icon": "♃"},
            {"value": "saturn", "label": "♄ 土星", "icon": "♄"}
        ],
        "oracle_source": OracleDataSource.WEATHER,
        "resolution_rule": "根据本月天象事件和能量气象站的行星能量统计",
        "default_session_type": SessionType.SPECIAL,
        "default_max_votes": 5,
        "default_base_cost": 5,
        "default_reward_type": RewardAssetType.TICKET,
        "default_reward_amount": 3
    }
}


@dataclass
class VoteValidationResult:
    valid: bool
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    user_vote_count: int = 0
    max_allowed: int = 0
    cost_required: int = 0
    user_balance: int = 0


@dataclass
class SettlementResult:
    success: bool
    prediction_id: int
    correct_option: str
    correct_count: int
    incorrect_count: int
    total_reward_distributed: int
    evidence_summary: Optional[str] = None
    error_message: Optional[str] = None


class AdvancedPredictionService:
    """
    增强版预测竞猜服务
    
    核心功能：
    - 固定主题竞猜管理
    - 每日/每周固定场次调度
    - 提前预告机制
    - 三类资产独立链路
    - 投票次数限制与付费追加
    - 会员加成机制
    - 用户标签沉淀
    - 预言机自动结算
    - 人工控场支持
    """
    
    _instance: Optional['AdvancedPredictionService'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self._weather_service: Optional[EnergyWeatherService] = None
        self._resonance_service: Optional[StarResonanceService] = None
    
    def _get_weather_service(self) -> EnergyWeatherService:
        if self._weather_service is None:
            self._weather_service = get_energy_weather_service()
        return self._weather_service
    
    def _get_resonance_service(self) -> StarResonanceService:
        if self._resonance_service is None:
            self._resonance_service = get_star_resonance_service()
        return self._resonance_service
    
    def initialize_fixed_themes(self, db: Session) -> List[Dict[str, Any]]:
        """
        初始化固定主题配置
        
        将预设的固定主题配置写入数据库
        """
        created_themes = []
        
        for theme_key, config in FIXED_THEMES_CONFIG.items():
            existing = db.query(PredictionTheme).filter(
                PredictionTheme.theme_key == theme_key
            ).first()
            
            if existing:
                created_themes.append(self._theme_to_dict(existing))
                continue
            
            theme = PredictionTheme(
                theme_key=theme_key,
                theme_name=config["theme_name"],
                description=config["description"],
                theme_category=config["theme_category"],
                default_options=json.dumps(config["default_options"], ensure_ascii=False),
                default_session_type=config["default_session_type"],
                default_max_votes=config["default_max_votes"],
                default_base_cost=config["default_base_cost"],
                default_reward_type=config["default_reward_type"],
                default_reward_amount=config["default_reward_amount"],
                oracle_source=config["oracle_source"],
                resolution_rule=config["resolution_rule"],
                is_active=True,
                is_permanent=True,
                sort_order=len(created_themes)
            )
            
            db.add(theme)
            db.commit()
            db.refresh(theme)
            
            created_themes.append(self._theme_to_dict(theme))
            logger.info(f"创建固定主题: {theme_key}")
        
        return created_themes
    
    def get_active_themes(self, db: Session) -> List[Dict[str, Any]]:
        """
        获取所有活跃的固定主题
        """
        themes = db.query(PredictionTheme).filter(
            PredictionTheme.is_active == True
        ).order_by(
            PredictionTheme.sort_order.asc()
        ).all()
        
        return [self._theme_to_dict(t) for t in themes]
    
    def create_daily_sessions(self, db: Session, target_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        创建每日场次
        
        为指定日期创建所有固定主题的每日场次
        """
        if target_date is None:
            tomorrow = datetime.utcnow().date() + timedelta(days=1)
            target_date = tomorrow.strftime("%Y-%m-%d")
        
        today = datetime.utcnow().strftime("%Y-%m-%d")
        
        active_themes = db.query(PredictionTheme).filter(
            PredictionTheme.is_active == True,
            PredictionTheme.default_session_type == SessionType.DAILY
        ).all()
        
        created_predictions = []
        
        for theme in active_themes:
            session_key = f"daily_{theme.theme_key}_{target_date}"
            
            existing = db.query(CollectivePrediction).filter(
                CollectivePrediction.session_key == session_key
            ).first()
            
            if existing:
                created_predictions.append(self._prediction_to_dict(existing))
                continue
            
            options = json.loads(theme.default_options) if theme.default_options else []
            
            target_dt = datetime.strptime(target_date, "%Y-%m-%d")
            voting_starts = datetime.combine(target_dt - timedelta(days=1), datetime.min.time()) + timedelta(hours=12)
            voting_ends = datetime.combine(target_dt, datetime.min.time())
            
            prediction = CollectivePrediction(
                prediction_date=today,
                target_date=target_date,
                title=f"{target_date} - {theme.theme_name}",
                description=theme.description,
                prediction_type=theme.theme_category,
                session_type=SessionType.DAILY,
                session_key=session_key,
                theme_id=theme.id,
                options=json.dumps({
                    "labels": [opt["label"] for opt in options],
                    "values": [opt["value"] for opt in options],
                    "icons": [opt.get("icon", "") for opt in options]
                }, ensure_ascii=False),
                status="scheduled",
                is_resolved=False,
                announced_at=datetime.utcnow(),
                voting_starts_at=voting_starts,
                voting_ends_at=voting_ends,
                max_votes_per_user=theme.default_max_votes,
                base_vote_cost=theme.default_base_cost,
                extra_vote_cost=10,
                reward_asset_type=theme.default_reward_type,
                base_reward_amount=theme.default_reward_amount,
                oracle_data_source=theme.oracle_source,
                total_votes=0,
                vote_distribution=json.dumps({}),
                total_stardust_pool=0
            )
            
            db.add(prediction)
            db.commit()
            db.refresh(prediction)
            
            created_predictions.append(self._prediction_to_dict(prediction))
            logger.info(f"创建每日场次: {session_key}")
        
        return created_predictions
    
    def create_weekly_sessions(self, db: Session) -> List[Dict[str, Any]]:
        """
        创建每周场次
        
        每周一创建本周的场次
        """
        now = datetime.utcnow()
        week_start = now - timedelta(days=now.weekday())
        week_end = week_start + timedelta(days=6)
        
        week_key = week_start.strftime("%Y-W%W")
        
        active_themes = db.query(PredictionTheme).filter(
            PredictionTheme.is_active == True,
            PredictionTheme.default_session_type == SessionType.WEEKLY
        ).all()
        
        created_predictions = []
        
        for theme in active_themes:
            session_key = f"weekly_{theme.theme_key}_{week_key}"
            
            existing = db.query(CollectivePrediction).filter(
                CollectivePrediction.session_key == session_key
            ).first()
            
            if existing:
                created_predictions.append(self._prediction_to_dict(existing))
                continue
            
            options = json.loads(theme.default_options) if theme.default_options else []
            
            voting_starts = week_start
            voting_ends = week_end + timedelta(hours=23, minutes=59, seconds=59)
            
            prediction = CollectivePrediction(
                prediction_date=now.strftime("%Y-%m-%d"),
                target_date=week_start.strftime("%Y-%m-%d"),
                title=f"{week_key} - {theme.theme_name}",
                description=theme.description,
                prediction_type=theme.theme_category,
                session_type=SessionType.WEEKLY,
                session_key=session_key,
                theme_id=theme.id,
                options=json.dumps({
                    "labels": [opt["label"] for opt in options],
                    "values": [opt["value"] for opt in options],
                    "icons": [opt.get("icon", "") for opt in options]
                }, ensure_ascii=False),
                status="scheduled",
                is_resolved=False,
                announced_at=datetime.utcnow(),
                voting_starts_at=voting_starts,
                voting_ends_at=voting_ends,
                max_votes_per_user=theme.default_max_votes,
                base_vote_cost=theme.default_base_cost,
                extra_vote_cost=20,
                reward_asset_type=theme.default_reward_type,
                base_reward_amount=theme.default_reward_amount,
                oracle_data_source=theme.oracle_source,
                total_votes=0,
                vote_distribution=json.dumps({}),
                total_stardust_pool=0
            )
            
            db.add(prediction)
            db.commit()
            db.refresh(prediction)
            
            created_predictions.append(self._prediction_to_dict(prediction))
            logger.info(f"创建每周场次: {session_key}")
        
        return created_predictions
    
    def get_upcoming_predictions(self, db: Session, include_announced: bool = True) -> List[Dict[str, Any]]:
        """
        获取即将开始的场次（提前预告）
        
        返回所有已预告但尚未开始投票的场次
        """
        now = datetime.utcnow()
        
        query = db.query(CollectivePrediction).filter(
            CollectivePrediction.is_resolved == False,
            CollectivePrediction.status != "resolved"
        )
        
        if include_announced:
            query = query.filter(
                or_(
                    CollectivePrediction.status == "scheduled",
                    CollectivePrediction.voting_starts_at > now
                )
            )
        else:
            query = query.filter(
                CollectivePrediction.voting_starts_at <= now,
                CollectivePrediction.voting_ends_at > now
            )
        
        predictions = query.order_by(
            CollectivePrediction.voting_starts_at.asc()
        ).all()
        
        return [self._prediction_to_dict(p) for p in predictions]
    
    def get_open_predictions(self, db: Session) -> List[Dict[str, Any]]:
        """
        获取当前开放投票的场次
        """
        now = datetime.utcnow()
        
        predictions = db.query(CollectivePrediction).filter(
            CollectivePrediction.is_resolved == False,
            CollectivePrediction.voting_starts_at <= now,
            CollectivePrediction.voting_ends_at > now
        ).order_by(
            CollectivePrediction.voting_ends_at.asc()
        ).all()
        
        return [self._prediction_to_dict(p) for p in predictions]
    
    def validate_vote(
        self,
        db: Session,
        user_id: int,
        prediction_id: int,
        use_asset: str = "fragment"
    ) -> VoteValidationResult:
        """
        验证投票是否合法
        
        检查：
        1. 场次是否开放
        2. 用户投票次数是否超限
        3. 用户资产是否足够
        """
        prediction = db.query(CollectivePrediction).filter(
            CollectivePrediction.id == prediction_id
        ).first()
        
        if not prediction:
            return VoteValidationResult(
                valid=False,
                error_code="PREDICTION_NOT_FOUND",
                error_message="预测场次不存在"
            )
        
        now = datetime.utcnow()
        
        if prediction.voting_starts_at and prediction.voting_starts_at > now:
            return VoteValidationResult(
                valid=False,
                error_code="VOTING_NOT_STARTED",
                error_message="投票尚未开始"
            )
        
        if prediction.voting_ends_at and prediction.voting_ends_at <= now:
            return VoteValidationResult(
                valid=False,
                error_code="VOTING_ENDED",
                error_message="投票已结束"
            )
        
        if prediction.is_resolved:
            return VoteValidationResult(
                valid=False,
                error_code="ALREADY_RESOLVED",
                error_message="场次已结算"
            )
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return VoteValidationResult(
                valid=False,
                error_code="USER_NOT_FOUND",
                error_message="用户不存在"
            )
        
        user_votes = db.query(PredictionVote).filter(
            PredictionVote.prediction_id == prediction_id,
            PredictionVote.user_id == user_id
        ).count()
        
        max_votes = prediction.max_votes_per_user or 1
        
        if user_votes >= max_votes:
            return VoteValidationResult(
                valid=False,
                error_code="MAX_VOTES_EXCEEDED",
                error_message=f"已达到最大投票次数 ({max_votes}次)",
                user_vote_count=user_votes,
                max_allowed=max_votes
            )
        
        base_cost = prediction.base_vote_cost or 0
        extra_cost = prediction.extra_vote_cost or 0
        
        if user_votes == 0:
            cost_required = base_cost
        else:
            cost_required = extra_cost
        
        user_balance = 0
        if use_asset == "fragment":
            user_balance = user.stardust_fragment_balance or 0
        elif use_asset == "point":
            user_balance = user.stardust_point_balance or 0
        elif use_asset == "ticket":
            valid_tickets = db.query(ProphecyTicket).filter(
                ProphecyTicket.user_id == user_id,
                ProphecyTicket.is_used == False,
                ProphecyTicket.valid_until > now
            ).count()
            user_balance = valid_tickets
        
        if cost_required > 0 and user_balance < cost_required:
            asset_name = {"fragment": "星元碎片", "point": "高阶星尘", "ticket": "预言券"}.get(use_asset, use_asset)
            return VoteValidationResult(
                valid=False,
                error_code="INSUFFICIENT_ASSETS",
                error_message=f"{asset_name}不足，需要 {cost_required}",
                cost_required=cost_required,
                user_balance=user_balance
            )
        
        return VoteValidationResult(
            valid=True,
            user_vote_count=user_votes,
            max_allowed=max_votes,
            cost_required=cost_required,
            user_balance=user_balance
        )
    
    def cast_vote(
        self,
        db: Session,
        user_id: int,
        prediction_id: int,
        selected_option: str,
        confidence: int = 50,
        use_asset: str = "fragment",
        is_vip: bool = False
    ) -> Dict[str, Any]:
        """
        用户投票
        
        完整的投票流程：
        1. 验证投票合法性
        2. 扣除相应资产
        3. 记录投票
        4. 更新场次统计
        5. 沉淀用户标签
        """
        validation = self.validate_vote(db, user_id, prediction_id, use_asset)
        
        if not validation.valid:
            return {
                "success": False,
                "error_code": validation.error_code,
                "error": validation.error_message
            }
        
        prediction = db.query(CollectivePrediction).filter(
            CollectivePrediction.id == prediction_id
        ).first()
        
        user = db.query(User).filter(User.id == user_id).first()
        
        options = json.loads(prediction.options) if prediction.options else {}
        option_values = options.get("values", [])
        
        if selected_option not in option_values:
            return {
                "success": False,
                "error_code": "INVALID_OPTION",
                "error": "无效的选项"
            }
        
        db.begin_nested()
        
        try:
            vote_number = validation.user_vote_count + 1
            cost_required = validation.cost_required
            
            applied_multiplier = 1.0
            is_vip_bonus = False
            if is_vip and prediction.is_vip_enabled:
                applied_multiplier = prediction.vip_multiplier or 1.5
                is_vip_bonus = True
            
            if cost_required > 0:
                self._deduct_asset(
                    db, user, use_asset, cost_required,
                    f"投票消耗 - {prediction.title}",
                    prediction_id
                )
            
            vote_asset_type = {
                "fragment": VoteAssetType.FRAGMENT,
                "point": VoteAssetType.POINT,
                "ticket": VoteAssetType.TICKET
            }.get(use_asset, VoteAssetType.FRAGMENT)
            
            vote = PredictionVote(
                prediction_id=prediction_id,
                user_id=user_id,
                vote_number=vote_number,
                selected_option=selected_option,
                confidence=max(0, min(100, confidence)),
                vote_asset_type=vote_asset_type,
                vote_cost=cost_required,
                stardust_bet=0,
                is_vip_bonus=is_vip_bonus,
                applied_multiplier=applied_multiplier,
                is_correct=None,
                reward_earned=0,
                reward_asset_type=prediction.reward_asset_type,
                reward_claimed=False,
                is_validated=True,
                validated_at=datetime.utcnow()
            )
            
            db.add(vote)
            
            prediction.total_votes = (prediction.total_votes or 0) + 1
            
            vote_distribution = json.loads(prediction.vote_distribution) if prediction.vote_distribution else {}
            if selected_option not in vote_distribution:
                vote_distribution[selected_option] = 0
            vote_distribution[selected_option] += 1
            prediction.vote_distribution = json.dumps(vote_distribution, ensure_ascii=False)
            
            prediction.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(vote)
            db.refresh(prediction)
            
            self._update_user_tags_from_vote(db, user_id, prediction, selected_option)
            
            return {
                "success": True,
                "vote": self._vote_to_dict(vote),
                "prediction": self._prediction_to_dict(prediction),
                "message": "投票成功！"
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"投票失败: {e}")
            return {
                "success": False,
                "error_code": "VOTE_FAILED",
                "error": str(e)
            }
    
    def _deduct_asset(
        self,
        db: Session,
        user: User,
        asset_type: str,
        amount: int,
        description: str,
        related_id: int
    ) -> bool:
        """
        扣除用户资产并记录交易
        """
        now = datetime.utcnow()
        
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
            ).order_by(ProphecyTicket.valid_until.asc()).limit(amount).all()
            
            if len(valid_tickets) < amount:
                raise ValueError("预言券不足")
            
            for ticket in valid_tickets:
                ticket.is_used = True
                ticket.used_at = now
                ticket.used_for = f"prediction_{related_id}"
            
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
            related_id=str(related_id),
            description=description,
            created_at=now
        )
        
        db.add(transaction)
        
        return True
    
    def _update_user_tags_from_vote(
        self,
        db: Session,
        user_id: int,
        prediction: CollectivePrediction,
        selected_option: str
    ):
        """
        根据投票更新用户标签
        
        沉淀的标签类型：
        1. 投票偏好
        2. 元素偏好
        3. 星座行为
        """
        now = datetime.utcnow()
        
        theme = db.query(PredictionTheme).filter(
            PredictionTheme.id == prediction.theme_id
        ).first()
        
        theme_category = theme.theme_category if theme else prediction.prediction_type
        
        tags_to_update = []
        
        voting_pref_tag = UserTag(
            user_id=user_id,
            tag_category=TagCategory.VOTING_PREFERENCE,
            tag_key=f"pref_{prediction.session_type}_{theme_category}",
            tag_value=selected_option,
            tag_score=1.0,
            confidence=0.7,
            source_type="voting",
            source_reference=f"prediction_{prediction.id}",
            first_seen_at=now,
            last_seen_at=now
        )
        tags_to_update.append(voting_pref_tag)
        
        if theme_category == "element" or selected_option in ["fire", "earth", "air", "water"]:
            element_tag = UserTag(
                user_id=user_id,
                tag_category=TagCategory.ELEMENT_PREFERENCE,
                tag_key=f"elem_{selected_option}",
                tag_value=selected_option,
                tag_score=1.0,
                confidence=0.6,
                source_type="voting",
                source_reference=f"prediction_{prediction.id}",
                first_seen_at=now,
                last_seen_at=now
            )
            tags_to_update.append(element_tag)
        
        for new_tag in tags_to_update:
            existing = db.query(UserTag).filter(
                UserTag.user_id == user_id,
                UserTag.tag_category == new_tag.tag_category,
                UserTag.tag_key == new_tag.tag_key
            ).first()
            
            if existing:
                existing.tag_score = min(existing.tag_score + 0.1, 5.0)
                existing.occurrence_count = (existing.occurrence_count or 0) + 1
                existing.last_seen_at = now
                existing.updated_at = now
            else:
                db.add(new_tag)
        
        inference_log = UserTagInferenceLog(
            user_id=user_id,
            inference_type="voting_behavior",
            inference_source=f"prediction_{prediction.id}",
            tags_inferred=json.dumps({
                "prediction_id": prediction.id,
                "selected_option": selected_option,
                "theme_category": theme_category
            }, ensure_ascii=False),
            created_at=now
        )
        db.add(inference_log)
        
        db.commit()
    
    def resolve_prediction_oracle(
        self,
        db: Session,
        prediction_id: int
    ) -> SettlementResult:
        """
        使用预言机自动结算
        
        根据场次配置的预言机数据源自动计算正确选项
        """
        prediction = db.query(CollectivePrediction).filter(
            CollectivePrediction.id == prediction_id
        ).first()
        
        if not prediction:
            return SettlementResult(
                success=False,
                prediction_id=prediction_id,
                correct_option="",
                correct_count=0,
                incorrect_count=0,
                total_reward_distributed=0,
                error_message="预测场次不存在"
            )
        
        if prediction.is_resolved:
            return SettlementResult(
                success=False,
                prediction_id=prediction_id,
                correct_option=prediction.correct_option or "",
                correct_count=0,
                incorrect_count=0,
                total_reward_distributed=0,
                error_message="场次已结算"
            )
        
        correct_option = None
        evidence_summary = ""
        
        if prediction.oracle_data_source == OracleDataSource.WEATHER:
            correct_option, evidence_summary = self._resolve_from_weather(db, prediction)
        elif prediction.oracle_data_source == OracleDataSource.RESONANCE_POOL:
            correct_option, evidence_summary = self._resolve_from_resonance_pool(db, prediction)
        else:
            return SettlementResult(
                success=False,
                prediction_id=prediction_id,
                correct_option="",
                correct_count=0,
                incorrect_count=0,
                total_reward_distributed=0,
                error_message="不支持的预言机数据源"
            )
        
        if not correct_option:
            return SettlementResult(
                success=False,
                prediction_id=prediction_id,
                correct_option="",
                correct_count=0,
                incorrect_count=0,
                total_reward_distributed=0,
                error_message="无法确定正确选项"
            )
        
        evidence = ResolutionEvidence(
            prediction_id=prediction_id,
            evidence_type=prediction.oracle_data_source,
            evidence_source="oracle_auto",
            evidence_data=evidence_summary,
            evidence_summary=f"预言机自动结算: {evidence_summary[:200]}",
            snapshot_at=datetime.utcnow(),
            is_used_for_resolution=True,
            resolution_outcome=correct_option
        )
        db.add(evidence)
        
        return self._execute_settlement(
            db, prediction, correct_option, "oracle_auto", evidence_summary
        )
    
    def _resolve_from_weather(
        self,
        db: Session,
        prediction: CollectivePrediction
    ) -> Tuple[Optional[str], str]:
        """
        从能量气象站获取数据进行结算
        """
        weather_service = self._get_weather_service()
        
        try:
            weather_data = weather_service.get_current_weather(db)
            
            prediction_type = prediction.prediction_type
            theme = db.query(PredictionTheme).filter(
                PredictionTheme.id == prediction.theme_id
            ).first()
            
            if theme and theme.theme_key == "daily_weather_forecast":
                weather_severity = weather_data.get("weather_severity", "mild")
                severity_map = {
                    "clear": "clear",
                    "mild": "mild",
                    "moderate": "moderate",
                    "severe": "severe",
                    "critical": "critical"
                }
                correct_option = severity_map.get(weather_severity, "mild")
                evidence_summary = f"能量气象站实际天气: {weather_data.get('weather_label', '未知')}, 严重程度: {weather_severity}"
                return correct_option, evidence_summary
            
            if theme and theme.theme_key == "monthly_dominant_planet":
                dominant_planets = weather_data.get("dominant_planets", [])
                if dominant_planets:
                    top_planet = dominant_planets[0].get("planet", "")
                    planet_map = {
                        "太阳": "sun", "月亮": "moon", "水星": "mercury",
                        "金星": "venus", "火星": "mars", "木星": "jupiter", "土星": "saturn"
                    }
                    correct_option = planet_map.get(top_planet)
                    if correct_option:
                        evidence_summary = f"能量气象站主导行星: {top_planet}, 完整列表: {dominant_planets}"
                        return correct_option, evidence_summary
            
            return None, "无法匹配天气数据源"
            
        except Exception as e:
            logger.error(f"从气象站获取结算数据失败: {e}")
            return None, f"获取气象数据失败: {str(e)}"
    
    def _resolve_from_resonance_pool(
        self,
        db: Session,
        prediction: CollectivePrediction
    ) -> Tuple[Optional[str], str]:
        """
        从星能共鸣池获取数据进行结算
        """
        resonance_service = self._get_resonance_service()
        
        try:
            pool_status = resonance_service.get_pool_status(db)
            
            theme = db.query(PredictionTheme).filter(
                PredictionTheme.id == prediction.theme_id
            ).first()
            
            if theme and theme.theme_key == "daily_element_dominance":
                element_dist = pool_status.element_distribution
                
                max_energy = 0.0
                dominant_element = None
                
                for elem, data in element_dist.items():
                    energy = float(data) if isinstance(data, (int, float)) else float(data.get("energy", 0))
                    if energy > max_energy:
                        max_energy = energy
                        dominant_element = elem
                
                if dominant_element:
                    evidence_summary = f"星能共鸣池元素分布: {element_dist}, 最高能量: {dominant_element} ({max_energy})"
                    return dominant_element, evidence_summary
            
            if theme and theme.theme_key == "weekly_lucky_sign":
                from app.services.community_energy_service import community_energy_service
                
                planet_dist = community_energy_service.aggregate_planet_distribution(db, [])
                dominant_planets = planet_dist.get("dominant_planets", [])
                
                if dominant_planets:
                    top_planet = dominant_planets[0].get("planet", "")
                    sign_map = {
                        "白羊座": "aries", "金牛座": "taurus", "双子座": "gemini",
                        "巨蟹座": "cancer", "狮子座": "leo", "处女座": "virgo",
                        "天秤座": "libra", "天蝎座": "scorpio", "射手座": "sagittarius",
                        "摩羯座": "capricorn", "水瓶座": "aquarius", "双鱼座": "pisces"
                    }
                    
                    zodiac_sign = dominant_planets[0].get("sign", "")
                    if zodiac_sign in sign_map:
                        correct_option = sign_map[zodiac_sign]
                        evidence_summary = f"星能共鸣池本周星座统计: {dominant_planets}, 最高: {zodiac_sign}"
                        return correct_option, evidence_summary
            
            return None, "无法匹配共鸣池数据源"
            
        except Exception as e:
            logger.error(f"从共鸣池获取结算数据失败: {e}")
            return None, f"获取共鸣池数据失败: {str(e)}"
    
    def resolve_prediction_manual(
        self,
        db: Session,
        prediction_id: int,
        correct_option: str,
        admin_id: int,
        reason: str = ""
    ) -> SettlementResult:
        """
        人工控场结算
        
        支持运营人员手动指定正确选项进行结算
        """
        prediction = db.query(CollectivePrediction).filter(
            CollectivePrediction.id == prediction_id
        ).first()
        
        if not prediction:
            return SettlementResult(
                success=False,
                prediction_id=prediction_id,
                correct_option="",
                correct_count=0,
                incorrect_count=0,
                total_reward_distributed=0,
                error_message="预测场次不存在"
            )
        
        if prediction.is_resolved:
            return SettlementResult(
                success=False,
                prediction_id=prediction_id,
                correct_option=prediction.correct_option or "",
                correct_count=0,
                incorrect_count=0,
                total_reward_distributed=0,
                error_message="场次已结算"
            )
        
        options = json.loads(prediction.options) if prediction.options else {}
        option_values = options.get("values", [])
        
        if correct_option not in option_values:
            return SettlementResult(
                success=False,
                prediction_id=prediction_id,
                correct_option="",
                correct_count=0,
                incorrect_count=0,
                total_reward_distributed=0,
                error_message="无效的正确选项"
            )
        
        evidence_summary = f"人工结算 - 管理员ID: {admin_id}, 原因: {reason or '运营调整'}"
        
        evidence = ResolutionEvidence(
            prediction_id=prediction_id,
            evidence_type="manual",
            evidence_source=f"admin_{admin_id}",
            evidence_data=json.dumps({
                "admin_id": admin_id,
                "reason": reason,
                "correct_option": correct_option
            }, ensure_ascii=False),
            evidence_summary=evidence_summary,
            snapshot_at=datetime.utcnow(),
            is_used_for_resolution=True,
            resolution_outcome=correct_option
        )
        db.add(evidence)
        
        return self._execute_settlement(
            db, prediction, correct_option, "manual", evidence_summary, admin_id
        )
    
    def _execute_settlement(
        self,
        db: Session,
        prediction: CollectivePrediction,
        correct_option: str,
        resolution_source: str,
        evidence_summary: str,
        admin_id: Optional[int] = None
    ) -> SettlementResult:
        """
        执行结算逻辑
        
        1. 更新场次状态
        2. 计算正确/错误票数
        3. 计算奖励金额
        4. 发放奖励
        5. 更新用户标签
        """
        now = datetime.utcnow()
        
        db.begin_nested()
        
        try:
            all_votes = db.query(PredictionVote).filter(
                PredictionVote.prediction_id == prediction.id
            ).all()
            
            correct_votes = []
            incorrect_votes = []
            
            for vote in all_votes:
                if vote.selected_option == correct_option:
                    vote.is_correct = True
                    correct_votes.append(vote)
                else:
                    vote.is_correct = False
                    incorrect_votes.append(vote)
            
            correct_count = len(correct_votes)
            incorrect_count = len(incorrect_votes)
            total_votes = correct_count + incorrect_count
            
            base_reward = prediction.base_reward_amount or 10
            bonus_reward = prediction.bonus_reward_amount or 0
            total_reward_amount = base_reward + bonus_reward
            
            total_reward_distributed = 0
            reward_transactions = []
            
            for vote in correct_votes:
                reward_amount = total_reward_amount
                
                if vote.is_vip_bonus and vote.applied_multiplier > 1:
                    reward_amount = int(reward_amount * vote.applied_multiplier)
                
                confidence = vote.confidence or 50
                if confidence >= 80:
                    reward_amount = int(reward_amount * 1.5)
                elif confidence >= 50:
                    reward_amount = int(reward_amount * 1.2)
                
                vote.reward_earned = reward_amount
                vote.reward_asset_type = prediction.reward_asset_type
                
                user = db.query(User).filter(User.id == vote.user_id).first()
                if user:
                    tx_result = self._grant_reward(
                        db, user,
                        prediction.reward_asset_type,
                        reward_amount,
                        f"竞猜奖励 - {prediction.title}",
                        prediction.id
                    )
                    reward_transactions.append({
                        "user_id": user.id,
                        "amount": reward_amount,
                        "asset_type": prediction.reward_asset_type
                    })
                    total_reward_distributed += reward_amount
                    
                    self._update_user_tags_from_settlement(
                        db, user.id, prediction, vote, True
                    )
            
            for vote in incorrect_votes:
                user = db.query(User).filter(User.id == vote.user_id).first()
                if user:
                    self._update_user_tags_from_settlement(
                        db, user.id, prediction, vote, False
                    )
            
            prediction.is_resolved = True
            prediction.resolved_at = now
            prediction.correct_option = correct_option
            prediction.status = "resolved"
            prediction.resolution_source = resolution_source
            prediction.is_manual_resolution = (resolution_source == "manual")
            prediction.resolved_by_admin_id = admin_id
            prediction.resolution_evidence = evidence_summary
            prediction.resolution_audit_log = json.dumps({
                "resolution_source": resolution_source,
                "admin_id": admin_id,
                "evidence_summary": evidence_summary,
                "correct_option": correct_option,
                "correct_count": correct_count,
                "incorrect_count": incorrect_count,
                "total_reward_distributed": total_reward_distributed,
                "resolved_at": now.isoformat()
            }, ensure_ascii=False)
            
            if total_votes > 0:
                accuracy_score = (correct_count / total_votes) * 100
                prediction.accuracy_score = round(accuracy_score, 1)
            
            prediction.updated_at = now
            
            db.commit()
            
            return SettlementResult(
                success=True,
                prediction_id=prediction.id,
                correct_option=correct_option,
                correct_count=correct_count,
                incorrect_count=incorrect_count,
                total_reward_distributed=total_reward_distributed,
                evidence_summary=evidence_summary
            )
            
        except Exception as e:
            db.rollback()
            logger.error(f"执行结算失败: {e}")
            return SettlementResult(
                success=False,
                prediction_id=prediction.id,
                correct_option=correct_option,
                correct_count=0,
                incorrect_count=0,
                total_reward_distributed=0,
                error_message=str(e)
            )
    
    def _grant_reward(
        self,
        db: Session,
        user: User,
        asset_type: str,
        amount: int,
        description: str,
        related_id: int
    ) -> bool:
        """
        发放奖励资产
        """
        now = datetime.utcnow()
        
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
            raise ValueError(f"不支持的资产类型: {asset_type}")
        
        transaction = StarDustTransaction(
            user_id=user.id,
            transaction_type="prediction_reward",
            currency_type=currency_type,
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_before + amount,
            related_type="prediction",
            related_id=str(related_id),
            description=description,
            created_at=now
        )
        
        db.add(transaction)
        
        return True
    
    def _update_user_tags_from_settlement(
        self,
        db: Session,
        user_id: int,
        prediction: CollectivePrediction,
        vote: PredictionVote,
        is_correct: bool
    ):
        """
        根据结算结果更新用户标签
        
        沉淀的标签：
        1. 投票准确率
        2. 风险偏好（信心值）
        3. 元素/星座预测能力
        """
        now = datetime.utcnow()
        
        accuracy_tag = UserTag(
            user_id=user_id,
            tag_category=TagCategory.VOTING_PREFERENCE,
            tag_key="prediction_accuracy",
            tag_value="correct" if is_correct else "incorrect",
            tag_score=1.0 if is_correct else 0.5,
            confidence=0.8,
            source_type="settlement",
            source_reference=f"prediction_{prediction.id}",
            first_seen_at=now,
            last_seen_at=now
        )
        
        confidence_tag = UserTag(
            user_id=user_id,
            tag_category=TagCategory.SPENDING_HABIT,
            tag_key="confidence_preference",
            tag_value=str(vote.confidence or 50),
            tag_score=1.0,
            confidence=0.7,
            source_type="voting",
            source_reference=f"prediction_{prediction.id}",
            first_seen_at=now,
            last_seen_at=now
        )
        
        for new_tag in [accuracy_tag, confidence_tag]:
            existing = db.query(UserTag).filter(
                UserTag.user_id == user_id,
                UserTag.tag_category == new_tag.tag_category,
                UserTag.tag_key == new_tag.tag_key
            ).first()
            
            if existing:
                existing.tag_value = new_tag.tag_value
                existing.occurrence_count = (existing.occurrence_count or 0) + 1
                existing.last_seen_at = now
                existing.updated_at = now
            else:
                db.add(new_tag)
        
        db.commit()
    
    def claim_reward(
        self,
        db: Session,
        user_id: int,
        prediction_id: int
    ) -> Dict[str, Any]:
        """
        领取奖励（兼容旧版接口）
        
        新系统中奖励已自动发放，此接口主要用于兼容
        """
        vote = db.query(PredictionVote).filter(
            PredictionVote.user_id == user_id,
            PredictionVote.prediction_id == prediction_id
        ).first()
        
        if not vote:
            return {
                "success": False,
                "error_code": "VOTE_NOT_FOUND",
                "error": "未找到投票记录"
            }
        
        if not vote.is_correct:
            return {
                "success": False,
                "error_code": "NOT_CORRECT",
                "error": "您没有猜对，无法领取奖励"
            }
        
        if vote.reward_claimed:
            return {
                "success": False,
                "error_code": "ALREADY_CLAIMED",
                "error": "奖励已领取"
            }
        
        prediction = db.query(CollectivePrediction).filter(
            CollectivePrediction.id == prediction_id
        ).first()
        
        if not prediction.is_resolved:
            return {
                "success": False,
                "error_code": "NOT_RESOLVED",
                "error": "预测尚未结算"
            }
        
        vote.reward_claimed = True
        vote.reward_claimed_at = datetime.utcnow()
        db.commit()
        
        return {
            "success": True,
            "message": "奖励已确认领取",
            "reward_amount": vote.reward_earned,
            "reward_asset_type": vote.reward_asset_type
        }
    
    def get_user_prediction_history(
        self,
        db: Session,
        user_id: int,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        获取用户预测历史
        """
        votes = db.query(PredictionVote).filter(
            PredictionVote.user_id == user_id
        ).order_by(
            PredictionVote.created_at.desc()
        ).limit(limit).all()
        
        result = []
        for vote in votes:
            prediction = db.query(CollectivePrediction).filter(
                CollectivePrediction.id == vote.prediction_id
            ).first()
            
            if prediction:
                result.append({
                    "prediction": self._prediction_to_dict(prediction),
                    "vote": self._vote_to_dict(vote)
                })
        
        return result
    
    def get_user_tags(
        self,
        db: Session,
        user_id: int,
        categories: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        获取用户标签
        """
        query = db.query(UserTag).filter(
            UserTag.user_id == user_id,
            UserTag.is_active == True
        )
        
        if categories:
            query = query.filter(UserTag.tag_category.in_(categories))
        
        tags = query.order_by(
            UserTag.tag_score.desc()
        ).all()
        
        return [self._tag_to_dict(t) for t in tags]
    
    def _theme_to_dict(self, theme: PredictionTheme) -> Dict[str, Any]:
        return {
            "id": theme.id,
            "theme_key": theme.theme_key,
            "theme_name": theme.theme_name,
            "description": theme.description,
            "theme_category": theme.theme_category,
            "default_options": json.loads(theme.default_options) if theme.default_options else [],
            "default_session_type": theme.default_session_type,
            "default_max_votes": theme.default_max_votes,
            "default_base_cost": theme.default_base_cost,
            "default_reward_type": theme.default_reward_type,
            "default_reward_amount": theme.default_reward_amount,
            "oracle_source": theme.oracle_source,
            "resolution_rule": theme.resolution_rule,
            "is_active": theme.is_active,
            "is_permanent": theme.is_permanent,
            "sort_order": theme.sort_order,
            "start_date": theme.start_date.isoformat() if theme.start_date else None,
            "end_date": theme.end_date.isoformat() if theme.end_date else None
        }
    
    def _prediction_to_dict(self, prediction: CollectivePrediction) -> Dict[str, Any]:
        now = datetime.utcnow()
        status = prediction.status
        
        if status == "scheduled" and prediction.voting_starts_at:
            if prediction.voting_starts_at <= now and (not prediction.voting_ends_at or prediction.voting_ends_at > now):
                status = "open"
        
        options = json.loads(prediction.options) if prediction.options else {}
        vote_distribution = json.loads(prediction.vote_distribution) if prediction.vote_distribution else {}
        
        return {
            "id": prediction.id,
            "prediction_date": prediction.prediction_date,
            "target_date": prediction.target_date,
            
            "title": prediction.title,
            "description": prediction.description,
            "prediction_type": prediction.prediction_type,
            "session_type": prediction.session_type,
            "session_key": prediction.session_key,
            "theme_id": prediction.theme_id,
            
            "options": options.get("labels", []),
            "option_values": options.get("values", []),
            "option_icons": options.get("icons", []),
            
            "total_votes": prediction.total_votes or 0,
            "vote_distribution": vote_distribution,
            
            "status": status,
            "is_resolved": prediction.is_resolved or False,
            "resolved_at": prediction.resolved_at.isoformat() if prediction.resolved_at else None,
            
            "correct_option": prediction.correct_option,
            "accuracy_score": prediction.accuracy_score,
            
            "total_stardust_pool": prediction.total_stardust_pool or 0,
            
            "announced_at": prediction.announced_at.isoformat() if prediction.announced_at else None,
            "voting_starts_at": prediction.voting_starts_at.isoformat() if prediction.voting_starts_at else None,
            "voting_ends_at": prediction.voting_ends_at.isoformat() if prediction.voting_ends_at else None,
            
            "max_votes_per_user": prediction.max_votes_per_user or 1,
            "base_vote_cost": prediction.base_vote_cost or 0,
            "extra_vote_cost": prediction.extra_vote_cost or 0,
            
            "is_vip_enabled": prediction.is_vip_enabled,
            "vip_multiplier": prediction.vip_multiplier,
            
            "reward_asset_type": prediction.reward_asset_type,
            "base_reward_amount": prediction.base_reward_amount,
            "bonus_reward_amount": prediction.bonus_reward_amount,
            
            "oracle_data_source": prediction.oracle_data_source,
            "resolution_evidence": prediction.resolution_evidence,
            "is_manual_resolution": prediction.is_manual_resolution,
            
            "created_at": prediction.created_at.isoformat() if prediction.created_at else None,
            "updated_at": prediction.updated_at.isoformat() if prediction.updated_at else None
        }
    
    def _vote_to_dict(self, vote: PredictionVote) -> Dict[str, Any]:
        return {
            "id": vote.id,
            "prediction_id": vote.prediction_id,
            "user_id": vote.user_id,
            
            "vote_number": vote.vote_number,
            
            "selected_option": vote.selected_option,
            "confidence": vote.confidence,
            
            "vote_asset_type": vote.vote_asset_type,
            "vote_cost": vote.vote_cost,
            "stardust_bet": vote.stardust_bet or 0,
            
            "is_vip_bonus": vote.is_vip_bonus,
            "applied_multiplier": vote.applied_multiplier,
            
            "is_correct": vote.is_correct,
            "reward_earned": vote.reward_earned or 0,
            "reward_asset_type": vote.reward_asset_type,
            "reward_claimed": vote.reward_claimed,
            "reward_claimed_at": vote.reward_claimed_at.isoformat() if vote.reward_claimed_at else None,
            
            "is_validated": vote.is_validated,
            "validated_at": vote.validated_at.isoformat() if vote.validated_at else None,
            "validation_notes": vote.validation_notes,
            
            "created_at": vote.created_at.isoformat() if vote.created_at else None
        }
    
    def _tag_to_dict(self, tag: UserTag) -> Dict[str, Any]:
        return {
            "id": tag.id,
            "user_id": tag.user_id,
            
            "tag_category": tag.tag_category,
            "tag_key": tag.tag_key,
            "tag_value": tag.tag_value,
            
            "tag_score": tag.tag_score,
            "confidence": tag.confidence,
            
            "source_type": tag.source_type,
            "source_reference": tag.source_reference,
            
            "is_manual": tag.is_manual,
            "is_active": tag.is_active,
            
            "first_seen_at": tag.first_seen_at.isoformat() if tag.first_seen_at else None,
            "last_seen_at": tag.last_seen_at.isoformat() if tag.last_seen_at else None,
            "occurrence_count": tag.occurrence_count,
            
            "created_at": tag.created_at.isoformat() if tag.created_at else None,
            "updated_at": tag.updated_at.isoformat() if tag.updated_at else None
        }


advanced_prediction_service = AdvancedPredictionService()


def get_advanced_prediction_service() -> AdvancedPredictionService:
    return advanced_prediction_service
