import logging
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class DignityType(str, Enum):
    RULER = "ruler"
    EXALTATION = "exaltation"
    TRIPLICITY = "triplicity"
    TERM = "term"
    FACE = "face"
    DETRIMENT = "detriment"
    FALL = "fall"


class Element(str, Enum):
    FIRE = "fire"
    EARTH = "earth"
    AIR = "air"
    WATER = "water"


class Quality(str, Enum):
    CARDINAL = "cardinal"
    FIXED = "fixed"
    MUTABLE = "mutable"


ZODIAC_SIGNS = [
    "白羊座", "金牛座", "双子座", "巨蟹座", "狮子座", "处女座",
    "天秤座", "天蝎座", "射手座", "摩羯座", "水瓶座", "双鱼座"
]

ZODIAC_SYMBOLS = [
    "♈", "♉", "♊", "♋", "♌", "♍",
    "♎", "♏", "♐", "♑", "♒", "♓"
]

ELEMENTS = [
    Element.FIRE, Element.EARTH, Element.AIR, Element.WATER,
    Element.FIRE, Element.EARTH, Element.AIR, Element.WATER,
    Element.FIRE, Element.EARTH, Element.AIR, Element.WATER
]

QUALITIES = [
    Quality.CARDINAL, Quality.FIXED, Quality.MUTABLE,
    Quality.CARDINAL, Quality.FIXED, Quality.MUTABLE,
    Quality.CARDINAL, Quality.FIXED, Quality.MUTABLE,
    Quality.CARDINAL, Quality.FIXED, Quality.MUTABLE
]

RULING_PLANETS = {
    0: "火星",
    1: "金星",
    2: "水星",
    3: "月亮",
    4: "太阳",
    5: "水星",
    6: "金星",
    7: "冥王星",
    8: "木星",
    9: "土星",
    10: "天王星",
    11: "海王星"
}

TRADITIONAL_RULING_PLANETS = {
    0: "火星",
    1: "金星",
    2: "水星",
    3: "月亮",
    4: "太阳",
    5: "水星",
    6: "金星",
    7: "火星",
    8: "木星",
    9: "土星",
    10: "土星",
    11: "木星"
}

EXALTATION_PLANETS = {
    0: "太阳",
    1: "月亮",
    2: "水星",
    3: "木星",
    4: "海王星",
    5: "水星",
    6: "土星",
    7: "天王星",
    8: "冥王星",
    9: "火星",
    10: "金星",
    11: "金星"
}

TRADITIONAL_EXALTATION = {
    0: "太阳",
    1: "月亮",
    2: "水星",
    3: "木星",
    4: "无",
    5: "水星",
    6: "土星",
    7: "无",
    8: "无",
    9: "火星",
    10: "无",
    11: "金星"
}

DETRIMENT_PLANETS = {
    0: "金星",
    1: "火星",
    2: "木星",
    3: "土星",
    4: "土星",
    5: "木星",
    6: "火星",
    7: "金星",
    8: "水星",
    9: "月亮",
    10: "太阳",
    11: "水星"
}

FALL_PLANETS = {
    0: "土星",
    1: "冥王星",
    2: "木星",
    3: "火星",
    4: "金星",
    5: "木星",
    6: "太阳",
    7: "月亮",
    8: "水星",
    9: "木星",
    10: "火星",
    11: "水星"
}

TRIPLICITY_RULERS = {
    Element.FIRE: {
        "day": ["太阳", "木星", "土星"],
        "night": ["木星", "太阳", "土星"],
        "participating": "土星"
    },
    Element.EARTH: {
        "day": ["金星", "月亮", "火星"],
        "night": ["月亮", "金星", "火星"],
        "participating": "火星"
    },
    Element.AIR: {
        "day": ["土星", "水星", "木星"],
        "night": ["水星", "土星", "木星"],
        "participating": "木星"
    },
    Element.WATER: {
        "day": ["金星", "火星", "月亮"],
        "night": ["火星", "金星", "月亮"],
        "participating": "月亮"
    }
}

