from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging
import swisseph as swe

from app.astro import (
    calculate_chart, parse_birth_datetime, HouseSystem,
    MAIN_PLANETS, PLANET_INFO, SE_FLAGS, degree_to_dms,
    longitude_to_zodiac, find_house_for_planet, calculate_planet_ut
)

logger = logging.getLogger(__name__)

SYNASTRY_ASPECT_TYPES = [
    {"name": "合相", "symbol": "☌", "angle": 0.0, "orb": 8.0, "nature": "neutral"},
    {"name": "六分相", "symbol": "⚹", "angle": 60.0, "orb": 6.0, "nature": "harmonious"},
    {"name": "四分相", "symbol": "□", "angle": 90.0, "orb": 8.0, "nature": "challenging"},
    {"name": "三分相", "symbol": "△", "angle": 120.0, "orb": 8.0, "nature": "harmonious"},
    {"name": "对分相", "symbol": "☍", "angle": 180.0, "orb": 8.0, "nature": "challenging"},
]

SYNASTRY_PLANET_PRIORITY = {
    '太阳': 10, '月亮': 9, '金星': 8, '火星': 7,
    '水星': 6, '木星': 5, '土星': 4, '天王星': 3,
    '海王星': 2, '冥王星': 1, '北交点': 0, '南交点': 0
}


def calculate_angular_distance(lon1: float, lon2: float) -> float:
    diff = abs(lon1 - lon2)
    if diff > 180.0:
        diff = 360.0 - diff
    return diff


