from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
import math
import swisseph as swe
import os

# 设置星历文件路径：优先使用项目 backend/ephe 目录
_astro_dir = os.path.dirname(os.path.abspath(__file__))
_ephe_path = os.path.join(os.path.dirname(_astro_dir), "ephe")
if os.path.isdir(_ephe_path):
    swe.set_ephe_path(_ephe_path)
else:
    swe.set_ephe_path("")

logger = logging.getLogger(__name__)

# timezone_service is lazy-imported inside local_to_utc() to avoid circular imports


class HouseSystem(str, Enum):
    PLACIDUS = "placidus"
    WHOLE_SIGN = "whole_sign"


ZODIAC_SIGNS = [
    "白羊座", "金牛座", "双子座", "巨蟹座", "狮子座", "处女座",
    "天秤座", "天蝎座", "射手座", "摩羯座", "水瓶座", "双鱼座"
]

ZODIAC_SYMBOLS = [
    "♈", "♉", "♊", "♋", "♌", "♍",
    "♎", "♏", "♐", "♑", "♒", "♓"
]

ELEMENTS = ["火", "土", "风", "水", "火", "土", "风", "水", "火", "土", "风", "水"]

QUALITIES = ["开创", "固定", "变动", "开创", "固定", "变动", "开创", "固定", "变动", "开创", "固定", "变动"]

RULING_PLANETS = [
    "火星", "金星", "水星", "月亮", "太阳", "水星",
    "金星", "冥王星", "木星", "土星", "天王星", "海王星"
]

PLANET_INFO = {
    swe.SUN: {"name": "太阳", "symbol": "☉", "ruler_of": ["狮子座"]},
    swe.MOON: {"name": "月亮", "symbol": "☽", "ruler_of": ["巨蟹座"]},
    swe.MERCURY: {"name": "水星", "symbol": "☿", "ruler_of": ["双子座", "处女座"]},
    swe.VENUS: {"name": "金星", "symbol": "♀", "ruler_of": ["金牛座", "天秤座"]},
    swe.MARS: {"name": "火星", "symbol": "♂", "ruler_of": ["白羊座", "天蝎座"]},
    swe.JUPITER: {"name": "木星", "symbol": "♃", "ruler_of": ["射手座", "双鱼座"]},
    swe.SATURN: {"name": "土星", "symbol": "♄", "ruler_of": ["摩羯座", "水瓶座"]},
    swe.URANUS: {"name": "天王星", "symbol": "♅", "ruler_of": ["水瓶座"]},
    swe.NEPTUNE: {"name": "海王星", "symbol": "♆", "ruler_of": ["双鱼座"]},
    swe.PLUTO: {"name": "冥王星", "symbol": "♇", "ruler_of": ["天蝎座"]},
    swe.CERES: {"name": "谷神星", "symbol": "⚳", "ruler_of": []},
    swe.PALLAS: {"name": "智神星", "symbol": "⚴", "ruler_of": []},
    swe.JUNO: {"name": "婚神星", "symbol": "⚵", "ruler_of": []},
    swe.VESTA: {"name": "灶神星", "symbol": "⚶", "ruler_of": []},
    swe.CHIRON: {"name": "凯龙星", "symbol": "⚷", "ruler_of": []},
}

MAIN_PLANETS = [
    swe.SUN, swe.MOON, swe.MERCURY, swe.VENUS, swe.MARS,
    swe.JUPITER, swe.SATURN, swe.URANUS, swe.NEPTUNE, swe.PLUTO
]

ASTEROID_PLANETS = [
    swe.CERES, swe.PALLAS, swe.JUNO, swe.VESTA, swe.CHIRON
]

SE_FLAGS = swe.FLG_SWIEPH + swe.FLG_SPEED


