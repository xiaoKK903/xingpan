import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.models import EnergyContribution, StarDustTransaction, User, CommunityEnergySnapshot

logger = logging.getLogger(__name__)

DIMENSION_BASE_POWER = {
    "career": 1.5,
    "wealth": 1.3,
    "love": 1.2,
    "health": 1.0,
    "social": 1.4,
    "study": 1.1,
    "spirituality": 1.0,
    "creativity": 1.3,
}

DIMENSION_MAX_BOOST = {
    "career": 30,
    "wealth": 25,
    "love": 20,
    "health": 15,
    "social": 25,
    "study": 20,
    "spirituality": 15,
    "creativity": 25,
}


class EnergyBalancingService:
    """
    能量平衡服务
    
    职责：
    - 实现边际效用递减算法，平衡大小用户参与感
    - 计算能量注入的实际效果
    - 防止单一用户过度影响社区能量
    """
    
    def __init__(self):
        self._diminishing_factor = 0.8
        self._daily_contribution_limit = 100
    
    def calculate_marginal_utility(
        self,
        user_id: int,
        dimension: str,
        base_power: int,
        total_contributions_today: int,
        community_total_contributions: int
    ) -> Dict[str, Any]:
        """
        计算边际效用递减后的实际能量值
        
        算法原理：
        1. 个人边际递减：同一用户同一天内多次注入，效果递减
        2. 社区边际递减：同一维度总能量越高，新增能量的效果递减
        3. 基础权重：不同维度有不同的基础影响力
        
        Args:
            user_id: 用户ID
            dimension: 维度名称
            base_power: 基础能量值
            total_contributions_today: 用户当天该维度已贡献次数
            community_total_contributions: 社区当天该维度总贡献次数
            
        Returns:
            包含实际能量值和相关计算参数的字典
        """
        user_factor = self._diminishing_factor ** total_contributions_today
        user_actual = base_power * user_factor
        
        saturation_factor = 1.0
        if community_total_contributions > 0:
            saturation = min(community_total_contributions / 100, 1.0)
            saturation_factor = 1.0 - (saturation * 0.5)
        
        base_dimension_power = DIMENSION_BASE_POWER.get(dimension, 1.0)
        dimension_factor = base_dimension_power / max(DIMENSION_BASE_POWER.values())
        
        actual_power = user_actual * saturation_factor * dimension_factor
        
        max_boost = DIMENSION_MAX_BOOST.get(dimension, 20)
        actual_power = min(actual_power, max_boost)
        
        user_diminish_rate = (1 - user_factor) * 100
        saturation_rate = (1 - saturation_factor) * 100
        
        return {
            "base_power": base_power,
            "user_actual_before_saturation": round(user_actual, 2),
            "actual_power": round(actual_power, 2),
            "user_diminish_rate": round(user_diminish_rate, 1),
            "saturation_rate": round(saturation_rate, 1),
            "user_factor": round(user_factor, 3),
            "saturation_factor": round(saturation_factor, 3),
            "dimension_factor": round(dimension_factor, 3),
            "max_boost": max_boost
        }
    
    def get_user_daily_contribution_count(
        self,
        db: Session,
        user_id: int,
        dimension: str
    ) -> int:
        """获取用户当天在某维度的贡献次数"""
        today = datetime.utcnow().date()
        start_time = datetime.combine(today, datetime.min.time())
        end_time = datetime.combine(today, datetime.max.time())
        
        count = db.query(func.count(EnergyContribution.id)).filter(
            and_(
                EnergyContribution.user_id == user_id,
                EnergyContribution.dimension == dimension,
                EnergyContribution.created_at >= start_time,
                EnergyContribution.created_at <= end_time
            )
        ).scalar()
        
        return count or 0
    
    def get_community_daily_contribution_count(
        self,
        db: Session,
        dimension: str,
        scope: str = "global",
        city: Optional[str] = None
    ) -> int:
        """获取社区当天在某维度的总贡献次数"""
        today = datetime.utcnow().date()
        start_time = datetime.combine(today, datetime.min.time())
        end_time = datetime.combine(today, datetime.max.time())
        
        query = db.query(func.count(EnergyContribution.id)).filter(
            and_(
                EnergyContribution.dimension == dimension,
                EnergyContribution.created_at >= start_time,
                EnergyContribution.created_at <= end_time,
                EnergyContribution.scope == scope
            )
        )
        
        if scope == "local" and city:
            query = query.filter(EnergyContribution.scope_city == city)
        
        return query.scalar() or 0
    
    def calculate_contribution_effect(
        self,
        db: Session,
        user_id: int,
        dimension: str,
        base_power: int,
        scope: str = "global",
        city: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        计算用户能量注入的实际效果
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            dimension: 维度名称
            base_power: 基础能量值
            scope: 范围
            city: 城市
            
        Returns:
            计算结果
        """
        user_count = self.get_user_daily_contribution_count(db, user_id, dimension)
        community_count = self.get_community_daily_contribution_count(db, dimension, scope, city)
        
        if user_count >= self._daily_contribution_limit:
            return {
                "success": False,
                "error": "今日贡献次数已达上限",
                "user_count": user_count,
                "limit": self._daily_contribution_limit
            }
        
        calculation = self.calculate_marginal_utility(
            user_id=user_id,
            dimension=dimension,
            base_power=base_power,
            total_contributions_today=user_count,
            community_total_contributions=community_count
        )
        
        user_dust_bonus = int(calculation["actual_power"] * 10)
        
        return {
            "success": True,
            "user_count": user_count,
            "community_count": community_count,
            "calculation": calculation,
            "actual_power": calculation["actual_power"],
            "dust_bonus": user_dust_bonus
        }
    
    def apply_diminishing_returns(
        self,
        base_value: float,
        count: int,
        factor: float = None
    ) -> float:
        """
        应用边际效用递减公式
        
        Args:
            base_value: 基础值
            count: 已执行次数
            factor: 递减因子（默认0.8）
            
        Returns:
            递减后的值
        """
        if factor is None:
            factor = self._diminishing_factor
        
        return base_value * (factor ** count)
    
    def get_contribution_summary(
        self,
        db: Session,
        user_id: int,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        获取用户贡献统计摘要
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            days: 统计天数
            
        Returns:
            统计摘要
        """
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        contributions = db.query(EnergyContribution).filter(
            and_(
                EnergyContribution.user_id == user_id,
                EnergyContribution.created_at >= cutoff_time
            )
        ).all()
        
        total_power = sum(c.actual_power or 0 for c in contributions)
        total_dust = sum(c.dust_earned or 0 for c in contributions)
        
        by_dimension = {}
        for c in contributions:
            dim = c.dimension
            if dim not in by_dimension:
                by_dimension[dim] = {
                    "count": 0,
                    "total_power": 0,
                    "total_dust": 0
                }
            by_dimension[dim]["count"] += 1
            by_dimension[dim]["total_power"] += c.actual_power or 0
            by_dimension[dim]["total_dust"] += c.dust_earned or 0
        
        today = datetime.utcnow().date()
        start_time = datetime.combine(today, datetime.min.time())
        
        today_contributions = db.query(EnergyContribution).filter(
            and_(
                EnergyContribution.user_id == user_id,
                EnergyContribution.created_at >= start_time
            )
        ).all()
        
        today_by_dimension = {}
        for c in today_contributions:
            dim = c.dimension
            if dim not in today_by_dimension:
                today_by_dimension[dim] = 0
            today_by_dimension[dim] += 1
        
        return {
            "period_days": days,
            "total_contributions": len(contributions),
            "total_power": round(total_power, 2),
            "total_dust_earned": total_dust,
            "by_dimension": by_dimension,
            "today_contributions": len(today_contributions),
            "today_by_dimension": today_by_dimension,
            "daily_limit": self._daily_contribution_limit
        }


energy_balancing_service = EnergyBalancingService()


def get_energy_balancing_service() -> EnergyBalancingService:
    """获取能量平衡服务单例"""
    return energy_balancing_service
