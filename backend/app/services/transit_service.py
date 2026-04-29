import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum

from app.services.ephemeris_calculator import (
    get_ephemeris_calculator,
    ASPECT_DEFINITIONS,
    MOON_PHASES,
    Planet
)
from app.services.energy_scoring import (
    get_energy_scoring_engine,
    Dimension,
    DIMENSION_INFO as DIMENSION_CONFIG,
    ENERGY_LEVEL_LABELS
)
from app.astro import MAIN_PLANETS, PLANET_INFO, SE_FLAGS, longitude_to_zodiac

logger = logging.getLogger(__name__)

ephemeris_calculator = get_ephemeris_calculator()
energy_engine = get_energy_scoring_engine()


TransitDimension = Dimension

DIMENSION_INFO = DIMENSION_CONFIG

ASPECT_TYPES_TRANSIT = [
    {k: v for k, v in d.items() if k != "type"}
    for d in ASPECT_DEFINITIONS
]


def get_aspect_nature(aspect_name: str) -> str:
    """获取相位性质（向后兼容）"""
    aspect_map = {
        "合相": "neutral",
        "六分相": "harmonious",
        "四分相": "challenging",
        "三分相": "harmonious",
        "对分相": "challenging"
    }
    return aspect_map.get(aspect_name, "neutral")


def calculate_transit_planets(jd: float) -> List[Dict[str, Any]]:
    """计算行运行星位置（向后兼容）"""
    return ephemeris_calculator.calculate_multiple_planets(jd, MAIN_PLANETS)


def calculate_transit_aspects(
    natal_planets: List[Dict[str, Any]],
    transit_planets: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """计算本命盘与行运行星的相位（向后兼容）"""
    aspects = ephemeris_calculator.calculate_all_aspects(
        natal_planets, transit_planets
    )
    
    transformed = []
    for aspect in aspects:
        transformed.append({
            "natal_planet": aspect["planet1_name"],
            "natal_planet_symbol": aspect["planet1_symbol"],
            "natal_zodiac": aspect["planet1_zodiac"],
            "transit_planet": aspect["planet2_name"],
            "transit_planet_symbol": aspect["planet2_symbol"],
            "transit_zodiac": aspect["planet2_zodiac"],
            "aspect": aspect["name"],
            "aspect_symbol": aspect["symbol"],
            "angle": aspect["angle"],
            "actual_angle": aspect["actual_angle"],
            "orb": aspect["orb"],
            "influence": aspect["influence"],
            "nature": aspect["nature"],
            "is_applying": aspect["is_applying"]
        })
    
    return transformed


def calculate_moon_phase(jd: float) -> Dict[str, Any]:
    """计算月相（向后兼容）"""
    return ephemeris_calculator.calculate_moon_phase(jd)


def check_mercury_retrograde(jd: float) -> Dict[str, Any]:
    """检测水星逆行（向后兼容）"""
    result = ephemeris_calculator.check_mercury_retrograde(jd)
    return {
        "is_retrograde": result["is_retrograde"],
        "speed": result["speed"],
        "status": result["status"]
    }


def calculate_dimension_energy(
    aspects: List[Dict[str, Any]],
    dimension: TransitDimension,
    natal_planets: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """计算维度能量（向后兼容）"""
    return energy_engine.calculate_dimension_energy(aspects, dimension, natal_planets)


def calculate_overall_energy(dimensions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """计算整体能量（向后兼容）"""
    return energy_engine.calculate_overall_energy(dimensions)


def calculate_7day_trend(
    natal_planets: List[Dict[str, Any]],
    start_date: datetime,
    latitude: float,
    longitude: float,
    house_system: str = "placidus"
) -> List[Dict[str, Any]]:
    """
    计算7天能量趋势（向后兼容）
    
    注意：此函数需要从 app.astro 导入 local_to_utc 和 utc_to_julday
    """
    from app.astro import local_to_utc, utc_to_julday
    
    trend_data = []
    
    for day_offset in range(7):
        current_date = start_date + timedelta(days=day_offset)
        
        utc_dt, _ = local_to_utc(
            current_date.year, current_date.month, current_date.day,
            12, 0, latitude, longitude
        )
        jd = utc_to_julday(utc_dt)
        
        transit_planets = calculate_transit_planets(jd)
        aspects = calculate_transit_aspects(natal_planets, transit_planets)
        
        dimensions = []
        for dim in TransitDimension:
            dim_energy = calculate_dimension_energy(aspects, dim, natal_planets)
            dimensions.append(dim_energy)
        
        overall = calculate_overall_energy(dimensions)
        
        moon_phase = calculate_moon_phase(jd)
        mercury_retro = check_mercury_retrograde(jd)
        
        key_aspects = aspects[:5]
        
        trend_data.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "day_of_week": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][current_date.weekday()],
            "overall_score": overall["overall_score"],
            "mood": overall["mood"],
            "mood_label": overall["mood_label"],
            "dimensions": {
                d["dimension"]: {
                    "score": d["score"],
                    "level": d["level"],
                    "level_label": d["level_label"]
                }
                for d in dimensions
            },
            "moon_phase": moon_phase,
            "mercury_status": mercury_retro,
            "key_aspects": [
                {
                    "natal_planet": a["natal_planet"],
                    "natal_symbol": a["natal_planet_symbol"],
                    "transit_planet": a["transit_planet"],
                    "transit_symbol": a["transit_planet_symbol"],
                    "aspect": a["aspect"],
                    "aspect_symbol": a["aspect_symbol"],
                    "nature": a["nature"],
                    "influence": a["influence"]
                }
                for a in key_aspects
            ]
        })
    
    return trend_data


