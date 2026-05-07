import logging
import math
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum

import swisseph as swe

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
    SEXTILE = "sextile"
    SQUARE = "square"
    TRINE = "trine"
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

ASTEROID_PLANET_NAMES = {"谷神星", "智神星", "婚神星", "灶神星", "凯龙星"}


class EphemerisCalculator:
    """
    星历计算器 - 纯计算逻辑，与业务逻辑解耦
    
    职责：
    - 计算行星位置
    - 计算相位关系
    - 计算月相
    - 检测逆行
    - 时区转换
    """
    
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
        """
        计算单个行星在指定儒略日的位置
        
        Args:
            jd: 儒略日
            planet_id: 行星ID (swisseph 常量)
            use_cache: 是否使用内存缓存
            
        Returns:
            行星位置数据
        """
        cache_key = (round(jd, 8), planet_id)
        
        if use_cache and cache_key in self._planet_cache:
            self._cache_hits += 1
            return self._planet_cache[cache_key].copy()
        
        self._cache_misses += 1
        
        result, ret_flag = swe.calc_ut(jd, planet_id, SE_FLAGS)
        longitude = result[0]
        latitude_planet = result[1]
        speed = result[3]
        
        planet_info = PLANET_INFO.get(planet_id, {})
        zodiac_info = longitude_to_zodiac(longitude)
        
        position = {
            "planet_id": planet_id,
            "name": planet_info.get("name", "未知"),
            "symbol": planet_info.get("symbol", "★"),
            "longitude": longitude,
            "latitude": latitude_planet,
            "speed": speed,
            "is_retrograde": speed < 0,
            "zodiac": zodiac_info
        }
        
        if use_cache:
            self._planet_cache[cache_key] = position.copy()
        
        return position
    
    def calculate_multiple_planets(
        self,
        jd: float,
        planet_ids: Optional[List[int]] = None,
        include_north_node: bool = True,
        include_chiron: bool = False
    ) -> List[Dict[str, Any]]:
        """
        计算多个行星在指定儒略日的位置
        
        Args:
            jd: 儒略日
            planet_ids: 行星ID列表，默认使用 MAIN_PLANETS
            include_north_node: 是否包含北交点
            include_chiron: 是否包含凯龙星
            
        Returns:
            行星位置列表
        """
        if planet_ids is None:
            planet_ids = MAIN_PLANETS
        
        planets = []
        
        for planet_id in planet_ids:
            planet = self.calculate_planet_position(jd, planet_id)
            planets.append(planet)
        
        if include_north_node:
            try:
                node = self.calculate_planet_position(jd, swe.TRUE_NODE, use_cache=False)
                node["name"] = "北交点"
                node["symbol"] = "☊"
                node["is_retrograde"] = False
                planets.append(node)
            except Exception as e:
                logger.warning(f"计算北交点失败: {e}")
        
        if include_chiron:
            try:
                chiron = self.calculate_planet_position(jd, swe.CHIRON, use_cache=False)
                chiron["name"] = "凯龙星"
                chiron["symbol"] = "⚷"
                planets.append(chiron)
            except Exception as e:
                logger.warning(f"计算凯龙星失败: {e}")
        
        return planets
    
    def calculate_aspect(
        self,
        planet1_long: float,
        planet2_long: float,
        aspect_def: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        计算两个行星之间是否形成特定相位
        
        Args:
            planet1_long: 行星1的经度
            planet2_long: 行星2的经度
            aspect_def: 相位定义
            
        Returns:
            相位数据，如果不形成相位则返回 None
        """
        angle = aspect_def["angle"]
        orb = aspect_def["orb"]
        
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
        """
        计算两组行星之间的所有相位
        
        Args:
            planets1: 第一组行星（如本命盘行星）
            planets2: 第二组行星（如行运行星），如果为 None 则计算行星1内部的相位
            aspect_defs: 相位定义列表，默认使用 ASPECT_DEFINITIONS
            exclude_same_planet: 是否排除同一行星的相位比较
            
        Returns:
            相位列表，按影响力排序
        """
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
                
                for aspect_def in aspect_defs:
                    aspect = self.calculate_aspect(p1_long, p2_long, aspect_def)
                    
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
        """
        计算指定儒略日的月相
        
        Args:
            jd: 儒略日
            
        Returns:
            月相数据
        """
        sun_result, _ = swe.calc_ut(jd, swe.SUN, SE_FLAGS)
        moon_result, _ = swe.calc_ut(jd, swe.MOON, SE_FLAGS)
        
        sun_long = sun_result[0]
        moon_long = moon_result[0]
        
        diff = (moon_long - sun_long) % 360
        
        current_phase = MOON_PHASES[0]
        for phase in MOON_PHASES:
            if phase["range"][0] <= diff < phase["range"][1]:
                current_phase = phase
                break
        
        illumination = (1 - math.cos(math.radians(diff))) / 2 * 100
        
        moon_speed = moon_result[3]
        avg_moon_speed = 13.18
        next_full_moon_days = (180 - diff) / avg_moon_speed if diff < 180 else (180 - diff + 360) / avg_moon_speed
        next_new_moon_days = (360 - diff) / avg_moon_speed
        
        is_full_moon = abs(diff - 180) < 5
        is_new_moon = abs(diff) < 5 or abs(diff - 360) < 5
        
        return {
            "phase_name": current_phase["name"],
            "phase_symbol": current_phase["symbol"],
            "sun_moon_angle": round(diff, 2),
            "illumination": round(illumination, 1),
            "is_waxing": diff < 180,
            "is_full_moon": is_full_moon,
            "is_new_moon": is_new_moon,
            "next_full_moon_days": round(next_full_moon_days, 1),
            "next_new_moon_days": round(next_new_moon_days, 1)
        }
    
    def check_planet_retrograde(
        self,
        jd: float,
        planet_id: int
    ) -> Dict[str, Any]:
        """
        检测指定行星是否逆行
        
        Args:
            jd: 儒略日
            planet_id: 行星ID
            
        Returns:
            逆行状态数据
        """
        result, _ = swe.calc_ut(jd, planet_id, SE_FLAGS)
        speed = result[3]
        
        planet_info = PLANET_INFO.get(planet_id, {})
        
        return {
            "planet_id": planet_id,
            "planet_name": planet_info.get("name", "未知"),
            "is_retrograde": speed < 0,
            "speed": round(speed, 4),
            "status": "逆行" if speed < 0 else "顺行"
        }
    
    def check_mercury_retrograde(self, jd: float) -> Dict[str, Any]:
        """检测水星逆行"""
        return self.check_planet_retrograde(jd, swe.MERCURY)
    
    def check_venus_retrograde(self, jd: float) -> Dict[str, Any]:
        """检测金星逆行"""
        return self.check_planet_retrograde(jd, swe.VENUS)
    
    def check_mars_retrograde(self, jd: float) -> Dict[str, Any]:
        """检测火星逆行"""
        return self.check_planet_retrograde(jd, swe.MARS)
    
    def local_time_to_julday(
        self,
        year: int, month: int, day: int, hour: int, minute: int,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        timezone_str: Optional[str] = None
    ) -> Tuple[float, Dict[str, Any]]:
        """
        将本地时间转换为儒略日
        
        Args:
            year, month, day, hour, minute: 本地时间
            latitude, longitude: 经纬度（用于自动检测时区）
            timezone_str: 可选的时区字符串
            
        Returns:
            (儒略日, 调试信息)
        """
        utc_dt, debug_info = timezone_service.local_to_utc(
            year, month, day, hour, minute,
            latitude, longitude, timezone_str
        )
        
        jd = utc_to_julday(utc_dt)
        debug_info["julday"] = jd
        
        return jd, debug_info
    
    def julday_to_local_time(
        self,
        jd: float,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        timezone_str: Optional[str] = None
    ) -> Tuple[datetime, Dict[str, Any]]:
        """
        将儒略日转换为本地时间
        
        Args:
            jd: 儒略日
            latitude, longitude: 经纬度
            timezone_str: 时区字符串
            
        Returns:
            (本地时间, 调试信息)
        """
        year, month, day, hour = swe.revjul(jd, swe.GREG_CAL)
        
        total_hours = hour
        hours = int(total_hours)
        minutes = int((total_hours - hours) * 60)
        seconds = int(((total_hours - hours) * 60 - minutes) * 60)
        
        utc_dt = datetime(int(year), int(month), int(day), hours, minutes, seconds)
        
        local_dt, debug_info = timezone_service.utc_to_local(
            utc_dt, latitude, longitude, timezone_str
        )
        
        return local_dt, debug_info
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        total = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total * 100) if total > 0 else 0
        
        return {
            "cache_size": len(self._planet_cache),
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate_percent": round(hit_rate, 2)
        }
    
    def clear_cache(self):
        """清除缓存"""
        self._planet_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
        logger.info("行星位置缓存已清除")


ephemeris_calculator = EphemerisCalculator()


def get_ephemeris_calculator() -> EphemerisCalculator:
    """获取星历计算器单例"""
    return ephemeris_calculator
