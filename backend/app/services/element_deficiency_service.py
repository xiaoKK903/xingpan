import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import random

logger = logging.getLogger(__name__)


class Element(str, Enum):
    FIRE = "fire"
    EARTH = "earth"
    AIR = "air"
    WATER = "water"


class EnergyLevel(str, Enum):
    ABUNDANT = "abundant"
    STRONG = "strong"
    BALANCED = "balanced"
    WEAK = "weak"
    DEFICIENT = "deficient"


class AspectType(str, Enum):
    CONJUNCTION = "合相"
    SEXTILE = "六分相"
    SQUARE = "四分相"
    TRINE = "三分相"
    OPPOSITION = "对分相"


ELEMENT_ENERGY_CONFIG = {
    "base_score_per_planet": 20.0,
    "ascendant_bonus": 12.0,
    "retrograde_factor": 0.7,
    "max_element_score": 150.0,
    "min_element_score": 0.0,
}

PLANET_WEIGHTS = {
    "太阳": 1.6,
    "月亮": 1.5,
    "水星": 1.0,
    "金星": 1.1,
    "火星": 1.2,
    "木星": 1.4,
    "土星": 1.3,
    "天王星": 1.0,
    "海王星": 1.0,
    "冥王星": 1.1,
}

HOUSE_WEIGHTS = {
    1: 1.3,
    4: 1.2,
    7: 1.2,
    10: 1.3,
    5: 1.0,
    8: 1.0,
    11: 1.0,
    2: 0.9,
    3: 0.9,
    6: 0.9,
    9: 0.9,
    12: 0.9,
}

ASPECT_CONFIG = {
    AspectType.CONJUNCTION: {
        "same_element_multiplier": 1.5,
        "diff_element_multiplier": 1.0,
        "base_bonus": 6.0,
        "description": "融合增强",
    },
    AspectType.SEXTILE: {
        "same_element_multiplier": 1.3,
        "diff_element_multiplier": 0.9,
        "base_bonus": 4.0,
        "description": "和谐流动",
    },
    AspectType.SQUARE: {
        "same_element_multiplier": 1.2,
        "diff_element_multiplier": 0.3,
        "base_bonus": 2.0,
        "description": "张力激发",
    },
    AspectType.TRINE: {
        "same_element_multiplier": 1.4,
        "diff_element_multiplier": 1.1,
        "base_bonus": 5.0,
        "description": "顺畅增益",
    },
    AspectType.OPPOSITION: {
        "same_element_multiplier": 1.1,
        "diff_element_multiplier": 0.4,
        "base_bonus": 2.0,
        "description": "对立平衡",
    },
}

ENERGY_LEVEL_THRESHOLDS = {
    EnergyLevel.ABUNDANT: {
        "min_score": 70.0,
        "label": "充沛",
        "description": "能量非常充沛，该元素特质明显",
    },
    EnergyLevel.STRONG: {
        "min_score": 50.0,
        "label": "旺盛",
        "description": "能量旺盛，该元素特质较强",
    },
    EnergyLevel.BALANCED: {
        "min_score": 30.0,
        "label": "平衡",
        "description": "能量平衡，该元素特质适中",
    },
    EnergyLevel.WEAK: {
        "min_score": 15.0,
        "label": "微弱",
        "description": "能量微弱，该元素特质较弱",
    },
    EnergyLevel.DEFICIENT: {
        "min_score": 0.0,
        "label": "缺角",
        "description": "能量缺角，该元素特质需要补充",
    },
}

ZODIAC_TO_ELEMENT = {
    "白羊座": Element.FIRE,
    "狮子座": Element.FIRE,
    "射手座": Element.FIRE,
    "金牛座": Element.EARTH,
    "处女座": Element.EARTH,
    "摩羯座": Element.EARTH,
    "双子座": Element.AIR,
    "天秤座": Element.AIR,
    "水瓶座": Element.AIR,
    "巨蟹座": Element.WATER,
    "天蝎座": Element.WATER,
    "双鱼座": Element.WATER,
}

