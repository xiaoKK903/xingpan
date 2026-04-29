import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum

from app.config import settings

logger = logging.getLogger(__name__)


class Dimension(str, Enum):
    COMMUNICATION = "communication"
    SOCIAL = "social"
    CAREER = "career"
    WEALTH = "wealth"
    EMOTION = "emotion"


DIMENSION_CONFIG = {
    Dimension.COMMUNICATION: {
        "name": "沟通",
        "name_cn": "沟通",
        "icon": "💬",
        "color": "#60a5fa",
        "planets": ["水星", "木星", "太阳"],
        "houses": [3, 9, 11],
        "weight": 1.0
    },
    Dimension.SOCIAL: {
        "name": "社交",
        "name_cn": "社交",
        "icon": "👥",
        "color": "#f472b6",
        "planets": ["金星", "月亮", "木星"],
        "houses": [7, 11, 5],
        "weight": 1.0
    },
    Dimension.CAREER: {
        "name": "事业",
        "name_cn": "事业",
        "icon": "💼",
        "color": "#f97316",
        "planets": ["太阳", "土星", "火星", "木星"],
        "houses": [10, 6, 1],
        "weight": 1.0
    },
    Dimension.WEALTH: {
        "name": "财运",
        "name_cn": "财运",
        "icon": "💰",
        "color": "#eab308",
        "planets": ["金星", "木星", "土星"],
        "houses": [2, 8, 5],
        "weight": 1.0
    },
    Dimension.EMOTION: {
        "name": "情绪",
        "name_cn": "情绪",
        "icon": "❤️",
        "color": "#ec4899",
        "planets": ["月亮", "金星", "海王星"],
        "houses": [4, 8, 12],
        "weight": 1.0
    }
}


class EnergyLevel(str, Enum):
    HIGH = "high"
    MEDIUM_HIGH = "medium_high"
    MEDIUM = "medium"
    MEDIUM_LOW = "medium_low"
    LOW = "low"


ENERGY_LEVEL_LABELS = {
    EnergyLevel.HIGH: "旺盛",
    EnergyLevel.MEDIUM_HIGH: "活跃",
    EnergyLevel.MEDIUM: "平稳",
    EnergyLevel.MEDIUM_LOW: "低迷",
    EnergyLevel.LOW: "停滞"
}


class AspectNature(str, Enum):
    HARMONIOUS = "harmonious"
    CHALLENGING = "challenging"
    NEUTRAL = "neutral"