def analyze_key_events(
    transit_planets: List[Dict[str, Any]],
    aspects: List[Dict[str, Any]],
    moon_phase: Dict[str, Any],
    mercury_retro: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """分析关键星象事件（向后兼容）"""
    events = []
    
    if moon_phase["is_full_moon"]:
        events.append({
            "type": "lunar_event",
            "title": "满月",
            "icon": "🌕",
            "description": "今日满月，情绪能量高涨，适合复盘与释放。",
            "importance": "high"
        })
    elif moon_phase["is_new_moon"]:
        events.append({
            "type": "lunar_event",
            "title": "新月",
            "icon": "🌑",
            "description": "今日新月，适合设定新目标，开启新计划。",
            "importance": "high"
        })
    elif moon_phase["illumination"] >= 95:
        events.append({
            "type": "lunar_event",
            "title": "满月前夕",
            "icon": "🌕",
            "description": f"月亮{moon_phase['illumination']}%照亮，即将迎来满月，注意情绪波动。",
            "importance": "medium"
        })
    elif moon_phase["illumination"] <= 5:
        events.append({
            "type": "lunar_event",
            "title": "新月前夕",
            "icon": "🌑",
            "description": f"月亮{moon_phase['illumination']}%照亮，能量内敛，适合休息充电。",
            "importance": "medium"
        })
    
    if mercury_retro["is_retrograde"]:
        events.append({
            "type": "planetary_event",
            "title": "水逆进行中",
            "icon": "☿",
            "description": "水星逆行期间，注意沟通细节、电子设备备份、出行计划预留缓冲时间。",
            "importance": "high"
        })
    
    for planet in transit_planets:
        if planet["is_retrograde"] and planet["name"] not in ["水星", "北交点", "南交点"]:
            events.append({
                "type": "planetary_event",
                "title": f"{planet['name']}逆行",
                "icon": planet["symbol"],
                "description": f"{planet['name']}正在逆行，适合回顾、反思与重新评估相关领域。",
                "importance": "medium"
            })
    
    significant_aspects = [a for a in aspects if a["influence"] >= 0.7]
    for aspect in significant_aspects[:5]:
        nature_label = "和谐" if aspect["nature"] == "harmonious" else "紧张" if aspect["nature"] == "challenging" else "中性"
        events.append({
            "type": "aspect_event",
            "title": f"{aspect['transit_planet']}{aspect['aspect_symbol']}{aspect['natal_planet']}",
            "icon": aspect["aspect_symbol"],
            "description": f"行运{aspect['transit_planet']}与本命{aspect['natal_planet']}形成{aspect['aspect']}({nature_label})，影响力{round(aspect['influence']*100)}%。",
            "importance": "high" if aspect["influence"] >= 0.85 else "medium",
            "nature": aspect["nature"]
        })
    
    events.sort(key=lambda x: {
        "high": 3,
        "medium": 2,
        "low": 1
    }.get(x.get("importance", "low"), 1), reverse=True)
    
    return events


def generate_transit_analysis_prompt(
    transit_data: Dict[str, Any],
    natal_planets: List[Dict[str, Any]]
) -> str:
    """生成AI解读提示词（向后兼容）"""
    overall = transit_data.get("overall", {})
    dimensions = transit_data.get("dimensions", [])
    aspects = transit_data.get("aspects", [])
    key_events = transit_data.get("key_events", [])
    moon_phase = transit_data.get("moon_phase", {})
    mercury_retro = transit_data.get("mercury_retrograde", {})
    
    prompt_parts = [
        "你是一位专业的占星师，请根据以下行运数据，为用户生成一份个性化的每日运势解读。\n",
        f"\n【今日整体运势】",
        f"- 整体能量指数: {overall.get('overall_score', 50)}分",
        f"- 星象天气: {overall.get('mood_label', '未知')} {overall.get('mood', '')}",
        f"- 描述: {overall.get('description', '')}",
    ]
    
    if overall.get("high_dimensions"):
        prompt_parts.append(f"- 能量旺盛领域: {', '.join(overall['high_dimensions'])}")
    if overall.get("low_dimensions"):
        prompt_parts.append(f"- 能量低迷领域: {', '.join(overall['low_dimensions'])}")
    
    prompt_parts.append("\n【各维度能量】")
    for dim in dimensions:
        prompt_parts.append(
            f"- {dim['icon']} {dim['name_cn']}: {dim['score']}分 ({dim['level_label']})"
        )
        prompt_parts.append(f"  说明: {dim['description']}")
    
    prompt_parts.append("\n【重要星象事件】")
    for event in key_events[:5]:
        prompt_parts.append(f"- {event['icon']} {event['title']}: {event['description']}")
    
    prompt_parts.append("\n【关键相位】")
    for aspect in aspects[:8]:
        nature_label = "和谐" if aspect["nature"] == "harmonious" else "紧张" if aspect["nature"] == "challenging" else "中性"
        prompt_parts.append(
            f"- 行运{aspect['transit_planet']}{aspect['aspect_symbol']}本命{aspect['natal_planet']} "
            f"({aspect['aspect']} - {nature_label}, 影响力{round(aspect['influence']*100)}%)"
        )
    
    prompt_parts.append("\n【月相状态】")
    prompt_parts.append(f"- 当前月相: {moon_phase.get('phase_symbol', '')} {moon_phase.get('phase_name', '未知')}")
    prompt_parts.append(f"- 照亮程度: {moon_phase.get('illumination', 0)}%")
    if moon_phase.get("next_full_moon_days"):
        prompt_parts.append(f"- 距离下次满月: {moon_phase['next_full_moon_days']}天")
    
    prompt_parts.append("\n【生成要求】")
    prompt_parts.append("请按照以下结构生成解读文案：")
    prompt_parts.append("1. 今日整体运势概述（3-4句话，要具体有画面感）")
    prompt_parts.append("2. 各维度详细解读（沟通、社交、事业、财运、情绪，每个维度2-3句话）")
    prompt_parts.append("3. 今日机遇（3-4个具体的机会点）")
    prompt_parts.append("4. 今日挑战（2-3个需要注意的问题）")
    prompt_parts.append("5. 行动建议（3-4条具体可执行的建议）")
    prompt_parts.append("\n要求：")
    prompt_parts.append("- 语言要通俗易懂，但要有占星专业度")
    prompt_parts.append("- 避免空泛的套话，要结合具体的行运相位")
    prompt_parts.append("- 语气要积极、建设性，避免负面断言")
    prompt_parts.append("- 要个性化，不要使用通用模板语言")
    
    return "\n".join(prompt_parts)


def generate_fallback_interpretation(transit_data: Dict[str, Any]) -> str:
    """生成备用解读（当AI API失败时使用）"""
    overall = transit_data.get("overall", {})
    dimensions = transit_data.get("dimensions", [])
    key_events = transit_data.get("key_events", [])
    
    sections = []
    
    sections.append("## 今日整体运势概述")
    sections.append(f"今日整体能量指数为{overall.get('overall_score', 50)}分，星象呈现「{overall.get('mood_label', '平稳')}」状态。{overall.get('description', '')}")
    
    if overall.get("high_dimensions"):
        sections.append(f"今日{', '.join(overall['high_dimensions'])}领域能量旺盛，适合在这些方面积极行动。")
    if overall.get("low_dimensions"):
        sections.append(f"需要注意{', '.join(overall['low_dimensions'])}领域可能遇到的挑战，保持耐心和灵活应对。")
    
    sections.append("\n## 各维度详细解读")
    for dim in dimensions:
        sections.append(f"\n### {dim['icon']} {dim['name_cn']}运势（{dim['score']}分）")
        sections.append(dim['description'])
        
        if dim['dominant_influence'] == 'harmonious':
            sections.append(f"今日{dim['name_cn']}领域和谐相位为主，能量流动顺畅，容易获得正面反馈。")
        elif dim['dominant_influence'] == 'challenging':
            sections.append(f"今日{dim['name_cn']}领域需要更多注意力，挑战相位提醒你保持警觉和灵活性。")
    
    sections.append("\n## 今日机遇")
    opportunities = [
        "利用能量高峰时段处理重要事务",
        "关注沟通领域的新机会",
        "保持开放心态，接受新的可能性",
        "回顾近期的进展，确认目标方向"
    ]
    for i, opp in enumerate(opportunities[:4], 1):
        sections.append(f"{i}. {opp}")
    
    sections.append("\n## 今日挑战")
    challenges = [
        "注意情绪波动，保持冷静",
        "避免冲动决策，三思而后行",
        "关注细节，防止疏漏",
        "给自己留出缓冲时间"
    ]
    for i, chal in enumerate(challenges[:3], 1):
        sections.append(f"{i}. {chal}")
    
    sections.append("\n## 行动建议")
    suggestions = [
        "早晨花5分钟冥想或规划今日目标",
        "将重要任务安排在精力最充沛的时段",
        "保持适度休息，避免过度消耗",
        "记录今日的感悟和灵感"
    ]
    for i, sug in enumerate(suggestions[:4], 1):
        sections.append(f"{i}. {sug}")
    
    return "\n".join(sections)


class TransitAnalysisEngine:
    """
    行运分析引擎 - 整合星历计算和能量打分
    
    这是一个更高级的接口，用于更复杂的行运分析
    """
    
    def __init__(self):
        self.ephemeris = ephemeris_calculator
        self.energy = energy_engine
    
    def calculate_full_transit(
        self,
        natal_planets: List[Dict[str, Any]],
        target_date: datetime,
        latitude: float,
        longitude: float,
        house_system: str = "placidus",
        timezone_str: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        计算完整的行运分析（使用时区服务）
        
        Args:
            natal_planets: 本命盘行星列表
            target_date: 目标日期（本地时间）
            latitude: 纬度
            longitude: 经度
            house_system: 宫位系统
            timezone_str: 可选时区字符串
            
        Returns:
            完整的行运分析数据
        """
        jd, debug_info = self.ephemeris.local_time_to_julday(
            target_date.year, target_date.month, target_date.day,
            target_date.hour, target_date.minute,
            latitude, longitude, timezone_str
        )
        
        transit_planets = self.ephemeris.calculate_multiple_planets(jd)
        
        aspects = self.ephemeris.calculate_all_aspects(natal_planets, transit_planets)
        
        dimensions = self.energy.calculate_all_dimensions(aspects, natal_planets)
        
        overall = self.energy.calculate_overall_energy(dimensions)
        
        moon_phase = self.ephemeris.calculate_moon_phase(jd)
        
        mercury_retro = self.ephemeris.check_mercury_retrograde(jd)
        
        return {
            "target_date": target_date.strftime("%Y-%m-%d %H:%M"),
            "julday": jd,
            "timezone_info": debug_info,
            "transit_planets": transit_planets,
            "aspects": aspects,
            "aspects_count": len(aspects),
            "moon_phase": moon_phase,
            "mercury_retrograde": {
                "is_retrograde": mercury_retro["is_retrograde"],
                "speed": mercury_retro["speed"],
                "status": mercury_retro["status"]
            },
            "dimensions": dimensions,
            "overall": overall
        }
    
    def calculate_trend(
        self,
        natal_planets: List[Dict[str, Any]],
        start_date: datetime,
        latitude: float,
        longitude: float,
        days: int = 7,
        house_system: str = "placidus"
    ) -> Dict[str, Any]:
        """
        计算多天能量趋势
        
        Args:
            natal_planets: 本命盘行星
            start_date: 开始日期
            latitude: 纬度
            longitude: 经度
            days: 天数（默认7天）
            house_system: 宫位系统
            
        Returns:
            趋势分析数据
        """
        trend_data = []
        
        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)
            
            transit = self.calculate_full_transit(
                natal_planets,
                current_date.replace(hour=12, minute=0),
                latitude,
                longitude,
                house_system
            )
            
            trend_data.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "day_of_week": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][current_date.weekday()],
                "overall_score": transit["overall"]["overall_score"],
                "mood": transit["overall"]["mood"],
                "mood_label": transit["overall"]["mood_label"],
                "dimensions": {
                    d["dimension"]: {
                        "score": d["score"],
                        "level": d["level"],
                        "level_label": d["level_label"]
                    }
                    for d in transit["dimensions"]
                },
                "moon_phase": transit["moon_phase"],
                "mercury_status": transit["mercury_retrograde"],
                "key_aspects": [
                    {
                        "natal_planet": a.get("planet1_name", a.get("natal_planet", "")),
                        "natal_symbol": a.get("planet1_symbol", a.get("natal_planet_symbol", "")),
                        "transit_planet": a.get("planet2_name", a.get("transit_planet", "")),
                        "transit_symbol": a.get("planet2_symbol", a.get("transit_planet_symbol", "")),
                        "aspect": a.get("name", a.get("aspect", "")),
                        "aspect_symbol": a.get("symbol", a.get("aspect_symbol", "")),
                        "nature": a.get("nature", "neutral"),
                        "influence": a.get("influence", 0.5)
                    }
                    for a in transit["aspects"][:5]
                ]
            })
        
        all_scores = [day["overall_score"] for day in trend_data]
        max_score = max(all_scores) if all_scores else 50
        min_score = min(all_scores) if all_scores else 50
        
        max_day = next((d for d in trend_data if d["overall_score"] == max_score), None)
        min_day = next((d for d in trend_data if d["overall_score"] == min_score), None)
        
        turning_points = []
        for i in range(1, len(trend_data) - 1):
            prev = trend_data[i - 1]["overall_score"]
            curr = trend_data[i]["overall_score"]
            next_score = trend_data[i + 1]["overall_score"]
            
            if (curr > prev and curr > next_score) or (curr < prev and curr < next_score):
                turning_points.append({
                    "index": i,
                    "date": trend_data[i]["date"],
                    "day_of_week": trend_data[i]["day_of_week"],
                    "score": curr,
                    "type": "peak" if curr > prev else "valley",
                    "mood": trend_data[i]["mood"],
                    "mood_label": trend_data[i]["mood_label"]
                })
        
        return {
            "trend_data": trend_data,
            "summary": {
                "max_score": max_score,
                "max_day": max_day,
                "min_score": min_score,
                "min_day": min_day,
                "avg_score": round(sum(all_scores) / len(all_scores), 1) if all_scores else 50,
                "turning_points": turning_points
            }
        }


transit_analysis_engine = TransitAnalysisEngine()


def get_transit_analysis_engine() -> TransitAnalysisEngine:
    """获取行运分析引擎单例"""
    return transit_analysis_engine