def degree_to_dms(degree: float) -> Dict[str, Any]:
    degrees = int(degree)
    minutes = int((degree - degrees) * 60)
    seconds = round(((degree - degrees) * 60 - minutes) * 60, 2)
    return {
        "degrees": degrees,
        "minutes": minutes,
        "seconds": seconds,
        "formatted": f"{degrees}°{minutes}'{seconds}\""
    }


def longitude_to_zodiac(longitude: float) -> Dict[str, Any]:
    sign_index = int(longitude / 30) % 12
    degree_in_sign = longitude % 30
    dms = degree_to_dms(degree_in_sign)
    
    return {
        "longitude": longitude,
        "sign_index": sign_index,
        "sign": ZODIAC_SIGNS[sign_index],
        "sign_symbol": ZODIAC_SYMBOLS[sign_index],
        "degree_in_sign": degree_in_sign,
        "dms": dms,
        "element": ELEMENTS[sign_index],
        "quality": QUALITIES[sign_index],
        "ruling_planet": RULING_PLANETS[sign_index]
    }


def find_house_for_planet(planet_longitude: float, house_cusps: List[float]) -> int:
    for i in range(12):
        cusp_current = house_cusps[i]
        cusp_next = house_cusps[(i + 1) % 12]
        
        if cusp_next > cusp_current:
            if cusp_current <= planet_longitude < cusp_next:
                return i + 1
        else:
            if planet_longitude >= cusp_current or planet_longitude < cusp_next:
                return i + 1
    
    return 1


def get_timezone_from_coords(latitude: float, longitude: float) -> Optional[str]:
    from app.services.timezone_service import get_timezone_service
    return get_timezone_service().get_timezone_from_coords(latitude, longitude)


def local_to_utc(
    year: int, month: int, day: int, hour: int, minute: int,
    latitude: float, longitude: float,
    use_true_solar_time: bool = False
) -> Tuple[datetime, Dict[str, Any]]:
    from app.services.timezone_service import get_timezone_service
    ts = get_timezone_service()
    utc_dt, debug_info = ts.local_to_utc(year, month, day, hour, minute, latitude, longitude)

    if use_true_solar_time:
        jd_for_eot = utc_to_julday(utc_dt)
        eot_minutes = calculate_equation_of_time(jd_for_eot)
        offset_hours = debug_info.get("offset_hours", 8.0)
        timezone_str = debug_info.get("timezone")
        standard_meridian = offset_hours * 15.0
        longitude_correction = (longitude - standard_meridian) * 4.0
        total_correction = eot_minutes + longitude_correction
        debug_info["eot_minutes"] = round(eot_minutes, 2)
        debug_info["longitude_correction_minutes"] = round(longitude_correction, 2)
        debug_info["true_solar_correction_minutes"] = round(total_correction, 2)
        local_dt = datetime(year, month, day, hour, minute)
        corrected_local = local_dt + timedelta(minutes=total_correction)
        debug_info["true_solar_time"] = corrected_local.strftime("%Y-%m-%d %H:%M")
        if timezone_str and ts.is_available():
            try:
                import pytz
                tz = pytz.timezone(timezone_str)
                try:
                    local_aware_corr = tz.localize(corrected_local, is_dst=None)
                except (pytz.NonExistentTimeError, pytz.AmbiguousTimeError):
                    local_aware_corr = tz.localize(corrected_local, is_dst=False)
                utc_dt = local_aware_corr.astimezone(pytz.utc)
                utc_dt = utc_dt.replace(tzinfo=None)
                debug_info["utc_time"] = utc_dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                utc_dt = corrected_local - timedelta(hours=offset_hours)
                debug_info["utc_time"] = utc_dt.strftime("%Y-%m-%d %H:%M:%S")
        else:
            utc_dt = corrected_local - timedelta(hours=offset_hours)
            debug_info["utc_time"] = utc_dt.strftime("%Y-%m-%d %H:%M:%S")

    return utc_dt, debug_info