EGYPTIAN_TERMS = {
    0: [
        {"start": 0, "end": 6, "ruler": "木星"},
        {"start": 6, "end": 14, "ruler": "金星"},
        {"start": 14, "end": 21, "ruler": "水星"},
        {"start": 21, "end": 28, "ruler": "火星"},
        {"start": 28, "end": 30, "ruler": "土星"}
    ],
    1: [
        {"start": 0, "end": 8, "ruler": "金星"},
        {"start": 8, "end": 16, "ruler": "月亮"},
        {"start": 16, "end": 22, "ruler": "水星"},
        {"start": 22, "end": 27, "ruler": "木星"},
        {"start": 27, "end": 30, "ruler": "土星"}
    ],
    2: [
        {"start": 0, "end": 6, "ruler": "木星"},
        {"start": 6, "end": 12, "ruler": "金星"},
        {"start": 12, "end": 20, "ruler": "水星"},
        {"start": 20, "end": 26, "ruler": "火星"},
        {"start": 26, "end": 30, "ruler": "土星"}
    ],
    3: [
        {"start": 0, "end": 7, "ruler": "火星"},
        {"start": 7, "end": 13, "ruler": "木星"},
        {"start": 13, "end": 20, "ruler": "水星"},
        {"start": 20, "end": 26, "ruler": "金星"},
        {"start": 26, "end": 30, "ruler": "月亮"}
    ],
    4: [
        {"start": 0, "end": 6, "ruler": "木星"},
        {"start": 6, "end": 13, "ruler": "金星"},
        {"start": 13, "end": 19, "ruler": "水星"},
        {"start": 19, "end": 25, "ruler": "火星"},
        {"start": 25, "end": 30, "ruler": "土星"}
    ],
    5: [
        {"start": 0, "end": 7, "ruler": "水星"},
        {"start": 7, "end": 14, "ruler": "金星"},
        {"start": 14, "end": 21, "ruler": "木星"},
        {"start": 21, "end": 28, "ruler": "月亮"},
        {"start": 28, "end": 30, "ruler": "火星"}
    ],
    6: [
        {"start": 0, "end": 6, "ruler": "土星"},
        {"start": 6, "end": 11, "ruler": "金星"},
        {"start": 11, "end": 19, "ruler": "木星"},
        {"start": 19, "end": 24, "ruler": "水星"},
        {"start": 24, "end": 30, "ruler": "火星"}
    ],
    7: [
        {"start": 0, "end": 6, "ruler": "火星"},
        {"start": 6, "end": 14, "ruler": "木星"},
        {"start": 14, "end": 21, "ruler": "水星"},
        {"start": 21, "end": 27, "ruler": "金星"},
        {"start": 27, "end": 30, "ruler": "月亮"}
    ],
    8: [
        {"start": 0, "end": 8, "ruler": "木星"},
        {"start": 8, "end": 14, "ruler": "金星"},
        {"start": 14, "end": 21, "ruler": "水星"},
        {"start": 21, "end": 26, "ruler": "火星"},
        {"start": 26, "end": 30, "ruler": "土星"}
    ],
    9: [
        {"start": 0, "end": 5, "ruler": "木星"},
        {"start": 5, "end": 13, "ruler": "火星"},
        {"start": 13, "end": 19, "ruler": "水星"},
        {"start": 19, "end": 25, "ruler": "金星"},
        {"start": 25, "end": 30, "ruler": "土星"}
    ],
    10: [
        {"start": 0, "end": 7, "ruler": "土星"},
        {"start": 7, "end": 14, "ruler": "金星"},
        {"start": 14, "end": 21, "ruler": "水星"},
        {"start": 21, "end": 25, "ruler": "木星"},
        {"start": 25, "end": 30, "ruler": "火星"}
    ],
    11: [
        {"start": 0, "end": 12, "ruler": "金星"},
        {"start": 12, "end": 16, "ruler": "月亮"},
        {"start": 16, "end": 20, "ruler": "木星"},
        {"start": 20, "end": 25, "ruler": "水星"},
        {"start": 25, "end": 30, "ruler": "火星"}
    ]
}

CHALDEAN_FACES = {
    0: [
        {"start": 0, "end": 10, "ruler": "火星"},
        {"start": 10, "end": 20, "ruler": "太阳"},
        {"start": 20, "end": 30, "ruler": "金星"}
    ],
    1: [
        {"start": 0, "end": 10, "ruler": "水星"},
        {"start": 10, "end": 20, "ruler": "月亮"},
        {"start": 10, "end": 30, "ruler": "土星"}
    ],
    2: [
        {"start": 0, "end": 10, "ruler": "木星"},
        {"start": 10, "end": 20, "ruler": "火星"},
        {"start": 20, "end": 30, "ruler": "太阳"}
    ],
    3: [
        {"start": 0, "end": 10, "ruler": "金星"},
        {"start": 10, "end": 20, "ruler": "水星"},
        {"start": 20, "end": 30, "ruler": "月亮"}
    ],
    4: [
        {"start": 0, "end": 10, "ruler": "土星"},
        {"start": 10, "end": 20, "ruler": "木星"},
        {"start": 20, "end": 30, "ruler": "火星"}
    ],
    5: [
        {"start": 0, "end": 10, "ruler": "太阳"},
        {"start": 10, "end": 20, "ruler": "金星"},
        {"start": 20, "end": 30, "ruler": "水星"}
    ],
    6: [
        {"start": 0, "end": 10, "ruler": "月亮"},
        {"start": 10, "end": 20, "ruler": "土星"},
        {"start": 20, "end": 30, "ruler": "木星"}
    ],
    7: [
        {"start": 0, "end": 10, "ruler": "火星"},
        {"start": 10, "end": 20, "ruler": "太阳"},
        {"start": 20, "end": 30, "ruler": "金星"}
    ],
    8: [
        {"start": 0, "end": 10, "ruler": "水星"},
        {"start": 10, "end": 20, "ruler": "月亮"},
        {"start": 20, "end": 30, "ruler": "土星"}
    ],
    9: [
        {"start": 0, "end": 10, "ruler": "木星"},
        {"start": 10, "end": 20, "ruler": "火星"},
        {"start": 20, "end": 30, "ruler": "太阳"}
    ],
    10: [
        {"start": 0, "end": 10, "ruler": "金星"},
        {"start": 10, "end": 20, "ruler": "水星"},
        {"start": 20, "end": 30, "ruler": "月亮"}
    ],
    11: [
        {"start": 0, "end": 10, "ruler": "土星"},
        {"start": 10, "end": 20, "ruler": "木星"},
        {"start": 20, "end": 30, "ruler": "火星"}
    ]
}

ANTISCIA_SIGNS = {
    0: 5,
    1: 4,
    2: 3,
    3: 2,
    4: 1,
    5: 0,
    6: 11,
    7: 10,
    8: 9,
    9: 8,
    10: 7,
    11: 6
}

CONTRAANTISCIA_SIGNS = {
    0: 11,
    1: 10,
    2: 9,
    3: 8,
    4: 7,
    5: 6,
    6: 5,
    7: 4,
    8: 3,
    9: 2,
    10: 1,
    11: 0
}

