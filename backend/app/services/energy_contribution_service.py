import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.models import (
    EnergyContribution,
    StarDustTransaction,
    User
)
from app.services.energy_weather_service import ENERGY_CONTRIBUTION_TYPES

logger = logging.getLogger(__name__)

CONTRIBUTION_TYPES = ENERGY_CONTRIBUTION_TYPES


class EnergyContributionService:
    """
    能量贡献服务
    
    职责：
    - 管理用户能量注入
    - 计算能量乘数（基于用户星盘）
    - 管理能量有效期
    - 计算社区能量加成
    """
    
    def get_available_contributions(
        self,
        db: Session,
        user_id: int
    ) -> List[Dict[str, Any]]:
        """
        获取用户可用的能量贡献类型
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            可用贡献类型列表
        """
        result = []
        
        for contrib_type, config in CONTRIBUTION_TYPES.items():
            result.append({
                "type": contrib_type,
                "name": config.get("name", "未知"),
                "planet": config.get("planet", ""),
                "planet_icon": config.get("icon", "✨"),
                "color": config.get("color", "#9370db"),
                "description": config.get("description", ""),
                "base_energy": config.get("base_energy", 10.0),
                "cost_stardust": config.get("cost_stardust", 5),
                "duration_minutes": config.get("duration_minutes", 30),
                "target_dimensions": config.get("target_dimensions", [])
            })
        
        return result
    
    def get_user_contributions(
        self,
        db: Session,
        user_id: int,
        only_active: bool = False,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        获取用户的能量贡献记录
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            only_active: 只获取活跃的贡献
            limit: 限制数量
            
        Returns:
            贡献记录列表
        """
        query = db.query(EnergyContribution).filter(
            EnergyContribution.user_id == user_id
        )
        
        if only_active:
            now = datetime.utcnow()
            query = query.filter(
                and_(
                    EnergyContribution.is_active == True,
                    EnergyContribution.expires_at > now
                )
            )
        
        query = query.order_by(EnergyContribution.created_at.desc()).limit(limit)
        contributions = query.all()
        
        return [self._contribution_to_dict(c) for c in contributions]
    
    def get_active_contributions(
        self,
        db: Session,
        scope: str = "global",
        city: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取当前活跃的社区能量贡献
        
        Args:
            db: 数据库会话
            scope: 范围
            city: 城市
            
        Returns:
            活跃贡献列表
        """
        now = datetime.utcnow()
        
        query = db.query(EnergyContribution).filter(
            and_(
                EnergyContribution.is_active == True,
                EnergyContribution.expires_at > now
            )
        )
        
        if scope == "local" and city:
            pass
        
        contributions = query.order_by(
            EnergyContribution.created_at.desc()
        ).all()
        
        return [self._contribution_to_dict(c) for c in contributions]
    
    def contribute_energy(
        self,
        db: Session,
        user_id: int,
        contribution_type: str,
        scope: str = "global",
        city: Optional[str] = None,
        multiplier: float = 1.0
    ) -> Dict[str, Any]:
        """
        用户注入能量
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            contribution_type: 贡献类型
            scope: 范围
            city: 城市
            multiplier: 能量乘数
            
        Returns:
            贡献结果
        """
        if contribution_type not in CONTRIBUTION_TYPES:
            return {"error": "无效的贡献类型", "code": "INVALID_CONTRIBUTION_TYPE"}
        
        config = CONTRIBUTION_TYPES[contribution_type]
        
        cost_stardust = config.get("cost_stardust", 5)
        base_energy = config.get("base_energy", 10.0)
        duration_minutes = config.get("duration_minutes", 30)
        target_dimensions = config.get("target_dimensions", [])
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "用户不存在", "code": "USER_NOT_FOUND"}
        
        now = datetime.utcnow()
        expires_at = now + timedelta(minutes=duration_minutes)
        
        actual_energy = base_energy * multiplier
        
        contribution = EnergyContribution(
            user_id=user_id,
            contribution_type=contribution_type,
            planet_type=contribution_type,
            planet_name=config.get("planet", ""),
            energy_amount=actual_energy,
            energy_multiplier=multiplier,
            target_scope=scope,
            target_dimension=target_dimensions[0] if target_dimensions else None,
            duration_minutes=duration_minutes,
            expires_at=expires_at,
            is_active=True,
            cost_stardust=cost_stardust,
            created_at=now,
            updated_at=now
        )
        
        db.add(contribution)
        
        if cost_stardust > 0:
            transaction = StarDustTransaction(
                user_id=user_id,
                transaction_type="contribution_cost",
                amount=-cost_stardust,
                balance_before=0,
                balance_after=-cost_stardust,
                related_type="contribution",
                related_id=contribution.id,
                description=f"注入{config.get('name', '能量')}消耗星尘",
                created_at=now
            )
            db.add(transaction)
        
        db.commit()
        db.refresh(contribution)
        
        return {
            "success": True,
            "contribution": self._contribution_to_dict(contribution),
            "message": f"成功注入{config.get('name', '能量')}！社区能量获得加成。"
        }
    
    def deactivate_contribution(
        self,
        db: Session,
        user_id: int,
        contribution_id: int
    ) -> Dict[str, Any]:
        """
        取消能量贡献
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            contribution_id: 贡献ID
            
        Returns:
            操作结果
        """
        contribution = db.query(EnergyContribution).filter(
            EnergyContribution.id == contribution_id,
            EnergyContribution.user_id == user_id
        ).first()
        
        if not contribution:
            return {"error": "未找到贡献记录", "code": "CONTRIBUTION_NOT_FOUND"}
        
        if not contribution.is_active:
            return {"error": "贡献已失效", "code": "ALREADY_INACTIVE"}
        
        now = datetime.utcnow()
        contribution.is_active = False
        contribution.updated_at = now
        
        db.commit()
        db.refresh(contribution)
        
        return {
            "success": True,
            "contribution": self._contribution_to_dict(contribution),
            "message": "能量贡献已取消"
        }
    
    def calculate_community_energy_bonus(
        self,
        db: Session,
        scope: str = "global",
        city: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        计算社区能量加成
        
        Args:
            db: 数据库会话
            scope: 范围
            city: 城市
            
        Returns:
            能量加成数据
        """
        active_contributions = self.get_active_contributions(db, scope, city)
        
        total_energy = 0.0
        contribution_by_type = {}
        contribution_by_dimension = {}
        
        for contrib in active_contributions:
            energy = contrib.get("energy_amount", 0.0)
            total_energy += energy
            
            contrib_type = contrib.get("type", "")
            if contrib_type not in contribution_by_type:
                contribution_by_type[contrib_type] = 0.0
            contribution_by_type[contrib_type] += energy
            
            target_dim = contrib.get("target_dimension")
            if target_dim:
                if target_dim not in contribution_by_dimension:
                    contribution_by_dimension[target_dim] = 0.0
                contribution_by_dimension[target_dim] += energy
        
        bonus_multiplier = 1.0 + (total_energy / 100.0)
        bonus_multiplier = min(bonus_multiplier, 3.0)
        
        top_contributions = sorted(
            active_contributions,
            key=lambda x: x.get("energy_amount", 0),
            reverse=True
        )[:5]
        
        return {
            "scope": scope,
            "city": city,
            
            "total_energy_contributed": round(total_energy, 2),
            "active_contribution_count": len(active_contributions),
            
            "bonus_multiplier": round(bonus_multiplier, 2),
            "bonus_percentage": round((bonus_multiplier - 1.0) * 100, 1),
            
            "contribution_by_type": contribution_by_type,
            "contribution_by_dimension": contribution_by_dimension,
            
            "top_contributions": top_contributions,
            
            "calculated_at": datetime.utcnow().isoformat()
        }
    
    def _contribution_to_dict(self, contribution: EnergyContribution) -> Dict[str, Any]:
        """将贡献记录转换为字典"""
        config = CONTRIBUTION_TYPES.get(contribution.contribution_type, {})
        
        now = datetime.utcnow()
        is_active = contribution.is_active and (contribution.expires_at > now if contribution.expires_at else False)
        
        remaining_minutes = 0
        if contribution.expires_at and is_active:
            remaining = contribution.expires_at - now
            remaining_minutes = int(remaining.total_seconds() / 60)
        
        return {
            "id": contribution.id,
            "user_id": contribution.user_id,
            
            "type": contribution.contribution_type,
            "name": config.get("name", "未知贡献"),
            "planet": contribution.planet_name,
            "planet_icon": config.get("icon", "✨"),
            "color": config.get("color", "#9370db"),
            "description": config.get("description", ""),
            
            "energy_amount": round(contribution.energy_amount or 0.0, 2),
            "energy_multiplier": contribution.energy_multiplier or 1.0,
            
            "target_scope": contribution.target_scope,
            "target_dimension": contribution.target_dimension,
            
            "duration_minutes": contribution.duration_minutes or 30,
            "remaining_minutes": max(0, remaining_minutes),
            
            "is_active": is_active,
            "cost_stardust": contribution.cost_stardust or 0,
            
            "created_at": contribution.created_at.isoformat() if contribution.created_at else None,
            "expires_at": contribution.expires_at.isoformat() if contribution.expires_at else None,
            "updated_at": contribution.updated_at.isoformat() if contribution.updated_at else None,
            
            "contribution_data": json.loads(contribution.contribution_data) if contribution.contribution_data else None
        }


energy_contribution_service = EnergyContributionService()


def get_energy_contribution_service() -> EnergyContributionService:
    """获取能量贡献服务单例"""
    return energy_contribution_service