ELEMENT_INFO = {
    Element.FIRE: {
        "name": "火",
        "name_cn": "火元素",
        "symbol": "🔥",
        "color": "#EF4444",
        "zodiacs": ["白羊座", "狮子座", "射手座"],
        "keywords": ["热情", "行动", "创造力", "领导力", "勇气"],
        "description": "代表能量、热情和行动力的元素",
    },
    Element.EARTH: {
        "name": "土",
        "name_cn": "土元素",
        "symbol": "🪨",
        "color": "#A16207",
        "zodiacs": ["金牛座", "处女座", "摩羯座"],
        "keywords": ["稳定", "务实", "耐心", "物质", "安全感"],
        "description": "代表稳定、务实和物质世界的元素",
    },
    Element.AIR: {
        "name": "风",
        "name_cn": "风元素",
        "symbol": "💨",
        "color": "#3B82F6",
        "zodiacs": ["双子座", "天秤座", "水瓶座"],
        "keywords": ["思维", "沟通", "社交", "理性", "自由"],
        "description": "代表思维、沟通和社交的元素",
    },
    Element.WATER: {
        "name": "水",
        "name_cn": "水元素",
        "symbol": "💧",
        "color": "#06B6D4",
        "zodiacs": ["巨蟹座", "天蝎座", "双鱼座"],
        "keywords": ["情感", "直觉", "同理心", "深层意识", "创造力"],
        "description": "代表情感、直觉和深层意识的元素",
    },
}

DEFICIENCY_DESCRIPTIONS = {
    Element.FIRE: {
        "short_term": "可能感到缺乏动力，行动迟缓，难以发起新项目",
        "long_term": "长期可能缺乏自信，害怕承担风险，回避领导角色",
        "suggestions": [
            "培养体育运动习惯，激发身体能量",
            "设定小目标，逐步建立成就感",
            "穿着暖色调衣物（红、橙、黄）",
            "多接触阳光，增加户外活动",
        ],
    },
    Element.EARTH: {
        "short_term": "可能感到不稳定，难以专注，财务计划容易混乱",
        "long_term": "长期可能缺乏安全感，难以坚持长期目标，容易焦虑",
        "suggestions": [
            "建立规律的作息习惯",
            "制定详细的财务计划并执行",
            "多接触自然，园艺或徒步",
            "使用水晶或石头进行能量平衡",
        ],
    },
    Element.AIR: {
        "short_term": "可能感到思维混乱，沟通困难，社交退缩",
        "long_term": "长期可能缺乏理性分析能力，难以做出明智决策",
        "suggestions": [
            "每天进行冥想或静心练习",
            "阅读和写作，训练思维清晰度",
            "参加社交活动，练习表达",
            "学习新技能，保持思维活跃",
        ],
    },
    Element.WATER: {
        "short_term": "可能感到情感麻木，难以共情，直觉迟钝",
        "long_term": "长期可能与深层情感疏离，创造力枯竭",
        "suggestions": [
            "练习情绪日记，关注内心感受",
            "进行艺术创作（绘画、音乐、写作）",
            "多靠近水（湖泊、海洋、温泉）",
            "培养同理心，倾听他人故事",
        ],
    },
}

ENERGY_LEVEL_LABELS = {
    "abundant": "充沛",
    "strong": "旺盛",
    "balanced": "平衡",
    "weak": "微弱",
    "deficient": "缺角",
}


@dataclass
class ElementEnergy:
    element: Element
    score: float
    level: EnergyLevel
    planets: List[Dict[str, Any]] = field(default_factory=list)
    aspects: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class EnergyTag:
    key: str
    name: str
    category: str
    score: float
    description: str


