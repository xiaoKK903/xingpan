import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import json
import hashlib
import asyncio
from concurrent.futures import ThreadPoolExecutor
import functools

from app.services.transit_service import get_transit_analysis_engine
from app.services.firdaria_service import get_firdaria_calculator
from app.services.progression_service import get_progression_calculator
from app.services.cache_service import get_cache_service
from app.services.ai_service import call_deepseek_api, call_qwen_api
from app.astro import (
    parse_birth_datetime, local_to_utc, utc_to_julday,
    calculate_all_planets, calculate_houses_ex
)

logger = logging.getLogger(__name__)

transit_engine = get_transit_analysis_engine()
firdaria_calculator = get_firdaria_calculator()
progression_calculator = get_progression_calculator()
cache_service = get_cache_service()

_executor = ThreadPoolExecutor(max_workers=4)
_natal_cache: Dict[str, Any] = {}


class ScriptMood(str, Enum):
    OPTIMISTIC = "optimistic"
    CHALLENGING = "challenging"
    SERIOUS = "serious"
    HARMONIOUS = "harmonious"
    TRANSFORMATIVE = "transformative"
    NEUTRAL = "neutral"


class LifeScriptAnalyzer:
    def __init__(self):
        self._script_cache: Dict[str, Any] = {}
        self._cache_max_age = 7 * 24 * 60 * 60

    def _generate_natal_cache_key(self, birth_date: str, birth_time: str, latitude: float, longitude: float, house_system: str) -> str:
        key_data = {
            "birth_date": birth_date,
            "birth_time": birth_time,
            "latitude": round(latitude, 4),
            "longitude": round(longitude, 4),
            "house_system": house_system,
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return f"natal:{hashlib.md5(key_str.encode()).hexdigest()}"

    def _generate_cache_key(self, birth_date: str, birth_time: str, latitude: float, longitude: float, target_year: int, house_system: str) -> str:
        key_data = {
            "birth_date": birth_date,
            "birth_time": birth_time,
            "latitude": round(latitude, 4),
            "longitude": round(longitude, 4),
            "target_year": target_year,
            "house_system": house_system,
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return f"lifescript:{hashlib.md5(key_str.encode()).hexdigest()}"

    def _prepare_natal_data(
        self,
        birth_date: str,
        birth_time: str,
        latitude: float,
        longitude: float,
        house_system: str
    ) -> Dict[str, Any]:
        cache_key = self._generate_natal_cache_key(birth_date, birth_time, latitude, longitude, house_system)
        
        cached = cache_service.get(cache_key)
        if cached:
            logger.info("使用缓存的本命盘数据")
            return cached
        
        birth_dt = parse_birth_datetime(birth_date, birth_time)
        utc_dt, _ = local_to_utc(
            birth_dt["year"], birth_dt["month"], birth_dt["day"],
            birth_dt["hour"], birth_dt["minute"],
            latitude, longitude
        )
        jd = utc_to_julday(utc_dt)
        
        houses_result = calculate_houses_ex(
            jd, latitude, longitude, house_system
        )
        house_cusps = houses_result["house_cusps"]
        
        natal_planets = calculate_all_planets(jd, house_cusps)
        
        main_planet_names = ["太阳", "月亮", "水星", "金星", "火星", "木星", "土星", "天王星", "海王星", "冥王星", "北交点", "南交点"]
        natal_planets = [p for p in natal_planets if p.get("name") in main_planet_names]
        
        birth_datetime = datetime(birth_dt["year"], birth_dt["month"], birth_dt["day"], birth_dt["hour"], birth_dt["minute"])
        
        result = {
            "birth_datetime": birth_datetime,
            "birth_jd": jd,
            "natal_planets": natal_planets,
            "house_cusps": house_cusps,
            "latitude": latitude,
            "longitude": longitude,
        }
        
        cache_service.set(cache_key, result, ttl=7 * 86400)
        
        return result

    def analyze_year(
        self,
        birth_date: str,
        birth_time: str,
        latitude: float,
        longitude: float,
        target_year: int,
        house_system: str = "placidus",
        natal_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        cache_key = self._generate_cache_key(birth_date, birth_time, latitude, longitude, target_year, house_system)
        
        cached = cache_service.get(cache_key)
        if cached:
            logger.info(f"使用缓存的人生剧本分析: {target_year}")
            return cached
        
        if natal_data is None:
            natal_data = self._prepare_natal_data(birth_date, birth_time, latitude, longitude, house_system)
        
        birth_datetime = natal_data["birth_datetime"]
        birth_jd = natal_data["birth_jd"]
        natal_planets = natal_data["natal_planets"]
        latitude = natal_data["latitude"]
        longitude = natal_data["longitude"]
        
        target_age = target_year - birth_datetime.year
        
        transit_data = self._analyze_transit_for_year(birth_datetime, natal_planets, latitude, longitude, target_year)
        
        firdaria_data = firdaria_calculator.analyze_firdaria_influence(
            birth_datetime, target_year, natal_planets
        )
        
        progression_data = progression_calculator.analyze_progressed_chart(
            birth_datetime, birth_jd, latitude, longitude, natal_planets, target_age, "secondary"
        )
        
        solar_arc_data = None
        if target_age >= 10:
            solar_arc_data = progression_calculator.analyze_progressed_chart(
                birth_datetime, birth_jd, latitude, longitude, natal_planets, target_age, "solar_arc"
            )
        
        combined_analysis = self._combine_analyses(
            transit_data,
            firdaria_data,
            progression_data,
            solar_arc_data,
            target_year,
            target_age
        )
        
        year_overview = {
            "overall_mood": combined_analysis.get("mood", "neutral"),
            "overall_mood_label": combined_analysis.get("mood_label", "平稳"),
            "overall_mood_description": combined_analysis.get("mood_description", "这一年能量相对平稳，适合稳步前行。"),
            "combined_intensity": combined_analysis.get("combined_intensity", 5),
            "is_key_year": combined_analysis.get("is_key_year", False),
            "has_saturn_return": combined_analysis.get("has_saturn_return", False),
            "has_major_outer_transit": combined_analysis.get("has_major_outer_transit", False),
        }
        
        dimensions = combined_analysis.get("dimensions", {})
        domains_summary = [
            {
                "domain": dim_key,
                "name": dim.get("name", ""),
                "intensity": dim.get("score", 50) // 10,
                "score": dim.get("score", 50),
                "level": dim.get("level", "medium"),
                "level_label": dim.get("level_label", "平稳"),
                "description": dim.get("description", "能量平稳"),
            }
            for dim_key, dim in dimensions.items()
        ]
        
        key_aspects = []
        key_transits = transit_data.get("key_transits_year", [])
        for kt in key_transits[:8]:
            nature = kt.get("nature", "neutral")
            aspect_type = "harmonious" if nature == "harmonious" else "challenging" if nature == "challenging" else "neutral"
            key_aspects.append({
                "transit_planet": kt.get("transit_planet", ""),
                "transit_symbol": kt.get("transit_symbol", ""),
                "natal_planet": kt.get("natal_planet", ""),
                "natal_symbol": kt.get("natal_symbol", ""),
                "aspect_name": kt.get("aspect", ""),
                "aspect_symbol": kt.get("aspect_symbol", ""),
                "aspect_type": aspect_type,
                "influence_score": kt.get("influence", 0),
                "influence": f"{kt.get('transit_planet', '')}与{kt.get('natal_planet', '')}形成{kt.get('aspect', '')}，在{kt.get('month', 1)}月附近影响显著。",
                "month": kt.get("month", 1),
                "importance": kt.get("importance", "medium"),
            })
        
        mid_transit = transit_data.get("mid_transit", {})
        transit_overall = mid_transit.get("overall", {})
        transit_summary = f"本年行运整体评分为{transit_overall.get('overall_score', 50)}分。{transit_overall.get('overall_description', '')}" if transit_overall else "本年行运能量相对平稳。"
        
        transit_analysis = {
            "overall_summary": transit_summary,
            "overall_score": transit_overall.get("overall_score", 50),
            "key_aspects": key_aspects,
            "saturn_return": transit_data.get("saturn_return"),
            "outer_planet_transits": transit_data.get("outer_planet_transits", []),
        }
        
        firdaria_analysis = {
            "has_active_period": firdaria_data.get("has_active_period", False),
        }
        
        if firdaria_data.get("has_active_period"):
            major_period = firdaria_data.get("major_period", {})
            minor_period = firdaria_data.get("minor_period")
            influence_analysis = firdaria_data.get("influence_analysis", {})
            minor_analysis = firdaria_data.get("minor_analysis", {})
            
            major_lord_name = major_period.get("planet_name", "")
            major_lord = f"{major_lord_name} {major_period.get('planet_symbol', '')}" if major_lord_name else ""
            
            minor_lord = ""
            if minor_period:
                minor_lord_name = minor_period.get("planet_name", "")
                minor_lord = f"{minor_lord_name} {minor_period.get('planet_symbol', '')}" if minor_lord_name else ""
            
            firdaria_analysis.update({
                "major_lord": major_lord,
                "major_lord_name": major_lord_name,
                "major_lord_symbol": major_period.get("planet_symbol", ""),
                "minor_lord": minor_lord,
                "minor_lord_name": minor_period.get("planet_name", "") if minor_period else "",
                "progress_percent": major_period.get("progress_percent", 0),
                "start_age": major_period.get("start_age", 0),
                "end_age": major_period.get("end_age", 0),
                "overall_summary": influence_analysis.get("full_description", f"当前处于{major_lord_name}大运期间。"),
                "key_themes": firdaria_data.get("themes", []),
                "intensity_score": firdaria_data.get("intensity_score", 5),
                "is_day_birth": firdaria_data.get("is_day_birth"),
            })
        
        prog_aspects = progression_data.get("aspects", [])
        key_changes = []
        for a in prog_aspects[:8]:
            nature = a.get("nature", "neutral")
            key_changes.append({
                "planet": a.get("progressed_planet", ""),
                "natal_planet": a.get("natal_planet", ""),
                "aspect": a.get("name", ""),
                "aspect_symbol": a.get("aspect_symbol", ""),
                "type": "和谐" if nature == "harmonious" else "紧张" if nature == "challenging" else "中性",
                "nature": nature,
                "influence": a.get("influence", 0.5),
                "influence_score": a.get("influence", 0.5),
                "description": f"次限{a.get('progressed_planet', '')}与本命{a.get('natal_planet', '')}形成{a.get('name', '')}。",
            })
        
        prog_tone = progression_data.get("emotional_tone", {})
        progression_summary = prog_tone.get("description", "次限推运显示本年能量相对平稳。")
        
        progression_analysis = {
            "overall_summary": progression_summary,
            "tone": prog_tone.get("tone", "neutral"),
            "tone_label": prog_tone.get("label", "平稳"),
            "key_changes": key_changes,
            "intensity_score": progression_data.get("intensity_score", 5),
            "themes": progression_data.get("themes", []),
        }
        
        script_data = {
            "target_year": target_year,
            "target_age": target_age,
            "birth_year": birth_datetime.year,
            
            "year_overview": year_overview,
            "domains_summary": domains_summary,
            "key_events": combined_analysis.get("key_events", []),
            "themes": combined_analysis.get("themes", []),
            
            "transit_analysis": transit_analysis,
            "firdaria_analysis": firdaria_analysis,
            "progression_analysis": progression_analysis,
            
            "analysis": combined_analysis,
            "transit": transit_data,
            "firdaria": firdaria_data,
            "progression": progression_data,
            "solar_arc": solar_arc_data,
        }
        
        cache_service.set(cache_key, script_data, ttl=86400)
        
        return script_data

    def _analyze_transit_for_year(
        self,
        birth_datetime: datetime,
        natal_planets: List[Dict[str, Any]],
        latitude: float,
        longitude: float,
        target_year: int
    ) -> Dict[str, Any]:
        year_start = datetime(target_year, 1, 1, 12, 0)
        year_mid = datetime(target_year, 7, 1, 12, 0)
        
        mid_transit = transit_engine.calculate_full_transit(
            natal_planets, year_mid, latitude, longitude
        )
        
        key_transits_this_year = self._identify_key_transits_in_year(
            birth_datetime, natal_planets, latitude, longitude, target_year
        )
        
        saturn_return = self._check_saturn_return(birth_datetime, natal_planets, target_year)
        
        jupiter_cycles = self._check_jupiter_cycles(birth_datetime, natal_planets, target_year)
        
        outer_planet_transits = self._check_outer_planet_transits(
            birth_datetime, natal_planets, latitude, longitude, target_year
        )
        
        overall_score = mid_transit.get("overall", {}).get("overall_score", 50)
        
        return {
            "year_start": year_start.strftime("%Y-%m-%d"),
            "year_mid": year_mid.strftime("%Y-%m-%d"),
            "mid_transit": mid_transit,
            "key_transits_year": key_transits_this_year,
            "saturn_return": saturn_return,
            "jupiter_cycles": jupiter_cycles,
            "outer_planet_transits": outer_planet_transits,
            "overall_score": overall_score,
            "dimensions": mid_transit.get("dimensions", []),
        }

    def _identify_key_transits_in_year(
        self,
        birth_datetime: datetime,
        natal_planets: List[Dict[str, Any]],
        latitude: float,
        longitude: float,
        target_year: int
    ) -> List[Dict[str, Any]]:
        key_transits = []
        
        for month in [1, 4, 7, 10]:
            check_date = datetime(target_year, month, 15, 12, 0)
            
            transit = transit_engine.calculate_full_transit(
                natal_planets, check_date, latitude, longitude
            )
            
            aspects = transit.get("aspects", [])
            
            for a in aspects:
                if a.get("influence", 0) >= 0.6:
                    p2 = a.get("planet2_name", "")
                    if p2 in ["土星", "木星", "天王星", "海王星", "冥王星"]:
                        key_transits.append({
                            "month": month,
                            "date": check_date.strftime("%Y-%m-%d"),
                            "transit_planet": a.get("planet2_name"),
                            "transit_symbol": a.get("planet2_symbol"),
                            "natal_planet": a.get("planet1_name"),
                            "natal_symbol": a.get("planet1_symbol"),
                            "aspect": a.get("name"),
                            "aspect_symbol": a.get("symbol"),
                            "nature": a.get("nature"),
                            "influence": a.get("influence"),
                            "importance": "high" if a.get("influence", 0) >= 0.8 else "medium",
                        })
        
        seen = set()
        unique_transits = []
        for t in key_transits:
            key = f"{t['transit_planet']}_{t['aspect']}_{t['natal_planet']}"
            if key not in seen:
                seen.add(key)
                unique_transits.append(t)
        
        unique_transits.sort(key=lambda x: x["influence"], reverse=True)
        return unique_transits[:8]

    def _check_saturn_return(
        self,
        birth_datetime: datetime,
        natal_planets: List[Dict[str, Any]],
        target_year: int
    ) -> Optional[Dict[str, Any]]:
        birth_year = birth_datetime.year
        
        saturn_return_ages = [29, 30, 58, 59, 60, 88, 89, 90]
        target_age = target_year - birth_year
        
        if target_age not in saturn_return_ages:
            return None
        
        phase = ""
        description = ""
        
        if 28 <= target_age <= 32:
            phase = "第一次土星回归"
            description = "这是人生中最重要的成长时期之一。土星回归标志着真正的成年开始，你将面对责任、承诺和人生结构的建立。过去的梦想需要与现实接轨，不成熟的选择需要修正。这可能是一段沉重但极其重要的成长时期。"
        elif 57 <= target_age <= 62:
            phase = "第二次土星回归"
            description = "第二次土星回归，人生进入成熟期。你需要重新评估过去几十年建立的结构，什么值得保留，什么需要放手。这是从成年向智慧老年过渡的关键时期。"
        elif 87 <= target_age <= 92:
            phase = "第三次土星回归"
            description = "第三次土星回归，人生智慧的巅峰。回顾一生的选择和经历，整合所有的教训。这是一个圆满和传承的时期。"
        
        return {
            "is_saturn_return": True,
            "phase": phase,
            "age": target_age,
            "year": target_year,
            "description": description,
            "intensity": 10,
            "themes": ["责任", "成长", "结构", "成熟", "承诺"],
        }

    def _check_jupiter_cycles(
        self,
        birth_datetime: datetime,
        natal_planets: List[Dict[str, Any]],
        target_year: int
    ) -> List[Dict[str, Any]]:
        birth_year = birth_datetime.year
        target_age = target_year - birth_year
        
        cycles = []
        
        jupiter_cycle_ages = [
            (11, 12, "第一次木星回归", "少年期向青春期的过渡，视野开始扩展，学习欲望强烈。"),
            (23, 24, "第二次木星回归", "青年期的扩展期，适合追求更高的教育、旅行、建立世界观。"),
            (35, 36, "第三次木星回归", "中年扩张期，事业和社会地位的提升期。"),
            (47, 48, "第四次木星回归", "成熟智慧的扩展期，可能有新的兴趣、学习或旅行。"),
            (59, 60, "第五次木星回归", "与土星回归同时，智慧的绽放期。"),
            (71, 72, "第六次木星回归", "晚年的扩张期，可能有新的社交圈子或爱好。"),
            (83, 84, "第七次木星回归", "智慧的传承期，分享一生的经验。"),
        ]
        
        for start_age, end_age, phase, desc in jupiter_cycle_ages:
            if start_age <= target_age <= end_age:
                cycles.append({
                    "phase": phase,
                    "age": target_age,
                    "year": target_year,
                    "description": desc,
                    "intensity": 8,
                    "themes": ["扩张", "机遇", "学习", "成长", "乐观"],
                })
                break
        
        return cycles

    def _check_outer_planet_transits(
        self,
        birth_datetime: datetime,
        natal_planets: List[Dict[str, Any]],
        latitude: float,
        longitude: float,
        target_year: int
    ) -> List[Dict[str, Any]]:
        outer_transits = []
        birth_year = birth_datetime.year
        target_age = target_year - birth_year
        
        uranus_opposition_ages = list(range(38, 45))
        if target_age in uranus_opposition_ages:
            outer_transits.append({
                "planet": "天王星",
                "symbol": "♅",
                "phase": "天王星对分相（中年危机）",
                "age": target_age,
                "year": target_year,
                "description": "天王星对分本命天王星，这是人生中的转折点。对现状的不满可能达到顶峰，渴望改变、自由和突破。这可能是人生方向的重大调整期。",
                "intensity": 9,
                "themes": ["变革", "自由", "突破", "觉醒", "意外"],
            })
        
        neptune_square_ages = list(range(40, 43)) + list(range(80, 83))
        if target_age in neptune_square_ages:
            outer_transits.append({
                "planet": "海王星",
                "symbol": "♆",
                "phase": "海王星四分相",
                "age": target_age,
                "year": target_year,
                "description": "海王星与本命海王星形成四分相，理想与现实的冲突。可能有幻灭、迷茫，也可能有灵性的觉醒。需要保持清醒，但也要保持敏感。",
                "intensity": 8,
                "themes": ["理想", "幻灭", "灵性", "迷茫", "艺术"],
            })
        
        pluto_square_ages = list(range(35, 40))
        if target_age in pluto_square_ages:
            outer_transits.append({
                "planet": "冥王星",
                "symbol": "♇",
                "phase": "冥王星四分相",
                "age": target_age,
                "year": target_year,
                "description": "冥王星与本命冥王星形成四分相，深度转化期。旧的自我结构需要瓦解，为新的成长腾出空间。这可能是痛苦但极其深刻的转变时期。",
                "intensity": 10,
                "themes": ["转化", "重生", "权力", "深度", "蜕变"],
            })
        
        return outer_transits

    def _combine_analyses(
        self,
        transit_data: Dict[str, Any],
        firdaria_data: Dict[str, Any],
        progression_data: Dict[str, Any],
        solar_arc_data: Optional[Dict[str, Any]],
        target_year: int,
        target_age: int
    ) -> Dict[str, Any]:
        all_intensities = []
        
        transit_score = transit_data.get("overall_score", 50)
        transit_intensity = min(10, round(transit_score / 10))
        all_intensities.append(("行运", transit_intensity))
        
        firdaria_intensity = firdaria_data.get("intensity_score", 5)
        all_intensities.append(("法达", firdaria_intensity))
        
        progression_intensity = progression_data.get("intensity_score", 5)
        all_intensities.append(("次限", progression_intensity))
        
        if firdaria_data.get("saturn_return"):
            all_intensities.append(("土星回归", 10))
        
        outer_transits = transit_data.get("outer_planet_transits", [])
        for ot in outer_transits:
            all_intensities.append((ot.get("planet", ""), ot.get("intensity", 5)))
        
        combined_intensity = sum(i[1] for i in all_intensities) / len(all_intensities)
        combined_intensity = min(10, max(1, round(combined_intensity)))
        
        mood, mood_label, mood_description = self._determine_combined_mood(
            transit_data, firdaria_data, progression_data
        )
        
        key_events = self._collect_key_events(
            transit_data, firdaria_data, progression_data
        )
        
        themes = self._collect_themes(
            transit_data, firdaria_data, progression_data
        )
        
        dimensions = self._analyze_dimensions(transit_data, progression_data)
        
        is_key_year = combined_intensity >= 7 or len(key_events) >= 3
        
        return {
            "target_year": target_year,
            "target_age": target_age,
            "combined_intensity": combined_intensity,
            "intensity_breakdown": all_intensities,
            "mood": mood,
            "mood_label": mood_label,
            "mood_description": mood_description,
            "key_events": key_events,
            "themes": themes,
            "dimensions": dimensions,
            "is_key_year": is_key_year,
            "has_saturn_return": firdaria_data.get("saturn_return") is not None,
            "has_major_outer_transit": len(transit_data.get("outer_planet_transits", [])) > 0,
        }

    def _determine_combined_mood(
        self,
        transit_data: Dict[str, Any],
        firdaria_data: Dict[str, Any],
        progression_data: Dict[str, Any]
    ) -> tuple:
        saturn_return = firdaria_data.get("saturn_return")
        if saturn_return:
            return (
                ScriptMood.SERIOUS.value,
                "深沉",
                "土星回归的能量主导这一年，这是一段需要耐心、责任和成长的时期。"
            )
        
        outer_transits = transit_data.get("outer_planet_transits", [])
        for ot in outer_transits:
            planet = ot.get("planet")
            if planet == "天王星":
                return (
                    ScriptMood.TRANSFORMATIVE.value,
                    "变革",
                    "天王星的能量带来意外和改变，这一年可能有出乎意料的转折。"
                )
            elif planet == "冥王星":
                return (
                    ScriptMood.TRANSFORMATIVE.value,
                    "蜕变",
                    "冥王星的深度转化能量，这一年可能经历深刻的内心蜕变。"
                )
        
        firdaria_planet = ""
        if firdaria_data.get("major_period"):
            firdaria_planet = firdaria_data["major_period"].get("planet", "")
        
        jupiter_cycles = transit_data.get("jupiter_cycles", [])
        if jupiter_cycles or firdaria_planet == "jupiter":
            return (
                ScriptMood.OPTIMISTIC.value,
                "扩张",
                "木星的能量带来机遇和乐观，这一年适合积极探索和尝试。"
            )
        
        if firdaria_planet == "saturn":
            return (
                ScriptMood.SERIOUS.value,
                "沉稳",
                "土星大运期间，需要更多耐心和责任感，稳扎稳打。"
            )
        
        if firdaria_planet == "mars":
            return (
                ScriptMood.CHALLENGING.value,
                "行动力",
                "火星的能量带来行动力和决断，但也需要注意冲动。"
            )
        
        progression_tone = progression_data.get("emotional_tone", {})
        progression_tone_type = progression_tone.get("tone", "neutral")
        
        tone_map = {
            "serious": (ScriptMood.SERIOUS.value, "深沉", progression_tone.get("description", "")),
            "expansive": (ScriptMood.OPTIMISTIC.value, "扩张", progression_tone.get("description", "")),
            "harmonious": (ScriptMood.HARMONIOUS.value, "和谐", progression_tone.get("description", "")),
            "challenging": (ScriptMood.CHALLENGING.value, "挑战", progression_tone.get("description", "")),
            "balanced": (ScriptMood.NEUTRAL.value, "平衡", progression_tone.get("description", "")),
        }
        
        return tone_map.get(progression_tone_type, (
            ScriptMood.NEUTRAL.value,
            "平稳",
            "这一年能量相对平稳，适合稳步前行。"
        ))

    def _collect_key_events(
        self,
        transit_data: Dict[str, Any],
        firdaria_data: Dict[str, Any],
        progression_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        key_events = []
        
        saturn_return = firdaria_data.get("saturn_return")
        if saturn_return:
            key_events.append({
                "type": "saturn_return",
                "title": saturn_return["phase"],
                "importance": "critical",
                "intensity": saturn_return["intensity"],
                "description": saturn_return["description"],
                "themes": saturn_return["themes"],
            })
        
        outer_transits = transit_data.get("outer_planet_transits", [])
        for ot in outer_transits:
            key_events.append({
                "type": "outer_planet_transit",
                "title": ot["phase"],
                "planet": ot["planet"],
                "symbol": ot["symbol"],
                "importance": "high",
                "intensity": ot["intensity"],
                "description": ot["description"],
                "themes": ot["themes"],
            })
        
        jupiter_cycles = transit_data.get("jupiter_cycles", [])
        for jc in jupiter_cycles:
            key_events.append({
                "type": "jupiter_cycle",
                "title": jc["phase"],
                "importance": "medium",
                "intensity": jc["intensity"],
                "description": jc["description"],
                "themes": jc["themes"],
            })
        
        if firdaria_data.get("major_period"):
            major = firdaria_data["major_period"]
            progress = major.get("progress_percent", 50)
            if 0 <= progress <= 10:
                key_events.append({
                    "type": "firdaria_start",
                    "title": f"进入{major['planet_name']}大运",
                    "planet": major["planet_name"],
                    "symbol": major["planet_symbol"],
                    "importance": "high",
                    "intensity": 8,
                    "description": f"新的{major['planet_name']}大运开始，未来{round(major['end_age'] - major['start_age'])}年将由{major['planet_name']}的能量主导。",
                })
            elif 45 <= progress <= 55:
                key_events.append({
                    "type": "firdaria_mid",
                    "title": f"{major['planet_name']}大运中期",
                    "planet": major["planet_name"],
                    "symbol": major["planet_symbol"],
                    "importance": "medium",
                    "intensity": 7,
                    "description": f"{major['planet_name']}大运过半，之前的努力开始显现成果。",
                })
        
        key_transits = transit_data.get("key_transits_year", [])
        for kt in key_transits[:3]:
            if kt.get("importance") == "high":
                nature = kt.get("nature", "neutral")
                nature_label = "和谐" if nature == "harmonious" else "紧张" if nature == "challenging" else "中性"
                
                key_events.append({
                    "type": "major_transit",
                    "title": f"行运{kt['transit_planet']}{kt['aspect_symbol']}本命{kt['natal_planet']}",
                    "aspect": kt["aspect"],
                    "nature": nature_label,
                    "month": kt["month"],
                    "importance": kt["importance"],
                    "intensity": round(kt["influence"] * 10),
                    "description": f"{nature_label}的相位在{kt['month']}月附近影响显著。",
                })
        
        return key_events

    def _collect_themes(
        self,
        transit_data: Dict[str, Any],
        firdaria_data: Dict[str, Any],
        progression_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        themes_dict = {}
        
        firdaria_themes = firdaria_data.get("themes", [])
        for theme in firdaria_themes:
            if theme not in themes_dict:
                themes_dict[theme] = {"count": 0, "sources": []}
            themes_dict[theme]["count"] += 2
            themes_dict[theme]["sources"].append("法达")
        
        progression_themes = progression_data.get("themes", [])
        for t in progression_themes:
            theme = t.get("theme", "")
            if theme and theme not in themes_dict:
                themes_dict[theme] = {"count": 0, "sources": []}
            if theme:
                themes_dict[theme]["count"] += t.get("intensity", 5)
                themes_dict[theme]["sources"].append("次限")
        
        saturn_return = firdaria_data.get("saturn_return")
        if saturn_return:
            for theme in saturn_return.get("themes", []):
                if theme not in themes_dict:
                    themes_dict[theme] = {"count": 0, "sources": []}
                themes_dict[theme]["count"] += 3
                themes_dict[theme]["sources"].append("土星回归")
        
        themes_list = [
            {"theme": theme, "score": data["count"], "sources": list(set(data["sources"]))}
            for theme, data in themes_dict.items()
        ]
        
        themes_list.sort(key=lambda x: x["score"], reverse=True)
        return themes_list[:6]

    def _analyze_dimensions(
        self,
        transit_data: Dict[str, Any],
        progression_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        transit_dims = transit_data.get("dimensions", [])
        
        dim_map = {
            "communication": {"name": "沟通", "icon": "💬", "color": "#60a5fa"},
            "social": {"name": "社交", "icon": "👥", "color": "#f472b6"},
            "career": {"name": "事业", "icon": "💼", "color": "#f97316"},
            "wealth": {"name": "财运", "icon": "💰", "color": "#eab308"},
            "emotion": {"name": "情绪", "icon": "❤️", "color": "#ec4899"},
        }
        
        result = {}
        
        for dim in transit_dims:
            dim_key = dim.get("dimension", "")
            if dim_key in dim_map:
                config = dim_map[dim_key]
                result[dim_key] = {
                    "name": config["name"],
                    "icon": config["icon"],
                    "color": config["color"],
                    "score": dim.get("score", 50),
                    "level": dim.get("level", "medium"),
                    "level_label": dim.get("level_label", "平稳"),
                    "description": dim.get("description", ""),
                }
        
        for dim_key, config in dim_map.items():
            if dim_key not in result:
                result[dim_key] = {
                    "name": config["name"],
                    "icon": config["icon"],
                    "color": config["color"],
                    "score": 50,
                    "level": "medium",
                    "level_label": "平稳",
                    "description": "能量平稳",
                }
        
        return result

    def generate_script_prompt(
        self,
        analysis: Dict[str, Any],
        previous_year_analysis: Optional[Dict[str, Any]] = None,
        next_year_analysis: Optional[Dict[str, Any]] = None
    ) -> str:
        target_year = analysis.get("target_year", 2020)
        target_age = analysis.get("target_age", 30)
        
        combined = analysis.get("analysis", {})
        mood = combined.get("mood", "neutral")
        mood_label = combined.get("mood_label", "平稳")
        intensity = combined.get("combined_intensity", 5)
        
        key_events = combined.get("key_events", [])
        themes = combined.get("themes", [])
        dimensions = combined.get("dimensions", {})
        
        is_key_year = combined.get("is_key_year", False)
        has_saturn_return = combined.get("has_saturn_return", False)
        has_major_outer_transit = combined.get("has_major_outer_transit", False)
        
        transit = analysis.get("transit", {})
        firdaria = analysis.get("firdaria", {})
        progression = analysis.get("progression", {})
        
        prompt_parts = []
        
        prompt_parts.append(f"""你是一位故事讲述者和占星师，现在要为用户生成一份「{target_year}年人生剧本」。

这不是冰冷的占星解读，而是以人生传记的口吻，讲述那一年发生的故事。

【基本信息】
- 年份：{target_year}年
- 年龄：{target_age}岁
- 整体强度：{intensity}/10
- 情绪基调：{mood_label}
- 关键年：{"是" if is_key_year else "否"}

""")
        
        if has_saturn_return:
            prompt_parts.append("【重要提示】这一年是土星回归年！这是人生中极其重要的成长节点，需要用深沉、严肃但充满希望的语调来描述。强调责任、成长、结构建立和成熟。\n")
        
        if has_major_outer_transit:
            prompt_parts.append("【重要提示】这一年有外行星的重要行运，可能带来重大的人生转变或觉醒。\n")
        
        if key_events:
            prompt_parts.append("【关键事件】")
            for event in key_events[:5]:
                title = event.get("title", "")
                importance = event.get("importance", "")
                desc = event.get("description", "")
                imp_label = "关键" if importance == "critical" else "重要" if importance == "high" else "次要"
                prompt_parts.append(f"- {imp_label}: {title}")
                if desc:
                    prompt_parts.append(f"  说明: {desc[:150]}")
            prompt_parts.append("")
        
        if themes:
            prompt_parts.append("【年度主题】")
            for t in themes[:4]:
                prompt_parts.append(f"- {t.get('theme', '')} (强度: {t.get('score', 5)}/10)")
            prompt_parts.append("")
        
        if dimensions:
            prompt_parts.append("【各领域能量】")
            for dim_key, dim_data in dimensions.items():
                score = dim_data.get("score", 50)
                label = dim_data.get("level_label", "平稳")
                desc = dim_data.get("description", "")
                prompt_parts.append(f"- {dim_data.get('name')}：{score}分 ({label})")
                if desc and len(desc) > 10:
                    prompt_parts.append(f"  {desc[:80]}")
            prompt_parts.append("")
        
        if firdaria.get("major_period"):
            major = firdaria["major_period"]
            prompt_parts.append(f"""【法达大运】
当前主星：{major.get('planet_name', '')} {major.get('planet_symbol', '')}
进度：{major.get('progress_percent', 50)}%
元素：{major.get('element', '')}
""")
            if firdaria.get("influence_analysis"):
                infl = firdaria["influence_analysis"]
                full_desc = infl.get("full_description", "")
                if full_desc:
                    prompt_parts.append(f"大运影响: {full_desc[:200]}\n")
        
        if progression.get("aspects"):
            aspects = progression["aspects"][:5]
            if aspects:
                prompt_parts.append("【次限推运重要相位】")
                for a in aspects:
                    prog_planet = a.get("progressed_planet", "")
                    natal_planet = a.get("natal_planet", "")
                    aspect = a.get("name", "")
                    nature = a.get("nature", "")
                    nature_label = "和谐" if nature == "harmonious" else "紧张" if nature == "challenging" else "中性"
                    prompt_parts.append(f"- 次限{prog_planet}{a.get('aspect_symbol', '')}本命{natal_planet} ({aspect} - {nature_label})")
                prompt_parts.append("")
        
        prog_tone = progression.get("emotional_tone", {})
        if prog_tone.get("description"):
            prompt_parts.append(f"【次限基调】{prog_tone.get('description')}\n")
        
        prompt_parts.append("""【生成要求】

请按照以下结构生成人生剧本，使用讲故事的口吻，像写一本自传一样：

## 一、年度概述（300-400字）
- 用一句话概括这一年的整体氛围
- 描述这一年在人生长河中的位置（如"这是你人生中土星回归的一年，标志着真正的成年开始"）
- 情绪基调要匹配：
  * 深沉/严肃年：语调稳重，强调耐心和成长
  * 扩张/乐观年：语调积极，充满希望和机遇
  * 变革/蜕变年：语调充满转折感，强调突破和新生
  * 和谐/平稳年：语调温和，稳步前行

## 二、关键转折点（每点150-200字）
针对每个关键事件，描述：
- 事件发生的时间感（如"年初"、"年中"、"下半年"）
- 事件带来的感受和影响
- 从中学到的教训或获得的成长

## 三、各领域故事（每领域100-150字）
1. 事业发展：描述这一年在工作/事业上的经历和感受
2. 感情关系：描述这一年在爱情/友情/亲情方面的经历
3. 财运状况：描述这一年的财务状况和金钱感受
4. 内心成长：描述这一年的心理变化和内心领悟

## 四、年度启示（200-300字）
- 这一年教会了你什么？
- 有什么重要的领悟？
- 为下一年留下了什么？

【风格要求】
1. 不要使用占星术语，要用普通人能理解的语言
2. 要用第一人称或传记式的口吻，像真实的回忆
3. 要有情绪起伏，不是平铺直叙
4. 重要年份要突出其"关键感"，让读者感受到这一年的分量
5. 如果是土星回归年，要强调"成长的阵痛但值得"
6. 如果是变革年，要强调"意外但必要的转折"
7. 不要做负面断言，要用"你可能会经历..."、"这可能是一个..."这样的表达
8. 前后要有连贯性，不要每段都是孤立的

【连贯性要求】
- 如果有前一年的信息，请在描述时注意与前一年的衔接
- 描述时要体现出人生的时间线感
- 重要的人生节点要标出其在整个生命周期中的位置

现在，请为这个用户生成{target_year}年的人生剧本：
""")
        
        return "\n".join(prompt_parts)

    async def generate_life_script(
        self,
        analysis: Dict[str, Any],
        previous_year_analysis: Optional[Dict[str, Any]] = None,
        next_year_analysis: Optional[Dict[str, Any]] = None,
        fast_mode: bool = True,
        max_tokens: int = 2500
    ) -> Dict[str, Any]:
        target_year = analysis.get("target_year", 2020)
        
        prompt = self.generate_script_prompt(analysis, previous_year_analysis, next_year_analysis)
        
        try:
            logger.info(f"开始为{target_year}年生成人生剧本，提示词长度: {len(prompt)}，快速模式: {fast_mode}")
            
            content = await call_deepseek_api(
                prompt=prompt,
                temperature=0.75 if fast_mode else 0.85,
                max_tokens=max_tokens,
                fast_mode=fast_mode
            )
            
            if not content or not content.strip():
                logger.warning("DeepSeek返回内容为空")
                return {
                    "success": False,
                    "error": "AI返回内容为空",
                    "error_type": "empty_response",
                    "target_year": target_year,
                }
            
            return {
                "success": True,
                "target_year": target_year,
                "content": content,
                "sections": self._parse_script_sections(content),
            }
            
        except Exception as e:
            error_str = str(e)
            logger.error(f"生成人生剧本失败: {error_str}", exc_info=True)
            
            error_type = "unknown"
            if "超时" in error_str or "timeout" in error_str.lower():
                error_type = "timeout"
            elif "认证" in error_str or "401" in error_str:
                error_type = "auth"
            elif "余额" in error_str or "403" in error_str:
                error_type = "quota"
            elif "频率" in error_str or "429" in error_str:
                error_type = "rate_limit"
            elif "网络连接" in error_str:
                error_type = "network"
            
            return {
                "success": False,
                "error": error_str,
                "error_type": error_type,
                "target_year": target_year,
            }

    def _parse_script_sections(self, content: str) -> Dict[str, str]:
        sections = {}
        
        section_patterns = [
            ("overview", ["一、年度概述", "年度概述", "## 一", "### 一"]),
            ("key_events", ["二、关键转折点", "关键转折点", "## 二", "### 二"]),
            ("areas", ["三、各领域故事", "各领域故事", "## 三", "### 三"]),
            ("insights", ["四、年度启示", "年度启示", "## 四", "### 四"]),
        ]
        
        lines = content.split("\n")
        current_section = None
        current_content = []
        
        for line in lines:
            line_stripped = line.strip()
            
            found_new_section = False
            for section_key, patterns in section_patterns:
                for pattern in patterns:
                    if line_stripped.startswith(pattern):
                        if current_section and current_content:
                            sections[current_section] = "\n".join(current_content).strip()
                        current_section = section_key
                        current_content = []
                        found_new_section = True
                        break
                if found_new_section:
                    break
            
            if not found_new_section and current_section:
                if line_stripped:
                    current_content.append(line)
        
        if current_section and current_content:
            sections[current_section] = "\n".join(current_content).strip()
        
        if not sections and content:
            sections["raw"] = content
        
        return sections

    def analyze_year_range(
        self,
        birth_date: str,
        birth_time: str,
        latitude: float,
        longitude: float,
        start_year: int,
        end_year: int,
        house_system: str = "placidus"
    ) -> List[Dict[str, Any]]:
        results = []
        
        for year in range(start_year, end_year + 1):
            try:
                analysis = self.analyze_year(
                    birth_date, birth_time, latitude, longitude, year, house_system
                )
                results.append(analysis)
            except Exception as e:
                logger.error(f"分析{year}年失败: {str(e)}")
                results.append({
                    "target_year": year,
                    "error": str(e),
                })
        
        return results

    def _get_sun_longitude(self, natal_planets: List[Dict[str, Any]]) -> float:
        """获取太阳黄经"""
        for p in natal_planets:
            if p.get("name") == "太阳":
                return p.get("longitude", 180.0)
        return 180.0

    def get_key_years(
        self,
        birth_date: str,
        birth_time: str,
        latitude: float,
        longitude: float,
        house_system: str = "placidus",
        start_age: int = 0,
        end_age: int = 80
    ) -> List[Dict[str, Any]]:
        natal_data = self._prepare_natal_data(birth_date, birth_time, latitude, longitude, house_system)
        birth_datetime = natal_data["birth_datetime"]
        birth_year = birth_datetime.year
        natal_planets = natal_data["natal_planets"]
        sun_longitude = self._get_sun_longitude(natal_planets)
        
        key_years = []
        
        firdaria_key_years = firdaria_calculator.get_key_firdaria_years(
            birth_datetime, sun_longitude, natal_planets
        )
        for fy in firdaria_key_years:
            year = birth_year + fy.get("age", 0)
            if start_age <= (year - birth_year) <= end_age:
                key_years.append({
                    "year": year,
                    "age": year - birth_year,
                    "type": "firdaria",
                    "subtype": fy.get("type"),
                    "planet": fy.get("planet"),
                    "planet_name": fy.get("planet_name"),
                    "planet_symbol": fy.get("planet_symbol"),
                    "description": fy.get("description"),
                    "intensity": fy.get("intensity", 7),
                })
        
        saturn_return_ages = [29, 30, 58, 59, 60, 88, 89, 90]
        for age in saturn_return_ages:
            if start_age <= age <= end_age:
                year = birth_year + age
                phase = ""
                if 28 <= age <= 32:
                    phase = "第一次土星回归"
                elif 57 <= age <= 62:
                    phase = "第二次土星回归"
                elif 87 <= age <= 92:
                    phase = "第三次土星回归"
                
                key_years.append({
                    "year": year,
                    "age": age,
                    "type": "saturn_return",
                    "phase": phase,
                    "description": f"土星回归，人生重要的成长和成熟期",
                    "intensity": 10,
                })
        
        uranus_opposition_ages = list(range(38, 45))
        for age in uranus_opposition_ages:
            if start_age <= age <= end_age and age == 42:
                year = birth_year + age
                key_years.append({
                    "year": year,
                    "age": age,
                    "type": "outer_planet",
                    "planet": "天王星",
                    "phase": "天王星对分相（中年转折）",
                    "description": "人生重要的转折点，渴望改变和自由",
                    "intensity": 9,
                })
        
        pluto_square_ages = list(range(35, 40))
        for age in pluto_square_ages:
            if start_age <= age <= end_age and age == 38:
                year = birth_year + age
                key_years.append({
                    "year": year,
                    "age": age,
                    "type": "outer_planet",
                    "planet": "冥王星",
                    "phase": "冥王星四分相（深度转化）",
                    "description": "深度转化期，旧的自我结构瓦解，新的自我重生",
                    "intensity": 10,
                })
        
        jupiter_return_ages = [12, 24, 36, 48, 60, 72, 84]
        for age in jupiter_return_ages:
            if start_age <= age <= end_age:
                year = birth_year + age
                nth = {12: "第一次", 24: "第二次", 36: "第三次", 48: "第四次", 60: "第五次", 72: "第六次", 84: "第七次"}.get(age, "第N次")
                key_years.append({
                    "year": year,
                    "age": age,
                    "type": "jupiter_return",
                    "phase": f"{nth}木星回归",
                    "description": "扩张和机遇期，适合学习、旅行和成长",
                    "intensity": 8,
                })
        
        key_years.sort(key=lambda x: x["year"])
        
        seen = set()
        unique_key_years = []
        for ky in key_years:
            key = f"{ky['year']}_{ky.get('type', '')}"
            if key not in seen:
                seen.add(key)
                unique_key_years.append(ky)
        
        return unique_key_years


life_script_analyzer = LifeScriptAnalyzer()


def get_life_script_analyzer() -> LifeScriptAnalyzer:
    return life_script_analyzer
