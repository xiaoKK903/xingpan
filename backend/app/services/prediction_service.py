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
    CommunityEnergySnapshot
)

logger = logging.getLogger(__name__)

PREDICTION_TYPES = {
    "mood": {
        "name": "集体情绪",
        "description": "预测明日集体情绪",
        "options": ["☀️ 晴朗 - 能量充沛", "⛅ 多云 - 能量适中", "🌥️ 阴天 - 能量较低", "⛈️ 雷雨 - 能量动荡"],
        "option_values": ["sunny", "cloudy", "overcast", "stormy"]
    },
    "dominant_planet": {
        "name": "主导行星",
        "description": "预测明日主导行星",
        "options": ["☉ 太阳", "☽ 月亮", "☿ 水星", "♀ 金星", "♂ 火星", "♃ 木星", "♄ 土星"],
        "option_values": ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]
    },
    "social_event": {
        "name": "社交事件",
        "description": "预测明日最活跃的社交维度",
        "options": ["💬 沟通交流", "👥 社交互动", "💼 事业发展", "💰 财运机会", "❤️ 情感连接"],
        "option_values": ["communication", "social", "career", "wealth", "emotion"]
    },
    "aspect_pattern": {
        "name": "相位格局",
        "description": "预测明日最显著的相位类型",
        "options": ["🌟 和谐相位主导", "⚡ 紧张相位主导", "⚖️ 平衡分布"],
        "option_values": ["harmonious", "challenging", "balanced"]
    }
}