ASPECT_TYPES_CLASSICAL = [
    {"name": "合相", "symbol": "☌", "angle": 0, "orb": 8, "type": "major", "nature": "neutral"},
    {"name": "六分相", "symbol": "⚹", "angle": 60, "orb": 6, "type": "major", "nature": "harmonious"},
    {"name": "四分相", "symbol": "□", "angle": 90, "orb": 8, "type": "major", "nature": "challenging"},
    {"name": "三分相", "symbol": "△", "angle": 120, "orb": 8, "type": "major", "nature": "harmonious"},
    {"name": "对分相", "symbol": "☍", "angle": 180, "orb": 8, "type": "major", "nature": "challenging"},
    {"name": "半六分相", "symbol": "∠", "angle": 30, "orb": 2, "type": "minor", "nature": "harmonious"},
    {"name": "八分相", "symbol": "∡", "angle": 45, "orb": 2, "type": "minor", "nature": "challenging"},
    {"name": "补八分相", "symbol": "⊿", "angle": 135, "orb": 2, "type": "minor", "nature": "challenging"},
    {"name": "倍六分相", "symbol": "≒", "angle": 150, "orb": 2, "type": "minor", "nature": "neutral"},
]

PLANET_ORDER = ["太阳", "月亮", "水星", "金星", "火星", "木星", "土星", "天王星", "海王星", "冥王星", "北交点", "南交点"]

TRADITIONAL_PLANETS = ["太阳", "月亮", "水星", "金星", "火星", "木星", "土星"]

SECT_LIGHT_PLANETS = {
    "day": ["太阳", "木星", "土星"],
    "night": ["金星", "火星", "月亮"]
}


@dataclass
class DignityInfo:
    planet: str
    sign_index: int
    degree_in_sign: float
    ruler: Optional[str] = None
    exaltation: Optional[str] = None
    triplicity: Optional[List[str]] = None
    term: Optional[str] = None
    face: Optional[str] = None
    detriment: Optional[str] = None
    fall: Optional[str] = None
    is_in_ruler: bool = False
    is_in_exaltation: bool = False
    is_in_detriment: bool = False
    is_in_fall: bool = False
    dignity_score: int = 0
    debility_score: int = 0
    essential_dignity: str = "neutral"


@dataclass
class ReceptionInfo:
    planet_a: str
    planet_b: str
    reception_type: str
    dignity_type: str
    is_mutual: bool
    description: str
    strength: float


@dataclass
class AntisciaInfo:
    planet_name: str
    antiscia_longitude: float
    antiscia_sign_index: int
    antiscia_degree: float
    contra_antiscia_longitude: float
    contra_antiscia_sign_index: int
    contra_antiscia_degree: float


@dataclass
class LightTranslationInfo:
    translator: str
    planet_a: str
    planet_b: str
    aspect_from_a: str
    aspect_to_b: str
    description: str
    is_perfecting: bool


@dataclass
class BesiegementInfo:
    besieged_planet: str
    besieging_planets: List[str]
    aspect_type: str
    description: str
    strength: float