class ElementDeficiencyService:
    """
    元素缺角服务 - 分析星盘四元素能量分布，识别缺角

    核心功能：
    1. 计算四元素能量分数（行星基础分数 + 相位影响）
    2. 基于绝对分数区间判定能量等级
    3. 生成能量标签
    4. 提供互补匹配建议

    计算规则：
    - 每个行星根据所在星座元素获得基础分数
    - 行星权重 * 宫位权重 * 逆行系数（如果逆行）
    - 同元素相位增强该元素能量
    - 不同元素相位弱增强或不增强
    - 所有相位均参与计算，无负分
    - 上升点给予额外加成
    """

    def __init__(self):
        self._base_score = ELEMENT_ENERGY_CONFIG["base_score_per_planet"]
        self._ascendant_bonus = ELEMENT_ENERGY_CONFIG["ascendant_bonus"]
        self._retrograde_factor = ELEMENT_ENERGY_CONFIG["retrograde_factor"]
        self._max_score = ELEMENT_ENERGY_CONFIG["max_element_score"]
        self._min_score = ELEMENT_ENERGY_CONFIG["min_element_score"]

        self._planet_weights = PLANET_WEIGHTS
        self._house_weights = HOUSE_WEIGHTS
        self._aspect_config = ASPECT_CONFIG
        self._zodiac_to_element = ZODIAC_TO_ELEMENT
        self._deficiency_descriptions = DEFICIENCY_DESCRIPTIONS

    def _get_element_for_zodiac(self, zodiac_name: str) -> Optional[Element]:
        """根据星座名称获取对应元素"""
        return self._zodiac_to_element.get(zodiac_name)

    def _get_planet_weight(self, planet_name: str) -> float:
        """获取行星权重"""
        return self._planet_weights.get(planet_name, 1.0)

    def _get_house_weight(self, house_number: int) -> float:
        """获取宫位权重"""
        return self._house_weights.get(house_number, 1.0)

    def _get_aspect_config(self, aspect_name: str) -> Dict[str, Any]:
        """获取相位配置"""
        try:
            aspect_type = AspectType(aspect_name)
            return self._aspect_config.get(aspect_type, {})
        except ValueError:
            return {}

    def _calculate_energy_level(self, score: float) -> Tuple[EnergyLevel, Dict[str, Any]]:
        """
        根据绝对分数计算能量等级

        使用绝对分数区间而非相对平均分，保证结果稳定。
        """
        thresholds = ENERGY_LEVEL_THRESHOLDS

        if score >= thresholds[EnergyLevel.ABUNDANT]["min_score"]:
            return EnergyLevel.ABUNDANT, thresholds[EnergyLevel.ABUNDANT]
        elif score >= thresholds[EnergyLevel.STRONG]["min_score"]:
            return EnergyLevel.STRONG, thresholds[EnergyLevel.STRONG]
        elif score >= thresholds[EnergyLevel.BALANCED]["min_score"]:
            return EnergyLevel.BALANCED, thresholds[EnergyLevel.BALANCED]
        elif score >= thresholds[EnergyLevel.WEAK]["min_score"]:
            return EnergyLevel.WEAK, thresholds[EnergyLevel.WEAK]
        else:
            return EnergyLevel.DEFICIENT, thresholds[EnergyLevel.DEFICIENT]

    def _clamp_score(self, score: float) -> float:
        """限制分数在有效范围内，确保无负分"""
        return max(self._min_score, min(self._max_score, score))

    def _calculate_planet_contribution(
        self, planet: Dict[str, Any]
    ) -> Tuple[Optional[Element], float, Dict[str, Any]]:
        """
        计算单个行星对元素能量的贡献

        返回: (元素, 分数, 详情)

        注意：中间阶段不进行 clamp，只在最终汇总后进行软约束，
        以保留真实的能量分布曲线。
        """
        zodiac_name = planet.get("zodiac", {}).get("sign", "")
        element = self._get_element_for_zodiac(zodiac_name)

        if not element:
            return None, 0.0, {}

        planet_name = planet.get("name", "")
        house = planet.get("house", 6)

        base_score = self._base_score
        planet_weight = self._get_planet_weight(planet_name)
        house_weight = self._get_house_weight(house)

        is_retrograde = planet.get("is_retrograde", False)
        retrograde_factor = self._retrograde_factor if is_retrograde else 1.0

        final_score = base_score * planet_weight * house_weight * retrograde_factor

        detail = {
            "name": planet_name,
            "zodiac": zodiac_name,
            "house": house,
            "score_contribution": round(final_score, 2),
            "is_retrograde": is_retrograde,
            "planet_weight": planet_weight,
            "house_weight": house_weight,
        }

        return element, final_score, detail

    def _calculate_aspect_contribution(
        self,
        aspect: Dict[str, Any],
        planet_map: Dict[str, Dict[str, Any]],
    ) -> List[Tuple[Element, float, Dict[str, Any]]]:
        """
        计算相位对元素能量的贡献

        规则：
        1. 同元素相位：增强该元素能量（乘数较高）
        2. 不同元素相位：弱增强或不增强（乘数较低）
        3. 所有相位均参与计算，无负分
        4. 刑相、对分相等挑战相位改为低加分而非负分

        性能优化：使用 planet_map 字典进行 O(1) 查找，避免 O(n) 线性扫描
        """
        results = []

        planet1_name = aspect.get("planet1", "")
        planet2_name = aspect.get("planet2", "")
        aspect_name = aspect.get("aspect", "")
        orb = aspect.get("orb", 0.0)

        planet1 = planet_map.get(planet1_name)
        planet2 = planet_map.get(planet2_name)

        if not planet1 or not planet2:
            return results

        zodiac1 = planet1.get("zodiac", {}).get("sign", "")
        zodiac2 = planet2.get("zodiac", {}).get("sign", "")

        element1 = self._get_element_for_zodiac(zodiac1)
        element2 = self._get_element_for_zodiac(zodiac2)

        aspect_config = self._get_aspect_config(aspect_name)
        if not aspect_config:
            return results

        base_bonus = aspect_config.get("base_bonus", 0.0)

        orb_factor = max(0.5, 1.0 - (orb / 10.0))

        if element1 and element2:
            if element1 == element2:
                multiplier = aspect_config.get("same_element_multiplier", 1.0)
                aspect_score = base_bonus * multiplier * orb_factor

                detail = {
                    "aspect": aspect_name,
                    "aspect_type": "same_element",
                    "with_planet": planet2_name,
                    "score_contribution": round(aspect_score, 2),
                    "multiplier": multiplier,
                    "description": aspect_config.get("description", ""),
                }
                results.append((element1, aspect_score, detail))

            else:
                multiplier = aspect_config.get("diff_element_multiplier", 0.0)
                if multiplier > 0:
                    aspect_score_1 = base_bonus * multiplier * orb_factor

                    detail1 = {
                        "aspect": aspect_name,
                        "aspect_type": "diff_element",
                        "with_planet": planet2_name,
                        "score_contribution": round(aspect_score_1, 2),
                        "multiplier": multiplier,
                        "description": aspect_config.get("description", ""),
                    }
                    results.append((element1, aspect_score_1, detail1))

                    aspect_score_2 = base_bonus * multiplier * orb_factor

                    detail2 = {
                        "aspect": aspect_name,
                        "aspect_type": "diff_element",
                        "with_planet": planet1_name,
                        "score_contribution": round(aspect_score_2, 2),
                        "multiplier": multiplier,
                        "description": aspect_config.get("description", ""),
                    }
                    results.append((element2, aspect_score_2, detail2))

        return results

    def calculate_element_energies(
        self, chart_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        计算星盘的四元素能量分布

        计算流程：
        1. 初始化四元素分数为0
        2. 遍历所有行星，计算每个行星对元素的贡献
        3. 遍历所有相位，计算相位对元素的增强（同元素强增强，不同元素弱增强）
        4. 添加上升点加成
        5. 计算能量等级（基于绝对分数区间）
        6. 生成分析结果

        性能优化：
        - 创建 planet_map 字典用于 O(1) 行星查找
        - 移除中间阶段的 clamp，只在最终阶段进行软约束

        Args:
            chart_data: 星盘数据，包含 planets, ascendant, aspects 等

        Returns:
            四元素能量分析结果
        """
        planets = chart_data.get("planets", [])
        aspects = chart_data.get("aspects", [])
        ascendant = chart_data.get("ascendant", {})

        planet_map = {p.get("name", ""): p for p in planets if p.get("name")}

        element_scores = {
            Element.FIRE: {"score": 0.0, "planets": [], "aspects": []},
            Element.EARTH: {"score": 0.0, "planets": [], "aspects": []},
            Element.AIR: {"score": 0.0, "planets": [], "aspects": []},
            Element.WATER: {"score": 0.0, "planets": [], "aspects": []},
        }

        for planet in planets:
            element, score, detail = self._calculate_planet_contribution(planet)
            if element and score > 0:
                element_scores[element]["score"] += score
                element_scores[element]["planets"].append(detail)

        for aspect in aspects:
            contributions = self._calculate_aspect_contribution(aspect, planet_map)
            for element, score, detail in contributions:
                if score > 0:
                    element_scores[element]["score"] += score
                    element_scores[element]["aspects"].append(detail)

        asc_zodiac = ascendant.get("sign", "")
        if asc_zodiac:
            asc_element = self._get_element_for_zodiac(asc_zodiac)
            if asc_element:
                element_scores[asc_element]["score"] += self._ascendant_bonus
                element_scores[asc_element]["planets"].append({
                    "name": "上升点",
                    "zodiac": asc_zodiac,
                    "house": 1,
                    "score_contribution": round(self._ascendant_bonus, 2),
                    "is_retrograde": False,
                    "planet_weight": 1.0,
                    "house_weight": 1.0,
                })

        for element in element_scores:
            element_scores[element]["score"] = max(
                self._min_score,
                min(self._max_score, element_scores[element]["score"])
            )

        total_score = sum(e["score"] for e in element_scores.values())

        element_energies = {}
        for element, data in element_scores.items():
            level, level_info = self._calculate_energy_level(data["score"])
            element_energies[element.value] = {
                "element": element.value,
                "info": ELEMENT_INFO[element],
                "score": round(data["score"], 2),
                "level": level.value,
                "level_label": level_info["label"],
                "level_description": level_info["description"],
                "planets": data["planets"],
                "aspects": data["aspects"],
                "percentage": round((data["score"] / total_score * 100) if total_score > 0 else 25, 1),
            }

        sorted_elements = sorted(
            element_energies.values(),
            key=lambda x: x["score"],
            reverse=True,
        )

        dominant_elements = sorted_elements[:2]

        deficient_elements = [
            e
            for e in sorted_elements
            if e["level"] == EnergyLevel.DEFICIENT.value
        ]

        if not deficient_elements:
            deficient_elements = [
                e
                for e in sorted_elements
                if e["level"] == EnergyLevel.WEAK.value
            ]

        primary_deficiency = None
        if sorted_elements:
            lowest_element = sorted_elements[-1]
            if (
                lowest_element["level"] == EnergyLevel.DEFICIENT.value
                or lowest_element["level"] == EnergyLevel.WEAK.value
            ):
                primary_deficiency = lowest_element

        deficiency_info = None
        if primary_deficiency:
            def_element = Element(primary_deficiency["element"])
            deficiency_info = {
                "element": def_element.value,
                "info": ELEMENT_INFO[def_element],
                "descriptions": self._deficiency_descriptions.get(def_element, {}),
            }

        return {
            "total_score": round(total_score, 2),
            "average_score": round(total_score / 4, 2) if total_score > 0 else 0,
            "elements": element_energies,
            "sorted_elements": sorted_elements,
            "dominant_elements": dominant_elements,
            "deficient_elements": deficient_elements,
            "primary_deficiency": deficiency_info,
            "has_deficiency": len(deficient_elements) > 0,
            "thresholds": {
                k.value: v for k, v in ENERGY_LEVEL_THRESHOLDS.items()
            },
            "config": {
                "base_score_per_planet": self._base_score,
                "ascendant_bonus": self._ascendant_bonus,
            },
            "calculated_at": datetime.utcnow().isoformat(),
        }

    def generate_energy_tags(
        self, element_analysis: Dict[str, Any]
    ) -> List[EnergyTag]:
        """
        基于元素分析生成用户能量标签
        """
        tags = []

        dominant = element_analysis.get("dominant_elements", [])
        if dominant:
            primary = dominant[0]
            tag = EnergyTag(
                key=f"dominant_{primary['element']}",
                name=f"{primary['info']['name']}元素主导",
                category="dominant",
                score=primary["score"],
                description=f"你的{primary['info']['name_cn']}能量最为充沛",
            )
            tags.append(tag)

        deficient = element_analysis.get("deficient_elements", [])
        for d in deficient:
            tag = EnergyTag(
                key=f"deficient_{d['element']}",
                name=f"{d['info']['name']}元素缺角",
                category="deficient",
                score=d["score"],
                description=f"你的{d['info']['name_cn']}能量需要补充",
            )
            tags.append(tag)

        elements = element_analysis.get("elements", {})
        fire_score = elements.get(Element.FIRE.value, {}).get("score", 0)
        earth_score = elements.get(Element.EARTH.value, {}).get("score", 0)
        air_score = elements.get(Element.AIR.value, {}).get("score", 0)
        water_score = elements.get(Element.WATER.value, {}).get("score", 0)

        max_score = max(fire_score, earth_score, air_score, water_score)

        if max_score > 0:
            if fire_score == max_score:
                tags.append(
                    EnergyTag(
                        key="action_oriented",
                        name="行动派",
                        category="trait",
                        score=fire_score,
                        description="充满热情，行动力强，善于发起新项目",
                    )
                )
            elif earth_score == max_score:
                tags.append(
                    EnergyTag(
                        key="practical",
                        name="务实派",
                        category="trait",
                        score=earth_score,
                        description="脚踏实地，注重实际，善于构建稳固基础",
                    )
                )
            elif air_score == max_score:
                tags.append(
                    EnergyTag(
                        key="intellectual",
                        name="思维派",
                        category="trait",
                        score=air_score,
                        description="思维敏捷，善于沟通，理性分析能力强",
                    )
                )
            elif water_score == max_score:
                tags.append(
                    EnergyTag(
                        key="emotional",
                        name="情感派",
                        category="trait",
                        score=water_score,
                        description="情感丰富，直觉敏锐，富有同理心和创造力",
                    )
                )

        return tags

    def find_complementary_users(
        self,
        user_analysis: Dict[str, Any],
        other_users_data: List[Dict[str, Any]],
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        寻找与用户元素缺角互补的用户
        """
        deficient_elements = user_analysis.get("deficient_elements", [])
        if not deficient_elements:
            sorted_elems = user_analysis.get("sorted_elements", [])
            if sorted_elems:
                deficient_elements = [sorted_elems[-1]]

        if not deficient_elements:
            return []

        deficient_element_keys = [d["element"] for d in deficient_elements]

        matches = []
        for user_data in other_users_data:
            other_analysis = user_data.get("element_analysis", {})
            other_elements = other_analysis.get("elements", {})
            other_dominant = other_analysis.get("dominant_elements", [])

            complement_score = 0.0
            complement_details = []

            for def_elem in deficient_element_keys:
                other_elem_data = other_elements.get(def_elem, {})
                other_score = other_elem_data.get("score", 0)
                other_level = other_elem_data.get("level", "")

                if other_level in [EnergyLevel.ABUNDANT.value, EnergyLevel.STRONG.value]:
                    complement_score += 30.0
                    complement_details.append({
                        "element": def_elem,
                        "match_type": "perfect",
                        "description": f"对方{other_elem_data.get('info', {}).get('name_cn', '')}能量充沛",
                    })
                elif other_level == EnergyLevel.BALANCED.value:
                    complement_score += 15.0
                    complement_details.append({
                        "element": def_elem,
                        "match_type": "good",
                        "description": f"对方{other_elem_data.get('info', {}).get('name_cn', '')}能量平衡",
                    })

            user_dominant = user_analysis.get("dominant_elements", [])
            for dom in user_dominant:
                dom_key = dom["element"]
                other_elem_data = other_elements.get(dom_key, {})
                other_level = other_elem_data.get("level", "")

                if other_level in [EnergyLevel.WEAK.value, EnergyLevel.DEFICIENT.value]:
                    complement_score += 10.0
                    complement_details.append({
                        "element": dom_key,
                        "match_type": "mutual",
                        "description": f"你可以补充对方{other_elem_data.get('info', {}).get('name_cn', '')}能量",
                    })

            if complement_score > 0:
                matches.append({
                    "user_id": user_data.get("user_id"),
                    "username": user_data.get("username"),
                    "avatar_info": user_data.get("avatar_info"),
                    "complement_score": round(complement_score, 2),
                    "complement_details": complement_details,
                    "element_analysis": other_analysis,
                    "match_type": "complementary" if complement_score >= 40 else "partial",
                })

        matches.sort(key=lambda x: x["complement_score"], reverse=True)

        return matches[:limit]

    def generate_blind_box_clues(
        self,
        matched_user: Dict[str, Any],
        current_user_analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        为盲盒匹配生成模糊线索提示
        """
        other_analysis = matched_user.get("element_analysis", {})
        other_elements = other_analysis.get("elements", {})
        complement_details = matched_user.get("complement_details", [])

        clues = []

        perfect_matches = [c for c in complement_details if c.get("match_type") == "perfect"]
        if perfect_matches:
            elem_key = perfect_matches[0].get("element")
            elem_info = ELEMENT_INFO.get(Element(elem_key), {})
            clues.append({
                "type": "element_hint",
                "clue": f"这个人身上带有强烈的{elem_info.get('name', '')}元素气息...",
                "hint_level": "strong",
            })

        mutual_matches = [c for c in complement_details if c.get("match_type") == "mutual"]
        if mutual_matches:
            clues.append({
                "type": "mutual_hint",
                "clue": "你们之间可能存在某种能量上的相互吸引...",
                "hint_level": "subtle",
            })

        other_dominant = other_analysis.get("dominant_elements", [])
        if other_dominant:
            primary_dom = other_dominant[0]
            keywords = primary_dom.get("info", {}).get("keywords", [])
            if keywords:
                random_keyword = random.choice(keywords)
                clues.append({
                    "type": "trait_hint",
                    "clue": f"这个人可能具有'{random_keyword}'的特质...",
                    "hint_level": "subtle",
                })

        other_sorted = other_analysis.get("sorted_elements", [])
        if len(other_sorted) >= 2:
            first = other_sorted[0]
            second = other_sorted[1]
            clues.append({
                "type": "combination_hint",
                "clue": f"这是一位{first['info']['name']}与{second['info']['name']}元素的融合体...",
                "hint_level": "medium",
            })

        deficient = current_user_analysis.get("primary_deficiency")
        if deficient:
            def_elem = deficient.get("element")
            other_def_elem = other_elements.get(def_elem, {})
            other_level = other_def_elem.get("level", "")

            if other_level in [EnergyLevel.ABUNDANT.value, EnergyLevel.STRONG.value]:
                clues.append({
                    "type": "completion_hint",
                    "clue": "这个人可能能够帮助你填补某种能量上的空缺...",
                    "hint_level": "strong",
                })

        random.shuffle(clues)

        selected_clues = clues[:3]

        return {
            "blind_box_id": f"blind_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "matched_user_id": matched_user.get("user_id"),
            "clues": selected_clues,
            "total_clues_available": len(clues),
            "revealed_count": len(selected_clues),
            "complement_score": matched_user.get("complement_score"),
            "created_at": datetime.utcnow().isoformat(),
        }

    def calculate_deficiency_completeness_score(
        self,
        user_analysis: Dict[str, Any],
        match_analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        计算缺角补全分数
        """
        user_elements = user_analysis.get("elements", {})
        match_elements = match_analysis.get("elements", {})

        completeness_scores = {}
        total_completeness = 0.0

        balanced_threshold = ENERGY_LEVEL_THRESHOLDS[EnergyLevel.BALANCED]["min_score"]

        for elem_key in [e.value for e in Element]:
            user_elem = user_elements.get(elem_key, {})
            match_elem = match_elements.get(elem_key, {})

            user_score = user_elem.get("score", 0)
            match_score = match_elem.get("score", 0)

            user_deficit = max(0, balanced_threshold - user_score)
            match_surplus = max(0, match_score - balanced_threshold)

            if user_deficit > 0:
                if match_surplus > 0:
                    fill_ratio = min(1.0, match_surplus / user_deficit)
                    completeness = fill_ratio * 100
                else:
                    completeness = 0.0
            else:
                completeness = 100.0

            completeness_scores[elem_key] = {
                "element": elem_key,
                "info": ELEMENT_INFO.get(Element(elem_key), {}),
                "user_score": user_score,
                "match_score": match_score,
                "user_deficit": round(user_deficit, 2),
                "match_surplus": round(match_surplus, 2),
                "completeness_percentage": round(completeness, 1),
                "is_complete": completeness >= 80.0,
                "balanced_threshold": balanced_threshold,
            }

            total_completeness += completeness

        overall_completeness = total_completeness / 4

        return {
            "overall_completeness": round(overall_completeness, 1),
            "is_fully_complete": overall_completeness >= 80.0,
            "balanced_threshold": balanced_threshold,
            "element_details": completeness_scores,
            "calculated_at": datetime.utcnow().isoformat(),
        }


element_deficiency_service = ElementDeficiencyService()


def get_element_deficiency_service() -> ElementDeficiencyService:
    """获取元素缺角服务单例"""
    return element_deficiency_service
