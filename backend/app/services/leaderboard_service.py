import logging
import json
import math
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import and_, func, or_, desc, asc

from app.models import (
    User,
    LeaderboardConfig,
    LeaderboardReward,
    LeaderboardEntry,
    UserBadge,
    UserTitle,
    LeaderboardType,
    LeaderboardCycle,
    StarDustTransaction,
    PredictionVote,
    CollectivePrediction,
    NetworkConnection,
    EnergyContribution,
    PKMatch,
    UserPKStats,
    PKTransaction,
    PKBattleResult,
)

logger = logging.getLogger(__name__)


DEFAULT_LEADERBOARD_CONFIGS = [
    {
        "board_key": "weekly_energy",
        "board_type": LeaderboardType.WEEKLY_ENERGY.value,
        "name": "周能量榜",
        "display_name": "周能量榜",
        "description": "每周能量贡献排行榜",
        "cycle_type": LeaderboardCycle.WEEKLY.value,
        "rank_count": 100,
        "display_count": 20,
        "icon": "⚡",
        "sort_order": 1,
        "scoring_rules": {
            "energy_contribution_weight": 1.0,
            "mission_complete_weight": 2.0,
            "daily_checkin_weight": 1.0,
        },
    },
    {
        "board_key": "weekly_pk",
        "board_type": LeaderboardType.WEEKLY_PK.value,
        "name": "周PK战绩榜",
        "display_name": "周PK战绩榜",
        "description": "每周星盘能量PK战绩排行榜",
        "cycle_type": LeaderboardCycle.WEEKLY.value,
        "rank_count": 100,
        "display_count": 20,
        "icon": "⚔️",
        "sort_order": 4,
        "scoring_rules": {
            "win_weight": 100.0,
            "loss_weight": -20.0,
            "fragment_earned_weight": 0.5,
            "win_streak_bonus": 20.0,
        },
    },
    {
        "board_key": "prediction_hit",
        "board_type": LeaderboardType.PREDICTION_HIT.value,
        "name": "预言家命中榜",
        "display_name": "预言家命中榜",
        "description": "预言家礼堂竞猜命中排行榜",
        "cycle_type": LeaderboardCycle.WEEKLY.value,
        "rank_count": 100,
        "display_count": 20,
        "icon": "🔮",
        "sort_order": 2,
        "scoring_rules": {
            "correct_prediction_weight": 10.0,
            "streak_bonus_weight": 5.0,
            "high_confidence_bonus": 2.0,
        },
    },
    {
        "board_key": "friend_network",
        "board_type": LeaderboardType.FRIEND_NETWORK.value,
        "name": "人脉好友榜",
        "display_name": "人脉好友榜",
        "description": "人脉好友数量排行榜",
        "cycle_type": LeaderboardCycle.WEEKLY.value,
        "rank_count": 100,
        "display_count": 20,
        "icon": "👥",
        "sort_order": 3,
        "scoring_rules": {
            "mutual_connection_weight": 5.0,
            "one_way_connection_weight": 1.0,
            "active_chats_weight": 2.0,
        },
    },
]