class PredictionService:
    """
    预测竞猜服务
    
    职责：
    - 创建每日预测
    - 处理用户投票
    - 验证预测结果
    - 发放奖励
    """
    
    def create_daily_prediction(
        self,
        db: Session,
        prediction_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        创建每日预测
        
        Args:
            db: 数据库会话
            prediction_date: 预测日期（格式：YYYY-MM-DD），默认为明天
            
        Returns:
            创建的预测列表
        """
        if prediction_date is None:
            tomorrow = datetime.utcnow() + timedelta(days=1)
            prediction_date = tomorrow.strftime("%Y-%m-%d")
        
        now = datetime.utcnow()
        today = now.strftime("%Y-%m-%d")
        
        existing = db.query(CollectivePrediction).filter(
            CollectivePrediction.target_date == prediction_date
        ).first()
        
        if existing:
            return []
        
        created_predictions = []
        
        for pred_type, config in PREDICTION_TYPES.items():
            prediction = CollectivePrediction(
                prediction_date=today,
                target_date=prediction_date,
                title=f"明日{config['name']}预测",
                description=config['description'],
                prediction_type=pred_type,
                options=json.dumps({
                    "labels": config['options'],
                    "values": config['option_values']
                }, ensure_ascii=False),
                total_votes=0,
                vote_distribution=json.dumps({v: 0 for v in config['option_values']}),
                status="open",
                is_resolved=False,
                total_stardust_pool=0,
                created_at=now,
                updated_at=now
            )
            
            db.add(prediction)
            db.commit()
            db.refresh(prediction)
            
            created_predictions.append(self._prediction_to_dict(prediction))
        
        return created_predictions
    
    def get_open_predictions(
        self,
        db: Session,
        target_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取开放投票的预测
        
        Args:
            db: 数据库会话
            target_date: 目标日期
            
        Returns:
            预测列表
        """
        query = db.query(CollectivePrediction).filter(
            CollectivePrediction.status == "open"
        )
        
        if target_date:
            query = query.filter(CollectivePrediction.target_date == target_date)
        
        predictions = query.order_by(CollectivePrediction.created_at.desc()).all()
        
        return [self._prediction_to_dict(p) for p in predictions]
    
    def get_prediction_detail(
        self,
        db: Session,
        prediction_id: int,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取预测详情
        
        Args:
            db: 数据库会话
            prediction_id: 预测ID
            user_id: 用户ID（可选，用于检查投票状态）
            
        Returns:
            预测详情
        """
        prediction = db.query(CollectivePrediction).filter(
            CollectivePrediction.id == prediction_id
        ).first()
        
        if not prediction:
            return {"error": "预测不存在", "code": "PREDICTION_NOT_FOUND"}
        
        result = self._prediction_to_dict(prediction)
        
        if user_id:
            vote = db.query(PredictionVote).filter(
                PredictionVote.prediction_id == prediction_id,
                PredictionVote.user_id == user_id
            ).first()
            
            if vote:
                result["user_vote"] = self._vote_to_dict(vote)
            else:
                result["user_vote"] = None
        
        return result
    
    def cast_vote(
        self,
        db: Session,
        user_id: int,
        prediction_id: int,
        selected_option: str,
        confidence: int = 50,
        stardust_bet: int = 0
    ) -> Dict[str, Any]:
        """
        用户投票
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            prediction_id: 预测ID
            selected_option: 选择的选项值
            confidence: 信心值（0-100）
            stardust_bet: 投注星尘数量
            
        Returns:
            投票结果
        """
        prediction = db.query(CollectivePrediction).filter(
            CollectivePrediction.id == prediction_id
        ).first()
        
        if not prediction:
            return {"error": "预测不存在", "code": "PREDICTION_NOT_FOUND"}
        
        if prediction.status != "open":
            return {"error": "预测已关闭投票", "code": "PREDICTION_CLOSED"}
        
        existing_vote = db.query(PredictionVote).filter(
            PredictionVote.prediction_id == prediction_id,
            PredictionVote.user_id == user_id
        ).first()
        
        if existing_vote:
            return {
                "error": "您已投过票",
                "code": "ALREADY_VOTED",
                "vote": self._vote_to_dict(existing_vote)
            }
        
        options = json.loads(prediction.options) if prediction.options else {}
        option_values = options.get("values", [])
        
        if selected_option not in option_values:
            return {"error": "无效的选项", "code": "INVALID_OPTION"}
        
        confidence = max(0, min(100, confidence))
        
        now = datetime.utcnow()
        
        vote = PredictionVote(
            prediction_id=prediction_id,
            user_id=user_id,
            selected_option=selected_option,
            confidence=confidence,
            stardust_bet=stardust_bet,
            is_correct=None,
            reward_earned=0,
            reward_claimed=False,
            created_at=now
        )
        
        db.add(vote)
        
        prediction.total_votes = (prediction.total_votes or 0) + 1
        
        vote_distribution = json.loads(prediction.vote_distribution) if prediction.vote_distribution else {}
        if selected_option not in vote_distribution:
            vote_distribution[selected_option] = 0
        vote_distribution[selected_option] += 1
        prediction.vote_distribution = json.dumps(vote_distribution, ensure_ascii=False)
        
        if stardust_bet > 0:
            prediction.total_stardust_pool = (prediction.total_stardust_pool or 0) + stardust_bet
        
        prediction.updated_at = now
        
        db.commit()
        db.refresh(vote)
        db.refresh(prediction)
        
        return {
            "success": True,
            "vote": self._vote_to_dict(vote),
            "prediction": self._prediction_to_dict(prediction),
            "message": "投票成功！"
        }
    
    def resolve_prediction(
        self,
        db: Session,
        prediction_id: int,
        actual_result: str
    ) -> Dict[str, Any]:
        """
        结算预测
        
        Args:
            db: 数据库会话
            prediction_id: 预测ID
            actual_result: 实际结果
            
        Returns:
            结算结果
        """
        prediction = db.query(CollectivePrediction).filter(
            CollectivePrediction.id == prediction_id
        ).first()
        
        if not prediction:
            return {"error": "预测不存在", "code": "PREDICTION_NOT_FOUND"}
        
        if prediction.is_resolved:
            return {"error": "预测已结算", "code": "ALREADY_RESOLVED"}
        
        options = json.loads(prediction.options) if prediction.options else {}
        option_values = options.get("values", [])
        
        if actual_result not in option_values:
            return {"error": "无效的结果", "code": "INVALID_RESULT"}
        
        now = datetime.utcnow()
        
        prediction.status = "resolved"
        prediction.is_resolved = True
        prediction.resolved_at = now
        prediction.actual_result = actual_result
        prediction.updated_at = now
        
        votes = db.query(PredictionVote).filter(
            PredictionVote.prediction_id == prediction_id
        ).all()
        
        correct_count = 0
        incorrect_count = 0
        
        for vote in votes:
            if vote.selected_option == actual_result:
                vote.is_correct = True
                correct_count += 1
                
                base_reward = 10
                
                confidence_bonus = 0
                if vote.confidence >= 80:
                    confidence_bonus = 10
                elif vote.confidence >= 50:
                    confidence_bonus = 5
                
                bet_reward = 0
                if vote.stardust_bet > 0 and prediction.total_stardust_pool > 0:
                    vote_ratio = vote.stardust_bet / prediction.total_stardust_pool
                    bet_reward = int(vote.stardust_bet * 2 * vote_ratio)
                
                vote.reward_earned = base_reward + confidence_bonus + bet_reward
            else:
                vote.is_correct = False
                incorrect_count += 1
        
        total_votes = correct_count + incorrect_count
        if total_votes > 0:
            accuracy_score = (correct_count / total_votes) * 100
            prediction.accuracy_score = round(accuracy_score, 1)
        
        db.commit()
        db.refresh(prediction)
        
        return {
            "success": True,
            "prediction": self._prediction_to_dict(prediction),
            "stats": {
                "total_votes": total_votes,
                "correct_count": correct_count,
                "incorrect_count": incorrect_count,
                "accuracy_rate": round((correct_count / total_votes * 100), 1) if total_votes > 0 else 0
            }
        }
    
    def claim_prediction_reward(
        self,
        db: Session,
        user_id: int,
        prediction_id: int
    ) -> Dict[str, Any]:
        """
        领取预测奖励
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            prediction_id: 预测ID
            
        Returns:
            领奖结果
        """
        vote = db.query(PredictionVote).filter(
            PredictionVote.user_id == user_id,
            PredictionVote.prediction_id == prediction_id
        ).first()
        
        if not vote:
            return {"error": "未找到投票记录", "code": "VOTE_NOT_FOUND"}
        
        if not vote.is_correct:
            return {"error": "您没有猜对，无法领取奖励", "code": "NOT_CORRECT"}
        
        if vote.reward_claimed:
            return {"error": "奖励已领取", "code": "ALREADY_CLAIMED"}
        
        prediction = db.query(CollectivePrediction).filter(
            CollectivePrediction.id == prediction_id
        ).first()
        
        if not prediction:
            return {"error": "预测不存在", "code": "PREDICTION_NOT_FOUND"}
        
        if not prediction.is_resolved:
            return {"error": "预测尚未结算", "code": "NOT_RESOLVED"}
        
        reward_amount = vote.reward_earned or 10
        
        now = datetime.utcnow()
        
        vote.reward_claimed = True
        vote.updated_at = now
        
        transaction = StarDustTransaction(
            user_id=user_id,
            transaction_type="prediction_reward",
            amount=reward_amount,
            balance_before=0,
            balance_after=reward_amount,
            related_type="prediction",
            related_id=prediction_id,
            description=f"猜对「{prediction.title}」获得奖励",
            created_at=now
        )
        
        db.add(transaction)
        db.commit()
        
        return {
            "success": True,
            "reward": reward_amount,
            "vote": self._vote_to_dict(vote),
            "transaction": {
                "id": transaction.id,
                "type": transaction.transaction_type,
                "amount": transaction.amount,
                "description": transaction.description,
                "created_at": transaction.created_at.isoformat()
            }
        }
    
    def get_user_predictions_history(
        self,
        db: Session,
        user_id: int,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        获取用户的预测历史
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            limit: 限制数量
            
        Returns:
            预测历史列表
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
    
    def calculate_actual_result_from_snapshot(
        self,
        db: Session,
        prediction_type: str,
        snapshot: Dict[str, Any]
    ) -> Optional[str]:
        """
        根据能量快照计算实际结果
        
        Args:
            db: 数据库会话
            prediction_type: 预测类型
            snapshot: 能量快照数据
            
        Returns:
            实际结果值
        """
        if prediction_type == "mood":
            score = snapshot.get("overall_energy_score", 50.0)
            if score >= 75:
                return "sunny"
            elif score >= 50:
                return "cloudy"
            elif score >= 30:
                return "overcast"
            else:
                return "stormy"
        
        elif prediction_type == "dominant_planet":
            dominant_planets = snapshot.get("dominant_planets", [])
            if dominant_planets:
                top_planet = dominant_planets[0].get("planet", "")
                planet_map = {
                    "太阳": "sun",
                    "月亮": "moon",
                    "水星": "mercury",
                    "金星": "venus",
                    "火星": "mars",
                    "木星": "jupiter",
                    "土星": "saturn"
                }
                return planet_map.get(top_planet)
        
        elif prediction_type == "social_event":
            dimensions = snapshot.get("dimension_energies", [])
            if dimensions:
                sorted_dims = sorted(dimensions, key=lambda x: x.get("score", 0), reverse=True)
                top_dim = sorted_dims[0].get("dimension", "")
                return top_dim
        
        elif prediction_type == "aspect_pattern":
            aspect_stats = snapshot.get("aspect_stats", {})
            harmonious = aspect_stats.get("harmonious", 0)
            challenging = aspect_stats.get("challenging", 0)
            
            total = harmonious + challenging
            if total == 0:
                return "balanced"
            
            harmonious_ratio = harmonious / total
            
            if harmonious_ratio > 0.6:
                return "harmonious"
            elif harmonious_ratio < 0.4:
                return "challenging"
            else:
                return "balanced"
        
        return None
    
    def _prediction_to_dict(self, prediction: CollectivePrediction) -> Dict[str, Any]:
        """将预测转换为字典"""
        now = datetime.utcnow()
        status = prediction.status
        
        if status == "open" and prediction.target_date:
            try:
                target_date = datetime.strptime(prediction.target_date, "%Y-%m-%d")
                if target_date.date() <= now.date():
                    status = "closed"
            except:
                pass
        
        options = json.loads(prediction.options) if prediction.options else {}
        vote_distribution = json.loads(prediction.vote_distribution) if prediction.vote_distribution else {}
        
        return {
            "id": prediction.id,
            "prediction_date": prediction.prediction_date,
            "target_date": prediction.target_date,
            
            "title": prediction.title,
            "description": prediction.description,
            "prediction_type": prediction.prediction_type,
            
            "options": options.get("labels", []),
            "option_values": options.get("values", []),
            
            "total_votes": prediction.total_votes or 0,
            "vote_distribution": vote_distribution,
            
            "status": status,
            "is_resolved": prediction.is_resolved or False,
            "resolved_at": prediction.resolved_at.isoformat() if prediction.resolved_at else None,
            
            "actual_result": prediction.actual_result,
            "accuracy_score": prediction.accuracy_score,
            
            "total_stardust_pool": prediction.total_stardust_pool or 0,
            
            "created_at": prediction.created_at.isoformat() if prediction.created_at else None,
            "updated_at": prediction.updated_at.isoformat() if prediction.updated_at else None
        }
    
    def _vote_to_dict(self, vote: PredictionVote) -> Dict[str, Any]:
        """将投票记录转换为字典"""
        return {
            "id": vote.id,
            "prediction_id": vote.prediction_id,
            "user_id": vote.user_id,
            
            "selected_option": vote.selected_option,
            "confidence": vote.confidence,
            "stardust_bet": vote.stardust_bet or 0,
            
            "is_correct": vote.is_correct,
            "reward_earned": vote.reward_earned or 0,
            "reward_claimed": vote.reward_claimed or False,
            
            "created_at": vote.created_at.isoformat() if vote.created_at else None,
            
            "vote_data": json.loads(vote.vote_data) if vote.vote_data else None
        }


prediction_service = PredictionService()


def get_prediction_service() -> PredictionService:
    """获取预测服务单例"""
    return prediction_service
