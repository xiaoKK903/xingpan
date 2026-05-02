import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.models import (
    CollectivePrediction,
    PredictionVote,
    StarDustTransaction,
    User
)

logger = logging.getLogger(__name__)

PREDICTION_TYPE_CONFIG = {
    "moon_phase": {
        "name": "月相预测",
        "description": "预测明日月相对应的情绪",
        "options": [
            {"value": "positive", "label": "积极乐观", "icon": "🌕"},
            {"value": "neutral", "label": "平稳过渡", "icon": "🌗"},
            {"value": "challenging", "label": "情绪波动", "icon": "🌑"}
        ],
        "resolution_method": "astro_calendar"
    },
    "mercury_status": {
        "name": "水星状态",
        "description": "预测明日水星逆行影响",
        "options": [
            {"value": "communication", "label": "沟通顺畅", "icon": "💬"},
            {"value": "delay", "label": "延误阻滞", "icon": "⏳"},
            {"value": "confusion", "label": "思维混乱", "icon": "🌀"}
        ],
        "resolution_method": "astro_calendar"
    },
    "collective_mood": {
        "name": "集体情绪",
        "description": "预测明日社区整体情绪",
        "options": [
            {"value": "harmonious", "label": "和谐融洽", "icon": "😊"},
            {"value": "balanced", "label": "平稳中性", "icon": "😐"},
            {"value": "tense", "label": "紧张压抑", "icon": "😰"}
        ],
        "resolution_method": "community_energy"
    },
    "sun_sign_energy": {
        "name": "太阳星座能量",
        "description": "预测明日最活跃太阳星座",
        "options": [
            {"value": "fire", "label": "火象活跃", "icon": "🔥"},
            {"value": "earth", "label": "土象稳健", "icon": "🌍"},
            {"value": "air", "label": "风象灵动", "icon": "💨"},
            {"value": "water", "label": "水象感性", "icon": "💧"}
        ],
        "resolution_method": "online_distribution"
    }
}