def utc_to_julday(utc_dt: datetime) -> float:
    year = utc_dt.year
    month = utc_dt.month
    day = utc_dt.day
    hour = utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0

    jd = swe.julday(year, month, day, hour)
    logger.info(f"UTC时间 {utc_dt} 转换为儒略日: {jd}")
    return jd


def calculate_equation_of_time(jd_ut: float) -> float:
    """
    计算真太阳时与平太阳时的差值 (Equation of Time)

    使用 Swiss Ephemeris 计算，返回值的单位是分钟。
    正值表示真太阳时比平太阳时快（真太阳在前），
    负值表示真太阳时比平太阳时慢。

    公式: True Solar Time = Mean Solar Time + EoT
    """
    try:
        eq = swe.time_equ(jd_ut)
        # swe.time_equ returns days as float (some wrappers return (float,))
        if isinstance(eq, (tuple, list)):
            eot_minutes = eq[0] * 1440
        else:
            eot_minutes = eq * 1440
        return eot_minutes
    except AttributeError:
        # swisseph 版本不支持 time_equ，使用近似公式计算
        # γ = 2π/365 × (day_of_year - 1 + hour_adjustment)
        try:
            # 获取太阳位置用于精确计算
            sun_pos = swe.calc_ut(jd_ut, swe.SUN, swe.FLG_SWIEPH)
            sun_longitude = sun_pos[0]

            # 太阳平近点角近似
            n = sun_longitude - 282.94
            if n < 0:
                n += 360

            # EoT 近似公式 (分钟)
            eot_minutes = (-1.915 * math.sin(math.radians(n))
                          - 0.020 * math.sin(math.radians(2 * n)))
            return eot_minutes
        except Exception:
            logger.warning("无法计算真太阳时")
            return 0.0


def apply_true_solar_time(
    local_dt: datetime,
    jd_ut: float,
    longitude: float,
    timezone_offset: float
) -> Tuple[datetime, float]:
    """
    将平太阳时（标准时间）校正为真太阳时（视太阳时）

    中国古法命理（八字、紫微斗数）要求使用真太阳时校正出生时间。
    校正量 = 时差(EoT) + 经度校正

    Args:
        local_dt: 本地标准时间
        jd_ut: 对应的儒略日 (UT)
        longitude: 当地经度
        timezone_offset: 时区偏移（小时）

    Returns:
        (校正后的本地时间, 校正总量(分钟))
    """
    # 1. 经度校正: 当地经度与标准子午线的差值 × 4 分钟/度
    standard_meridian = timezone_offset * 15.0
    longitude_correction = (longitude - standard_meridian) * 4.0

    # 2. 真太阳时差 (Equation of Time)
    eot_minutes = calculate_equation_of_time(jd_ut)

    # 3. 总校正量
    total_correction = eot_minutes + longitude_correction

    corrected_dt = local_dt + timedelta(minutes=total_correction)

    return corrected_dt, total_correction


def calculate_planet_ut(jd: float, planet_id: int) -> Dict[str, Any]:
    result, ret_flag = swe.calc_ut(jd, planet_id, SE_FLAGS)
    
    longitude = result[0]
    latitude_planet = result[1]
    speed = result[3]
    
    planet_info = PLANET_INFO.get(planet_id, {})
    
    return {
        "planet_id": planet_id,
        "name": planet_info.get("name", "未知"),
        "symbol": planet_info.get("symbol", "★"),
        "longitude": longitude,
        "latitude": latitude_planet,
        "speed": speed,
        "is_retrograde": speed < 0
    }


