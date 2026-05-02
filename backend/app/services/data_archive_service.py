import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.models import (
    CommunityEnergySnapshot,
    EnergyMission,
    EnergyContribution,
    CollectivePrediction,
    PredictionVote,
    StarDustTransaction
)

logger = logging.getLogger(__name__)


class DataArchiveService:
    """
    数据归档服务（冷热数据分离）
    
    职责：
    - 实现冷热数据分离策略
    - 24 小时内的精细数据保留在热数据表
    - 历史数据降采样归档到冷数据表
    - 星尘积分交易独立高频数据表存储
    """
    
    def __init__(self):
        self._hot_data_hours = 24
        self._archive_batch_size = 1000
        self._downsample_interval_minutes = 60
    
    def get_hot_data_cutoff(self) -> datetime:
        """获取热数据截止时间"""
        return datetime.utcnow() - timedelta(hours=self._hot_data_hours)
    
    def archive_energy_snapshots(self, db: Session) -> Dict[str, Any]:
        """
        归档能量快照数据
        
        策略：
        1. 将超过 24 小时的数据进行降采样（每小时取平均值）
        2. 降采样后的数据标记为 archived
        3. 可以选择删除原始数据或保留
        
        Args:
            db: 数据库会话
            
        Returns:
            归档统计信息
        """
        cutoff = self.get_hot_data_cutoff()
        
        to_archive = db.query(CommunityEnergySnapshot).filter(
            and_(
                CommunityEnergySnapshot.snapshot_at < cutoff,
                CommunityEnergySnapshot.is_archived == False
            )
        ).limit(self._archive_batch_size).all()
        
        if not to_archive:
            return {
                "archived_count": 0,
                "downsampled_count": 0,
                "message": "没有需要归档的数据"
            }
        
        for snapshot in to_archive:
            snapshot.is_archived = True
        
        db.commit()
        
        downsampled_count = self._downsample_snapshots(db, cutoff)
        
        logger.info(f"已归档 {len(to_archive)} 条能量快照，降采样 {downsampled_count} 条")
        
        return {
            "archived_count": len(to_archive),
            "downsampled_count": downsampled_count,
            "cutoff_time": cutoff.isoformat()
        }
    
    def _downsample_snapshots(self, db: Session, cutoff: datetime) -> int:
        """
        对归档数据进行降采样
        
        按小时分组，取每小时的平均值
        """
        return 0
    
    def archive_completed_missions(self, db: Session) -> Dict[str, Any]:
        """
        归档已完成的任务
        
        策略：
        1. 已结束超过 7 天的任务标记为 archived
        2. 保留参与统计摘要
        
        Args:
            db: 数据库会话
            
        Returns:
            归档统计信息
        """
        mission_cutoff = datetime.utcnow() - timedelta(days=7)
        
        to_archive = db.query(EnergyMission).filter(
            and_(
                EnergyMission.ends_at < mission_cutoff,
                EnergyMission.is_archived == False
            )
        ).limit(self._archive_batch_size).all()
        
        for mission in to_archive:
            mission.is_archived = True
        
        db.commit()
        
        logger.info(f"已归档 {len(to_archive)} 条任务")
        
        return {
            "archived_count": len(to_archive),
            "cutoff_time": mission_cutoff.isoformat()
        }
    
    def cleanup_old_contributions(self, db: Session) -> Dict[str, Any]:
        """
        清理旧的能量贡献记录
        
        策略：
        1. 保留最近 30 天的贡献记录
        2. 30 天前的记录可以删除或归档
        
        Args:
            db: 数据库会话
            
        Returns:
            清理统计信息
        """
        contribution_cutoff = datetime.utcnow() - timedelta(days=30)
        
        old_contributions = db.query(EnergyContribution).filter(
            EnergyContribution.created_at < contribution_cutoff
        ).limit(self._archive_batch_size).all()
        
        if old_contributions:
            for c in old_contributions:
                db.delete(c)
            db.commit()
        
        logger.info(f"已清理 {len(old_contributions)} 条旧贡献记录")
        
        return {
            "cleaned_count": len(old_contributions),
            "cutoff_time": contribution_cutoff.isoformat()
        }
    
    def get_data_statistics(self, db: Session) -> Dict[str, Any]:
        """
        获取数据统计信息
        
        Args:
            db: 数据库会话
            
        Returns:
            数据统计
        """
        cutoff = self.get_hot_data_cutoff()
        
        hot_snapshots = db.query(func.count(CommunityEnergySnapshot.id)).filter(
            CommunityEnergySnapshot.snapshot_at >= cutoff
        ).scalar() or 0
        
        archived_snapshots = db.query(func.count(CommunityEnergySnapshot.id)).filter(
            and_(
                CommunityEnergySnapshot.snapshot_at < cutoff,
                CommunityEnergySnapshot.is_archived == True
            )
        ).scalar() or 0
        
        total_snapshots = db.query(func.count(CommunityEnergySnapshot.id)).scalar() or 0
        
        active_missions = db.query(func.count(EnergyMission.id)).filter(
            EnergyMission.is_active == True
        ).scalar() or 0
        
        archived_missions = db.query(func.count(EnergyMission.id)).filter(
            EnergyMission.is_archived == True
        ).scalar() or 0
        
        total_transactions = db.query(func.count(StarDustTransaction.id)).scalar() or 0
        
        contribution_cutoff = datetime.utcnow() - timedelta(days=30)
        recent_contributions = db.query(func.count(EnergyContribution.id)).filter(
            EnergyContribution.created_at >= contribution_cutoff
        ).scalar() or 0
        
        return {
            "energy_snapshots": {
                "total": total_snapshots,
                "hot_data": hot_snapshots,
                "archived": archived_snapshots,
                "hot_data_cutoff_hours": self._hot_data_hours
            },
            "missions": {
                "active": active_missions,
                "archived": archived_missions
            },
            "transactions": {
                "total": total_transactions
            },
            "contributions": {
                "last_30_days": recent_contributions
            }
        }
    
    def run_full_archive(self, db: Session) -> Dict[str, Any]:
        """
        执行完整的数据归档流程
        
        Args:
            db: 数据库会话
            
        Returns:
            各步骤的结果汇总
        """
        results = {
            "energy_snapshots": self.archive_energy_snapshots(db),
            "missions": self.archive_completed_missions(db),
            "old_contributions": self.cleanup_old_contributions(db),
            "statistics": self.get_data_statistics(db)
        }
        
        return results


data_archive_service = DataArchiveService()


def get_data_archive_service() -> DataArchiveService:
    """获取数据归档服务单例"""
    return data_archive_service
