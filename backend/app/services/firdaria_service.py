import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from dateutil.relativedelta import relativedelta
import json
import hashlib

logger = logging.getLogger(__name__)


PLANET_CN_TO_EN = {
    "太阳": "sun",
    "月亮": "moon",
    "水星": "mercury",
    "金星": "venus",
    "火星": "mars",
    "木星": "jupiter",
    "土星": "saturn",
    "天王星": "uranus",
    "海王星": "neptune",
    "冥王星": "pluto",
    "北交点": "north_node",
    "南交点": "south_node",
}

PLANET_EN_TO_CN = {v: k for k, v in PLANET_CN_TO_EN.items()}


RULING_SIGNS = {
    "太阳": ["狮子座"],
    "月亮": ["巨蟹座"],
    "水星": ["双子座", "处女座"],
    "金星": ["金牛座", "天秤座"],
    "火星": ["白羊座", "天蝎座"],
    "木星": ["射手座", "双鱼座"],
    "土星": ["摩羯座", "水瓶座"],
    "天王星": ["水瓶座"],
    "海王星": ["双鱼座"],
    "冥王星": ["天蝎座"],
}

EXALTATION_SIGNS = {
    "太阳": ["白羊座"],
    "月亮": ["金牛座"],
    "水星": ["处女座", "水瓶座"],
    "金星": ["双鱼座", "天秤座"],
    "火星": ["摩羯座", "天蝎座"],
    "木星": ["巨蟹座", "射手座"],
    "土星": ["天秤座", "摩羯座"],
    "天王星": ["天蝎座", "水瓶座"],
    "海王星": ["巨蟹座", "双鱼座"],
    "冥王星": ["白羊座", "天蝎座"],
}

DETRIMENT_SIGNS = {
    "太阳": ["水瓶座"],
    "月亮": ["摩羯座"],
    "水星": ["射手座", "双鱼座"],
    "金星": ["白羊座", "天蝎座"],
    "火星": ["天秤座", "金牛座"],
    "木星": ["双子座", "处女座"],
    "土星": ["巨蟹座", "狮子座"],
    "天王星": ["狮子座", "金牛座"],
    "海王星": ["处女座", "双子座"],
    "冥王星": ["金牛座", "天秤座"],
}

FALL_SIGNS = {
    "太阳": ["天秤座"],
    "月亮": ["天蝎座"],
    "水星": ["狮子座", "双鱼座"],
    "金星": ["天蝎座", "白羊座"],
    "火星": ["巨蟹座", "摩羯座"],
    "木星": ["摩羯座", "双子座"],
    "土星": ["白羊座", "巨蟹座"],
    "天王星": ["金牛座", "狮子座"],
    "海王星": ["双子座", "处女座"],
    "冥王星": ["金牛座", "天秤座"],
}

HOUSE_STRENGTH = {
    1: 1.5, 2: 1.0, 3: 0.8, 4: 1.2, 5: 1.3, 6: 0.7,
    7: 1.3, 8: 0.8, 9: 1.2, 10: 1.5, 11: 1.0, 12: 0.6
}


FIRDAIRA_PLANET_INFO = {
    "sun": {"years": 19, "name": "太阳", "symbol": "☉", "element": "火", "quality": "热干", "is_node": False},
    "moon": {"years": 25, "name": "月亮", "symbol": "☽", "element": "水", "quality": "冷湿", "is_node": False},
    "mercury": {"years": 13, "name": "水星", "symbol": "☿", "element": "混合", "quality": "多变", "is_node": False},
    "venus": {"years": 8, "name": "金星", "symbol": "♀", "element": "土", "quality": "冷湿", "is_node": False},
    "mars": {"years": 7, "name": "火星", "symbol": "♂", "element": "火", "quality": "热干", "is_node": False},
    "jupiter": {"years": 12, "name": "木星", "symbol": "♃", "element": "风", "quality": "热湿", "is_node": False},
    "saturn": {"years": 30, "name": "土星", "symbol": "♄", "element": "土", "quality": "冷干", "is_node": False},
    "north_node": {"years": 3, "name": "北交点", "symbol": "☊", "element": "特殊", "quality": "连接", "is_node": True},
    "south_node": {"years": 2, "name": "南交点", "symbol": "☋", "element": "特殊", "quality": "过去", "is_node": True},
}


DAY_BIRTH_ORDER = [
    "sun", "venus", "mercury", "moon", "saturn", "jupiter", "mars", "north_node", "south_node"
]

NIGHT_BIRTH_ORDER = [
    "moon", "saturn", "jupiter", "mars", "sun", "venus", "mercury", "north_node", "south_node"
]


MINOR_PERIOD_PLANETS = [
    "saturn", "jupiter", "mars", "sun", "venus", "mercury", "moon"
]