def calculate_houses_ex(
    jd: float, latitude: float, longitude: float, house_system: str
) -> Dict[str, Any]:
    if house_system == HouseSystem.WHOLE_SIGN.value:
        houses, ascmc = swe.houses_ex(jd, latitude, longitude, b'P', 0)
        ascendant_longitude = ascmc[0]

        asc_sign = int(ascendant_longitude / 30)

        # 整宫制：每个宫位正好30°，第1宫从上升星座的0°开始
        # house_cusps[0]=asc_sign*30°, [1]=next_sign*30°, ..., [11]=prev_sign*30°
        cusp_start = asc_sign * 30.0
        house_cusps = [(cusp_start + i * 30) % 360 for i in range(12)]

        return {
            "system": HouseSystem.WHOLE_SIGN.value,
            "house_cusps": house_cusps,
            "houses": [longitude_to_zodiac(cusp) for cusp in house_cusps],
            "ascendant": longitude_to_zodiac(ascendant_longitude),
            "midheaven": longitude_to_zodiac(ascmc[1]) if len(ascmc) > 1 else None,
            "ascendant_longitude": ascendant_longitude,
            "midheaven_longitude": ascmc[1] if len(ascmc) > 1 else None,
            "debug": {
                "ascendant_longitude": ascendant_longitude,
                "asc_sign": asc_sign
            }
        }
    else:
        houses, ascmc = swe.houses_ex(jd, latitude, longitude, b'P', 0)

        house_cusps = list(houses[:12])

        return {
            "system": HouseSystem.PLACIDUS.value,
            "house_cusps": house_cusps,
            "houses": [longitude_to_zodiac(cusp) for cusp in house_cusps],
            "ascendant": longitude_to_zodiac(ascmc[0]),
            "midheaven": longitude_to_zodiac(ascmc[1]),
            "ascendant_longitude": ascmc[0],
            "midheaven_longitude": ascmc[1],
            "debug": {
                "ascendant_longitude": ascmc[0],
                "midheaven_longitude": ascmc[1]
            }
        }


def calculate_all_planets(jd: float, house_cusps: List[float]) -> List[Dict[str, Any]]:
    planets = []
    
    for planet_id in MAIN_PLANETS:
        planet_data = calculate_planet_ut(jd, planet_id)
        
        zodiac_info = longitude_to_zodiac(planet_data["longitude"])
        house = find_house_for_planet(planet_data["longitude"], house_cusps)
        
        planet_data["zodiac"] = zodiac_info
        planet_data["house"] = house
        planets.append(planet_data)
    
    for planet_id in ASTEROID_PLANETS:
        try:
            planet_data = calculate_planet_ut(jd, planet_id)
            
            zodiac_info = longitude_to_zodiac(planet_data["longitude"])
            house = find_house_for_planet(planet_data["longitude"], house_cusps)
            
            planet_data["zodiac"] = zodiac_info
            planet_data["house"] = house
            planets.append(planet_data)
        except Exception as e:
            planet_info = PLANET_INFO.get(planet_id, {})
            logger.warning(f"计算小行星 {planet_info.get('name', planet_id)} 失败(需要星历文件): {e}")
    
    try:
        result, ret_flag = swe.calc_ut(jd, swe.TRUE_NODE, SE_FLAGS)
        longitude = result[0]
        
        zodiac_info = longitude_to_zodiac(longitude)
        house = find_house_for_planet(longitude, house_cusps)
        
        north_speed = result[3]
        planets.append({
            "planet_id": swe.TRUE_NODE,
            "name": "北交点",
            "symbol": "☊",
            "longitude": longitude,
            "latitude": 0,
            "speed": north_speed,
            "zodiac": zodiac_info,
            "house": house,
            "is_retrograde": north_speed < 0
        })
        
        south_longitude = (longitude + 180) % 360
        south_zodiac = longitude_to_zodiac(south_longitude)
        south_house = find_house_for_planet(south_longitude, house_cusps)
        
        planets.append({
            "planet_id": -1,
            "name": "南交点",
            "symbol": "☋",
            "longitude": south_longitude,
            "latitude": 0,
            "speed": north_speed,
            "zodiac": south_zodiac,
            "house": south_house,
            "is_retrograde": north_speed < 0
        })
    except Exception as e:
        logger.warning(f"计算交点失败: {e}")
    
    return planets