DEFAULT_LEADERBOARD_REWARDS = {
    "weekly_energy": [
        {"rank_start": 1, "rank_end": 1, "reward_type": "badge", "reward_name": "能量王者", "badge_key": "energy_king", "badge_name": "能量王者", "badge_icon": "👑", "badge_rarity": "legendary", "valid_days": 30},
        {"rank_start": 2, "rank_end": 3, "reward_type": "badge", "reward_name": "能量大师", "badge_key": "energy_master", "badge_name": "能量大师", "badge_icon": "💎", "badge_rarity": "epic", "valid_days": 30},
        {"rank_start": 4, "rank_end": 10, "reward_type": "badge", "reward_name": "能量达人", "badge_key": "energy_expert", "badge_name": "能量达人", "badge_icon": "⭐", "badge_rarity": "rare", "valid_days": 30},
        {"rank_start": 11, "rank_end": 50, "reward_type": "fragment", "reward_amount": 50, "reward_name": "星元碎片 x50", "valid_days": None},
        {"rank_start": 51, "rank_end": 100, "reward_type": "fragment", "reward_amount": 20, "reward_name": "星元碎片 x20", "valid_days": None},
    ],
    "prediction_hit": [
        {"rank_start": 1, "rank_end": 1, "reward_type": "title", "reward_name": "预言大师", "title_key": "prophecy_master", "title_name": "预言大师", "title_color": "#FFD700", "valid_days": 30},
        {"rank_start": 2, "rank_end": 3, "reward_type": "title", "reward_name": "先知", "title_key": "prophet", "title_name": "先知", "title_color": "#C0C0C0", "valid_days": 30},
        {"rank_start": 4, "rank_end": 10, "reward_type": "badge", "reward_name": "预测达人", "badge_key": "prediction_expert", "badge_name": "预测达人", "badge_icon": "🎯", "badge_rarity": "rare", "valid_days": 30},
        {"rank_start": 11, "rank_end": 50, "reward_type": "ticket", "reward_amount": 3, "reward_name": "预言券 x3", "valid_days": None},
        {"rank_start": 51, "rank_end": 100, "reward_type": "ticket", "reward_amount": 1, "reward_name": "预言券 x1", "valid_days": None},
    ],
    "friend_network": [
        {"rank_start": 1, "rank_end": 1, "reward_type": "badge", "reward_name": "社交之王", "badge_key": "social_king", "badge_name": "社交之王", "badge_icon": "👑", "badge_rarity": "legendary", "valid_days": 30},
        {"rank_start": 2, "rank_end": 3, "reward_type": "badge", "reward_name": "社交达人", "badge_key": "social_master", "badge_name": "社交达人", "badge_icon": "💎", "badge_rarity": "epic", "valid_days": 30},
        {"rank_start": 4, "rank_end": 10, "reward_type": "badge", "reward_name": "人脉之星", "badge_key": "network_star", "badge_name": "人脉之星", "badge_icon": "⭐", "badge_rarity": "rare", "valid_days": 30},
        {"rank_start": 11, "rank_end": 50, "reward_type": "fragment", "reward_amount": 30, "reward_name": "星元碎片 x30", "valid_days": None},
        {"rank_start": 51, "rank_end": 100, "reward_type": "fragment", "reward_amount": 10, "reward_name": "星元碎片 x10", "valid_days": None},
    ],
    "weekly_pk": [
        {"rank_start": 1, "rank_end": 1, "reward_type": "badge", "reward_name": "PK战神", "badge_key": "pk_champion", "badge_name": "PK战神", "badge_icon": "🏆", "badge_rarity": "legendary", "valid_days": 30},
        {"rank_start": 2, "rank_end": 3, "reward_type": "badge", "reward_name": "PK大师", "badge_key": "pk_master", "badge_name": "PK大师", "badge_icon": "⚔️", "badge_rarity": "epic", "valid_days": 30},
        {"rank_start": 4, "rank_end": 10, "reward_type": "badge", "reward_name": "PK达人", "badge_key": "pk_expert", "badge_name": "PK达人", "badge_icon": "🎯", "badge_rarity": "rare", "valid_days": 30},
        {"rank_start": 11, "rank_end": 50, "reward_type": "fragment", "reward_amount": 100, "reward_name": "星元碎片 x100", "valid_days": None},
        {"rank_start": 51, "rank_end": 100, "reward_type": "fragment", "reward_amount": 50, "reward_name": "星元碎片 x50", "valid_days": None},
    ],
}