def find_exact_aspect(diff: float, aspect_type: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    angle = aspect_type["angle"]
    orb = aspect_type["orb"]
    
    if abs(diff - angle) <= orb:
        orb_used = abs(diff - angle)
        return {
            "aspect": aspect_type["name"],
            "aspect_symbol": aspect_type["symbol"],
            "angle": angle,
            "actual_angle": round(diff, 6),
            "orb": round(orb_used, 6),
            "orb_arcminutes": round(orb_used * 60, 2),
            "nature": aspect_type["nature"],
            "is_applying": None
        }
    return None


def calculate_synastry_aspects(
    planets_a: List[Dict[str, Any]],
    planets_b: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    aspects = []
    
    main_planet_names = set(p["name"] for p in PLANET_INFO.values())
    
    for p_a in planets_a:
        if p_a["name"] not in main_planet_names:
            continue
            
        for p_b in planets_b:
            if p_b["name"] not in main_planet_names:
                continue
            
            diff = calculate_angular_distance(p_a["longitude"], p_b["longitude"])
            
            for aspect_type in SYNASTRY_ASPECT_TYPES:
                aspect = find_exact_aspect(diff, aspect_type)
                if aspect:
                    aspects.append({
                        "planet_a": p_a["name"],
                        "planet_a_symbol": p_a["symbol"],
                        "planet_a_longitude": p_a["longitude"],
                        "planet_b": p_b["name"],
                        "planet_b_symbol": p_b["symbol"],
                        "planet_b_longitude": p_b["longitude"],
                        **aspect,
                        "priority": (
                            SYNASTRY_PLANET_PRIORITY.get(p_a["name"], 0) + 
                            SYNASTRY_PLANET_PRIORITY.get(p_b["name"], 0)
                        )
                    })
                    break
    
    aspects.sort(key=lambda x: (x["orb"], -x["priority"]))
    
    return aspects


def calculate_synastry_chart(
    person_a: Dict[str, Any],
    person_b: Dict[str, Any]
) -> Dict[str, Any]:
    required_keys = ["birth_date", "birth_time", "latitude", "longitude", "house_system"]
    
    for key in required_keys:
        if key not in person_a or key not in person_b:
            raise ValueError(f"Missing required key: {key}")
    
    dt_a = parse_birth_datetime(person_a["birth_date"], person_a["birth_time"])
    dt_b = parse_birth_datetime(person_b["birth_date"], person_b["birth_time"])
    
    chart_a = calculate_chart(
        year=dt_a["year"],
        month=dt_a["month"],
        day=dt_a["day"],
        hour=dt_a["hour"],
        minute=dt_a["minute"],
        latitude=person_a["latitude"],
        longitude=person_a["longitude"],
        house_system=person_a.get("house_system", HouseSystem.PLACIDUS.value)
    )
    
    chart_b = calculate_chart(
        year=dt_b["year"],
        month=dt_b["month"],
        day=dt_b["day"],
        hour=dt_b["hour"],
        minute=dt_b["minute"],
        latitude=person_b["latitude"],
        longitude=person_b["longitude"],
        house_system=person_b.get("house_system", HouseSystem.PLACIDUS.value)
    )
    
    synastry_aspects = calculate_synastry_aspects(chart_a["planets"], chart_b["planets"])
    
    harmonious_aspects = [a for a in synastry_aspects if a["nature"] == "harmonious"]
    challenging_aspects = [a for a in synastry_aspects if a["nature"] == "challenging"]
    neutral_aspects = [a for a in synastry_aspects if a["nature"] == "neutral"]
    
    result = {
        "person_a": {
            "name": person_a.get("name", "A"),
            "input": {
                "birth_date": person_a["birth_date"],
                "birth_time": person_a["birth_time"],
                "latitude": person_a["latitude"],
                "longitude": person_a["longitude"],
                "house_system": person_a.get("house_system", HouseSystem.PLACIDUS.value)
            },
            "chart": chart_a
        },
        "person_b": {
            "name": person_b.get("name", "B"),
            "input": {
                "birth_date": person_b["birth_date"],
                "birth_time": person_b["birth_time"],
                "latitude": person_b["latitude"],
                "longitude": person_b["longitude"],
                "house_system": person_b.get("house_system", HouseSystem.PLACIDUS.value)
            },
            "chart": chart_b
        },
        "synastry": {
            "aspects": synastry_aspects,
            "aspect_summary": {
                "total": len(synastry_aspects),
                "harmonious": len(harmonious_aspects),
                "challenging": len(challenging_aspects),
                "neutral": len(neutral_aspects)
            },
            "harmonious_aspects": harmonious_aspects,
            "challenging_aspects": challenging_aspects,
            "neutral_aspects": neutral_aspects
        },
        "calculation_info": {
            "aspect_accuracy_arcseconds": 0.01,
            "calculated_at": datetime.utcnow().isoformat()
        }
    }
    
    return result


def verify_synastry_calculation() -> Dict[str, Any]:
    test_person_a = {
        "name": "测试者A",
        "birth_date": "1988-05-15",
        "birth_time": "10:30",
        "latitude": 39.9042,
        "longitude": 116.4074,
        "house_system": "placidus"
    }
    
    test_person_b = {
        "name": "测试者B",
        "birth_date": "1990-03-20",
        "birth_time": "14:15",
        "latitude": 31.2304,
        "longitude": 121.4737,
        "house_system": "placidus"
    }
    
    result = calculate_synastry_chart(test_person_a, test_person_b)
    
    logger.info(f"""
========== 合盘计算验证 ==========
人物A: {test_person_a['name']}
  太阳: {result['person_a']['chart']['sun_sign']['sign']} {result['person_a']['chart']['sun_sign']['dms']['formatted']}
  月亮: {result['person_a']['chart']['moon_sign']['sign']} {result['person_a']['chart']['moon_sign']['dms']['formatted']}

人物B: {test_person_b['name']}
  太阳: {result['person_b']['chart']['sun_sign']['sign']} {result['person_b']['chart']['sun_sign']['dms']['formatted']}
  月亮: {result['person_b']['chart']['moon_sign']['sign']} {result['person_b']['chart']['moon_sign']['dms']['formatted']}

合盘相位:
  总相位数: {result['synastry']['aspect_summary']['total']}
  和谐相位: {result['synastry']['aspect_summary']['harmonious']}
  紧张相位: {result['synastry']['aspect_summary']['challenging']}
  中性相位: {result['synastry']['aspect_summary']['neutral']}

前5个相位 (按容许度排序):
""")
    
    for i, aspect in enumerate(result['synastry']['aspects'][:5]):
        logger.info(f"  {i+1}. {aspect['planet_a']} {aspect['aspect_symbol']} {aspect['planet_b']} - {aspect['aspect']}, 容许度: {aspect['orb_arcminutes']}'")
    
    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    verify_synastry_calculation()