ASTEROID_PLANET_NAMES = {"谷神星", "智神星", "婚神星", "灶神星", "凯龙星"}


def is_aspect_applying(p1_longitude: float, p1_speed: float,
                       p2_longitude: float, p2_speed: float,
                       current_diff: float, exact_angle: float) -> bool:
    """判断相位是入相位(applying)还是出相位(separating)。

    计算一个极短时间后的角距离变化，如果轨道在缩小则为入相位。
    """
    dt = 0.01
    f1 = p1_longitude + p1_speed * dt
    f2 = p2_longitude + p2_speed * dt
    future_diff = abs(f1 - f2)
    if future_diff > 180:
        future_diff = 360 - future_diff

    current_orb = abs(current_diff - exact_angle)
    future_orb = abs(future_diff - exact_angle)
    return future_orb < current_orb


def calculate_aspects(planets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    ASPECT_TYPES = [
        {"name": "合相", "symbol": "☌", "angle": 0, "orb": 8, "asteroid_orb": 3},
        {"name": "半六合", "symbol": "⚺", "angle": 30, "orb": 3, "asteroid_orb": 1},
        {"name": "六分相", "symbol": "⚹", "angle": 60, "orb": 6, "asteroid_orb": 2},
        {"name": "四分相", "symbol": "□", "angle": 90, "orb": 8, "asteroid_orb": 3},
        {"name": "三分相", "symbol": "△", "angle": 120, "orb": 8, "asteroid_orb": 3},
        {"name": "梅花相", "symbol": "⚻", "angle": 150, "orb": 3, "asteroid_orb": 1},
        {"name": "对分相", "symbol": "☍", "angle": 180, "orb": 8, "asteroid_orb": 3},
    ]

    aspects = []

    for i in range(len(planets)):
        for j in range(i + 1, len(planets)):
            p1 = planets[i]
            p2 = planets[j]

            diff = abs(p1["longitude"] - p2["longitude"])
            if diff > 180:
                diff = 360 - diff

            for aspect_type in ASPECT_TYPES:
                angle = aspect_type["angle"]
                is_asteroid_aspect = p1["name"] in ASTEROID_PLANET_NAMES or p2["name"] in ASTEROID_PLANET_NAMES
                orb = aspect_type["asteroid_orb"] if is_asteroid_aspect else aspect_type["orb"]

                if abs(diff - angle) <= orb:
                    applying = is_aspect_applying(
                        p1["longitude"], p1.get("speed", 0),
                        p2["longitude"], p2.get("speed", 0),
                        diff, angle
                    )
                    aspects.append({
                        "planet1": p1["name"],
                        "planet1_symbol": p1["symbol"],
                        "planet2": p2["name"],
                        "planet2_symbol": p2["symbol"],
                        "aspect": aspect_type["name"],
                        "aspect_symbol": aspect_type["symbol"],
                        "angle": angle,
                        "actual_angle": round(diff, 4),
                        "orb": round(abs(diff - angle), 4),
                        "is_applying": applying
                    })
                    break

    return aspects


def calculate_chart(
    year: int,
    month: int,
    day: int,
    hour: int = 12,
    minute: int = 0,
    latitude: float = 39.9,
    longitude: float = 116.4,
    house_system: str = HouseSystem.PLACIDUS.value,
    use_true_solar_time: bool = False
) -> Dict[str, Any]:
    logger.info(f"""
========== 星盘计算开始 ==========
输入参数:
  日期: {year}-{month:02d}-{day:02d}
  时间: {hour:02d}:{minute:02d} (本地时间)
  经纬度: {longitude}°, {latitude}°
  宫位系统: {house_system}
====================================
    """)
    
    utc_dt, timezone_info = local_to_utc(year, month, day, hour, minute, latitude, longitude, use_true_solar_time=use_true_solar_time)
    jd = utc_to_julday(utc_dt)
    
    houses_result = calculate_houses_ex(jd, latitude, longitude, house_system)
    house_cusps = houses_result["house_cusps"]
    
    planets = calculate_all_planets(jd, house_cusps)
    
    sun_sign = None
    moon_sign = None
    moon_data = None
    
    for planet in planets:
        if planet["name"] == "太阳":
            sun_sign = planet["zodiac"]
        elif planet["name"] == "月亮":
            moon_sign = planet["zodiac"]
            moon_data = planet
    
    aspects = calculate_aspects(planets)
    
    logger.info(f"""
========== 计算结果 ==========
儒略日: {jd}
时区信息: {timezone_info}

上升点: {houses_result['ascendant_longitude']}° = {houses_result['ascendant']['sign']} {houses_result['ascendant']['dms']['formatted']}
天顶: {houses_result.get('midheaven_longitude')}°

太阳: {sun_sign['sign']} {sun_sign['dms']['formatted']} 第{[p['house'] for p in planets if p['name'] == '太阳'][0]}宫
月亮: {moon_sign['sign']} {moon_sign['dms']['formatted']} 第{[p['house'] for p in planets if p['name'] == '月亮'][0]}宫
==============================
    """)
    
    chart_data = {
        "input": {
            "date": f"{year}-{month:02d}-{day:02d}",
            "time": f"{hour:02d}:{minute:02d}",
            "latitude": latitude,
            "longitude": longitude,
            "house_system": house_system
        },
        "timezone_info": timezone_info,
        "julday": jd,
        "houses": houses_result,
        "ascendant": houses_result["ascendant"],
        "midheaven": houses_result.get("midheaven"),
        "sun_sign": sun_sign,
        "moon_sign": moon_sign,
        "planets": planets,
        "aspects": aspects,
        "zodiac_signs_info": [
            {
                "index": i,
                "name": ZODIAC_SIGNS[i],
                "symbol": ZODIAC_SYMBOLS[i],
                "element": ELEMENTS[i],
                "quality": QUALITIES[i],
                "ruling_planet": RULING_PLANETS[i]
            }
            for i in range(12)
        ]
    }
    
    return chart_data


def parse_birth_datetime(birth_date: str, birth_time: str) -> Dict[str, int]:
    date_parts = birth_date.split("-")
    year = int(date_parts[0])
    month = int(date_parts[1])
    day = int(date_parts[2])
    
    time_parts = birth_time.split(":")
    hour = int(time_parts[0])
    minute = int(time_parts[1])
    
    return {
        "year": year,
        "month": month,
        "day": day,
        "hour": hour,
        "minute": minute
    }


def verify_chart():
    test_cases = [
        {
            "name": "基础测试",
            "year": 1988,
            "month": 5,
            "day": 15,
            "hour": 10,
            "minute": 30,
            "latitude": 39.9042,
            "longitude": 116.4074,
            "house_system": "placidus"
        }
    ]
    
    for tc in test_cases:
        logger.info(f"\n{'='*60}\n测试案例: {tc['name']}\n{'='*60}")
        result = calculate_chart(
            year=tc["year"],
            month=tc["month"],
            day=tc["day"],
            hour=tc["hour"],
            minute=tc["minute"],
            latitude=tc["latitude"],
            longitude=tc["longitude"],
            house_system=tc["house_system"]
        )
        
        logger.info(f"""
验证结果摘要:
- 儒略日: {result['julday']}
- 上升点: {result['ascendant']['sign']} {result['ascendant']['dms']['formatted']}
- 太阳: {result['sun_sign']['sign']} {result['sun_sign']['dms']['formatted']}
- 月亮: {result['moon_sign']['sign']} {result['moon_sign']['dms']['formatted']}
- 宫位系统: {result['houses']['system']}
- 行星数量: {len(result['planets'])}
- 相位数量: {len(result['aspects'])}
""")
    
    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    verify_chart()
