import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from enum import Enum

from app.schemas import ApiResponse, HouseSystemEnum
from app.astro import calculate_chart, parse_birth_datetime, longitude_to_zodiac, find_house_for_planet
from app.services.classical_astrology_service import get_classical_astrology_service, ClassicalAstrologyService

logger = logging.getLogger(__name__)

router = APIRouter()
classical_service = get_classical_astrology_service()


class ChartTimeType(str, Enum):
    day = "day"
    night = "night"
    auto = "auto"


class DignitySystem(str, Enum):
    traditional = "traditional"
    modern = "modern"


class AspectIncludeType(str, Enum):
    major = "major"
    all = "all"


class WorkbenchChartRequest(BaseModel):
    name: Optional[str] = Field(None, description="姓名")
    birth_date: str = Field(..., description="出生日期 YYYY-MM-DD")
    birth_time: str = Field(..., description="出生时间 HH:MM")
    latitude: float = Field(39.9, ge=-90, le=90, description="纬度")
    longitude: float = Field(116.4, ge=-180, le=180, description="经度")
    birth_place: Optional[str] = Field(None, description="出生地点")
    house_system: HouseSystemEnum = Field(
        default=HouseSystemEnum.placidus,
        description="宫位系统"
    )
    chart_time_type: ChartTimeType = Field(
        default=ChartTimeType.auto,
        description="日夜盘类型：auto自动判断，day日盘，night夜盘"
    )
    dignity_system: DignitySystem = Field(
        default=DignitySystem.traditional,
        description="庙旺弱陷系统：traditional传统守护星，modern现代守护星"
    )
    aspect_include: AspectIncludeType = Field(
        default=AspectIncludeType.major,
        description="相位包含类型：major仅主相位，all包含次要相位"
    )


class PlanetAdjustRequest(BaseModel):
    original_chart: Dict[str, Any] = Field(..., description="原始星盘数据")
    planet_name: str = Field(..., description="要调整的行星名称")
    new_longitude: float = Field(..., ge=0, le=360, description="新的黄经度数")


class ProbePlanetRequest(BaseModel):
    chart_data: Dict[str, Any] = Field(..., description="星盘数据")
    planet_name: str = Field(..., description="要探测的行星名称")
    chart_time_type: ChartTimeType = Field(default=ChartTimeType.auto)
    dignity_system: DignitySystem = Field(default=DignitySystem.traditional)


class GenerateNotesRequest(BaseModel):
    analysis_data: Dict[str, Any] = Field(..., description="完整分析数据")
    focus_areas: Optional[List[str]] = Field(None, description="重点关注领域")


def _is_day_chart(chart_data: Dict[str, Any], time_type: ChartTimeType) -> bool:
    """判断是否为日盘"""
    if time_type == ChartTimeType.day:
        return True
    if time_type == ChartTimeType.night:
        return False
    
    ascendant_long = chart_data.get("houses", {}).get("ascendant_longitude", 0)
    sun_long = None
    for planet in chart_data.get("planets", []):
        if planet.get("name") == "太阳":
            sun_long = planet.get("longitude", 0)
            break
    
    if sun_long is None:
        return True
    
    sun_sign = int(sun_long / 30) % 12
    asc_sign = int(ascendant_long / 30) % 12
    
    sun_above_horizon = False
    diff = (sun_long - ascendant_long) % 360
    if 0 <= diff < 180:
        sun_above_horizon = True
    
    return sun_above_horizon


@router.post("/calculate", response_model=ApiResponse)
def calculate_workbench_chart(request: WorkbenchChartRequest):
    """
    计算占星师工作台星盘 - 包含完整古典占星分析
    """
    try:
        dt = parse_birth_datetime(request.birth_date, request.birth_time)
        
        chart_data = calculate_chart(
            year=dt["year"],
            month=dt["month"],
            day=dt["day"],
            hour=dt["hour"],
            minute=dt["minute"],
            latitude=request.latitude,
            longitude=request.longitude,
            house_system=request.house_system.value
        )
        
        is_day = _is_day_chart(chart_data, request.chart_time_type)
        use_traditional = request.dignity_system == DignitySystem.traditional
        include_minor = request.aspect_include == AspectIncludeType.all
        
        analysis = classical_service.analyze_full_chart(
            chart_data,
            is_day_chart=is_day,
            use_traditional=use_traditional,
            include_minor_aspects=include_minor
        )
        
        return ApiResponse(
            code=200,
            message="星盘计算成功",
            data={
                "chart": chart_data,
                "analysis": analysis,
                "name": request.name,
                "birth_place": request.birth_place,
                "is_day_chart": is_day,
                "calculated_at": datetime.utcnow().isoformat()
            }
        )
        
    except ValueError as e:
        logger.error(f"参数错误: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"计算失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"计算失败: {str(e)}")