class EnergyScoringEngine:
    """
    能量打分引擎 - 基于相位和维度计算能量分数
    
    职责：
    - 分析相位对各维度的影响
    - 计算各维度能量分数
    - 计算整体能量指数
    - 生成能量趋势预测
    """
    
    def __init__(self):
        self._base_score = 50
        self._harmonious_multiplier = 15.0
        self._challenging_multiplier = 12.0
        self._neutral_multiplier = 5.0
        
        self._aspect_nature_map = {
            "合相": AspectNature.NEUTRAL,
            "六分相": AspectNature.HARMONIOUS,
            "四分相": AspectNature.CHALLENGING,
            "三分相": AspectNature.HARMONIOUS,
            "对分相": AspectNature.CHALLENGING
        }
    
    def get_aspect_nature(self, aspect_name: str) -> AspectNature:
        """获取相位的性质（和谐/紧张/中性）"""
        return self._aspect_nature_map.get(aspect_name, AspectNature.NEUTRAL)
    
    def _is_planet_relevant_to_dimension(
        self,
        planet_name: str,
        dimension: Dimension
    ) -> bool:
        """检查行星是否与特定维度相关"""
        dim_config = DIMENSION_CONFIG.get(dimension)
        if not dim_config:
            return False
        return planet_name in dim_config.get("planets", [])
    
    def _is_house_relevant_to_dimension(
        self,
        house_number: int,
        dimension: Dimension
    ) -> bool:
        """检查宫位是否与特定维度相关"""
        dim_config = DIMENSION_CONFIG.get(dimension)
        if not dim_config:
            return False
        return house_number in dim_config.get("houses", [])
    
    def _calculate_relevance_score(
        self,
        aspect: Dict[str, Any],
        dimension: Dimension
    ) -> float:
        """
        计算相位对特定维度的相关度分数
        
        返回值：
        - 0.0: 不相关
        - 0.5: 部分相关（一个行星相关）
        - 1.0: 高度相关（两个行星都相关）
        """
        natal_involved = self._is_planet_relevant_to_dimension(
            aspect.get("natal_planet", aspect.get("planet1_name", "")),
            dimension
        )
        transit_involved = self._is_planet_relevant_to_dimension(
            aspect.get("transit_planet", aspect.get("planet2_name", "")),
            dimension
        )
        
        if natal_involved and transit_involved:
            return 1.0
        elif natal_involved or transit_involved:
            return 0.5
        else:
            return 0.0
    
    def calculate_dimension_energy(
        self,
        aspects: List[Dict[str, Any]],
        dimension: Dimension,
        natal_planets: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        计算特定维度的能量分数
        
        Args:
            aspects: 相位列表
            dimension: 维度枚举
            natal_planets: 本命盘行星列表（可选，用于高级分析）
            
        Returns:
            维度能量数据
        """
        dim_config = DIMENSION_CONFIG.get(dimension)
        if not dim_config:
            raise ValueError(f"未知的维度: {dimension}")
        
        base_score = self._base_score
        harmonious_bonus = 0.0
        challenging_penalty = 0.0
        
        relevant_aspects = []
        planet_influences = {}
        
        for aspect in aspects:
            relevance = self._calculate_relevance_score(aspect, dimension)
            
            if relevance <= 0:
                continue
            
            influence = aspect.get("influence", 0.5) * relevance
            
            aspect_name = aspect.get("aspect", aspect.get("name", ""))
            nature = aspect.get("nature", self.get_aspect_nature(aspect_name).value)
            
            planet_key = aspect.get(
                "transit_planet",
                aspect.get("planet2_name", "未知")
            )
            
            if planet_key not in planet_influences:
                planet_influences[planet_key] = {
                    "harmonious": 0,
                    "challenging": 0,
                    "neutral": 0
                }
            
            if nature == AspectNature.HARMONIOUS.value or nature == "harmonious":
                harmonious_bonus += influence * self._harmonious_multiplier
                planet_influences[planet_key]["harmonious"] += influence
                relevant_aspects.append(aspect)
            elif nature == AspectNature.CHALLENGING.value or nature == "challenging":
                challenging_penalty += influence * self._challenging_multiplier
                planet_influences[planet_key]["challenging"] += influence
                relevant_aspects.append(aspect)
            else:
                base_score += influence * self._neutral_multiplier
                planet_influences[planet_key]["neutral"] += influence
                relevant_aspects.append(aspect)
        
        weight = dim_config.get("weight", 1.0)
        raw_score = base_score + harmonious_bonus - challenging_penalty
        energy_score = max(0, min(100, raw_score * weight))
        
        level, level_label, description = self._get_energy_level(
            energy_score, dim_config["name_cn"]
        )
        
        dominant_influence = AspectNature.NEUTRAL.value
        if harmonious_bonus > challenging_penalty * 1.5:
            dominant_influence = AspectNature.HARMONIOUS.value
        elif challenging_penalty > harmonious_bonus * 1.5:
            dominant_influence = AspectNature.CHALLENGING.value
        
        return {
            "dimension": dimension.value,
            "name": dim_config["name"],
            "name_cn": dim_config["name_cn"],
            "icon": dim_config["icon"],
            "color": dim_config["color"],
            "score": round(energy_score, 1),
            "raw_score": round(raw_score, 2),
            "level": level,
            "level_label": level_label,
            "description": description,
            "harmonious_bonus": round(harmonious_bonus, 2),
            "challenging_penalty": round(challenging_penalty, 2),
            "dominant_influence": dominant_influence,
            "relevant_aspects_count": len(relevant_aspects),
            "planet_influences": planet_influences
        }
    
    def _get_energy_level(
        self,
        score: float,
        dimension_name: str
    ) -> tuple:
        """根据分数获取能量等级"""
        if score >= 80:
            return (
                EnergyLevel.HIGH.value,
                ENERGY_LEVEL_LABELS[EnergyLevel.HIGH],
                f"{dimension_name}能量非常旺盛，适合积极行动和把握机遇。"
            )
        elif score >= 60:
            return (
                EnergyLevel.MEDIUM_HIGH.value,
                ENERGY_LEVEL_LABELS[EnergyLevel.MEDIUM_HIGH],
                f"{dimension_name}能量较为活跃，保持专注可获得良好成果。"
            )
        elif score >= 40:
            return (
                EnergyLevel.MEDIUM.value,
                ENERGY_LEVEL_LABELS[EnergyLevel.MEDIUM],
                f"{dimension_name}能量平稳，适合按部就班推进计划。"
            )
        elif score >= 20:
            return (
                EnergyLevel.MEDIUM_LOW.value,
                ENERGY_LEVEL_LABELS[EnergyLevel.MEDIUM_LOW],
                f"{dimension_name}能量较低，需要更多耐心和调整。"
            )
        else:
            return (
                EnergyLevel.LOW.value,
                ENERGY_LEVEL_LABELS[EnergyLevel.LOW],
                f"{dimension_name}能量停滞，建议休息蓄力，等待时机。"
            )
    
    def calculate_all_dimensions(
        self,
        aspects: List[Dict[str, Any]],
        natal_planets: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """计算所有维度的能量分数"""
        results = []
        for dimension in Dimension:
            dim_energy = self.calculate_dimension_energy(
                aspects, dimension, natal_planets
            )
            results.append(dim_energy)
        return results
    
    def calculate_overall_energy(
        self,
        dimensions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        计算整体能量指数
        
        Args:
            dimensions: 各维度能量数据列表
            
        Returns:
            整体能量数据
        """
        if not dimensions:
            return {
                "overall_score": 50.0,
                "mood": "⛅",
                "mood_label": "多云",
                "description": "暂无足够数据计算整体运势。",
                "high_dimensions": [],
                "low_dimensions": [],
                "harmonious_dominant": 0,
                "challenging_dominant": 0
            }
        
        total_score = sum(d["score"] for d in dimensions)
        avg_score = total_score / len(dimensions)
        
        high_dims = [d for d in dimensions if d["level"] in [
            EnergyLevel.HIGH.value,
            EnergyLevel.MEDIUM_HIGH.value
        ]]
        low_dims = [d for d in dimensions if d["level"] in [
            EnergyLevel.LOW.value,
            EnergyLevel.MEDIUM_LOW.value
        ]]
        
        harmonious_count = sum(
            1 for d in dimensions 
            if d["dominant_influence"] == AspectNature.HARMONIOUS.value
        )
        challenging_count = sum(
            1 for d in dimensions 
            if d["dominant_influence"] == AspectNature.CHALLENGING.value
        )
        
        mood, mood_label, description = self._get_overall_mood(avg_score)
        
        return {
            "overall_score": round(avg_score, 1),
            "mood": mood,
            "mood_label": mood_label,
            "description": description,
            "high_dimensions": [d["name_cn"] for d in high_dims],
            "low_dimensions": [d["name_cn"] for d in low_dims],
            "harmonious_dominant": harmonious_count,
            "challenging_dominant": challenging_count
        }
    
    def _get_overall_mood(self, avg_score: float) -> tuple:
        """根据平均分数获取整体情绪状态（类似天气预报）"""
        if avg_score >= 75:
            return (
                "☀️",
                "晴朗",
                "今日星象晴朗，能量充沛，适合积极行动。"
            )
        elif avg_score >= 60:
            return (
                "⛅",
                "多云",
                "今日星象多云，能量适中，保持稳健即可。"
            )
        elif avg_score >= 40:
            return (
                "🌤️",
                "晴间多云",
                "今日星象有起伏，需灵活应对变化。"
            )
        elif avg_score >= 25:
            return (
                "🌥️",
                "阴天",
                "今日星象阴沉，能量较低，建议调整节奏。"
            )
        else:
            return (
                "🌧️",
                "雷雨",
                "今日星象动荡，建议谨慎行事，避免冲动决策。"
            )
    
    def analyze_energy_trend(
        self,
        daily_dimensions: List[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        分析多日能量趋势
        
        Args:
            daily_dimensions: 每日维度数据列表
            
        Returns:
            趋势分析结果
        """
        if not daily_dimensions:
            return {"error": "没有数据可分析"}
        
        overall_scores = []
        dimension_trends = {dim.value: [] for dim in Dimension}
        
        for day_dims in daily_dimensions:
            overall = self.calculate_overall_energy(day_dims)
            overall_scores.append(overall["overall_score"])
            
            for dim in day_dims:
                dim_key = dim["dimension"]
                if dim_key in dimension_trends:
                    dimension_trends[dim_key].append(dim["score"])
        
        max_score = max(overall_scores) if overall_scores else 50
        min_score = min(overall_scores) if overall_scores else 50
        avg_score = sum(overall_scores) / len(overall_scores) if overall_scores else 50
        
        turning_points = []
        for i in range(1, len(overall_scores) - 1):
            prev = overall_scores[i - 1]
            curr = overall_scores[i]
            next_score = overall_scores[i + 1]
            
            if (curr > prev and curr > next_score):
                turning_points.append({
                    "index": i,
                    "type": "peak",
                    "score": curr
                })
            elif (curr < prev and curr < next_score):
                turning_points.append({
                    "index": i,
                    "type": "valley",
                    "score": curr
                })
        
        return {
            "overall_scores": overall_scores,
            "dimension_trends": dimension_trends,
            "summary": {
                "max_score": round(max_score, 1),
                "min_score": round(min_score, 1),
                "avg_score": round(avg_score, 1),
                "turning_points": turning_points,
                "trend_direction": "up" if overall_scores[-1] > overall_scores[0] else "down" if overall_scores[-1] < overall_scores[0] else "stable"
            }
        }
    
    def generate_suggestions(
        self,
        overall_energy: Dict[str, Any],
        dimensions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        基于能量数据生成建议
        
        Args:
            overall_energy: 整体能量数据
            dimensions: 各维度能量数据
            
        Returns:
            建议数据
        """
        high_dims = [d for d in dimensions if d["level"] in [
            EnergyLevel.HIGH.value,
            EnergyLevel.MEDIUM_HIGH.value
        ]]
        low_dims = [d for d in dimensions if d["level"] in [
            EnergyLevel.LOW.value,
            EnergyLevel.MEDIUM_LOW.value
        ]]
        
        opportunities = []
        challenges = []
        suggestions = []
        
        for dim in high_dims:
            opportunities.append(
                f"在{dim['name_cn']}领域积极行动，利用当前能量优势"
            )
        
        for dim in low_dims:
            challenges.append(
                f"{dim['name_cn']}领域需要更多注意，保持耐心"
            )
        
        overall_score = overall_energy.get("overall_score", 50)
        
        if overall_score >= 70:
            suggestions.extend([
                "把握今日能量高峰，处理重要事务",
                "主动出击，创造机会",
                "保持积极心态，扩大影响力"
            ])
        elif overall_score >= 50:
            suggestions.extend([
                "保持稳健节奏，按计划推进",
                "关注细节，稳步前进",
                "适当休息，保持平衡"
            ])
        else:
            suggestions.extend([
                "调整节奏，给自己更多缓冲时间",
                "优先处理必要事务，避免重大决策",
                "注重休息和恢复，为未来蓄力"
            ])
        
        return {
            "opportunities": opportunities[:3],
            "challenges": challenges[:3],
            "suggestions": suggestions[:4]
        }


energy_scoring_engine = EnergyScoringEngine()


def get_energy_scoring_engine() -> EnergyScoringEngine:
    """获取能量打分引擎单例"""
    return energy_scoring_engine


DIMENSION_INFO = {dim: DIMENSION_CONFIG[dim] for dim in Dimension}