class LeaderboardService:
    """
    排行榜服务
    
    核心功能：
    - 排行榜配置管理
    - 排行榜数据计算与更新
    - 排行榜奖励发放
    - 用户徽章和称号管理
    """
    
    _instance: Optional['LeaderboardService'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def initialize_default_configs(self, db: Session) -> List[Dict[str, Any]]:
        """
        初始化默认排行榜配置
        """
        try:
            created_configs = []
            
            for config_data in DEFAULT_LEADERBOARD_CONFIGS:
                existing = db.query(LeaderboardConfig).filter(
                    LeaderboardConfig.board_key == config_data["board_key"]
                ).first()
                
                if existing:
                    created_configs.append(self._config_to_dict(existing))
                    continue
                
                scoring_rules_json = json.dumps(config_data.get("scoring_rules", {}), ensure_ascii=False)
                
                config = LeaderboardConfig(
                    board_key=config_data["board_key"],
                    board_type=config_data["board_type"],
                    name=config_data["name"],
                    display_name=config_data["display_name"],
                    description=config_data.get("description"),
                    cycle_type=config_data["cycle_type"],
                    rank_count=config_data.get("rank_count", 100),
                    display_count=config_data.get("display_count", 20),
                    icon=config_data.get("icon"),
                    sort_order=config_data.get("sort_order", 0),
                    scoring_rules=scoring_rules_json,
                    is_active=True,
                )
                
                db.add(config)
                db.flush()
                
                self._init_default_rewards(db, config.id, config_data["board_key"])
                
                created_configs.append(self._config_to_dict(config))
                logger.info(f"创建排行榜配置: {config.board_key} - {config.name}")
            
            db.commit()
            return created_configs
            
        except Exception as e:
            db.rollback()
            logger.error(f"初始化排行榜配置异常: {str(e)}", exc_info=True)
            raise
    
    def _init_default_rewards(self, db: Session, config_id: int, board_key: str):
        """
        初始化默认排行榜奖励
        """
        rewards = DEFAULT_LEADERBOARD_REWARDS.get(board_key, [])
        
        for reward_data in rewards:
            existing = db.query(LeaderboardReward).filter(
                LeaderboardReward.config_id == config_id,
                LeaderboardReward.rank_start == reward_data["rank_start"],
                LeaderboardReward.rank_end == reward_data["rank_end"]
            ).first()
            
            if existing:
                continue
            
            reward_value_json = None
            if reward_data.get("reward_value"):
                reward_value_json = json.dumps(reward_data["reward_value"], ensure_ascii=False)
            
            reward = LeaderboardReward(
                config_id=config_id,
                rank_start=reward_data["rank_start"],
                rank_end=reward_data["rank_end"],
                reward_type=reward_data["reward_type"],
                reward_amount=reward_data.get("reward_amount", 1),
                reward_value=reward_value_json,
                reward_name=reward_data["reward_name"],
                reward_description=reward_data.get("reward_description"),
                badge_key=reward_data.get("badge_key"),
                badge_name=reward_data.get("badge_name"),
                badge_icon=reward_data.get("badge_icon"),
                badge_animation=reward_data.get("badge_animation"),
                title_key=reward_data.get("title_key"),
                title_name=reward_data.get("title_name"),
                title_color=reward_data.get("title_color"),
                card_key=reward_data.get("card_key"),
                card_name=reward_data.get("card_name"),
                card_rarity=reward_data.get("card_rarity", "limited"),
                is_auto_distribute=reward_data.get("is_auto_distribute", True),
                valid_days=reward_data.get("valid_days"),
                is_active=True,
            )
            
            db.add(reward)
            logger.info(f"创建排行榜奖励: rank {reward.rank_start}-{reward.rank_end} - {reward.reward_name}")
    
    def get_active_configs(self, db: Session) -> List[Dict[str, Any]]:
        """
        获取所有激活的排行榜配置
        """
        configs = db.query(LeaderboardConfig).filter(
            LeaderboardConfig.is_active == True,
            LeaderboardConfig.is_deleted == False
        ).order_by(LeaderboardConfig.sort_order.asc()).all()
        
        return [self._config_to_dict(c) for c in configs]
    
    def get_leaderboard_data(
        self,
        db: Session,
        board_key: str,
        cycle_key: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        获取排行榜数据
        
        如果没有指定周期，自动计算当前周期并获取数据
        """
        config = db.query(LeaderboardConfig).filter(
            LeaderboardConfig.board_key == board_key,
            LeaderboardConfig.is_active == True,
            LeaderboardConfig.is_deleted == False
        ).first()
        
        if not config:
            return {"success": False, "error": "排行榜不存在", "code": "BOARD_NOT_FOUND"}
        
        if not cycle_key:
            cycle_key = self._get_current_cycle_key(config.cycle_type)
        
        entries = db.query(LeaderboardEntry).filter(
            LeaderboardEntry.config_id == config.id,
            LeaderboardEntry.cycle_key == cycle_key,
            LeaderboardEntry.is_eligible == True
        ).order_by(
            LeaderboardEntry.rank.asc()
        ).limit(limit).all()
        
        cycle_start, cycle_end = self._get_cycle_date_range(config.cycle_type, cycle_key)
        
        return {
            "success": True,
            "data": {
                "config": self._config_to_dict(config),
                "cycle_key": cycle_key,
                "cycle_start": cycle_start.isoformat() if cycle_start else None,
                "cycle_end": cycle_end.isoformat() if cycle_end else None,
                "entries": [self._entry_to_dict(e) for e in entries],
                "total_count": len(entries)
            }
        }
    
    def get_user_rank(
        self,
        db: Session,
        user_id: int,
        board_key: str,
        cycle_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取用户在排行榜中的排名
        """
        config = db.query(LeaderboardConfig).filter(
            LeaderboardConfig.board_key == board_key,
            LeaderboardConfig.is_active == True,
            LeaderboardConfig.is_deleted == False
        ).first()
        
        if not config:
            return {"success": False, "error": "排行榜不存在", "code": "BOARD_NOT_FOUND"}
        
        if not cycle_key:
            cycle_key = self._get_current_cycle_key(config.cycle_type)
        
        entry = db.query(LeaderboardEntry).filter(
            LeaderboardEntry.config_id == config.id,
            LeaderboardEntry.user_id == user_id,
            LeaderboardEntry.cycle_key == cycle_key
        ).first()
        
        if not entry:
            return {
                "success": True,
                "data": {
                    "has_ranked": False,
                    "rank": None,
                    "score": 0.0,
                    "message": "尚未进入排行榜"
                }
            }
        
        return {
            "success": True,
            "data": {
                "has_ranked": True,
                "rank": entry.rank,
                "previous_rank": entry.previous_rank,
                "score": entry.score,
                "score_display": entry.score_display,
                "score_detail": json.loads(entry.score_detail) if entry.score_detail else None,
                "is_eligible": entry.is_eligible,
                "reward_claimed": entry.reward_claimed,
                "reward_claimed_at": entry.reward_claimed_at.isoformat() if entry.reward_claimed_at else None
            }
        }
    
    def calculate_and_update_leaderboard(
        self,
        db: Session,
        board_key: str,
        cycle_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        计算并更新排行榜数据
        """
        config = db.query(LeaderboardConfig).filter(
            LeaderboardConfig.board_key == board_key,
            LeaderboardConfig.is_active == True,
            LeaderboardConfig.is_deleted == False
        ).first()
        
        if not config:
            return {"success": False, "error": "排行榜不存在", "code": "BOARD_NOT_FOUND"}
        
        if not cycle_key:
            cycle_key = self._get_current_cycle_key(config.cycle_type)
        
        cycle_start, cycle_end = self._get_cycle_date_range(config.cycle_type, cycle_key)
        
        scoring_rules = {}
        if config.scoring_rules:
            try:
                scoring_rules = json.loads(config.scoring_rules)
            except:
                scoring_rules = {}
        
        user_scores = self._calculate_user_scores(
            db, config.board_type, scoring_rules, cycle_start, cycle_end
        )
        
        sorted_users = sorted(user_scores.items(), key=lambda x: x[1]["score"], reverse=True)
        
        rank_count = config.rank_count or 100
        top_users = sorted_users[:rank_count]
        
        updated_count = 0
        for rank, (user_id, score_data) in enumerate(top_users, start=1):
            existing_entry = db.query(LeaderboardEntry).filter(
                LeaderboardEntry.config_id == config.id,
                LeaderboardEntry.user_id == user_id,
                LeaderboardEntry.cycle_key == cycle_key
            ).first()
            
            if existing_entry:
                existing_entry.previous_rank = existing_entry.rank
                existing_entry.rank = rank
                existing_entry.score = score_data["score"]
                existing_entry.score_display = score_data.get("score_display")
                existing_entry.score_detail = json.dumps(score_data.get("detail", {}), ensure_ascii=False)
                existing_entry.is_eligible = True
            else:
                entry = LeaderboardEntry(
                    config_id=config.id,
                    user_id=user_id,
                    cycle_key=cycle_key,
                    cycle_start=cycle_start,
                    cycle_end=cycle_end,
                    rank=rank,
                    score=score_data["score"],
                    score_display=score_data.get("score_display"),
                    score_detail=json.dumps(score_data.get("detail", {}), ensure_ascii=False),
                    is_eligible=True,
                    reward_claimed=False
                )
                db.add(entry)
            
            updated_count += 1
        
        db.commit()
        
        logger.info(f"排行榜更新完成: {board_key}, 周期: {cycle_key}, 更新用户数: {updated_count}")
        
        return {
            "success": True,
            "data": {
                "board_key": board_key,
                "cycle_key": cycle_key,
                "updated_count": updated_count,
                "top_users_count": len(top_users)
            }
        }
    
    def distribute_leaderboard_rewards(
        self,
        db: Session,
        board_key: str,
        cycle_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        发放排行榜奖励
        """
        config = db.query(LeaderboardConfig).filter(
            LeaderboardConfig.board_key == board_key,
            LeaderboardConfig.is_active == True,
            LeaderboardConfig.is_deleted == False
        ).first()
        
        if not config:
            return {"success": False, "error": "排行榜不存在", "code": "BOARD_NOT_FOUND"}
        
        if not cycle_key:
            cycle_key = self._get_current_cycle_key(config.cycle_type)
        
        rewards = db.query(LeaderboardReward).filter(
            LeaderboardReward.config_id == config.id,
            LeaderboardReward.is_active == True
        ).order_by(LeaderboardReward.rank_start.asc()).all()
        
        if not rewards:
            return {"success": True, "data": {"message": "没有配置奖励", "distributed_count": 0}}
        
        distributed_count = 0
        
        for reward in rewards:
            entries = db.query(LeaderboardEntry).filter(
                LeaderboardEntry.config_id == config.id,
                LeaderboardEntry.cycle_key == cycle_key,
                LeaderboardEntry.rank >= reward.rank_start,
                LeaderboardEntry.rank <= reward.rank_end,
                LeaderboardEntry.is_eligible == True,
                LeaderboardEntry.reward_claimed == False
            ).all()
            
            for entry in entries:
                result = self._distribute_single_reward(
                    db, entry, reward, config, cycle_key
                )
                if result:
                    distributed_count += 1
        
        db.commit()
        
        logger.info(f"排行榜奖励发放完成: {board_key}, 周期: {cycle_key}, 发放数量: {distributed_count}")
        
        return {
            "success": True,
            "data": {
                "board_key": board_key,
                "cycle_key": cycle_key,
                "distributed_count": distributed_count
            }
        }
    
    def _calculate_user_scores(
        self,
        db: Session,
        board_type: str,
        scoring_rules: Dict,
        cycle_start: datetime,
        cycle_end: datetime
    ) -> Dict[int, Dict[str, Any]]:
        """
        根据排行榜类型计算用户分数
        """
        user_scores = {}
        
        if board_type == LeaderboardType.WEEKLY_ENERGY.value:
            user_scores = self._calculate_energy_scores(db, scoring_rules, cycle_start, cycle_end)
        
        elif board_type == LeaderboardType.WEEKLY_PK.value:
            user_scores = self._calculate_pk_scores(db, scoring_rules, cycle_start, cycle_end)
        
        elif board_type == LeaderboardType.PREDICTION_HIT.value:
            user_scores = self._calculate_prediction_scores(db, scoring_rules, cycle_start, cycle_end)
        
        elif board_type == LeaderboardType.FRIEND_NETWORK.value:
            user_scores = self._calculate_network_scores(db, scoring_rules, cycle_start, cycle_end)
        
        return user_scores
    
    def _calculate_pk_scores(
        self,
        db: Session,
        scoring_rules: Dict,
        cycle_start: datetime,
        cycle_end: datetime
    ) -> Dict[int, Dict[str, Any]]:
        """
        计算PK战绩榜分数
        """
        user_scores = {}
        
        win_weight = scoring_rules.get("win_weight", 100.0)
        loss_weight = scoring_rules.get("loss_weight", -20.0)
        fragment_weight = scoring_rules.get("fragment_earned_weight", 0.5)
        win_streak_bonus = scoring_rules.get("win_streak_bonus", 20.0)
        
        matches = db.query(
            PKMatch.challenger_id,
            PKMatch.defender_id,
            PKMatch.winner_id,
            PKMatch.loser_id,
            PKMatch.fragments_transferred,
            PKMatch.challenger_energy,
            PKMatch.defender_energy,
            PKMatch.match_completed_at
        ).filter(
            PKMatch.status == "completed",
            PKMatch.match_completed_at >= cycle_start,
            PKMatch.match_completed_at <= cycle_end
        ).all()
        
        user_stats = {}
        
        for match in matches:
            challenger_id = match.challenger_id
            defender_id = match.defender_id
            winner_id = match.winner_id
            loser_id = match.loser_id
            fragments = match.fragments_transferred or 0
            
            if challenger_id not in user_stats:
                user_stats[challenger_id] = {
                    "wins": 0, "losses": 0, "draws": 0,
                    "fragments_earned": 0, "fragments_lost": 0,
                    "max_energy_used": 0.0
                }
            if defender_id not in user_stats:
                user_stats[defender_id] = {
                    "wins": 0, "losses": 0, "draws": 0,
                    "fragments_earned": 0, "fragments_lost": 0,
                    "max_energy_used": 0.0
                }
            
            if winner_id == challenger_id:
                user_stats[challenger_id]["wins"] += 1
                user_stats[challenger_id]["fragments_earned"] += fragments
                user_stats[defender_id]["losses"] += 1
                user_stats[defender_id]["fragments_lost"] += fragments
            elif winner_id == defender_id:
                user_stats[defender_id]["wins"] += 1
                user_stats[defender_id]["fragments_earned"] += fragments
                user_stats[challenger_id]["losses"] += 1
                user_stats[challenger_id]["fragments_lost"] += fragments
            else:
                user_stats[challenger_id]["draws"] += 1
                user_stats[defender_id]["draws"] += 1
            
            if match.challenger_energy > user_stats[challenger_id]["max_energy_used"]:
                user_stats[challenger_id]["max_energy_used"] = match.challenger_energy
            if match.defender_energy > user_stats[defender_id]["max_energy_used"]:
                user_stats[defender_id]["max_energy_used"] = match.defender_energy
        
        for user_id, stats in user_stats.items():
            wins = stats["wins"]
            losses = stats["losses"]
            draws = stats["draws"]
            fragments_earned = stats["fragments_earned"]
            max_energy = stats["max_energy_used"]
            
            base_score = (
                wins * win_weight +
                losses * loss_weight +
                fragments_earned * fragment_weight
            )
            
            total_matches = wins + losses + draws
            win_rate = (wins / total_matches) if total_matches > 0 else 0
            
            estimated_win_streak = min(wins, 5)
            streak_bonus = estimated_win_streak * win_streak_bonus
            
            score = max(0, base_score + streak_bonus)
            
            user_scores[user_id] = {
                "score": score,
                "score_display": str(int(score)),
                "detail": {
                    "total_matches": total_matches,
                    "wins": wins,
                    "losses": losses,
                    "draws": draws,
                    "win_rate": round(win_rate * 100, 1),
                    "fragments_earned": fragments_earned,
                    "max_energy_used": max_energy
                }
            }
        
        return user_scores
    
    def _calculate_energy_scores(
        self,
        db: Session,
        scoring_rules: Dict,
        cycle_start: datetime,
        cycle_end: datetime
    ) -> Dict[int, Dict[str, Any]]:
        """
        计算能量榜分数
        """
        user_scores = {}
        
        energy_weight = scoring_rules.get("energy_contribution_weight", 1.0)
        
        contributions = db.query(
            EnergyContribution.user_id,
            func.sum(EnergyContribution.energy_amount).label("total_energy")
        ).filter(
            EnergyContribution.is_active == True,
            EnergyContribution.created_at >= cycle_start,
            EnergyContribution.created_at <= cycle_end
        ).group_by(EnergyContribution.user_id).all()
        
        for contrib in contributions:
            user_id = contrib.user_id
            total_energy = contrib.total_energy or 0.0
            score = total_energy * energy_weight
            
            user_scores[user_id] = {
                "score": score,
                "score_display": f"{score:.1f}",
                "detail": {
                    "total_energy": total_energy,
                    "energy_weight": energy_weight
                }
            }
        
        return user_scores
    
    def _calculate_prediction_scores(
        self,
        db: Session,
        scoring_rules: Dict,
        cycle_start: datetime,
        cycle_end: datetime
    ) -> Dict[int, Dict[str, Any]]:
        """
        计算预言家命中榜分数
        """
        user_scores = {}
        
        correct_weight = scoring_rules.get("correct_prediction_weight", 10.0)
        
        correct_votes = db.query(
            PredictionVote.user_id,
            func.count(PredictionVote.id).label("correct_count")
        ).filter(
            PredictionVote.is_correct == True,
            PredictionVote.created_at >= cycle_start,
            PredictionVote.created_at <= cycle_end
        ).group_by(PredictionVote.user_id).all()
        
        for vote in correct_votes:
            user_id = vote.user_id
            correct_count = vote.correct_count or 0
            score = correct_count * correct_weight
            
            user_scores[user_id] = {
                "score": score,
                "score_display": str(int(score)),
                "detail": {
                    "correct_count": correct_count,
                    "correct_weight": correct_weight
                }
            }
        
        return user_scores
    
    def _calculate_network_scores(
        self,
        db: Session,
        scoring_rules: Dict,
        cycle_start: datetime,
        cycle_end: datetime
    ) -> Dict[int, Dict[str, Any]]:
        """
        计算人脉好友榜分数
        """
        user_scores = {}
        
        mutual_weight = scoring_rules.get("mutual_connection_weight", 5.0)
        one_way_weight = scoring_rules.get("one_way_connection_weight", 1.0)
        
        connections = db.query(
            NetworkConnection.from_user_id,
            func.count(NetworkConnection.id).label("connection_count")
        ).filter(
            NetworkConnection.is_active == True,
            NetworkConnection.created_at <= cycle_end
        ).group_by(NetworkConnection.from_user_id).all()
        
        for conn in connections:
            user_id = conn.from_user_id
            connection_count = conn.connection_count or 0
            
            mutual_count = db.query(NetworkConnection).filter(
                NetworkConnection.from_user_id == user_id,
                NetworkConnection.is_mutual == True,
                NetworkConnection.is_active == True
            ).count()
            
            one_way_count = connection_count - mutual_count
            score = (mutual_count * mutual_weight) + (one_way_count * one_way_weight)
            
            user_scores[user_id] = {
                "score": score,
                "score_display": str(int(score)),
                "detail": {
                    "mutual_count": mutual_count,
                    "one_way_count": one_way_count,
                    "total_connections": connection_count
                }
            }
        
        return user_scores
    
    def _distribute_single_reward(
        self,
        db: Session,
        entry: LeaderboardEntry,
        reward: LeaderboardReward,
        config: LeaderboardConfig,
        cycle_key: str
    ) -> bool:
        """
        发放单个奖励
        """
        try:
            user_id = entry.user_id
            now = datetime.utcnow()
            
            valid_from = now
            valid_until = None
            if reward.valid_days:
                valid_until = now + timedelta(days=reward.valid_days)
            
            if reward.reward_type == "badge":
                self._grant_badge(
                    db, user_id, reward, config.board_key, cycle_key,
                    valid_from, valid_until
                )
            
            elif reward.reward_type == "title":
                self._grant_title(
                    db, user_id, reward, config.board_key, cycle_key,
                    valid_from, valid_until
                )
            
            elif reward.reward_type == "fragment":
                self._grant_fragments(
                    db, user_id, reward.reward_amount,
                    f"{config.display_name} 排名奖励"
                )
            
            entry.reward_claimed = True
            entry.reward_claimed_at = now
            
            logger.info(f"发放排行榜奖励: user_id={user_id}, rank={entry.rank}, reward={reward.reward_name}")
            return True
            
        except Exception as e:
            logger.error(f"发放排行榜奖励失败: user_id={entry.user_id}, error={str(e)}", exc_info=True)
            return False
    
    def _grant_badge(
        self,
        db: Session,
        user_id: int,
        reward: LeaderboardReward,
        board_key: str,
        cycle_key: str,
        valid_from: datetime,
        valid_until: Optional[datetime]
    ):
        """
        发放徽章
        """
        existing = db.query(UserBadge).filter(
            UserBadge.user_id == user_id,
            UserBadge.badge_key == reward.badge_key,
            UserBadge.valid_until > valid_from if valid_until else True
        ).first()
        
        if existing:
            existing.valid_from = valid_from
            existing.valid_until = valid_until
            existing.updated_at = datetime.utcnow()
        else:
            badge = UserBadge(
                user_id=user_id,
                badge_key=reward.badge_key or "",
                badge_name=reward.badge_name or reward.reward_name,
                badge_description=f"{board_key} 排行榜奖励 - 周期 {cycle_key}",
                badge_icon=reward.badge_icon,
                badge_animation=reward.badge_animation,
                badge_rarity=reward.badge_rarity or "rare",
                source_type="leaderboard",
                source_reference=f"{board_key}:{cycle_key}",
                is_equipped=False,
                is_limited=True,
                valid_from=valid_from,
                valid_until=valid_until
            )
            db.add(badge)
    
    def _grant_title(
        self,
        db: Session,
        user_id: int,
        reward: LeaderboardReward,
        board_key: str,
        cycle_key: str,
        valid_from: datetime,
        valid_until: Optional[datetime]
    ):
        """
        发放称号
        """
        existing = db.query(UserTitle).filter(
            UserTitle.user_id == user_id,
            UserTitle.title_key == reward.title_key,
            UserTitle.valid_until > valid_from if valid_until else True
        ).first()
        
        if existing:
            existing.valid_from = valid_from
            existing.valid_until = valid_until
            existing.updated_at = datetime.utcnow()
        else:
            title = UserTitle(
                user_id=user_id,
                title_key=reward.title_key or "",
                title_name=reward.title_name or reward.reward_name,
                title_description=f"{board_key} 排行榜奖励 - 周期 {cycle_key}",
                title_color=reward.title_color,
                source_type="leaderboard",
                source_reference=f"{board_key}:{cycle_key}",
                is_equipped=False,
                is_limited=True,
                valid_from=valid_from,
                valid_until=valid_until
            )
            db.add(title)
    
    def _grant_fragments(
        self,
        db: Session,
        user_id: int,
        amount: int,
        description: str
    ):
        """
        发放星元碎片
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return
        
        balance_before = user.stardust_fragment_balance or 0
        balance_after = balance_before + amount
        
        user.stardust_fragment_balance = balance_after
        
        transaction = StarDustTransaction(
            user_id=user_id,
            transaction_type="leaderboard_reward",
            currency_type="fragment",
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            related_type="leaderboard",
            description=description
        )
        db.add(transaction)
    
    def _get_current_cycle_key(self, cycle_type: str) -> str:
        """
        获取当前周期的key
        """
        now = datetime.utcnow()
        
        if cycle_type == LeaderboardCycle.DAILY.value:
            return now.strftime("%Y-%m-%d")
        
        elif cycle_type == LeaderboardCycle.WEEKLY.value:
            year, week, _ = now.isocalendar()
            return f"{year}-W{week:02d}"
        
        elif cycle_type == LeaderboardCycle.MONTHLY.value:
            return now.strftime("%Y-%m")
        
        elif cycle_type == LeaderboardCycle.SEASONAL.value:
            month = now.month
            if month in [1, 2, 3]:
                season = "Q1"
            elif month in [4, 5, 6]:
                season = "Q2"
            elif month in [7, 8, 9]:
                season = "Q3"
            else:
                season = "Q4"
            return f"{now.year}-{season}"
        
        return now.strftime("%Y-%m-%d")
    
    def _get_cycle_date_range(
        self,
        cycle_type: str,
        cycle_key: str
    ) -> Tuple[Optional[datetime], Optional[datetime]]:
        """
        获取周期的开始和结束日期
        """
        try:
            if cycle_type == LeaderboardCycle.DAILY.value:
                date = datetime.strptime(cycle_key, "%Y-%m-%d")
                start = datetime(date.year, date.month, date.day)
                end = start + timedelta(days=1)
                return start, end
            
            elif cycle_type == LeaderboardCycle.WEEKLY.value:
                parts = cycle_key.split("-W")
                if len(parts) == 2:
                    year = int(parts[0])
                    week = int(parts[1])
                    start = datetime.fromisocalendar(year, week, 1)
                    end = start + timedelta(weeks=1)
                    return start, end
            
            elif cycle_type == LeaderboardCycle.MONTHLY.value:
                year, month = map(int, cycle_key.split("-"))
                start = datetime(year, month, 1)
                if month == 12:
                    end = datetime(year + 1, 1, 1)
                else:
                    end = datetime(year, month + 1, 1)
                return start, end
        
        except Exception as e:
            logger.warning(f"解析周期日期范围失败: cycle_type={cycle_type}, cycle_key={cycle_key}, error={str(e)}")
        
        return None, None
    
    def _config_to_dict(self, config: LeaderboardConfig) -> Dict[str, Any]:
        """将排行榜配置转换为字典"""
        scoring_rules = {}
        if config.scoring_rules:
            try:
                scoring_rules = json.loads(config.scoring_rules)
            except:
                scoring_rules = {}
        
        eligibility_rules = {}
        if config.eligibility_rules:
            try:
                eligibility_rules = json.loads(config.eligibility_rules)
            except:
                eligibility_rules = {}
        
        return {
            "id": config.id,
            "board_key": config.board_key,
            "board_type": config.board_type,
            "name": config.name,
            "display_name": config.display_name,
            "description": config.description,
            "cycle_type": config.cycle_type,
            "rank_count": config.rank_count,
            "display_count": config.display_count,
            "scoring_rules": scoring_rules,
            "eligibility_rules": eligibility_rules,
            "is_active": config.is_active,
            "sort_order": config.sort_order,
            "icon": config.icon,
            "banner_url": config.banner_url,
            "created_at": config.created_at.isoformat() if config.created_at else None,
            "updated_at": config.updated_at.isoformat() if config.updated_at else None
        }
    
    def _entry_to_dict(self, entry: LeaderboardEntry) -> Dict[str, Any]:
        """将排行榜条目转换为字典"""
        score_detail = {}
        if entry.score_detail:
            try:
                score_detail = json.loads(entry.score_detail)
            except:
                score_detail = {}
        
        user_name = None
        if entry.user:
            user_name = entry.user.username
        
        return {
            "id": entry.id,
            "config_id": entry.config_id,
            "user_id": entry.user_id,
            "user_name": user_name,
            "cycle_key": entry.cycle_key,
            "rank": entry.rank,
            "previous_rank": entry.previous_rank,
            "score": entry.score,
            "score_display": entry.score_display,
            "score_detail": score_detail,
            "is_eligible": entry.is_eligible,
            "ineligibility_reason": entry.ineligibility_reason,
            "reward_claimed": entry.reward_claimed,
            "reward_claimed_at": entry.reward_claimed_at.isoformat() if entry.reward_claimed_at else None
        }


leaderboard_service = LeaderboardService()


def get_leaderboard_service() -> LeaderboardService:
    """获取排行榜服务单例"""
    return leaderboard_service