@router.post("/adjust-planet", response_model=ApiResponse)
def adjust_planet_position(request: PlanetAdjustRequest):
    """
    调整行星位置并重新计算所有相关征象
    
    用于实时探针功能：占星师拖动行星时，立即计算变动影响
    """
    try:
        original_chart = request.original_chart
        planet_name = request.planet_name
        new_longitude = request.new_longitude
        
        planets = original_chart.get("planets", [])
        house_cusps = original_chart.get("houses", {}).get("house_cusps", [])
        
        adjusted_planets = []
        target_planet = None
        
        for planet in planets:
            if planet.get("name") == planet_name:
                new_zodiac = longitude_to_zodiac(new_longitude)
                new_house = find_house_for_planet(new_longitude, house_cusps)
                
                adjusted_planet = {
                    **planet,
                    "longitude": new_longitude,
                    "zodiac": new_zodiac,
                    "house": new_house,
                    "was_adjusted": True,
                    "original_longitude": planet.get("longitude")
                }
                adjusted_planets.append(adjusted_planet)
                target_planet = adjusted_planet
            else:
                adjusted_planets.append(planet)
        
        adjusted_chart = {
            **original_chart,
            "planets": adjusted_planets
        }
        
        is_day = original_chart.get("is_day_chart", True)
        use_traditional = True
        
        new_analysis = classical_service.analyze_full_chart(
            adjusted_chart,
            is_day_chart=is_day,
            use_traditional=use_traditional,
            include_minor_aspects=False
        )
        
        original_analysis = original_chart.get("analysis", {})
        changes = _detect_changes(original_analysis, new_analysis, planet_name)
        
        return ApiResponse(
            code=200,
            message="行星位置调整成功",
            data={
                "adjusted_planet": target_planet,
                "adjusted_chart": adjusted_chart,
                "new_analysis": new_analysis,
                "changes": changes
            }
        )
        
    except Exception as e:
        logger.error(f"调整行星位置失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"调整失败: {str(e)}")


def _detect_changes(
    original: Dict[str, Any],
    new: Dict[str, Any],
    planet_name: str
) -> Dict[str, Any]:
    """检测调整前后的变化"""
    changes = {
        "aspects": {"added": [], "removed": [], "changed": []},
        "receptions": {"added": [], "removed": []},
        "dignities": {"original": None, "new": None},
        "light_translations": {"added": [], "removed": []},
        "besiegements": {"added": [], "removed": []}
    }
    
    original_aspects = original.get("aspects", [])
    new_aspects = new.get("aspects", [])
    
    original_set = set()
    for a in original_aspects:
        key = tuple(sorted([a.get("planet1", ""), a.get("planet2", "")]) + [a.get("aspect", "")])
        original_set.add(key)
    
    new_set = set()
    for a in new_aspects:
        key = tuple(sorted([a.get("planet1", ""), a.get("planet2", "")]) + [a.get("aspect", "")])
        new_set.add(key)
    
    for a in new_aspects:
        key = tuple(sorted([a.get("planet1", ""), a.get("planet2", "")]) + [a.get("aspect", "")])
        if key not in original_set:
            changes["aspects"]["added"].append(a)
    
    for a in original_aspects:
        key = tuple(sorted([a.get("planet1", ""), a.get("planet2", "")]) + [a.get("aspect", "")])
        if key not in new_set:
            changes["aspects"]["removed"].append(a)
    
    original_receptions = original.get("receptions", [])
    new_receptions = new.get("receptions", [])
    
    original_rec_set = set()
    for r in original_receptions:
        key = tuple(sorted([r.get("planet_a", ""), r.get("planet_b", "")]) + [r.get("reception_type", "")])
        original_rec_set.add(key)
    
    for r in new_receptions:
        key = tuple(sorted([r.get("planet_a", ""), r.get("planet_b", "")]) + [r.get("reception_type", "")])
        if key not in original_rec_set:
            changes["receptions"]["added"].append(r)
    
    for r in original_receptions:
        key = tuple(sorted([r.get("planet_a", ""), r.get("planet_b", "")]) + [r.get("reception_type", "")])
        if key not in original_rec_set:
            changes["receptions"]["removed"].append(r)
    
    original_planets = original.get("planets", [])
    new_planets = new.get("planets", [])
    
    for p in original_planets:
        if p.get("name") == planet_name:
            changes["dignities"]["original"] = p.get("dignities")
    
    for p in new_planets:
        if p.get("name") == planet_name:
            changes["dignities"]["new"] = p.get("dignities")
    
    return changes


@router.post("/probe-planet", response_model=ApiResponse)
def probe_planet(request: ProbePlanetRequest):
    """
    探测单个行星的所有相关征象
    
    返回该行星的：
    - 庙旺弱陷状态
    - 所有相位
    - 接纳/互容关系
    - 映点信息
    - 参与的光线传递
    - 是否被围攻
    """
    try:
        chart_data = request.chart_data
        planet_name = request.planet_name
        
        is_day = _is_day_chart(chart_data, request.chart_time_type)
        use_traditional = request.dignity_system == DignitySystem.traditional
        
        analysis = classical_service.analyze_full_chart(
            chart_data,
            is_day_chart=is_day,
            use_traditional=use_traditional,
            include_minor_aspects=False
        )
        
        planets = analysis.get("planets", [])
        target_planet = None
        for p in planets:
            if p.get("name") == planet_name:
                target_planet = p
                break
        
        if not target_planet:
            raise HTTPException(status_code=404, detail=f"未找到行星: {planet_name}")
        
        aspects = analysis.get("aspects", [])
        related_aspects = [
            a for a in aspects
            if a.get("planet1") == planet_name or a.get("planet2") == planet_name
        ]
        
        receptions = analysis.get("receptions", [])
        related_receptions = [
            r for r in receptions
            if r.get("planet_a") == planet_name or r.get("planet_b") == planet_name
        ]
        
        light_translations = analysis.get("light_translations", [])
        related_translations = [
            t for t in light_translations
            if t.get("translator") == planet_name 
            or t.get("planet_a") == planet_name 
            or t.get("planet_b") == planet_name
        ]
        
        besiegements = analysis.get("besiegements", [])
        related_besiegements = [
            b for b in besiegements
            if b.get("besieged_planet") == planet_name
            or planet_name in b.get("besieging_planets", [])
        ]
        
        antiscia_aspects = analysis.get("antiscia_aspects", [])
        related_antiscia = [
            a for a in antiscia_aspects
            if a.get("planet_a") == planet_name or a.get("planet_b") == planet_name
        ]
        
        return ApiResponse(
            code=200,
            message="探测成功",
            data={
                "planet": target_planet,
                "aspects": related_aspects,
                "receptions": related_receptions,
                "light_translations": related_translations,
                "besiegements": related_besiegements,
                "antiscia_aspects": related_antiscia,
                "is_day_chart": is_day
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"探测行星失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"探测失败: {str(e)}")


@router.post("/generate-notes", response_model=ApiResponse)
def generate_interpretation_notes(request: GenerateNotesRequest):
    """
    自动生成标准化解盘笔记草稿
    """
    try:
        analysis_data = request.analysis_data
        focus_areas = request.focus_areas
        
        notes = classical_service.generate_interpretation_notes(analysis_data)
        
        if focus_areas:
            filtered_notes = {
                "executive_summary": notes.get("executive_summary", ""),
                "planets_analysis": [],
                "aspects_analysis": [],
                "receptions_analysis": [],
                "special_indicators": [],
                "key_themes": []
            }
            
            focus_areas_set = set(focus_areas)
            
            for pa in notes.get("planets_analysis", []):
                if pa.get("planet") in focus_areas_set:
                    filtered_notes["planets_analysis"].append(pa)
            
            for aa in notes.get("aspects_analysis", []):
                planets = aa.get("planets", "")
                for focus in focus_areas:
                    if focus in planets:
                        filtered_notes["aspects_analysis"].append(aa)
                        break
            
            for ra in notes.get("receptions_analysis", []):
                planets = ra.get("planets", "")
                for focus in focus_areas:
                    if focus in planets:
                        filtered_notes["receptions_analysis"].append(ra)
                        break
            
            notes = filtered_notes
        
        return ApiResponse(
            code=200,
            message="解盘笔记生成成功",
            data={
                "notes": notes,
                "generated_at": datetime.utcnow().isoformat(),
                "focus_areas": focus_areas
            }
        )
        
    except Exception as e:
        logger.error(f"生成解盘笔记失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@router.get("/classical-rules", response_model=ApiResponse)
def get_classical_rules():
    """
    获取古典占星规则参考
    """
    from app.services.classical_astrology_service import (
        TRADITIONAL_RULING_PLANETS, TRADITIONAL_EXALTATION,
        DETRIMENT_PLANETS, FALL_PLANETS,
        TRIPLICITY_RULERS, EGYPTIAN_TERMS, CHALDEAN_FACES,
        ZODIAC_SIGNS, ELEMENTS, QUALITIES
    )
    
    rules = {
        "zodiac_signs": [
            {
                "index": i,
                "name": ZODIAC_SIGNS[i],
                "element": ELEMENTS[i].value if hasattr(ELEMENTS[i], "value") else ELEMENTS[i],
                "quality": QUALITIES[i].value if hasattr(QUALITIES[i], "value") else QUALITIES[i],
                "traditional_ruler": TRADITIONAL_RULING_PLANETS.get(i),
                "exaltation": TRADITIONAL_EXALTATION.get(i),
                "detriment": DETRIMENT_PLANETS.get(i),
                "fall": FALL_PLANETS.get(i)
            }
            for i in range(12)
        ],
        "triplicity_rulers": {
            k.value if hasattr(k, "value") else k: v
            for k, v in TRIPLICITY_RULERS.items()
        },
        "egyptian_terms": EGYPTIAN_TERMS,
        "chaldean_faces": CHALDEAN_FACES,
        "aspects": [
            {"name": "合相", "symbol": "☌", "angle": 0, "orb": 8, "nature": "neutral"},
            {"name": "六分相", "symbol": "⚹", "angle": 60, "orb": 6, "nature": "harmonious"},
            {"name": "四分相", "symbol": "□", "angle": 90, "orb": 8, "nature": "challenging"},
            {"name": "三分相", "symbol": "△", "angle": 120, "orb": 8, "nature": "harmonious"},
            {"name": "对分相", "symbol": "☍", "angle": 180, "orb": 8, "nature": "challenging"},
        ],
        "concepts": {
            "reception": "接纳：当行星A位于行星B所守护的星座时，行星B接纳行星A的能量",
            "mutual_reception": "互容：当两颗行星互相位于对方所守护的星座时，形成互容关系",
            "antiscia": "映点：以夏至点为轴的对称点，两星映点相合象征隐藏的连接",
            "translation_of_light": "光线传递：较轻的行星通过相位连接两颗较重的行星，传递能量",
            "besiegement": "围攻：行星被凶星通过相同相位从两侧包围"
        }
    }
    
    return ApiResponse(
        code=200,
        message="success",
        data=rules
    )


@router.get("/planets-info", response_model=ApiResponse)
def get_planets_info():
    """
    获取行星信息列表（用于工作台选择）
    """
    planets = [
        {"name": "太阳", "symbol": "☉", "type": "personal", "traditional": True},
        {"name": "月亮", "symbol": "☽", "type": "personal", "traditional": True},
        {"name": "水星", "symbol": "☿", "type": "personal", "traditional": True},
        {"name": "金星", "symbol": "♀", "type": "personal", "traditional": True},
        {"name": "火星", "symbol": "♂", "type": "personal", "traditional": True},
        {"name": "木星", "symbol": "♃", "type": "social", "traditional": True},
        {"name": "土星", "symbol": "♄", "type": "social", "traditional": True},
        {"name": "天王星", "symbol": "♅", "type": "outer", "traditional": False},
        {"name": "海王星", "symbol": "♆", "type": "outer", "traditional": False},
        {"name": "冥王星", "symbol": "♇", "type": "outer", "traditional": False},
        {"name": "北交点", "symbol": "☊", "type": "node", "traditional": True},
        {"name": "南交点", "symbol": "☋", "type": "node", "traditional": True},
    ]
    
    return ApiResponse(
        code=200,
        message="success",
        data={"planets": planets}
    )
