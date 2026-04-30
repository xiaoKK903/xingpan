import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum

from app.services.ephemeris_calculator import (
    get_ephemeris_calculator,
    ASPECT_DEFINITIONS,
)
from app.astro import (
    MAIN_PLANETS, PLANET_INFO, SE_FLAGS, longitude_to_zodiac, utc_to_julday
)

logger = logging.getLogger(__name__)

ephemeris_calculator = get_ephemeris_calculator()


class ProgressionType(str, Enum):
    SECONDARY = "secondary"
    TERTIARY = "tertiary"
    SOLAR_ARC = "solar_arc"


class SecondaryProgressionCalculator:
    def __init__(self):
        self._cache: Dict[str, Any] = {}

    def _progressed_date(self, birth_date: datetime, target_age: int, progression_type: str = "secondary") -> datetime:
        if progression_type == "secondary":
            return birth_date + timedelta(days=target_age)
        elif progression_type == "tertiary":
            return birth_date + timedelta(days=target_age * 30)
        else:
            return birth_date + timedelta(days=target_age)

    def _get_solar_arc(self, birth_jd: float, target_jd: float) -> float:
        from app.astro import utc_to_julday
        import swisseph as swe
        
        sun_birth, _ = swe.calc_ut(birth_jd, swe.SUN, SE_FLAGS)
        sun_target, _ = swe.calc_ut(target_jd, swe.SUN, SE_FLAGS)
        
        return (sun_target[0] - sun_birth[0]) % 360

    def calculate_progressed_planets(
        self,
        birth_date: datetime,
        birth_jd: float,
        latitude: float,
        longitude: float,
        target_age: int,
        progression_type: str = "secondary"
    ) -> List[Dict[str, Any]]:
        cache_key = f"prog:{birth_date.strftime('%Y%m%d')}:{target_age}:{progression_type}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        if progression_type == "secondary":
            progressed_calendar_date = self._progressed_date(birth_date, target_age, "secondary")
            
            from app.services.timezone_service import get_timezone_service
            timezone_service = get_timezone_service()
            
            utc_dt, _ = timezone_service.local_to_utc(
                progressed_calendar_date.year,
                progressed_calendar_date.month,
                progressed_calendar_date.day,
                progressed_calendar_date.hour,
                progressed_calendar_date.minute,
                latitude,
                longitude
            )
            
            progressed_jd = utc_to_julday(utc_dt)
            
            planets = ephemeris_calculator.calculate_multiple_planets(progressed_jd)
            
        elif progression_type == "solar_arc":
            birth_planets = ephemeris_calculator.calculate_multiple_planets(birth_jd)
            
            current_year = birth_date.year + target_age
            solar_arc_date = datetime(current_year, birth_date.month, birth_date.day)
            
            from app.services.timezone_service import get_timezone_service
            timezone_service = get_timezone_service()
            
            target_utc_dt, _ = timezone_service.local_to_utc(
                solar_arc_date.year,
                solar_arc_date.month,
                solar_arc_date.day,
                12, 0,
                latitude,
                longitude
            )
            
            target_jd = utc_to_julday(target_utc_dt)
            solar_arc = self._get_solar_arc(birth_jd, target_jd)
            
            planets = []
            for p in birth_planets:
                new_long = (p["longitude"] + solar_arc) % 360
                zodiac_info = longitude_to_zodiac(new_long)
                planets.append({
                    **p,
                    "longitude": new_long,
                    "zodiac": zodiac_info,
                    "solar_arc": solar_arc
                })
        else:
            planets = []
        
        self._cache[cache_key] = planets
        return planets

    def calculate_progressed_aspects(
        self,
        natal_planets: List[Dict[str, Any]],
        progressed_planets: List[Dict[str, Any]],
        aspect_defs: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        if aspect_defs is None:
            aspect_defs = ASPECT_DEFINITIONS
        
        aspects = []
        
        for prog_planet in progressed_planets:
            prog_name = prog_planet.get("name")
            if prog_name in ["北交点", "南交点", "凯龙星"]:
                continue
            
            prog_long = prog_planet["longitude"]
            
            for natal_planet in natal_planets:
                natal_name = natal_planet.get("name")
                if natal_name in ["北交点", "南交点", "凯龙星"]:
                    continue
                
                if prog_name == natal_name:
                    continue
                
                natal_long = natal_planet["longitude"]
                
                for aspect_def in aspect_defs:
                    angle = aspect_def["angle"]
                    orb = aspect_def["orb"] * 0.7
                    
                    diff = abs(prog_long - natal_long)
                    if diff > 180:
                        diff = 360 - diff
                    
                    if abs(diff - angle) <= orb:
                        orb_exact = abs(diff - angle)
                        influence = aspect_def["influence"] * (1 - orb_exact / orb)
                        
                        aspects.append({
                            "type": aspect_def["type"].value if hasattr(aspect_def["type"], "value") else aspect_def["type"],
                            "name": aspect_def["name"],
                            "symbol": aspect_def["symbol"],
                            "angle": angle,
                            "actual_angle": round(diff, 4),
                            "orb": round(orb_exact, 4),
                            "influence": round(influence, 4),
                            "nature": aspect_def["nature"],
                            "natal_planet": natal_planet.get("name"),
                            "natal_planet_symbol": natal_planet.get("symbol"),
                            "natal_zodiac": natal_planet.get("zodiac"),
                            "natal_house": natal_planet.get("house"),
                            "progressed_planet": prog_planet.get("name"),
                            "progressed_planet_symbol": prog_planet.get("symbol"),
                            "progressed_zodiac": prog_planet.get("zodiac"),
                            "is_applying": True,
                        })
                        break
        
        aspects.sort(key=lambda x: x["influence"], reverse=True)
        return aspects

    def calculate_progressed_houses(
        self,
        birth_jd: float,
        latitude: float,
        longitude: float,
        progressed_jd: float
    ) -> Dict[str, Any]:
        try:
            import swisseph as swe
            from app.astro import calculate_houses_ex
            
            houses_result = calculate_houses_ex(
                progressed_jd, latitude, longitude, "placidus"
            )
            
            return {
                "house_cusps": houses_result.get("house_cusps", []),
                "ascendant": houses_result.get("ascendant", 0),
                "midheaven": houses_result.get("midheaven", 0),
                "ascendant_zodiac": longitude_to_zodiac(houses_result.get("ascendant", 0)) if houses_result.get("ascendant") else None,
                "midheaven_zodiac": longitude_to_zodiac(houses_result.get("midheaven", 0)) if houses_result.get("midheaven") else None,
            }
        except Exception as e:
            logger.warning(f"计算次限宫位失败: {e}")
            return {}

    def analyze_progressed_chart(
        self,
        birth_date: datetime,
        birth_jd: float,
        latitude: float,
        longitude: float,
        natal_planets: List[Dict[str, Any]],
        target_age: int,
        progression_type: str = "secondary"
    ) -> Dict[str, Any]:
        progressed_planets = self.calculate_progressed_planets(
            birth_date, birth_jd, latitude, longitude, target_age, progression_type
        )
        
        aspects = self.calculate_progressed_aspects(natal_planets, progressed_planets)
        
        significant_aspects = [a for a in aspects if a["influence"] >= 0.5]
        
        intensity_score = self._calculate_progression_intensity(significant_aspects, target_age)
        
        themes = self._extract_progression_themes(significant_aspects, target_age)
        
        emotional_tone = self._determine_emotional_tone(significant_aspects)
        
        return {
            "progression_type": progression_type,
            "target_age": target_age,
            "target_year": birth_date.year + target_age,
            "progressed_planets": [
                {
                    "name": p.get("name"),
                    "symbol": p.get("symbol"),
                    "longitude": p.get("longitude"),
                    "zodiac": p.get("zodiac"),
                    "is_retrograde": p.get("is_retrograde", False),
                }
                for p in progressed_planets
            ],
            "aspects": significant_aspects[:15],
            "aspects_count": len(significant_aspects),
            "intensity_score": intensity_score,
            "themes": themes,
            "emotional_tone": emotional_tone,
            "key_transits": self._identify_key_transits(significant_aspects),
        }

    def _calculate_progression_intensity(self, aspects: List[Dict[str, Any]], age: int) -> int:
        if not aspects:
            return 5
        
        total_influence = sum(a["influence"] for a in aspects)
        base_score = min(10, 5 + total_influence)
        
        challenging_count = sum(1 for a in aspects if a["nature"] == "challenging")
        harmonious_count = sum(1 for a in aspects if a["nature"] == "harmonious")
        
        if challenging_count > harmonious_count:
            base_score += 1
        elif harmonious_count > challenging_count:
            base_score -= 0.5
        
        saturn_aspects = [a for a in aspects if a["progressed_planet"] == "土星" or a["natal_planet"] == "土星"]
        if saturn_aspects:
            base_score += 1
        
        jupiter_aspects = [a for a in aspects if a["progressed_planet"] == "木星" or a["natal_planet"] == "木星"]
        if jupiter_aspects:
            base_score += 0.5
        
        return min(10, max(1, round(base_score)))

    def _extract_progression_themes(self, aspects: List[Dict[str, Any]], age: int) -> List[Dict[str, Any]]:
        themes = []
        
        career_houses = [2, 6, 10]
        relationship_houses = [5, 7, 8]
        home_houses = [4, 12]
        self_houses = [1, 5, 9]
        
        career_aspects = []
        relationship_aspects = []
        home_aspects = []
        self_aspects = []
        
        for a in aspects:
            natal_house = a.get("natal_house")
            if natal_house in career_houses:
                career_aspects.append(a)
            if natal_house in relationship_houses:
                relationship_aspects.append(a)
            if natal_house in home_houses:
                home_aspects.append(a)
            if natal_house in self_houses:
                self_aspects.append(a)
            
            prog_planet = a.get("progressed_planet")
            if prog_planet in ["土星", "木星", "火星", "太阳", "月亮", "金星", "水星"]:
                if prog_planet == "土星":
                    themes.append({"theme": "责任与成长", "intensity": 8, "planet": "土星"})
                elif prog_planet == "木星":
                    themes.append({"theme": "扩张与机遇", "intensity": 7, "planet": "木星"})
                elif prog_planet == "火星":
                    themes.append({"theme": "行动与突破", "intensity": 9, "planet": "火星"})
                elif prog_planet == "太阳":
                    themes.append({"theme": "自我认同", "intensity": 7, "planet": "太阳"})
                elif prog_planet == "月亮":
                    themes.append({"theme": "情感变化", "intensity": 6, "planet": "月亮"})
                elif prog_planet == "金星":
                    themes.append({"theme": "关系与价值", "intensity": 6, "planet": "金星"})
                elif prog_planet == "水星":
                    themes.append({"theme": "思维转变", "intensity": 5, "planet": "水星"})
        
        if career_aspects:
            themes.append({
                "theme": "事业发展",
                "intensity": round(sum(a["influence"] for a in career_aspects) / len(career_aspects) * 10),
                "aspects_count": len(career_aspects),
            })
        
        if relationship_aspects:
            themes.append({
                "theme": "感情关系",
                "intensity": round(sum(a["influence"] for a in relationship_aspects) / len(relationship_aspects) * 10),
                "aspects_count": len(relationship_aspects),
            })
        
        if home_aspects:
            themes.append({
                "theme": "家庭与内心",
                "intensity": round(sum(a["influence"] for a in home_aspects) / len(home_aspects) * 10),
                "aspects_count": len(home_aspects),
            })
        
        seen = set()
        unique_themes = []
        for t in themes:
            theme_key = t["theme"]
            if theme_key not in seen:
                seen.add(theme_key)
                unique_themes.append(t)
        
        unique_themes.sort(key=lambda x: x["intensity"], reverse=True)
        return unique_themes[:6]

    def _determine_emotional_tone(self, aspects: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not aspects:
            return {
                "tone": "neutral",
                "tone_label": "平稳",
                "description": "这一年能量相对平稳，适合稳步前行。",
                "harmony_ratio": 0.5,
            }
        
        harmonious = [a for a in aspects if a["nature"] == "harmonious"]
        challenging = [a for a in aspects if a["nature"] == "challenging"]
        neutral = [a for a in aspects if a["nature"] == "neutral"]
        
        total = len(aspects)
        harmony_ratio = len(harmonious) / total if total > 0 else 0.5
        
        saturn_aspects = [a for a in aspects if a["progressed_planet"] == "土星" or a["natal_planet"] == "土星"]
        jupiter_aspects = [a for a in aspects if a["progressed_planet"] == "木星" or a["natal_planet"] == "木星"]
        
        if len(challenging) > len(harmonious) and saturn_aspects:
            return {
                "tone": "serious",
                "tone_label": "深沉",
                "description": "这一年需要更多耐心和责任感，土星的能量在教导你成长的功课。",
                "harmony_ratio": round(harmony_ratio, 2),
                "challenging_count": len(challenging),
                "harmonious_count": len(harmonious),
            }
        elif len(harmonious) > len(challenging) and jupiter_aspects:
            return {
                "tone": "expansive",
                "tone_label": "扩张",
                "description": "木星的能量带来机遇和成长，适合积极探索和尝试新事物。",
                "harmony_ratio": round(harmony_ratio, 2),
                "challenging_count": len(challenging),
                "harmonious_count": len(harmonious),
            }
        elif harmony_ratio >= 0.6:
            return {
                "tone": "harmonious",
                "tone_label": "和谐",
                "description": "整体能量和谐顺畅，适合建立连接和享受生活。",
                "harmony_ratio": round(harmony_ratio, 2),
                "challenging_count": len(challenging),
                "harmonious_count": len(harmonious),
            }
        elif harmony_ratio <= 0.4:
            return {
                "tone": "challenging",
                "tone_label": "挑战",
                "description": "这一年有较多需要突破的地方，但每一个挑战都是成长的机会。",
                "harmony_ratio": round(harmony_ratio, 2),
                "challenging_count": len(challenging),
                "harmonious_count": len(harmonious),
            }
        else:
            return {
                "tone": "balanced",
                "tone_label": "平衡",
                "description": "这一年能量相对平衡，有机遇也有挑战，需要灵活应对。",
                "harmony_ratio": round(harmony_ratio, 2),
                "challenging_count": len(challenging),
                "harmonious_count": len(harmonious),
            }

    def _identify_key_transits(self, aspects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        key_events = []
        
        for a in aspects:
            if a["influence"] < 0.6:
                continue
            
            prog_planet = a.get("progressed_planet")
            natal_planet = a.get("natal_planet")
            aspect_name = a.get("name")
            nature = a.get("nature")
            influence = a.get("influence")
            
            importance = "high" if influence >= 0.8 else "medium"
            
            if prog_planet == "土星" and aspect_name in ["合相", "四分相", "对分相"]:
                key_events.append({
                    "type": "saturn_transit",
                    "title": f"次限土星{a['symbol']}本命{natal_planet}",
                    "aspect": aspect_name,
                    "nature": nature,
                    "importance": "high",
                    "influence": influence,
                    "description": "土星带来的重要功课，涉及责任、限制和成长。这是一段需要耐心和坚持的时期。",
                })
            
            if prog_planet == "木星" and aspect_name in ["合相", "三分相", "六分相"]:
                key_events.append({
                    "type": "jupiter_transit",
                    "title": f"次限木星{a['symbol']}本命{natal_planet}",
                    "aspect": aspect_name,
                    "nature": "harmonious",
                    "importance": "high",
                    "influence": influence,
                    "description": "木星带来扩张和机遇，适合积极把握可能出现的机会。",
                })
            
            if prog_planet == "太阳" and aspect_name == "合相":
                key_events.append({
                    "type": "solar_return",
                    "title": f"次限太阳{a['symbol']}本命{natal_planet}",
                    "aspect": aspect_name,
                    "nature": "neutral",
                    "importance": importance,
                    "influence": influence,
                    "description": "太阳的能量激活相关领域，这是自我表达和展现的时期。",
                })
        
        key_events.sort(key=lambda x: x["influence"], reverse=True)
        return key_events[:5]

    def get_key_progression_years(
        self,
        birth_date: datetime,
        birth_jd: float,
        latitude: float,
        longitude: float,
        natal_planets: List[Dict[str, Any]],
        start_age: int = 0,
        end_age: int = 80
    ) -> List[Dict[str, Any]]:
        key_years = []
        
        birth_year = birth_date.year
        
        for age in range(start_age, end_age + 1):
            analysis = self.analyze_progressed_chart(
                birth_date, birth_jd, latitude, longitude, natal_planets, age, "secondary"
            )
            
            intensity = analysis.get("intensity_score", 5)
            aspects_count = analysis.get("aspects_count", 0)
            key_transits = analysis.get("key_transits", [])
            
            if intensity >= 7 or aspects_count >= 5 or key_transits:
                key_years.append({
                    "year": birth_year + age,
                    "age": age,
                    "type": "progression",
                    "intensity": intensity,
                    "aspects_count": aspects_count,
                    "description": f"次限推运关键年，{aspects_count}个重要相位",
                    "themes": [t["theme"] for t in analysis.get("themes", [])[:3]],
                    "key_transits": key_transits[:2],
                })
        
        return key_years


progression_calculator = SecondaryProgressionCalculator()


def get_progression_calculator() -> SecondaryProgressionCalculator:
    return progression_calculator