class ClassicalAstrologyService:
    """
    古典占星专业规则引擎
    
    职责：
    - 行星庙旺弱陷计算 (Essential Dignities)
    - 互容与接纳计算 (Mutual Reception & Reception)
    - 映点计算 (Antiscia)
    - 光线传递计算 (Translation of Light)
    - 围攻计算 (Besiegement)
    - 相位计算 (古典相位规则)
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_essential_dignities(
        self,
        planet_name: str,
        sign_index: int,
        degree_in_sign: float,
        is_day_chart: bool = True,
        use_traditional: bool = True
    ) -> DignityInfo:
        """
        计算行星的庙旺弱陷
        
        Args:
            planet_name: 行星名称
            sign_index: 星座索引 (0-11)
            degree_in_sign: 星座内度数 (0-30)
            is_day_chart: 是否为日间盘
            use_traditional: 是否使用传统守护星规则
            
        Returns:
            DignityInfo 对象
        """
        ruling_planets = TRADITIONAL_RULING_PLANETS if use_traditional else RULING_PLANETS
        exaltation_planets = TRADITIONAL_EXALTATION if use_traditional else EXALTATION_PLANETS
        
        ruler = ruling_planets.get(sign_index)
        exaltation = exaltation_planets.get(sign_index)
        detriment = DETRIMENT_PLANETS.get(sign_index)
        fall = FALL_PLANETS.get(sign_index)
        
        element = ELEMENTS[sign_index]
        triplicity_rulers = TRIPLICITY_RULERS.get(element, {})
        triplicity = triplicity_rulers.get("day" if is_day_chart else "night", [])
        
        term_ruler = self._get_term_ruler(sign_index, degree_in_sign)
        face_ruler = self._get_face_ruler(sign_index, degree_in_sign)
        
        is_in_ruler = planet_name == ruler
        is_in_exaltation = planet_name == exaltation
        is_in_triplicity = planet_name in triplicity
        is_in_term = planet_name == term_ruler
        is_in_face = planet_name == face_ruler
        
        is_in_detriment = planet_name == detriment
        is_in_fall = planet_name == fall
        
        dignity_score = 0
        if is_in_ruler: dignity_score += 5
        if is_in_exaltation: dignity_score += 4
        if is_in_triplicity: dignity_score += 3
        if is_in_term: dignity_score += 2
        if is_in_face: dignity_score += 1
        
        debility_score = 0
        if is_in_detriment: debility_score += 5
        if is_in_fall: debility_score += 4
        
        net_score = dignity_score - debility_score
        if net_score >= 5:
            essential_dignity = "exalted"
        elif net_score >= 3:
            essential_dignity = "strong"
        elif net_score >= 1:
            essential_dignity = "moderate"
        elif net_score >= -2:
            essential_dignity = "neutral"
        elif net_score >= -4:
            essential_dignity = "weak"
        else:
            essential_dignity = "debilitated"
        
        return DignityInfo(
            planet=planet_name,
            sign_index=sign_index,
            degree_in_sign=degree_in_sign,
            ruler=ruler,
            exaltation=exaltation,
            triplicity=triplicity,
            term=term_ruler,
            face=face_ruler,
            detriment=detriment,
            fall=fall,
            is_in_ruler=is_in_ruler,
            is_in_exaltation=is_in_exaltation,
            is_in_detriment=is_in_detriment,
            is_in_fall=is_in_fall,
            dignity_score=dignity_score,
            debility_score=debility_score,
            essential_dignity=essential_dignity
        )
    
    def _get_term_ruler(self, sign_index: int, degree_in_sign: float) -> Optional[str]:
        """获取界主星 (Egyptian Terms)"""
        terms = EGYPTIAN_TERMS.get(sign_index, [])
        for term in terms:
            if term["start"] <= degree_in_sign < term["end"]:
                return term["ruler"]
        return None
    
    def _get_face_ruler(self, sign_index: int, degree_in_sign: float) -> Optional[str]:
        """获取面主星 (Chaldean Faces)"""
        faces = CHALDEAN_FACES.get(sign_index, [])
        for face in faces:
            if face["start"] <= degree_in_sign < face["end"]:
                return face["ruler"]
        return None
    
    def calculate_all_dignities(
        self,
        planets: List[Dict[str, Any]],
        is_day_chart: bool = True,
        use_traditional: bool = True
    ) -> List[Dict[str, Any]]:
        """
        计算所有行星的庙旺弱陷
        
        Args:
            planets: 行星列表
            is_day_chart: 是否日间盘
            use_traditional: 是否使用传统守护星
            
        Returns:
            包含庙旺弱陷信息的行星列表
        """
        result = []
        for planet in planets:
            zodiac = planet.get("zodiac", {})
            sign_index = zodiac.get("sign_index", 0)
            degree_in_sign = zodiac.get("degree_in_sign", 0)
            planet_name = planet.get("name", "")
            
            dignity = self.calculate_essential_dignities(
                planet_name,
                sign_index,
                degree_in_sign,
                is_day_chart,
                use_traditional
            )
            
            result.append({
                **planet,
                "dignities": {
                    "ruler": dignity.ruler,
                    "exaltation": dignity.exaltation,
                    "triplicity": dignity.triplicity,
                    "term": dignity.term,
                    "face": dignity.face,
                    "detriment": dignity.detriment,
                    "fall": dignity.fall,
                    "is_in_ruler": dignity.is_in_ruler,
                    "is_in_exaltation": dignity.is_in_exaltation,
                    "is_in_detriment": dignity.is_in_detriment,
                    "is_in_fall": dignity.is_in_fall,
                    "dignity_score": dignity.dignity_score,
                    "debility_score": dignity.debility_score,
                    "essential_dignity": dignity.essential_dignity
                }
            })
        
        return result
    
    def calculate_receptions(
        self,
        planets: List[Dict[str, Any]],
        is_day_chart: bool = True,
        use_traditional: bool = True
    ) -> List[Dict[str, Any]]:
        """
        计算行星之间的接纳与互容关系
        
        Args:
            planets: 行星列表（需包含庙旺弱陷信息）
            is_day_chart: 是否日间盘
            use_traditional: 是否使用传统守护星
            
        Returns:
            接纳关系列表
        """
        receptions = []
        planet_map = {p["name"]: p for p in planets}
        
        traditional_planets = [p for p in planets if p["name"] in TRADITIONAL_PLANETS]
        
        for i in range(len(traditional_planets)):
            for j in range(i + 1, len(traditional_planets)):
                p1 = traditional_planets[i]
                p2 = traditional_planets[j]
                
                p1_name = p1["name"]
                p2_name = p2["name"]
                
                p1_dignities = p1.get("dignities", {})
                p2_dignities = p2.get("dignities", {})
                
                p1_ruler = p1_dignities.get("ruler")
                p2_ruler = p2_dignities.get("ruler")
                p1_exaltation = p1_dignities.get("exaltation")
                p2_exaltation = p2_dignities.get("exaltation")
                
                p1_receives_p2_by_ruler = p2_name == p1_ruler
                p2_receives_p1_by_ruler = p1_name == p2_ruler
                p1_receives_p2_by_exaltation = p2_name == p1_exaltation
                p2_receives_p1_by_exaltation = p1_name == p2_exaltation
                
                if p1_receives_p2_by_ruler:
                    is_mutual = p2_receives_p1_by_ruler
                    receptions.append({
                        "planet_a": p2_name,
                        "planet_b": p1_name,
                        "reception_type": "mutual_ruler" if is_mutual else "single_ruler",
                        "dignity_type": "ruler",
                        "is_mutual": is_mutual,
                        "description": self._generate_reception_description(
                            p2_name, p1_name, "ruler", is_mutual
                        ),
                        "strength": 1.0 if is_mutual else 0.5
                    })
                
                if p1_receives_p2_by_exaltation and p2_name != p1_ruler:
                    is_mutual = p2_receives_p1_by_exaltation
                    receptions.append({
                        "planet_a": p2_name,
                        "planet_b": p1_name,
                        "reception_type": "mutual_exaltation" if is_mutual else "single_exaltation",
                        "dignity_type": "exaltation",
                        "is_mutual": is_mutual,
                        "description": self._generate_reception_description(
                            p2_name, p1_name, "exaltation", is_mutual
                        ),
                        "strength": 0.8 if is_mutual else 0.4
                    })
                
                if (p1_receives_p2_by_ruler and p2_receives_p1_by_exaltation) or \
                   (p1_receives_p2_by_exaltation and p2_receives_p1_by_ruler):
                    receptions.append({
                        "planet_a": p1_name,
                        "planet_b": p2_name,
                        "reception_type": "mixed_mutual",
                        "dignity_type": "mixed",
                        "is_mutual": True,
                        "description": f"{p1_name}与{p2_name}形成混合互容，一方通过守护星接纳另一方，另一方通过旺势接纳。",
                        "strength": 0.9
                    })
        
        return receptions
    
    def _generate_reception_description(
        self,
        planet_a: str,
        planet_b: str,
        dignity_type: str,
        is_mutual: bool
    ) -> str:
        """生成接纳关系描述"""
        dignity_names = {
            "ruler": "守护星",
            "exaltation": "旺势"
        }
        
        if is_mutual:
            return f"{planet_a}与{planet_b}形成{dignity_names.get(dignity_type, '')}互容，双方通过{dignity_names.get(dignity_type, '')}关系彼此接纳，象征着能量的顺畅交流与相互支持。"
        else:
            return f"{planet_a}被{planet_b}通过{dignity_names.get(dignity_type, '')}关系接纳，{planet_b}对{planet_a}的能量表现出支持和认可。"
    
    def calculate_antiscia(
        self,
        planets: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        计算行星的映点和对照映点
        
        Args:
            planets: 行星列表
            
        Returns:
            包含映点信息的行星列表
        """
        result = []
        
        for planet in planets:
            longitude = planet.get("longitude", 0)
            sign_index = int(longitude / 30) % 12
            degree_in_sign = longitude % 30
            
            antiscia_sign = ANTISCIA_SIGNS.get(sign_index, sign_index)
            antiscia_degree = 30 - degree_in_sign
            antiscia_longitude = antiscia_sign * 30 + antiscia_degree
            
            contra_sign = CONTRAANTISCIA_SIGNS.get(sign_index, sign_index)
            contra_degree = 30 - degree_in_sign
            contra_longitude = contra_sign * 30 + contra_degree
            
            result.append({
                **planet,
                "antiscia": {
                    "longitude": antiscia_longitude,
                    "sign_index": antiscia_sign,
                    "sign": ZODIAC_SIGNS[antiscia_sign],
                    "sign_symbol": ZODIAC_SYMBOLS[antiscia_sign],
                    "degree_in_sign": antiscia_degree
                },
                "contra_antiscia": {
                    "longitude": contra_longitude,
                    "sign_index": contra_sign,
                    "sign": ZODIAC_SIGNS[contra_sign],
                    "sign_symbol": ZODIAC_SYMBOLS[contra_sign],
                    "degree_in_sign": contra_degree
                }
            })
        
        return result
    
    def check_antiscia_aspects(
        self,
        planets: List[Dict[str, Any]],
        orb: float = 2.0
    ) -> List[Dict[str, Any]]:
        """
        检查映点相位
        
        Args:
            planets: 包含映点信息的行星列表
            orb: 容许度
            
        Returns:
            映点相位列表
        """
        antiscia_aspects = []
        
        for i in range(len(planets)):
            for j in range(i + 1, len(planets)):
                p1 = planets[i]
                p2 = planets[j]
                
                p1_name = p1["name"]
                p2_name = p2["name"]
                
                p1_antiscia = p1.get("antiscia", {}).get("longitude", 0)
                p2_long = p2.get("longitude", 0)
                
                diff = abs(p1_antiscia - p2_long)
                if diff > 180:
                    diff = 360 - diff
                
                if diff <= orb:
                    antiscia_aspects.append({
                        "type": "antiscia",
                        "planet_a": p1_name,
                        "planet_b": p2_name,
                        "description": f"{p1_name}的映点与{p2_name}形成映点相合（{diff:.2f}°）",
                        "orb": round(diff, 4),
                        "strength": 1 - diff / orb
                    })
                
                p1_contra = p1.get("contra_antiscia", {}).get("longitude", 0)
                diff_contra = abs(p1_contra - p2_long)
                if diff_contra > 180:
                    diff_contra = 360 - diff_contra
                
                if diff_contra <= orb:
                    antiscia_aspects.append({
                        "type": "contra_antiscia",
                        "planet_a": p1_name,
                        "planet_b": p2_name,
                        "description": f"{p1_name}的对照映点与{p2_name}形成对照映点相合（{diff_contra:.2f}°）",
                        "orb": round(diff_contra, 4),
                        "strength": 1 - diff_contra / orb
                    })
        
        return antiscia_aspects
    
    def calculate_light_translation(
        self,
        planets: List[Dict[str, Any]],
        aspects: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        计算光线传递 (Translation of Light)
        
        光线传递是指：一个较轻的行星与两个较重的行星分别形成相位，
        从而传递这两个较重行星之间的能量。
        
        Args:
            planets: 行星列表
            aspects: 相位列表
            
        Returns:
            光线传递情况列表
        """
        translations = []
        
        planet_weights = {
            "土星": 7,
            "木星": 6,
            "火星": 5,
            "太阳": 4,
            "金星": 3,
            "水星": 2,
            "月亮": 1
        }
        
        traditional_planets = [p for p in planets if p["name"] in TRADITIONAL_PLANETS]
        
        for translator in traditional_planets:
            translator_name = translator["name"]
            translator_weight = planet_weights.get(translator_name, 0)
            
            translator_aspects = [
                a for a in aspects
                if a.get("planet1") == translator_name or a.get("planet2") == translator_name
            ]
            
            if len(translator_aspects) >= 2:
                other_planets_in_aspect = set()
                aspect_map = {}
                
                for aspect in translator_aspects:
                    other_planet = aspect["planet2"] if aspect["planet1"] == translator_name else aspect["planet1"]
                    if other_planet in planet_weights:
                        other_planets_in_aspect.add(other_planet)
                        aspect_map[other_planet] = aspect
                
                heavier_planets = [
                    p for p in other_planets_in_aspect
                    if planet_weights.get(p, 0) > translator_weight
                ]
                
                if len(heavier_planets) >= 2:
                    for i in range(len(heavier_planets)):
                        for j in range(i + 1, len(heavier_planets)):
                            p_a = heavier_planets[i]
                            p_b = heavier_planets[j]
                            
                            aspect_a = aspect_map.get(p_a)
                            aspect_b = aspect_map.get(p_b)
                            
                            if aspect_a and aspect_b:
                                translations.append({
                                    "translator": translator_name,
                                    "planet_a": p_a,
                                    "planet_b": p_b,
                                    "aspect_from_a": aspect_a.get("aspect", ""),
                                    "aspect_to_b": aspect_b.get("aspect", ""),
                                    "description": f"{translator_name}作为光线传递者，连接了{p_a}和{p_b}。{translator_name}与{p_a}形成{aspect_a.get('aspect', '')}，与{p_b}形成{aspect_b.get('aspect', '')}，传递着两星之间的能量。",
                                    "is_perfecting": self._check_perfecting(translator, p_a, p_b, planets)
                                })
        
        return translations
    
    def _check_perfecting(
        self,
        translator: Dict,
        p_a_name: str,
        p_b_name: str,
        planets: List[Dict]
    ) -> bool:
        """检查光线传递是否正在完成中"""
        p_a = next((p for p in planets if p["name"] == p_a_name), None)
        p_b = next((p for p in planets if p["name"] == p_b_name), None)
        
        if not p_a or not p_b:
            return False
        
        translator_speed = translator.get("speed", 0)
        p_a_speed = p_a.get("speed", 0)
        p_b_speed = p_b.get("speed", 0)
        
        if translator_speed > p_a_speed and translator_speed > p_b_speed:
            return True
        
        return False
    
    def calculate_besiegement(
        self,
        planets: List[Dict[str, Any]],
        aspects: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        计算围攻 (Besiegement)
        
        围攻是指：一颗行星被两个凶星（火星、土星）通过同一类型的相位所包围，
        或者被其他行星在特定度数范围内包围。
        
        Args:
            planets: 行星列表
            aspects: 相位列表
            
        Returns:
            围攻情况列表
        """
        besiegements = []
        
        malefics = ["火星", "土星"]
        traditional_planets = [p for p in planets if p["name"] in TRADITIONAL_PLANETS]
        planet_map = {p["name"]: p for p in traditional_planets}
        
        for planet in traditional_planets:
            planet_name = planet["name"]
            if planet_name in malefics:
                continue
            
            planet_aspects = [
                a for a in aspects
                if a.get("planet1") == planet_name or a.get("planet2") == planet_name
            ]
            
            malefic_aspects = []
            for aspect in planet_aspects:
                other_planet = aspect["planet2"] if aspect["planet1"] == planet_name else aspect["planet1"]
                if other_planet in malefics:
                    malefic_aspects.append({
                        "malefic": other_planet,
                        "aspect": aspect,
                        "aspect_type": aspect.get("aspect", "")
                    })
            
            if len(malefic_aspects) >= 2:
                aspect_types = set([ma["aspect_type"] for ma in malefic_aspects])
                
                for aspect_type in aspect_types:
                    same_type_aspects = [ma for ma in malefic_aspects if ma["aspect_type"] == aspect_type]
                    if len(same_type_aspects) >= 2:
                        besieging_planets = [ma["malefic"] for ma in same_type_aspects]
                        besiegements.append({
                            "besieged_planet": planet_name,
                            "besieging_planets": besieging_planets,
                            "aspect_type": aspect_type,
                            "description": f"{planet_name}被{', '.join(besieging_planets)}通过{aspect_type}形成围攻。这种配置可能带来压力和限制。",
                            "strength": len(same_type_aspects) * 0.5
                        })
            
            planet_long = planet.get("longitude", 0)
            nearby_malefics = []
            for malefic in malefics:
                malefic_planet = planet_map.get(malefic)
                if malefic_planet:
                    malefic_long = malefic_planet.get("longitude", 0)
                    diff = abs(planet_long - malefic_long)
                    if diff > 180:
                        diff = 360 - diff
                    if diff <= 17 and diff >= 3:
                        nearby_malefics.append({
                            "name": malefic,
                            "distance": diff
                        })
            
            if len(nearby_malefics) >= 2:
                besiegements.append({
                    "besieged_planet": planet_name,
                    "besieging_planets": [m["name"] for m in nearby_malefics],
                    "aspect_type": "conjunction_proximity",
                    "description": f"{planet_name}位于{', '.join([m['name'] for m in nearby_malefics])}之间，度数接近形成围攻态势。",
                    "strength": 0.7
                })
        
        return besiegements
    
    def calculate_classical_aspects(
        self,
        planets: List[Dict[str, Any]],
        include_minor: bool = False
    ) -> List[Dict[str, Any]]:
        """
        计算古典相位
        
        Args:
            planets: 行星列表
            include_minor: 是否包含次要相位
            
        Returns:
            相位列表
        """
        aspects = []
        
        if include_minor:
            aspect_types = ASPECT_TYPES_CLASSICAL
        else:
            aspect_types = [a for a in ASPECT_TYPES_CLASSICAL if a["type"] == "major"]
        
        for i in range(len(planets)):
            for j in range(i + 1, len(planets)):
                p1 = planets[i]
                p2 = planets[j]
                
                p1_name = p1.get("name", "")
                p2_name = p2.get("name", "")
                p1_long = p1.get("longitude", 0)
                p2_long = p2.get("longitude", 0)
                
                diff = abs(p1_long - p2_long)
                if diff > 180:
                    diff = 360 - diff
                
                for aspect_def in aspect_types:
                    angle = aspect_def["angle"]
                    orb = aspect_def["orb"]
                    
                    if abs(diff - angle) <= orb:
                        orb_exact = abs(diff - angle)
                        influence = aspect_def.get("influence", 0.5) * (1 - orb_exact / orb)
                        
                        aspects.append({
                            "planet1": p1_name,
                            "planet1_symbol": p1.get("symbol", ""),
                            "planet1_zodiac": p1.get("zodiac"),
                            "planet2": p2_name,
                            "planet2_symbol": p2.get("symbol", ""),
                            "planet2_zodiac": p2.get("zodiac"),
                            "aspect": aspect_def["name"],
                            "aspect_symbol": aspect_def["symbol"],
                            "angle": angle,
                            "actual_angle": round(diff, 4),
                            "orb": round(orb_exact, 4),
                            "influence": round(influence, 4),
                            "nature": aspect_def["nature"],
                            "aspect_type": aspect_def["type"],
                            "is_applying": self._check_applying(p1, p2, angle)
                        })
                        break
        
        aspects.sort(key=lambda x: x["influence"], reverse=True)
        return aspects
    
    def _check_applying(
        self,
        planet1: Dict[str, Any],
        planet2: Dict[str, Any],
        aspect_angle: float
    ) -> bool:
        """检查相位是否在入相中"""
        p1_long = planet1.get("longitude", 0)
        p2_long = planet2.get("longitude", 0)
        p1_speed = planet1.get("speed", 0)
        p2_speed = planet2.get("speed", 0)
        
        diff = abs(p1_long - p2_long)
        if diff > 180:
            diff = 360 - diff
        
        future_diff = abs((p1_long + p1_speed) - (p2_long + p2_speed))
        if future_diff > 180:
            future_diff = 360 - future_diff
        
        current_orb_to_aspect = abs(diff - aspect_angle)
        future_orb_to_aspect = abs(future_diff - aspect_angle)
        
        return future_orb_to_aspect < current_orb_to_aspect
    
    def analyze_full_chart(
        self,
        chart_data: Dict[str, Any],
        is_day_chart: bool = True,
        use_traditional: bool = True,
        include_minor_aspects: bool = False
    ) -> Dict[str, Any]:
        """
        完整星盘古典占星分析
        
        Args:
            chart_data: 星盘数据
            is_day_chart: 是否日间盘
            use_traditional: 是否使用传统守护星规则
            include_minor_aspects: 是否包含次要相位
            
        Returns:
            完整分析结果
        """
        planets = chart_data.get("planets", [])
        
        planets_with_dignities = self.calculate_all_dignities(
            planets, is_day_chart, use_traditional
        )
        
        planets_with_antiscia = self.calculate_antiscia(planets_with_dignities)
        
        aspects = self.calculate_classical_aspects(
            planets_with_antiscia, include_minor_aspects
        )
        
        receptions = self.calculate_receptions(
            planets_with_antiscia, is_day_chart, use_traditional
        )
        
        antiscia_aspects = self.check_antiscia_aspects(planets_with_antiscia)
        
        light_translations = self.calculate_light_translation(
            planets_with_antiscia, aspects
        )
        
        besiegements = self.calculate_besiegement(
            planets_with_antiscia, aspects
        )
        
        dignities_summary = self._summarize_dignities(planets_with_antiscia)
        
        return {
            "planets": planets_with_antiscia,
            "aspects": aspects,
            "receptions": receptions,
            "antiscia_aspects": antiscia_aspects,
            "light_translations": light_translations,
            "besiegements": besiegements,
            "dignities_summary": dignities_summary,
            "is_day_chart": is_day_chart,
            "use_traditional": use_traditional
        }
    
    def _summarize_dignities(self, planets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """汇总庙旺弱陷信息"""
        summary = {
            "strong_planets": [],
            "weak_planets": [],
            "ruler_planets": [],
            "exaltation_planets": [],
            "detriment_planets": [],
            "fall_planets": []
        }
        
        for planet in planets:
            dignities = planet.get("dignities", {})
            planet_name = planet.get("name", "")
            
            if dignities.get("is_in_ruler"):
                summary["ruler_planets"].append(planet_name)
            if dignities.get("is_in_exaltation"):
                summary["exaltation_planets"].append(planet_name)
            if dignities.get("is_in_detriment"):
                summary["detriment_planets"].append(planet_name)
            if dignities.get("is_in_fall"):
                summary["fall_planets"].append(planet_name)
            
            essential_dignity = dignities.get("essential_dignity", "neutral")
            if essential_dignity in ["exalted", "strong"]:
                summary["strong_planets"].append({
                    "name": planet_name,
                    "dignity": essential_dignity,
                    "score": dignities.get("dignity_score", 0)
                })
            elif essential_dignity in ["weak", "debilitated"]:
                summary["weak_planets"].append({
                    "name": planet_name,
                    "dignity": essential_dignity,
                    "score": dignities.get("debility_score", 0)
                })
        
        return summary
    
    def generate_interpretation_notes(
        self,
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        自动生成解盘笔记草稿
        
        Args:
            analysis: 完整分析结果
            
        Returns:
            解盘笔记结构
        """
        notes = {
            "executive_summary": "",
            "planets_analysis": [],
            "aspects_analysis": [],
            "receptions_analysis": [],
            "special_indicators": [],
            "key_themes": []
        }
        
        dignities_summary = analysis.get("dignities_summary", {})
        strong_planets = dignities_summary.get("strong_planets", [])
        weak_planets = dignities_summary.get("weak_planets", [])
        
        summary_parts = []
        if strong_planets:
            summary_parts.append(f"此星盘中{', '.join([p['name'] for p in strong_planets])}力量较强，")
        if weak_planets:
            summary_parts.append(f"而{', '.join([p['name'] for p in weak_planets])}力量较弱。")
        notes["executive_summary"] = "".join(summary_parts) if summary_parts else "此星盘能量分布相对平衡。"
        
        planets = analysis.get("planets", [])
        for planet in planets:
            dignities = planet.get("dignities", {})
            planet_name = planet.get("name", "")
            zodiac = planet.get("zodiac", {})
            
            dignity_notes = []
            if dignities.get("is_in_ruler"):
                dignity_notes.append(f"{planet_name}位于守护星座，力量增强。")
            if dignities.get("is_in_exaltation"):
                dignity_notes.append(f"{planet_name}位于旺势星座，表现优异。")
            if dignities.get("is_in_detriment"):
                dignity_notes.append(f"{planet_name}位于落陷星座，能量表达受阻。")
            if dignities.get("is_in_fall"):
                dignity_notes.append(f"{planet_name}位于弱势星座，力量削弱。")
            
            notes["planets_analysis"].append({
                "planet": planet_name,
                "sign": zodiac.get("sign", ""),
                "house": planet.get("house", 0),
                "dignity_notes": dignity_notes,
                "antiscia_note": f"映点位于{planet.get('antiscia', {}).get('sign', '')} {planet.get('antiscia', {}).get('degree_in_sign', 0):.1f}°"
            })
        
        aspects = analysis.get("aspects", [])
        major_aspects = [a for a in aspects if a.get("aspect_type") == "major"]
        
        for aspect in major_aspects[:15]:
            nature = aspect.get("nature", "neutral")
            nature_desc = {
                "harmonious": "和谐的",
                "challenging": "有挑战的",
                "neutral": "中性的"
            }.get(nature, "中性的")
            
            applying_note = "入相中" if aspect.get("is_applying") else "出相中"
            
            notes["aspects_analysis"].append({
                "planets": f"{aspect.get('planet1')} {aspect.get('aspect_symbol')} {aspect.get('planet2')}",
                "aspect_type": aspect.get("aspect", ""),
                "nature": nature_desc,
                "orb": aspect.get("orb", 0),
                "applying": applying_note,
                "interpretation": self._generate_aspect_interpretation(aspect)
            })
        
        receptions = analysis.get("receptions", [])
        for reception in receptions:
            if reception.get("is_mutual"):
                notes["receptions_analysis"].append({
                    "type": "互容",
                    "planets": f"{reception.get('planet_a')} ↔ {reception.get('planet_b')}",
                    "description": reception.get("description", ""),
                    "strength": reception.get("strength", 0)
                })
            else:
                notes["receptions_analysis"].append({
                    "type": "接纳",
                    "planets": f"{reception.get('planet_a')} → {reception.get('planet_b')}",
                    "description": reception.get("description", ""),
                    "strength": reception.get("strength", 0)
                })
        
        light_translations = analysis.get("light_translations", [])
        for translation in light_translations:
            notes["special_indicators"].append({
                "type": "光线传递",
                "description": translation.get("description", "")
            })
        
        besiegements = analysis.get("besiegements", [])
        for besiegement in besiegements:
            notes["special_indicators"].append({
                "type": "围攻",
                "description": besiegement.get("description", "")
            })
        
        antiscia_aspects = analysis.get("antiscia_aspects", [])
        for antiscia in antiscia_aspects:
            notes["special_indicators"].append({
                "type": "映点相合",
                "description": antiscia.get("description", "")
            })
        
        key_themes = set()
        for aspect in major_aspects[:10]:
            theme = self._extract_theme(aspect)
            if theme:
                key_themes.add(theme)
        
        notes["key_themes"] = list(key_themes)
        
        return notes
    
    def _generate_aspect_interpretation(self, aspect: Dict[str, Any]) -> str:
        """生成相位解释"""
        p1 = aspect.get("planet1", "")
        p2 = aspect.get("planet2", "")
        aspect_name = aspect.get("aspect", "")
        nature = aspect.get("nature", "neutral")
        
        base_interps = {
            ("太阳", "月亮"): {
                "合相": "自我认同与情感需求高度融合，内心和谐。",
                "三分相": "自我表达与情感需求自然和谐，内心平衡。",
                "六分相": "意志与情感有良好的沟通渠道。",
                "四分相": "自我意志与情感需求存在张力，需要整合。",
                "对分相": "自我表达与情感需求需要平衡与协调。"
            },
            ("太阳", "水星"): {
                "合相": "心智与自我认同结合，思维清晰表达直接。",
                "三分相": "思维与自我表达顺畅，沟通能力强。",
                "六分相": "心智为自我表达提供支持。",
                "四分相": "思维与自我认同有摩擦，需要调整。",
                "对分相": "思维与自我表达需要找到平衡点。"
            }
        }
        
        key = tuple(sorted([p1, p2]))
        if key in base_interps and aspect_name in base_interps[key]:
            return base_interps[key][aspect_name]
        
        if nature == "harmonious":
            return f"{p1}与{p2}形成{aspect_name}，能量自然融合，带来顺畅的表达与支持。"
        elif nature == "challenging":
            return f"{p1}与{p2}形成{aspect_name}，能量之间存在张力，需要通过努力来整合与转化。"
        else:
            return f"{p1}与{p2}形成{aspect_name}，能量相互强调，影响取决于整体星盘配置。"
    
    def _extract_theme(self, aspect: Dict[str, Any]) -> Optional[str]:
        """从相位提取主题"""
        p1 = aspect.get("planet1", "")
        p2 = aspect.get("planet2", "")
        nature = aspect.get("nature", "neutral")
        
        emotional_planets = ["月亮", "金星", "太阳"]
        mental_planets = ["水星", "木星", "天王星"]
        action_planets = ["火星", "太阳", "木星"]
        structure_planets = ["土星", "冥王星"]
        
        if p1 in emotional_planets and p2 in emotional_planets:
            return "情感关系" if nature == "harmonious" else "情感挑战"
        if p1 in mental_planets and p2 in mental_planets:
            return "思维模式"
        if p1 in action_planets and p2 in action_planets:
            return "行动力与决断"
        if p1 in structure_planets or p2 in structure_planets:
            return "成长与转化"
        
        return None


classical_astrology_service = ClassicalAstrologyService()


def get_classical_astrology_service() -> ClassicalAstrologyService:
    """获取古典占星服务单例"""
    return classical_astrology_service
