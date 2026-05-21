import logging
import math
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum

import swisseph as swe
import os as _os

# 设置星历文件路径：优先使用项目 backend/ephe 目录
_services_dir = _os.path.dirname(_os.path.abspath(__file__))
_ephe_path = _os.path.join(_os.path.dirname(_services_dir), "ephe")
if _os.path.isdir(_ephe_path):
    swe.set_ephe_path(_ephe_path)
else:
    swe.set_ephe_path("")

from app.config import settings
from app.astro import (
    MAIN_PLANETS, PLANET_INFO, SE_FLAGS,
    longitude_to_zodiac, degree_to_dms, utc_to_julday
)
from app.services.timezone_service import get_timezone_service

logger = logging.getLogger(__name__)

timezone_service = get_timezone_service()


class Planet(str, Enum):
    SUN = "sun"
    MOON = "moon"
    MERCURY = "mercury"
    VENUS = "venus"
    MARS = "mars"
    JUPITER = "jupiter"
    SATURN = "saturn"
    URANUS = "uranus"
    NEPTUNE = "neptune"
    PLUTO = "pluto"
    NORTH_NODE = "north_node"
    CHIRON = "chiron"
    CERES = "ceres"
    PALLAS = "pallas"
    JUNO = "juno"
    VESTA = "vesta"


PLANET_SWISSEPH_IDS = {
    Planet.SUN: swe.SUN,
    Planet.MOON: swe.MOON,
    Planet.MERCURY: swe.MERCURY,
    Planet.VENUS: swe.VENUS,
    Planet.MARS: swe.MARS,
    Planet.JUPITER: swe.JUPITER,
    Planet.SATURN: swe.SATURN,
    Planet.URANUS: swe.URANUS,
    Planet.NEPTUNE: swe.NEPTUNE,
    Planet.PLUTO: swe.PLUTO,
    Planet.NORTH_NODE: swe.TRUE_NODE,
    Planet.CHIRON: swe.CHIRON,
    Planet.CERES: swe.CERES,
    Planet.PALLAS: swe.PALLAS,
    Planet.JUNO: swe.JUNO,
    Planet.VESTA: swe.VESTA,
}


class AspectType(str, Enum):
    CONJUNCTION = "conjunction"
    SEMI_SEXTILE = "semi_sextile"
    SEXTILE = "sextile"
    SQUARE = "square"
    TRINE = "trine"
    QUINCUNX = "quincunx"
    OPPOSITION = "opposition"


ASPECT_DEFINITIONS = [
    {
        "type": AspectType.CONJUNCTION,
        "name": "合相",
        "symbol": "☌",
        "angle": 0,
        "orb": 8,
        "asteroid_orb": 3,
        "influence": 1.0,
        "nature": "neutral"
    },
    {
        "type": AspectType.SEMI_SEXTILE,
        "name": "半六合",
        "symbol": "⚺",
        "angle": 30,
        "orb": 3,
        "asteroid_orb": 1,
        "influence": 0.3,
        "nature": "harmonious"
    },
    {
        "type": AspectType.SEXTILE,
        "name": "六分相",
        "symbol": "⚹",
        "angle": 60,
        "orb": 6,
        "asteroid_orb": 2,
        "influence": 0.7,
        "nature": "harmonious"
    },
    {
        "type": AspectType.SQUARE,
        "name": "四分相",
        "symbol": "□",
        "angle": 90,
        "orb": 8,
        "asteroid_orb": 3,
        "influence": 1.0,
        "nature": "challenging"
    },
    {
        "type": AspectType.TRINE,
        "name": "三分相",
        "symbol": "△",
        "angle": 120,
        "orb": 8,
        "asteroid_orb": 3,
        "influence": 0.9,
        "nature": "harmonious"
    },
    {
        "type": AspectType.QUINCUNX,
        "name": "梅花相",
        "symbol": "⚻",
        "angle": 150,
        "orb": 3,
        "asteroid_orb": 1,
        "influence": 0.4,
        "nature": "challenging"
    },
    {
        "type": AspectType.OPPOSITION,
        "name": "对分相",
        "symbol": "☍",
        "angle": 180,
        "orb": 8,
        "asteroid_orb": 3,
        "influence": 1.0,
        "nature": "challenging"
    },
]


ASTEROID_PLANET_NAMES = {"谷神星", "智神星", "婚神星", "灶神星", "凯龙星"}


MOON_PHASES = [
    {"name": "新月", "symbol": "🌑", "angle": 0, "range": (0, 45)},
    {"name": "蛾眉月", "symbol": "🌒", "angle": 45, "range": (45, 90)},
    {"name": "上弦月", "symbol": "🌓", "angle": 90, "range": (90, 135)},
    {"name": "盈凸月", "symbol": "🌔", "angle": 135, "range": (135, 180)},
    {"name": "满月", "symbol": "🌕", "angle": 180, "range": (180, 225)},
    {"name": "亏凸月", "symbol": "🌖", "angle": 225, "range": (225, 270)},
    {"name": "下弦月", "symbol": "🌗", "angle": 270, "range": (270, 315)},
    {"name": "残月", "symbol": "🌘", "angle": 315, "range": (315, 360)},
]