def is_day_birth(sun_longitude: float) -> bool:
    """
    判断日生还是夜生
    古典法达规则：太阳在 7° 狮子座 到 7° 水瓶座 之间 = 日生
    太阳在 7° 水瓶座 到 7° 狮子座 之间 = 夜生
    
    更准确的说法：
    日生：太阳位于地平线以上，或者太阳经度在大约 125° (5° 狮子座) 到 305° (5° 水瓶座) 之间
    简化判断：太阳经度 >= 120° 且 < 300° = 日生
    """
    sun_degree = sun_longitude % 360
    
    if 120 <= sun_degree < 300:
        return True
    else:
        return False


def get_firdaria_order(sun_longitude: float) -> List[str]:
    """根据太阳位置获取法达行星顺序"""
    if is_day_birth(sun_longitude):
        return DAY_BIRTH_ORDER
    else:
        return NIGHT_BIRTH_ORDER


def get_planet_dignity_score(planet_name_cn: str, sign_name: str) -> float:
    """计算行星庙旺落陷分数"""
    score = 1.0
    
    if planet_name_cn in RULING_SIGNS and sign_name in RULING_SIGNS[planet_name_cn]:
        score += 0.5
    elif planet_name_cn in EXALTATION_SIGNS and sign_name in EXALTATION_SIGNS[planet_name_cn]:
        score += 0.3
    elif planet_name_cn in DETRIMENT_SIGNS and sign_name in DETRIMENT_SIGNS[planet_name_cn]:
        score -= 0.4
    elif planet_name_cn in FALL_SIGNS and sign_name in FALL_SIGNS[planet_name_cn]:
        score -= 0.3
    
    return max(0.3, score)


def get_house_strength_score(house_number: int) -> float:
    """获取宫位强度分数"""
    return HOUSE_STRENGTH.get(house_number, 1.0)


def get_natal_planet_info(natal_planets: List[Dict[str, Any]], planet_name_cn: str) -> Optional[Dict[str, Any]]:
    """从本命盘获取行星信息"""
    for p in natal_planets:
        if p.get("name") == planet_name_cn:
            return p
    return None


def get_sun_longitude(natal_planets: List[Dict[str, Any]]) -> float:
    """获取太阳黄经"""
    sun = get_natal_planet_info(natal_planets, "太阳")
    if sun:
        return sun.get("longitude", 0.0)
    return 180.0


class FirdariaPeriod:
    def __init__(self, planet: str, start_age: float, end_age: float, start_date: datetime, end_date: datetime):
        self.planet = planet
        self.start_age = start_age
        self.end_age = end_age
        self.start_date = start_date
        self.end_date = end_date
        self.info = FIRDAIRA_PLANET_INFO.get(planet, {})
        self.minor_periods: List[Dict[str, Any]] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "planet": self.planet,
            "planet_name": self.info.get("name", ""),
            "planet_symbol": self.info.get("symbol", ""),
            "element": self.info.get("element", ""),
            "quality": self.info.get("quality", ""),
            "is_node": self.info.get("is_node", False),
            "start_age": round(self.start_age, 2),
            "end_age": round(self.end_age, 2),
            "duration_years": round(self.end_age - self.start_age, 2),
            "start_date": self.start_date.strftime("%Y-%m-%d") if self.start_date else None,
            "end_date": self.end_date.strftime("%Y-%m-%d") if self.end_date else None,
            "minor_periods": self.minor_periods,
        }