class PredictionSettlementService:
    """
    预测结算服务（预言机机制）
    
    职责：
    - 定义预测类型和选项
    - 实现预言机结算机制
    - 计算投票结果，分配星尘奖励
    - 确保结算的公平性和透明性
    """
    
    def __init__(self):
        self._base_reward_pool = 1000
        self._correct_predictor_multiplier = 2.0
    
    def get_prediction_types(self) -> Dict[str, Any]:
        """获取所有预测类型配置"""
        return PREDICTION_TYPE_CONFIG
    
    def create_daily_predictions(self, db: Session) -> List[Dict[str, Any]]:
        """
        创建每日预测
        
        Args:
            db: 数据库会话
            
        Returns:
            创建的预测列表
        """
        tomorrow = datetime.utcnow().date() + timedelta(days=1)
        existing_predictions = db.query(CollectivePrediction).filter(
            CollectivePrediction.target_date == tomorrow
        ).all()
        
        if existing_predictions:
            return [self._prediction_to_dict(p) for p in existing_predictions]
        
        created_predictions = []
        
        for pred_type, config in PREDICTION_TYPE_CONFIG.items():
            prediction = CollectivePrediction(
                prediction_type=pred_type,
                title=config["name"],
                description=config["description"],
                options=json.dumps(config["options"], ensure_ascii=False),
                target_date=tomorrow,
                voting_ends_at=datetime.combine(tomorrow, datetime.min.time()),
                is_resolved=False,
                created_at=datetime.utcnow()
            )
            db.add(prediction)
            created_predictions.append(prediction)
        
        db.commit()
        
        return [self._prediction_to_dict(p) for p in created_predictions]
    
    def resolve_prediction(
        self,
        db: Session,
        prediction_id: int,
        correct_option: str,
        resolution_source: str = "oracle",
        resolution_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        结算预测
        
        Args:
            db: 数据库会话
            prediction_id: 预测ID
            correct_option: 正确选项值
            resolution_source: 结算来源
            resolution_details: 结算详情
            
        Returns:
            结算结果
        """
        prediction = db.query(CollectivePrediction).filter(
            CollectivePrediction.id == prediction_id
        ).first()
        
        if not prediction:
            return {"success": False, "error": "预测不存在"}
        
        if prediction.is_resolved:
            return {"success": False, "error": "预测已结算"}
        
        correct_votes = db.query(PredictionVote).filter(
            and_(
                PredictionVote.prediction_id == prediction_id,
                PredictionVote.selected_option == correct_option
            )
        ).all()
        
        all_votes = db.query(PredictionVote).filter(
            PredictionVote.prediction_id == prediction_id
        ).all()
        
        total_votes = len(all_votes)
        correct_count = len(correct_votes)
        
        config = PREDICTION_TYPE_CONFIG.get(prediction.prediction_type, {})
        options = config.get("options", [])
        correct_option_label = correct_option
        for opt in options:
            if opt["value"] == correct_option:
                correct_option_label = opt["label"]
                break
        
        total_pool = self._calculate_reward_pool(total_votes)
        reward_per_correct = 0
        
        if correct_count > 0:
            reward_per_correct = int(total_pool / correct_count)
        
        transactions = []
        for vote in correct_votes:
            user = db.query(User).filter(User.id == vote.user_id).first()
            if user:
                transaction = StarDustTransaction(
                    user_id=vote.user_id,
                    amount=reward_per_correct,
                    transaction_type="prediction_reward",
                    reference_id=prediction.id,
                    description=f"预测奖励: {prediction.title}",
                    created_at=datetime.utcnow()
                )
                db.add(transaction)
                transactions.append({
                    "user_id": vote.user_id,
                    "username": user.username,
                    "amount": reward_per_correct
                })
                
                if user.star_dust is None:
                    user.star_dust = 0
                user.star_dust += reward_per_correct
        
        prediction.is_resolved = True
        prediction.resolved_at = datetime.utcnow()
        prediction.correct_option = correct_option
        prediction.resolution_source = resolution_source
        prediction.resolution_details = json.dumps(resolution_details or {}, ensure_ascii=False) if resolution_details else None
        prediction.total_votes = total_votes
        prediction.total_reward_pool = total_pool
        prediction.winner_count = correct_count
        
        db.commit()
        
        return {
            "success": True,
            "prediction_id": prediction_id,
            "prediction_type": prediction.prediction_type,
            "title": prediction.title,
            "target_date": prediction.target_date.isoformat() if prediction.target_date else None,
            "correct_option": correct_option,
            "correct_option_label": correct_option_label,
            "total_votes": total_votes,
            "correct_count": correct_count,
            "total_reward_pool": total_pool,
            "reward_per_winner": reward_per_correct,
            "transactions": transactions
        }
    
    def _calculate_reward_pool(self, total_votes: int) -> int:
        """
        计算奖励池
        
        基础奖励 + 参与人数加成
        """
        base = self._base_reward_pool
        participation_bonus = total_votes * 10
        
        return base + participation_bonus
    
    def resolve_daily_predictions(self, db: Session) -> Dict[str, Any]:
        """
        结算所有昨日的预测
        
        Args:
            db: 数据库会话
            
        Returns:
            结算结果汇总
        """
        yesterday = datetime.utcnow().date() - timedelta(days=1)
        
        predictions_to_resolve = db.query(CollectivePrediction).filter(
            and_(
                CollectivePrediction.target_date == yesterday,
                CollectivePrediction.is_resolved == False
            )
        ).all()
        
        if not predictions_to_resolve:
            return {
                "resolved_count": 0,
                "message": "没有需要结算的预测"
            }
        
        results = []
        for prediction in predictions_to_resolve:
            resolution = self._auto_resolve_prediction(db, prediction)
            results.append(resolution)
        
        return {
            "resolved_count": len(results),
            "results": results
        }
    
    def _auto_resolve_prediction(
        self,
        db: Session,
        prediction: CollectivePrediction
    ) -> Dict[str, Any]:
        """
        自动结算预测
        
        根据预测类型的结算方法进行自动结算
        """
        config = PREDICTION_TYPE_CONFIG.get(prediction.prediction_type, {})
        resolution_method = config.get("resolution_method", "random")
        
        votes = db.query(PredictionVote).filter(
            PredictionVote.prediction_id == prediction.id
        ).all()
        
        if not votes:
            return self.resolve_prediction(
                db,
                prediction.id,
                correct_option="none",
                resolution_source="oracle",
                resolution_details={"reason": "无有效投票"}
            )
        
        vote_counts = {}
        for vote in votes:
            opt = vote.selected_option
            vote_counts[opt] = vote_counts.get(opt, 0) + 1
        
        max_votes = max(vote_counts.values())
        leading_options = [k for k, v in vote_counts.items() if v == max_votes]
        
        correct_option = leading_options[0] if leading_options else None
        
        resolution_details = {
            "method": resolution_method,
            "vote_counts": vote_counts,
            "leading_options": leading_options,
            "selected_correct": correct_option
        }
        
        return self.resolve_prediction(
            db,
            prediction.id,
            correct_option=correct_option or "none",
            resolution_source="auto_oracle",
            resolution_details=resolution_details
        )
    
    def get_prediction_statistics(
        self,
        db: Session,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取预测统计
        
        Args:
            db: 数据库会话
            user_id: 用户ID（可选）
            
        Returns:
            统计信息
        """
        total_predictions = db.query(func.count(CollectivePrediction.id)).scalar() or 0
        
        resolved_predictions = db.query(func.count(CollectivePrediction.id)).filter(
            CollectivePrediction.is_resolved == True
        ).scalar() or 0
        
        total_votes = db.query(func.count(PredictionVote.id)).scalar() or 0
        
        total_rewards = db.query(func.sum(StarDustTransaction.amount)).filter(
            StarDustTransaction.transaction_type == "prediction_reward"
        ).scalar() or 0
        
        stats = {
            "overall": {
                "total_predictions": total_predictions,
                "resolved_predictions": resolved_predictions,
                "active_predictions": total_predictions - resolved_predictions,
                "total_votes": total_votes,
                "total_rewards_distributed": int(total_rewards)
            }
        }
        
        if user_id:
            user_votes = db.query(PredictionVote).filter(
                PredictionVote.user_id == user_id
            ).all()
            
            correct_votes = db.query(PredictionVote).filter(
                and_(
                    PredictionVote.user_id == user_id,
                    PredictionVote.is_correct == True
                )
            ).count()
            
            user_rewards = db.query(func.sum(StarDustTransaction.amount)).filter(
                and_(
                    StarDustTransaction.user_id == user_id,
                    StarDustTransaction.transaction_type == "prediction_reward"
                )
            ).scalar() or 0
            
            accuracy = (correct_votes / len(user_votes) * 100) if user_votes else 0
            
            stats["user"] = {
                "user_id": user_id,
                "total_votes": len(user_votes),
                "correct_votes": correct_votes,
                "accuracy_rate": round(accuracy, 1),
                "total_rewards": int(user_rewards)
            }
        
        return stats
    
    def _prediction_to_dict(self, prediction: CollectivePrediction) -> Dict[str, Any]:
        """将预测转换为字典"""
        return {
            "id": prediction.id,
            "prediction_type": prediction.prediction_type,
            "title": prediction.title,
            "description": prediction.description,
            "options": json.loads(prediction.options) if prediction.options else [],
            "target_date": prediction.target_date.isoformat() if prediction.target_date else None,
            "voting_ends_at": prediction.voting_ends_at.isoformat() if prediction.voting_ends_at else None,
            "is_resolved": prediction.is_resolved,
            "resolved_at": prediction.resolved_at.isoformat() if prediction.resolved_at else None,
            "correct_option": prediction.correct_option,
            "total_votes": prediction.total_votes,
            "winner_count": prediction.winner_count,
            "total_reward_pool": prediction.total_reward_pool
        }


prediction_settlement_service = PredictionSettlementService()


def get_prediction_settlement_service() -> PredictionSettlementService:
    """获取预测结算服务单例"""
    return prediction_settlement_service