class EphemerisCalculator:
    def __init__(self):
        self._planet_cache: Dict[Tuple[float, int], Dict[str, Any]] = {}
        self._cache_hits = 0
        self._cache_misses = 0

    def calculate_planet_position(
        self,
        jd: float,
        planet_id: int,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        if use_cache:
            cache_key = (jd, planet_id)
            if cache_key in self._planet_cache:
                self._cache_hits += 1
                return self._planet_cache[cache_key]

        self._cache_misses += 1
        
        result = swe.calc_ut(jd, planet_id, SE_FLAGS)
        longitude = result[0]
        latitude = result[1]
        speed = result[3]

        zodiac_info = longitude_to_zodiac(longitude)
        
        planet_info = PLANET_INFO.get(planet_id, {"name": "未知", "symbol": "★"})

        position_data = {
            "planet_id": planet_id,
            "name": planet_info["name"],
            "symbol": planet_info["symbol"],
            "longitude": round(longitude, 4),
            "latitude": round(latitude, 4),
            "speed": round(speed, 4),
            "zodiac": zodiac_info,
            "is_retrograde": speed < 0
        }

        if use_cache:
            self._planet_cache[cache_key] = position_data

        return position_data

    def calculate_houses(
        self,
        jd: float,
        latitude: float,
        longitude: float,
        house_system: str = "placidus"
    ) -> Dict[str, Any]:
        house_sys_char = 'P'
        if house_system.lower() == "koch":
            house_sys_char = 'K'
        elif house_system.lower() == "equal":
            house_sys_char = 'E'
        elif house_system.lower() == "whole_sign":
            asc_result = swe.houses(jd, latitude, longitude, 'P')
            asc_longitude = asc_result[0][0]
            mc_longitude = asc_result[1][1] if len(asc_result[1]) > 1 else None
            sign_start_longitude = int(asc_longitude / 30) * 30

            # 整宫制：每个宫位30°，从上升星座的0°开始
            house_cusps = [(sign_start_longitude + i * 30) % 360 for i in range(12)]

            return {
                "house_system": "whole_sign",
                "ascendant_longitude": round(asc_longitude, 4),
                "ascendant_zodiac": longitude_to_zodiac(asc_longitude),
                "midheaven_longitude": round(mc_longitude, 4) if mc_longitude is not None else None,
                "midheaven_zodiac": longitude_to_zodiac(mc_longitude) if mc_longitude is not None else None,
                "house_cusps": [round(c, 4) for c in house_cusps]
            }

        try:
            result = swe.houses(jd, latitude, longitude, house_sys_char)
            house_cusps = result[0]
            asc_longitude = house_cusps[0]
            mc_longitude = house_cusps[9]
            
            return {
                "house_system": house_system,
                "ascendant_longitude": round(asc_longitude, 4),
                "ascendant_zodiac": longitude_to_zodiac(asc_longitude),
                "midheaven_longitude": round(mc_longitude, 4),
                "midheaven_zodiac": longitude_to_zodiac(mc_longitude),
                "house_cusps": [round(c, 4) for c in house_cusps]
            }
        except Exception as e:
            logger.error(f"宫位计算失败: {e}")
            return {}

    def calculate_aspect(
        self,
        planet1_long: float,
        planet2_long: float,
        aspect_def: Dict[str, Any],
        planet1_name: str = "",
        planet2_name: str = ""
    ) -> Optional[Dict[str, Any]]:
        angle = aspect_def["angle"]
        
        is_asteroid_aspect = planet1_name in ASTEROID_PLANET_NAMES or planet2_name in ASTEROID_PLANET_NAMES
        orb = aspect_def.get("asteroid_orb", aspect_def["orb"]) if is_asteroid_aspect else aspect_def["orb"]
        
        diff = abs(planet1_long - planet2_long)
        if diff > 180:
            diff = 360 - diff
        
        if abs(diff - angle) <= orb:
            orb_exact = abs(diff - angle)
            influence = aspect_def["influence"] * (1 - orb_exact / orb)
            
            return {
                "type": aspect_def["type"].value if hasattr(aspect_def["type"], "value") else aspect_def["type"],
                "name": aspect_def["name"],
                "symbol": aspect_def["symbol"],
                "angle": angle,
                "actual_angle": round(diff, 4),
                "orb": round(orb_exact, 4),
                "influence": round(influence, 4),
                "nature": aspect_def["nature"]
            }
        
        return None

    def calculate_all_aspects(
        self,
        planets1: List[Dict[str, Any]],
        planets2: Optional[List[Dict[str, Any]]] = None,
        aspect_defs: Optional[List[Dict[str, Any]]] = None,
        exclude_same_planet: bool = True
    ) -> List[Dict[str, Any]]:
        if aspect_defs is None:
            aspect_defs = ASPECT_DEFINITIONS
        
        if planets2 is None:
            planets2 = planets1
        
        aspects = []
        
        for p1 in planets1:
            for p2 in planets2:
                if exclude_same_planet and p1.get("name") == p2.get("name"):
                    continue
                
                p1_long = p1["longitude"]
                p2_long = p2["longitude"]
                p1_name = p1.get("name", "")
                p2_name = p2.get("name", "")
                
                for aspect_def in aspect_defs:
                    aspect = self.calculate_aspect(p1_long, p2_long, aspect_def, p1_name, p2_name)
                    
                    if aspect:
                        aspect.update({
                            "planet1_name": p1.get("name"),
                            "planet1_symbol": p1.get("symbol"),
                            "planet1_zodiac": p1.get("zodiac"),
                            "planet2_name": p2.get("name"),
                            "planet2_symbol": p2.get("symbol"),
                            "planet2_zodiac": p2.get("zodiac"),
                            "is_applying": p2.get("speed", 0) > 0
                        })
                        aspects.append(aspect)
                        break
        
        aspects.sort(key=lambda x: x["influence"], reverse=True)
        return aspects

    def calculate_moon_phase(self, jd: float) -> Dict[str, Any]:
        sun_pos = swe.calc_ut(jd, swe.SUN, SE_FLAGS)
        moon_pos = swe.calc_ut(jd, swe.MOON, SE_FLAGS)
        
        sun_long = sun_pos[0]
        moon_long = moon_pos[0]
        
        diff = moon_long - sun_long
        if diff < 0:
            diff += 360
        
        for phase in MOON_PHASES:
            start, end = phase["range"]
            if start <= diff < end or (end == 360 and diff >= start):
                return {
                    "phase": phase["name"],
                    "symbol": phase["symbol"],
                    "angle": round(diff, 2),
                    "illumination": round(min(100, (diff % 180) / 1.8), 2)
                }
        
        return {"phase": "新月", "symbol": "🌑", "angle": 0, "illumination": 0}

    def local_time_to_julday(self, year: int, month: int, day: int, hour: int, minute: int, latitude: float, longitude: float) -> Tuple[float, Dict[str, Any]]:
        local_dt = datetime(year, month, day, hour, minute)
        
        debug_info = {
            "input_local": local_dt.strftime("%Y-%m-%d %H:%M"),
            "latitude": latitude,
            "longitude": longitude,
            "timezone": None,
            "offset_hours": None,
            "is_dst": None,
            "utc_time": None
        }
        
        utc_dt = None
        
        try:
            timezone_str = timezone_service.get_timezone_from_coords(latitude, longitude)
            debug_info["timezone"] = timezone_str
            
            if timezone_str:
                tz = pytz.timezone(timezone_str)
                
                try:
                    local_aware = tz.localize(local_dt, is_dst=None)
                except pytz.NonExistentTimeError:
                    local_aware = tz.localize(local_dt, is_dst=True)
                except pytz.AmbiguousTimeError:
                    local_aware = tz.localize(local_dt, is_dst=False)
                
                utc_dt = local_aware.astimezone(pytz.utc)
                debug_info["utc_time"] = utc_dt.strftime("%Y-%m-%d %H:%M:%S")
                debug_info["is_dst"] = local_aware.dst() is not None and local_aware.dst() != timedelta(0)
                debug_info["offset_hours"] = local_aware.utcoffset().total_seconds() / 3600 if local_aware.utcoffset() else 0
                
        except Exception as e:
            logger.warning(f"时区转换失败，使用默认UTC+8: {e}")
        
        if utc_dt is None:
            offset_hours = 8.0
            utc_dt = local_dt - timedelta(hours=offset_hours)
            debug_info["timezone"] = "Asia/Shanghai (fallback)"
            debug_info["offset_hours"] = offset_hours
            debug_info["utc_time"] = utc_dt.strftime("%Y-%m-%d %H:%M:%S")
        
        jd = utc_to_julday(utc_dt)
        return jd, debug_info

    def check_mercury_retrograde(self, jd: float) -> Dict[str, Any]:
        """检测水星是否逆行"""
        position = self.calculate_planet_position(jd, swe.MERCURY)
        is_retro = position["speed"] < 0
        return {
            "is_retrograde": is_retro,
            "speed": position["speed"],
            "status": "逆行中" if is_retro else "顺行中",
            "longitude": position["longitude"],
            "zodiac": position["zodiac"]
        }

    def get_cache_stats(self) -> Dict[str, int]:
        return {
            "hits": self._cache_hits,
            "misses": self._cache_misses,
            "total": self._cache_hits + self._cache_misses
        }

    def clear_cache(self):
        self._planet_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0


_ephemeris_calculator = None

def get_ephemeris_calculator() -> EphemerisCalculator:
    global _ephemeris_calculator
    if _ephemeris_calculator is None:
        _ephemeris_calculator = EphemerisCalculator()
    return _ephemeris_calculator