class FirdariaCalculator:
    def __init__(self):
        self._period_cache: Dict[str, List[FirdariaPeriod]] = {}

    def _calculate_minor_periods(
        self, 
        major_planet: str, 
        major_start_age: float, 
        major_duration: float, 
        birth_date: datetime,
        is_node: bool = False
    ) -> List[Dict[str, Any]]:
        """
        计算小运周期
        古典法达规则：
        1. 小运周期为7个可见行星（不包含交点）
        2. 小运必须以大运行星自身开头
        3. 大限年数按比例分配给7个小运
        4. 交点（北交点/南交点）不设次限/小运
        """
        minor_periods = []
        
        if is_node:
            return minor_periods
        
        if major_planet not in MINOR_PERIOD_PLANETS:
            return minor_periods
        
        start_idx = MINOR_PERIOD_PLANETS.index(major_planet)
        
        minor_ratio = major_duration / 7.0
        
        current_age = major_start_age
        
        for i in range(7):
            idx = (start_idx + i) % len(MINOR_PERIOD_PLANETS)
            planet = MINOR_PERIOD_PLANETS[idx]
            info = FIRDAIRA_PLANET_INFO.get(planet, {})
            
            duration = minor_ratio
            
            try:
                start_years = int(current_age)
                start_days_frac = current_age - start_years
                start_days = int(start_days_frac * 365.25)
                
                end_years = int(current_age + duration)
                end_days_frac = (current_age + duration) - end_years
                end_days = int(end_days_frac * 365.25)
                
                start_date = birth_date + relativedelta(years=start_years, days=start_days)
                end_date = birth_date + relativedelta(years=end_years, days=end_days)
            except Exception as e:
                logger.warning(f"计算小运日期出错: {e}")
                start_date = birth_date
                end_date = birth_date
            
            minor_periods.append({
                "planet": planet,
                "planet_name": info.get("name", ""),
                "planet_symbol": info.get("symbol", ""),
                "start_age": round(current_age, 2),
                "end_age": round(current_age + duration, 2),
                "duration_years": round(duration, 2),
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
            })
            
            current_age += duration
        
        return minor_periods

    def calculate_firdaria_periods(
        self, 
        birth_date: datetime,
        sun_longitude: float = 180.0,
        natal_planets: Optional[List[Dict[str, Any]]] = None
    ) -> List[FirdariaPeriod]:
        """
        计算完整的法达周期
        """
        cache_parts = [
            birth_date.strftime("%Y-%m-%d"),
            str(round(sun_longitude, 2)),
        ]
        cache_key = hashlib.md5("_".join(cache_parts).encode()).hexdigest()
        
        if cache_key in self._period_cache:
            return self._period_cache[cache_key]
        
        planet_order = get_firdaria_order(sun_longitude)
        is_day = is_day_birth(sun_longitude)
        
        logger.info(f"法达推运计算: {'日生' if is_day else '夜生'}, 太阳经度: {sun_longitude}°, 行星顺序: {planet_order}")
        
        periods = []
        current_age = 0.0
        
        for planet in planet_order:
            info = FIRDAIRA_PLANET_INFO.get(planet, {})
            if not info:
                logger.warning(f"未知行星: {planet}")
                continue
            
            duration = info.get("years", 0)
            is_node = info.get("is_node", False)
            
            try:
                start_years = int(current_age)
                end_years = int(current_age + duration)
                start_date = birth_date + relativedelta(years=start_years)
                end_date = birth_date + relativedelta(years=end_years)
            except Exception as e:
                logger.warning(f"计算大运日期出错: {e}")
                start_date = birth_date
                end_date = birth_date
            
            period = FirdariaPeriod(
                planet=planet,
                start_age=current_age,
                end_age=current_age + duration,
                start_date=start_date,
                end_date=end_date
            )
            
            if not is_node:
                period.minor_periods = self._calculate_minor_periods(
                    planet, current_age, duration, birth_date, is_node
                )
            
            periods.append(period)
            current_age += duration
        
        self._period_cache[cache_key] = periods
        return periods

    def get_active_periods_for_year(
        self, 
        birth_date: datetime, 
        target_year: int,
        sun_longitude: float = 180.0,
        natal_planets: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """获取指定年份的活跃周期"""
        try:
            periods = self.calculate_firdaria_periods(birth_date, sun_longitude, natal_planets)
            
            birth_year = birth_date.year
            target_age = target_year - birth_year
            
            major_period: Optional[FirdariaPeriod] = None
            minor_period: Optional[Dict[str, Any]] = None
            
            for period in periods:
                if period.start_age <= target_age < period.end_age:
                    major_period = period
                    
                    if period.minor_periods:
                        for minor in period.minor_periods:
                            if minor["start_age"] <= target_age < minor["end_age"]:
                                minor_period = minor
                                break
                    break
            
            is_day = is_day_birth(sun_longitude)
            
            if not major_period:
                return {
                    "has_active_period": False,
                    "message": "该年份超出法达推运范围",
                    "is_day_birth": is_day,
                    "sun_longitude": sun_longitude,
                }
            
            major_dict = major_period.to_dict()
            progress = (target_age - major_period.start_age) / (major_period.end_age - major_period.start_age) * 100
            major_dict["progress_percent"] = round(progress, 1)
            
            return {
                "has_active_period": True,
                "target_year": target_year,
                "target_age": target_age,
                "is_day_birth": is_day,
                "sun_longitude": sun_longitude,
                "major_period": major_dict,
                "minor_period": minor_period,
            }
            
        except Exception as e:
            logger.error(f"获取活跃周期失败: {str(e)}", exc_info=True)
            return {
                "has_active_period": False,
                "message": f"计算出错: {str(e)}",
                "error": str(e),
            }

    def _calculate_personalized_intensity(
        self,
        planet_en: str,
        progress: float,
        natal_planets: List[Dict[str, Any]]
    ) -> int:
        """
        个性化强度计算
        结合：
        1. 行星基础强度
        2. 庙旺落陷
        3. 宫位权重
        4. 周期阶段
        """
        planet_cn = PLANET_EN_TO_CN.get(planet_en, planet_en)
        
        base_intensity = {
            "saturn": 8,
            "jupiter": 7,
            "mars": 9,
            "sun": 8,
            "venus": 6,
            "mercury": 6,
            "moon": 7,
            "north_node": 9,
            "south_node": 7,
        }
        
        base = base_intensity.get(planet_en, 5)
        
        planet_info = get_natal_planet_info(natal_planets, planet_cn)
        dignity_multiplier = 1.0
        house_multiplier = 1.0
        
        if planet_info:
            zodiac = planet_info.get("zodiac", {})
            sign_name = zodiac.get("sign", "")
            house = planet_info.get("house", 0)
            
            if sign_name:
                dignity_multiplier = get_planet_dignity_score(planet_cn, sign_name)
            
            if house and 1 <= house <= 12:
                house_multiplier = get_house_strength_score(house)
        
        phase_factor = 1.0
        if 30 <= progress <= 40:
            phase_factor = 1.2
        elif 60 <= progress <= 70:
            phase_factor = 1.15
        
        final_score = base * dignity_multiplier * house_multiplier * phase_factor
        
        return min(10, max(1, round(final_score)))

    def _get_period_themes(self, planet: str) -> List[str]:
        """获取周期主题"""
        themes = {
            "saturn": ["责任", "纪律", "耐心", "结构", "成长", "限制中学习"],
            "jupiter": ["扩张", "机遇", "学习", "旅行", "乐观", "信仰"],
            "mars": ["行动", "勇气", "竞争", "能量", "决断", "独立"],
            "sun": ["自我表达", "自信", "创造", "领导力", "认可", "真实"],
            "venus": ["关系", "美感", "价值", "爱情", "和谐", "愉悦"],
            "mercury": ["沟通", "学习", "思维", "写作", "灵活", "适应"],
            "moon": ["情感", "直觉", "家庭", "滋养", "安全感", "内心"],
            "north_node": ["命运", "成长", "方向", "连接", "灵魂目标", "进化"],
            "south_node": ["过去", "习惯", "安全区", "已掌握", "释放", "传承"],
        }
        return themes.get(planet, [])

    def _analyze_major_period_influence(
        self, 
        planet_en: str, 
        sign: Optional[str], 
        house: Optional[int], 
        progress: float,
        natal_planets: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """分析大运影响"""
        planet_cn = PLANET_EN_TO_CN.get(planet_en, planet_en)
        info = FIRDAIRA_PLANET_INFO.get(planet_en, {})
        is_node = info.get("is_node", False)
        
        phase = "early" if progress < 33 else "mid" if progress < 66 else "late"
        
        base_descriptions = {
            "saturn": {
                "early": f"这是{planet_cn}大运的开始阶段。{planet_cn}教导责任、纪律与耐心。你会感到生活中的某些领域需要更加务实和认真对待。可能会遇到一些考验和限制，但这是成长的必经之路。",
                "mid": f"{planet_cn}大运的中期，你开始真正理解{planet_cn}带来的教训。之前的努力开始显现成果，责任感加深，对长期目标有了更清晰的认识。",
                "late": f"{planet_cn}大运的收尾阶段，{planet_cn}的考验即将结束。你已经学会了耐心、坚持和责任。现在是收获的时候了，你建立的结构将为未来提供坚实的基础。"
            },
            "jupiter": {
                "early": f"{planet_cn}大运的开始，带来扩张与机遇的能量。好运似乎不期而至，适合探索新领域、学习新事物。保持开放心态，机会会比你想象的更多。",
                "mid": f"{planet_cn}大运的黄金时期，扩张能量达到顶峰。事业、学习、旅行都极为有利。但要注意不要过度自信或过度扩张，保持适度。",
                "late": f"{planet_cn}大运的尾声，扩张能量逐渐收敛。之前的机遇和学习成果需要巩固。回顾这段时期的成长，为下一阶段做准备。"
            },
            "mars": {
                "early": f"{planet_cn}大运启动，能量、行动、竞争是关键词。你会感到有更多动力去追求目标，但也可能更容易冲动或与人发生冲突。学会引导这股能量。",
                "mid": f"{planet_cn}大运的能量高峰期，行动力最强。适合需要勇气和决心的项目。注意控制脾气，避免鲁莽行事。",
                "late": f"{planet_cn}能量逐渐消退，从行动转向反思。回顾这段时期的成就与教训，学会更智慧地运用能量。"
            },
            "sun": {
                "early": f"{planet_cn}大运开始，自我表达、创造力、领导力成为主题。你会感到更有自信，更愿意展现真实的自我。适合追求个人目标和认可。",
                "mid": f"{planet_cn}大运的黄金时期，个人能量和自信达到顶峰。领导力显现，创造力充沛。注意不要过度自我中心，保持谦逊。",
                "late": f"{planet_cn}大运接近尾声，自我认同更加稳固。从追求外部认可转向内在满足。你已经找到了真正的自己。"
            },
            "venus": {
                "early": f"{planet_cn}大运开启，关系、美感、价值成为焦点。人际关系变得更加重要，可能有新的恋情或友谊。对艺术和美有更强的感知力。",
                "mid": f"{planet_cn}能量最盛时期，桃花运旺盛，社交活动频繁。适合发展亲密关系、提升美感。注意不要过度享乐或物质主义。",
                "late": f"{planet_cn}大运收尾，对关系和价值有更深的理解。学会在关系中保持平衡，真正理解什么是珍贵的。"
            },
            "mercury": {
                "early": f"{planet_cn}大运开始，思维、沟通、学习活跃。适合学习新技能、写作、教学、短途旅行。思维敏捷但可能分散，需要专注。",
                "mid": f"{planet_cn}能量高峰期，智力活动最为活跃。学习能力强，沟通顺畅。适合需要脑力和表达的工作。",
                "late": f"{planet_cn}大运尾声，思维方式更加成熟。从收集信息转向整合知识，学会在多变中保持灵活。"
            },
            "moon": {
                "early": f"{planet_cn}大运启动，情感、直觉、家庭变得重要。情绪更加敏感，需要情感滋养和安全感。可能与母亲或家人有更深入的连接。",
                "mid": f"{planet_cn}能量最盛，情感丰富，直觉敏锐。适合倾听内心声音，关注家庭和情感需求。注意不要过度情绪化或依赖他人。",
                "late": f"{planet_cn}大运收尾，情感更加成熟稳定。从寻求外部安全感转向内在的情绪自主。你已经学会了滋养自己和他人。"
            },
            "north_node": {
                "early": f"{planet_cn}大运是特殊的时期，象征命运的方向和灵魂的成长。这段时期可能会遇到重要的人和事，指引你走向人生的真正目标。",
                "mid": f"{planet_cn}能量的关键时期，命运的主题更加清晰。过去的经历让你理解了生命的方向，现在是朝着目标前进的时候。",
                "late": f"{planet_cn}大运即将完成，你已经吸收了这段时期的功课。对人生方向有了更深的领悟，准备好迎接新的循环。"
            },
            "south_node": {
                "early": f"{planet_cn}大运激活过去的模式和技能。这是回顾和整合你已经掌握的能力的时期。有些旧习惯可能带来安全感，但也需要识别哪些需要释放。",
                "mid": f"{planet_cn}能量中期，过去的模式清晰显现。你有机会看到哪些模式服务于你，哪些限制了你。这是一个清理和释放的时期。",
                "late": f"{planet_cn}大运收尾，你已经理解了过去的模式。学会从过去中学习，但不被过去束缚。准备好走向未来。"
            },
        }
        
        sign_context = ""
        if sign:
            sign_themes = {
                "白羊座": f"在白羊座的影响下，{planet_cn}展现出勇敢、直接和开拓精神。",
                "金牛座": f"在金牛座的影响下，{planet_cn}展现出稳重、务实和坚韧的品质。",
                "双子座": f"在双子座的影响下，{planet_cn}展现出灵活、好奇和善于沟通的特质。",
                "巨蟹座": f"在巨蟹座的影响下，{planet_cn}展现出关怀、保护和情绪化的一面。",
                "狮子座": f"在狮子座的影响下，{planet_cn}展现出自信、创造和领导能力。",
                "处女座": f"在处女座的影响下，{planet_cn}展现出细致、分析和服务精神。",
                "天秤座": f"在天秤座的影响下，{planet_cn}展现出和谐、美学和公正的追求。",
                "天蝎座": f"在天蝎座的影响下，{planet_cn}展现出深邃、转化和坚韧的力量。",
                "射手座": f"在射手座的影响下，{planet_cn}展现出乐观、探索和追求真理的精神。",
                "摩羯座": f"在摩羯座的影响下，{planet_cn}展现出稳重、野心和责任担当。",
                "水瓶座": f"在水瓶座的影响下，{planet_cn}展现出独特、创新和人道主义精神。",
                "双鱼座": f"在双鱼座的影响下，{planet_cn}展现出敏感、想象和灵性的特质。"
            }
            sign_context = sign_themes.get(sign, "")
        
        house_context = ""
        if house and 1 <= house <= 12:
            house_themes = {
                1: f"在第一宫，{planet_cn}影响你的自我认同和个人表现方式。",
                2: f"在第二宫，{planet_cn}影响你的自我价值感、财务和物质资源。",
                3: f"在第三宫，{planet_cn}影响你的思维方式、沟通和学习。",
                4: f"在第四宫，{planet_cn}影响你的家庭根基、情感安全和内心世界。",
                5: f"在第五宫，{planet_cn}影响你的创造力、自我表达和恋爱。",
                6: f"在第六宫，{planet_cn}影响你的健康、日常工作和服务他人。",
                7: f"在第七宫，{planet_cn}影响你的亲密关系、合作和伴侣关系。",
                8: f"在第八宫，{planet_cn}影响你的深度转化、共享资源和亲密连接。",
                9: f"在第九宫，{planet_cn}影响你的高等学习、旅行和哲学追求。",
                10: f"在第十宫，{planet_cn}影响你的事业成就、社会地位和公众形象。",
                11: f"在第十一宫，{planet_cn}影响你的社交网络、团体活动和未来愿景。",
                12: f"在第十二宫，{planet_cn}影响你的潜意识、灵性和隐秘之事。"
            }
            house_context = house_themes.get(house, "")
        
        planet_info = get_natal_planet_info(natal_planets, planet_cn)
        dignity_info = ""
        if planet_info:
            zodiac = planet_info.get("zodiac", {})
            sign_name = zodiac.get("sign", "")
            h = planet_info.get("house", 0)
            
            if sign_name:
                dignity = get_planet_dignity_score(planet_cn, sign_name)
                if dignity > 1.2:
                    dignity_info = f"{planet_cn}在{sign_name}庙旺，能量得到增强。"
                elif dignity < 0.8:
                    dignity_info = f"{planet_cn}在{sign_name}落陷，能量需要更多努力才能发挥。"
        
        full_description_parts = [
            base_descriptions.get(planet_en, {}).get(phase, ""),
        ]
        if sign_context:
            full_description_parts.append(sign_context)
        if house_context:
            full_description_parts.append(house_context)
        if dignity_info:
            full_description_parts.append(dignity_info)
        
        return {
            "phase": phase,
            "is_node": is_node,
            "base_description": base_descriptions.get(planet_en, {}).get(phase, ""),
            "sign_context": sign_context,
            "house_context": house_context,
            "dignity_info": dignity_info,
            "full_description": " ".join(filter(None, full_description_parts))
        }

    def _get_minor_combination_description(self, major_planet: str, minor_planet: str) -> str:
        """获取大小运组合描述"""
        major_cn = PLANET_EN_TO_CN.get(major_planet, major_planet)
        minor_cn = PLANET_EN_TO_CN.get(minor_planet, minor_planet)
        
        combinations = {
            ("saturn", "sun"): f"{major_cn}大运下的{minor_cn}小运：责任与自我表达的平衡。你需要在履行职责的同时找到自我实现的方式。",
            ("saturn", "moon"): f"{major_cn}大运下的{minor_cn}小运：情感需要稳定和结构。家庭事务需要更多关注，情绪需要耐心处理。",
            ("saturn", "mercury"): f"{major_cn}大运下的{minor_cn}小运：思维更加严谨和务实。适合详细规划、长期学习和专业研究。",
            ("saturn", "venus"): f"{major_cn}大运下的{minor_cn}小运：关系需要责任感和承诺。可能遇到需要认真对待的感情，或需要修复现有的关系。",
            ("saturn", "mars"): f"{major_cn}大运下的{minor_cn}小运：行动需要纪律和耐心。冲动可能带来挫折，学会战略性地运用能量。",
            ("saturn", "jupiter"): f"{major_cn}大运下的{minor_cn}小运：限制中有机遇。在责任框架内寻找扩展和成长的可能性。",
            ("saturn", "saturn"): f"{major_cn}大运下的{minor_cn}小运：双重{major_cn}能量，考验加剧但成长也加速。坚持就是胜利。",
            
            ("jupiter", "sun"): f"{major_cn}大运下的{minor_cn}小运：自我表达更加自信和乐观。适合追求个人目标，好运伴随。",
            ("jupiter", "moon"): f"{major_cn}大运下的{minor_cn}小运：情感更加开放和包容。家庭可能扩大，或有情感上的幸运。",
            ("jupiter", "mercury"): f"{major_cn}大运下的{minor_cn}小运：思维更加开阔，学习能力强。适合高等教育、写作和发表观点。",
            ("jupiter", "venus"): f"{major_cn}大运下的{minor_cn}小运：桃花运旺盛，社交活动频繁。适合恋爱和享受美好时光。",
            ("jupiter", "mars"): f"{major_cn}大运下的{minor_cn}小运：行动带来机遇。勇气和乐观的组合，适合大胆追求目标。",
            ("jupiter", "jupiter"): f"{major_cn}大运下的{minor_cn}小运：双重{major_cn}，扩张能量最强。机会众多，但要避免过度。",
            ("jupiter", "saturn"): f"{major_cn}大运下的{minor_cn}小运：乐观中需要谨慎。在扩展的同时建立稳固的基础。",
            
            ("mars", "sun"): f"{major_cn}大运下的{minor_cn}小运：行动力与自我认同融合。你更有动力去追求个人目标，展现真实的自我。",
            ("mars", "moon"): f"{major_cn}大运下的{minor_cn}小运：情绪与行动交织。需要注意控制情绪化的反应，学会冷静表达需求。",
            ("mars", "mercury"): f"{major_cn}大运下的{minor_cn}小运：思维敏锐且直接。适合快速决策和表达，但要注意言语不要过于尖锐。",
            ("mars", "venus"): f"{major_cn}大运下的{minor_cn}小运：激情与关系的组合。感情关系可能充满火花，但也要注意平衡与和谐。",
            ("mars", "mars"): f"{major_cn}大运下的{minor_cn}小运：双重{major_cn}能量，行动力极强。适合需要决心和勇气的重大行动。",
            ("mars", "jupiter"): f"{major_cn}大运下的{minor_cn}小运：行动与扩张的完美组合。勇气和乐观带来重大机遇。",
            ("mars", "saturn"): f"{major_cn}大运下的{minor_cn}小运：行动需要纪律。冲动会被约束，学会有策略地运用能量。",
            
            ("sun", "sun"): f"{major_cn}大运下的{minor_cn}小运：双重自我能量，自信达到顶峰。适合展现自我、追求认可和领导角色。",
            ("sun", "moon"): f"{major_cn}大运下的{minor_cn}小运：自我与情感的平衡。你需要在展现自我的同时关注内心感受。",
            ("sun", "mercury"): f"{major_cn}大运下的{minor_cn}小运：自我表达流畅。思维与自我认同融合，适合沟通、教学和表达观点。",
            ("sun", "venus"): f"{major_cn}大运下的{minor_cn}小运：自我价值与美感的结合。适合发展个人风格、享受美好和建立关系。",
            ("sun", "mars"): f"{major_cn}大运下的{minor_cn}小运：自我与行动的融合。你有强烈的动力去实现个人目标，展现领导能力。",
            ("sun", "jupiter"): f"{major_cn}大运下的{minor_cn}小运：自我与扩张的组合。自信和乐观带来好运，适合追求个人发展。",
            ("sun", "saturn"): f"{major_cn}大运下的{minor_cn}小运：自我需要纪律。在展现自我的同时需要责任感和耐心。",
            
            ("venus", "sun"): f"{major_cn}大运下的{minor_cn}小运：在关系中展现自我。社交场合中你更加自信和有魅力。",
            ("venus", "moon"): f"{major_cn}大运下的{minor_cn}小运：情感与美感融合。对美和艺术有更深的感受，情感关系更加和谐。",
            ("venus", "mercury"): f"{major_cn}大运下的{minor_cn}小运：沟通与美感结合。社交场合中你能言善辩，善于调解和协调。",
            ("venus", "venus"): f"{major_cn}大运下的{minor_cn}小运：双重{major_cn}能量，关系和美感到达顶峰。桃花运旺盛，适合恋爱和社交。",
            ("venus", "mars"): f"{major_cn}大运下的{minor_cn}小运：激情与吸引力的组合。感情关系充满火花，可能有强烈的吸引力。",
            ("venus", "jupiter"): f"{major_cn}大运下的{minor_cn}小运：社交扩张期。人脉扩展，社交活动增多，可能遇到重要的人际关系。",
            ("venus", "saturn"): f"{major_cn}大运下的{minor_cn}小运：关系需要承诺。感情关系进入更加严肃的阶段，或需要修复。",
            
            ("mercury", "sun"): f"{major_cn}大运下的{minor_cn}小运：思维与自我表达融合。你更愿意表达自己的想法，适合教学和演讲。",
            ("mercury", "moon"): f"{major_cn}大运下的{minor_cn}小运：思维与情感交织。你的言语带有情感色彩，善于表达感受。",
            ("mercury", "mercury"): f"{major_cn}大运下的{minor_cn}小运：双重{major_cn}能量，思维和沟通最活跃。适合学习、写作和各种智力活动。",
            ("mercury", "venus"): f"{major_cn}大运下的{minor_cn}小运：思维与美感结合。你的言语优雅，善于调解，社交场合表现出色。",
            ("mercury", "mars"): f"{major_cn}大运下的{minor_cn}小运：思维敏捷且直接。适合快速决策和辩论，但要注意言语不要过于尖锐。",
            ("mercury", "jupiter"): f"{major_cn}大运下的{minor_cn}小运：思维开阔，学习能力强。适合高等教育、旅行和哲学思考。",
            ("mercury", "saturn"): f"{major_cn}大运下的{minor_cn}小运：思维严谨实际。适合详细规划、长期研究和专业学习。",
            
            ("moon", "sun"): f"{major_cn}大运下的{minor_cn}小运：情感与自我的平衡。你需要在关注内心感受的同时展现自我。",
            ("moon", "moon"): f"{major_cn}大运下的{minor_cn}小运：双重{major_cn}能量，情感最丰富。直觉敏锐，与家庭和内心世界连接最深。",
            ("moon", "mercury"): f"{major_cn}大运下的{minor_cn}小运：情感与思维交织。你的表达带有情感色彩，善于理解他人的感受。",
            ("moon", "venus"): f"{major_cn}大运下的{minor_cn}小运：情感与美感融合。对美和艺术有更深的感受，情感关系更加和谐。",
            ("moon", "mars"): f"{major_cn}大运下的{minor_cn}小运：情绪与行动交织。需要注意控制情绪化的反应，学会冷静表达需求。",
            ("moon", "jupiter"): f"{major_cn}大运下的{minor_cn}小运：情感与扩张结合。家庭可能扩大，或有情感上的幸运和成长。",
            ("moon", "saturn"): f"{major_cn}大运下的{minor_cn}小运：情感需要稳定和结构。家庭事务需要更多关注，情绪需要耐心处理。",
        }
        
        return combinations.get((major_planet, minor_planet), 
            f"{major_cn}大运下的{minor_cn}小运，两种能量的互动创造独特的成长机会。"
        )

    def analyze_firdaria_influence(
        self, 
        birth_date: datetime, 
        target_year: int, 
        natal_planets: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """分析法达推运影响"""
        try:
            sun_longitude = get_sun_longitude(natal_planets)
            
            periods_info = self.get_active_periods_for_year(
                birth_date, target_year, sun_longitude, natal_planets
            )
            
            if not periods_info.get("has_active_period"):
                return periods_info
            
            major_period = periods_info.get("major_period", {})
            major_planet_en = major_period.get("planet", "")
            major_planet_cn = PLANET_EN_TO_CN.get(major_planet_en, major_planet_en)
            progress = major_period.get("progress_percent", 0)
            
            planet_info = get_natal_planet_info(natal_planets, major_planet_cn)
            planet_sign = None
            planet_house = None
            
            if planet_info:
                zodiac = planet_info.get("zodiac", {})
                planet_sign = zodiac.get("sign")
                planet_house = planet_info.get("house")
            
            influence_analysis = self._analyze_major_period_influence(
                major_planet_en,
                planet_sign,
                planet_house,
                progress,
                natal_planets
            )
            
            minor_analysis = None
            minor_period = periods_info.get("minor_period")
            if minor_period:
                minor_planet_en = minor_period.get("planet", "")
                minor_planet_cn = PLANET_EN_TO_CN.get(minor_planet_en, minor_planet_en)
                
                minor_info = get_natal_planet_info(natal_planets, minor_planet_cn)
                minor_sign = None
                minor_house = None
                
                if minor_info:
                    zodiac = minor_info.get("zodiac", {})
                    minor_sign = zodiac.get("sign")
                    minor_house = minor_info.get("house")
                
                combination_desc = self._get_minor_combination_description(
                    major_planet_en, minor_planet_en
                )
                
                minor_analysis = {
                    "description": combination_desc,
                    "major_planet": major_planet_en,
                    "major_planet_name": major_planet_cn,
                    "minor_planet": minor_planet_en,
                    "minor_planet_name": minor_planet_cn,
                    "minor_sign": minor_sign,
                    "minor_house": minor_house,
                }
            
            intensity_score = self._calculate_personalized_intensity(
                major_planet_en, progress, natal_planets
            )
            
            return {
                **periods_info,
                "major_planet_sign": planet_sign,
                "major_planet_house": planet_house,
                "influence_analysis": influence_analysis,
                "minor_analysis": minor_analysis,
                "intensity_score": intensity_score,
                "themes": self._get_period_themes(major_planet_en),
            }
            
        except Exception as e:
            logger.error(f"分析法达推运失败: {str(e)}", exc_info=True)
            return {
                "has_active_period": False,
                "message": f"分析失败: {str(e)}",
                "error": str(e),
            }

    def get_key_firdaria_years(
        self, 
        birth_date: datetime,
        sun_longitude: float = 180.0,
        natal_planets: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """获取关键法达年份"""
        try:
            periods = self.calculate_firdaria_periods(birth_date, sun_longitude, natal_planets)
            
            key_years = []
            birth_year = birth_date.year
            
            for period in periods:
                info = period.info
                
                start_year = birth_year + int(period.start_age)
                mid_year = birth_year + int((period.start_age + period.end_age) / 2)
                
                key_years.append({
                    "year": start_year,
                    "age": round(period.start_age),
                    "type": "major_start",
                    "planet": period.planet,
                    "planet_name": info.get("name", ""),
                    "planet_symbol": info.get("symbol", ""),
                    "description": f"开始{info.get('name', '')}大运（{info.get('years', 0)}年）",
                    "intensity": 9,
                    "is_node": info.get("is_node", False),
                })
                
                key_years.append({
                    "year": mid_year,
                    "age": round((period.start_age + period.end_age) / 2),
                    "type": "major_mid",
                    "planet": period.planet,
                    "planet_name": info.get("name", ""),
                    "planet_symbol": info.get("symbol", ""),
                    "description": f"{info.get('name', '')}大运高峰期",
                    "intensity": 10,
                    "is_node": info.get("is_node", False),
                })
                
                for i, minor in enumerate(period.minor_periods[:2]):
                    minor_year = birth_year + int(minor["start_age"])
                    key_years.append({
                        "year": minor_year,
                        "age": round(minor["start_age"]),
                        "type": "minor_start",
                        "planet": minor["planet"],
                        "planet_name": minor["planet_name"],
                        "planet_symbol": minor["planet_symbol"],
                        "description": f"{minor['planet_name']}小运开始",
                        "intensity": 7,
                    })
            
            key_years.sort(key=lambda x: x["year"])
            
            seen = set()
            unique = []
            for ky in key_years:
                key = f"{ky['year']}_{ky['type']}_{ky.get('planet', '')}"
                if key not in seen:
                    seen.add(key)
                    unique.append(ky)
            
            return unique
            
        except Exception as e:
            logger.error(f"获取关键年份失败: {str(e)}", exc_info=True)
            return []


firdaria_calculator = FirdariaCalculator()


def get_firdaria_calculator() -> FirdariaCalculator:
    return firdaria_calculator
