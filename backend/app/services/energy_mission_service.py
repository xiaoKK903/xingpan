import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.models import (
    EnergyMission,
    MissionParticipation,
    StarDustTransaction,
    User
)

logger = logging.getLogger(__name__)

MISSION_STATUSES = {
    "pending": "待开始",
    "active": "进行中",
    "completed": "已完成",
    "expired": "已过期",
    "cancelled": "已取消"
}

PARTICIPATION_STATUSES = {
    "joined": "已加入",
    "in_progress": "进行中",
    "completed": "已完成",
    "claimed": "已领取奖励"
}

DIFFICULTY_CONFIG = {
    "easy": {
        "label": "简单",
        "reward_multiplier": 1.0,
        "energy_requirement": 0.0,
        "description": "适合新手，低门槛参与"
    },
    "medium": {
        "label": "中等",
        "reward_multiplier": 1.5,
        "energy_requirement": 5.0,
        "description": "需要一定投入，奖励适中"
    },
    "hard": {
        "label": "困难",
        "reward_multiplier": 2.5,
        "energy_requirement": 15.0,
        "description": "高投入高回报，适合深度参与"
    }
}


class EnergyMissionService:
    """
    能量任务服务
    
    职责：
    - 任务创建与管理
    - 用户参与管理
    - 任务进度跟踪
    - 奖励发放
    """
    
    def get_active_missions(
        self,
        db: Session,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取进行中的任务
        
        Args:
            db: 数据库会话
            limit: 限制数量
            
        Returns:
            任务列表
        """
        now = datetime.utcnow()
        
        missions = db.query(EnergyMission).filter(
            and_(
                EnergyMission.status == "active",
                EnergyMission.start_at <= now,
                EnergyMission.end_at >= now
            )
        ).order_by(
            EnergyMission.start_at.desc()
        ).limit(limit).all()
        
        return [self._mission_to_dict(m) for m in missions]
    
    def get_upcoming_missions(
        self,
        db: Session,
        hours: int = 24,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        获取即将开始的任务
        
        Args:
            db: 数据库会话
            hours: 未来小时数
            limit: 限制数量
            
        Returns:
            任务列表
        """
        now = datetime.utcnow()
        future_cutoff = now + timedelta(hours=hours)
        
        missions = db.query(EnergyMission).filter(
            and_(
                EnergyMission.status == "pending",
                EnergyMission.start_at > now,
                EnergyMission.start_at <= future_cutoff
            )
        ).order_by(
            EnergyMission.start_at.asc()
        ).limit(limit).all()
        
        return [self._mission_to_dict(m) for m in missions]
    
    def get_completed_missions(
        self,
        db: Session,
        user_id: int,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取用户已完成的任务
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            limit: 限制数量
            
        Returns:
            任务列表
        """
        participations = db.query(MissionParticipation).filter(
            MissionParticipation.user_id == user_id,
            MissionParticipation.status.in_(["completed", "claimed"])
        ).order_by(
            MissionParticipation.completed_at.desc()
        ).limit(limit).all()
        
        result = []
        for p in participations:
            mission = db.query(EnergyMission).filter(
                EnergyMission.id == p.mission_id
            ).first()
            
            if mission:
                mission_dict = self._mission_to_dict(mission)
                mission_dict["participation"] = {
                    "id": p.id,
                    "status": p.status,
                    "energy_contributed": p.energy_contributed,
                    "reward_earned": p.reward_earned,
                    "reward_claimed": p.reward_claimed,
                    "joined_at": p.joined_at.isoformat() if p.joined_at else None,
                    "completed_at": p.completed_at.isoformat() if p.completed_at else None
                }
                result.append(mission_dict)
        
        return result
    
    def join_mission(
        self,
        db: Session,
        user_id: int,
        mission_id: int
    ) -> Dict[str, Any]:
        """
        用户加入任务
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            mission_id: 任务ID
            
        Returns:
            参与信息
        """
        mission = db.query(EnergyMission).filter(
            EnergyMission.id == mission_id
        ).first()
        
        if not mission:
            return {"error": "任务不存在", "code": "MISSION_NOT_FOUND"}
        
        if mission.status != "active":
            return {"error": "任务不在进行中", "code": "MISSION_NOT_ACTIVE"}
        
        now = datetime.utcnow()
        if mission.end_at and mission.end_at < now:
            return {"error": "任务已过期", "code": "MISSION_EXPIRED"}
        
        existing = db.query(MissionParticipation).filter(
            MissionParticipation.user_id == user_id,
            MissionParticipation.mission_id == mission_id
        ).first()
        
        if existing:
            return {
                "error": "您已加入该任务",
                "code": "ALREADY_JOINED",
                "participation": self._participation_to_dict(existing, mission)
            }
        
        participation = MissionParticipation(
            mission_id=mission_id,
            user_id=user_id,
            status="joined",
            energy_contributed=0.0,
            reward_earned=0,
            reward_claimed=False,
            joined_at=now,
            created_at=now
        )
        
        db.add(participation)
        
        mission.participant_count = (mission.participant_count or 0) + 1
        mission.updated_at = now
        
        db.commit()
        db.refresh(participation)
        db.refresh(mission)
        
        return {
            "success": True,
            "participation": self._participation_to_dict(participation, mission),
            "mission": self._mission_to_dict(mission)
        }
    
    def update_participation_progress(
        self,
        db: Session,
        user_id: int,
        mission_id: int,
        energy_contributed: float,
        contribution_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        更新任务参与进度
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            mission_id: 任务ID
            energy_contributed: 贡献的能量值
            contribution_type: 贡献类型
            
        Returns:
            更新后的参与信息
        """
        participation = db.query(MissionParticipation).filter(
            MissionParticipation.user_id == user_id,
            MissionParticipation.mission_id == mission_id
        ).first()
        
        if not participation:
            return {"error": "未找到参与记录", "code": "PARTICIPATION_NOT_FOUND"}
        
        mission = db.query(EnergyMission).filter(
            EnergyMission.id == mission_id
        ).first()
        
        if not mission:
            return {"error": "任务不存在", "code": "MISSION_NOT_FOUND"}
        
        now = datetime.utcnow()
        
        participation.energy_contributed = (participation.energy_contributed or 0) + energy_contributed
        if contribution_type:
            participation.contribution_type = contribution_type
        
        difficulty_config = DIFFICULTY_CONFIG.get(mission.difficulty, DIFFICULTY_CONFIG["medium"])
        energy_requirement = difficulty_config.get("energy_requirement", 0)
        
        if participation.energy_contributed >= energy_requirement:
            participation.status = "completed"
            participation.completed_at = now
            
            base_reward = mission.base_reward or 10
            reward_multiplier = difficulty_config.get("reward_multiplier", 1.0)
            participation.reward_earned = int(base_reward * reward_multiplier)
        
        mission.energy_contributed = (mission.energy_contributed or 0) + energy_contributed
        mission.updated_at = now
        
        db.commit()
        db.refresh(participation)
        db.refresh(mission)
        
        return {
            "success": True,
            "participation": self._participation_to_dict(participation, mission),
            "mission": self._mission_to_dict(mission)
        }
    
    def claim_reward(
        self,
        db: Session,
        user_id: int,
        mission_id: int
    ) -> Dict[str, Any]:
        """
        领取任务奖励
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            mission_id: 任务ID
            
        Returns:
            领奖结果
        """
        participation = db.query(MissionParticipation).filter(
            MissionParticipation.user_id == user_id,
            MissionParticipation.mission_id == mission_id
        ).first()
        
        if not participation:
            return {"error": "未找到参与记录", "code": "PARTICIPATION_NOT_FOUND"}
        
        if participation.status != "completed":
            return {"error": "任务未完成，无法领取奖励", "code": "MISSION_NOT_COMPLETED"}
        
        if participation.reward_claimed:
            return {"error": "奖励已领取", "code": "REWARD_ALREADY_CLAIMED"}
        
        mission = db.query(EnergyMission).filter(
            EnergyMission.id == mission_id
        ).first()
        
        if not mission:
            return {"error": "任务不存在", "code": "MISSION_NOT_FOUND"}
        
        reward_amount = participation.reward_earned or mission.base_reward or 10
        
        now = datetime.utcnow()
        
        participation.reward_claimed = True
        participation.status = "claimed"
        participation.updated_at = now
        
        transaction = StarDustTransaction(
            user_id=user_id,
            transaction_type="mission_reward",
            amount=reward_amount,
            balance_before=0,
            balance_after=reward_amount,
            related_type="mission",
            related_id=mission_id,
            description=f"完成任务「{mission.title}」获得奖励",
            created_at=now
        )
        
        db.add(transaction)
        db.commit()
        
        return {
            "success": True,
            "reward": reward_amount,
            "participation": self._participation_to_dict(participation, mission),
            "transaction": {
                "id": transaction.id,
                "type": transaction.transaction_type,
                "amount": transaction.amount,
                "description": transaction.description,
                "created_at": transaction.created_at.isoformat()
            }
        }
    
    def get_mission_detail(
        self,
        db: Session,
        mission_id: int,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取任务详情
        
        Args:
            db: 数据库会话
            mission_id: 任务ID
            user_id: 用户ID（可选，用于检查参与状态）
            
        Returns:
            任务详情
        """
        mission = db.query(EnergyMission).filter(
            EnergyMission.id == mission_id
        ).first()
        
        if not mission:
            return {"error": "任务不存在", "code": "MISSION_NOT_FOUND"}
        
        result = self._mission_to_dict(mission)
        
        if user_id:
            participation = db.query(MissionParticipation).filter(
                MissionParticipation.user_id == user_id,
                MissionParticipation.mission_id == mission_id
            ).first()
            
            if participation:
                result["user_participation"] = self._participation_to_dict(participation, mission)
            else:
                result["user_participation"] = None
        
        return result
    
    def _mission_to_dict(self, mission: EnergyMission) -> Dict[str, Any]:
        """将任务转换为字典"""
        difficulty_config = DIFFICULTY_CONFIG.get(mission.difficulty, DIFFICULTY_CONFIG["medium"])
        
        now = datetime.utcnow()
        status = mission.status
        
        if status == "active" and mission.end_at and mission.end_at < now:
            status = "expired"
        
        return {
            "id": mission.id,
            "type": mission.mission_type,
            "title": mission.title,
            "description": mission.description,
            
            "trigger_condition": mission.trigger_condition,
            "trigger_aspect": mission.trigger_aspect,
            "trigger_planet": mission.trigger_planet,
            "target_dimension": mission.target_dimension,
            
            "difficulty": mission.difficulty,
            "difficulty_label": difficulty_config.get("label", "中等"),
            "difficulty_description": difficulty_config.get("description", ""),
            
            "base_reward": mission.base_reward or 10,
            "reward_multiplier": difficulty_config.get("reward_multiplier", 1.0),
            "energy_requirement": difficulty_config.get("energy_requirement", 0),
            
            "max_participants": mission.max_participants or 100,
            "participant_count": mission.participant_count or 0,
            "energy_contributed": mission.energy_contributed or 0.0,
            
            "status": status,
            "status_label": MISSION_STATUSES.get(status, "未知"),
            
            "start_at": mission.start_at.isoformat() if mission.start_at else None,
            "end_at": mission.end_at.isoformat() if mission.end_at else None,
            "duration_minutes": mission.duration_minutes or 30,
            
            "mission_data": json.loads(mission.mission_data) if mission.mission_data else None,
            
            "created_at": mission.created_at.isoformat() if mission.created_at else None,
            "updated_at": mission.updated_at.isoformat() if mission.updated_at else None
        }
    
    def _participation_to_dict(
        self,
        participation: MissionParticipation,
        mission: Optional[EnergyMission] = None
    ) -> Dict[str, Any]:
        """将参与记录转换为字典"""
        return {
            "id": participation.id,
            "mission_id": participation.mission_id,
            "user_id": participation.user_id,
            
            "status": participation.status,
            "status_label": PARTICIPATION_STATUSES.get(participation.status, "未知"),
            
            "energy_contributed": participation.energy_contributed or 0.0,
            "contribution_type": participation.contribution_type,
            
            "reward_earned": participation.reward_earned or 0,
            "reward_claimed": participation.reward_claimed or False,
            
            "joined_at": participation.joined_at.isoformat() if participation.joined_at else None,
            "completed_at": participation.completed_at.isoformat() if participation.completed_at else None,
            
            "participation_data": json.loads(participation.participation_data) if participation.participation_data else None
        }


energy_mission_service = EnergyMissionService()


def get_energy_mission_service() -> EnergyMissionService:
    """获取能量任务服务单例"""
    return energy_mission_service
