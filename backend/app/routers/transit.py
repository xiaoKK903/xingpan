from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import logging
import hashlib
from sqlalchemy.orm import Session

from app.schemas import ApiResponse
from app.database import get_db
from app.models import User, Chart
from app.routers.users import get_current_user
from app.astro import (
    local_to_utc, utc_to_julday, parse_birth_datetime,
    calculate_all_planets, calculate_houses_ex
)
from app.services.transit_service import (
    TransitDimension,
    calculate_transit_planets,
    calculate_transit_aspects,
    calculate_moon_phase,
    check_mercury_retrograde,
    calculate_dimension_energy,
    calculate_overall_energy,
    calculate_7day_trend,
    analyze_key_events,
    generate_transit_analysis_prompt,
    generate_fallback_interpretation
)
from app.services.cache_service import get_cache_service
from app.services.ai_service import call_qwen_api

logger = logging.getLogger(__name__)

router = APIRouter()

cache_service = get_cache_service()


def _generate_transit_cache_key(
    action: str,
    birth_date: str,
    birth_time: str,
    latitude: float,
    longitude: float,
    house_system: str,
    target_date: Optional[str] = None
) -> str:
    """生成行运计算的缓存键"""
    key_data = {
        "action": action,
        "birth_date": birth_date,
        "birth_time": birth_time,
        "latitude": round(latitude, 4),
        "longitude": round(longitude, 4),
        "house_system": house_system,
        "target_date": target_date or datetime.now().strftime("%Y-%m-%d")
    }
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return f"transit:{hashlib.md5(key_str.encode()).hexdigest()}"


class TransitRequest(BaseModel):
    birth_date: str = Field(..., description="出生日期 YYYY-MM-DD")
    birth_time: str = Field(..., description="出生时间 HH:MM")
    latitude: float = Field(..., description="出生地点纬度")
    longitude: float = Field(..., description="出生地点经度")
    house_system: str = Field("placidus", description="宫位系统: placidus/whole_sign")
    target_date: Optional[str] = Field(None, description="目标日期 YYYY-MM-DD，默认今天")


class TrendRequest(BaseModel):
    birth_date: str = Field(..., description="出生日期 YYYY-MM-DD")
    birth_time: str = Field(..., description="出生时间 HH:MM")
    latitude: float = Field(..., description="出生地点纬度")
    longitude: float = Field(..., description="出生地点经度")
    house_system: str = Field("placidus", description="宫位系统")
    start_date: Optional[str] = Field(None, description="开始日期，默认今天")


def extract_natal_planets(chart_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    planets = chart_data.get("planets", [])
    main_planet_names = ["太阳", "月亮", "水星", "金星", "火星", "木星", "土星", "天王星", "海王星", "冥王星"]
    return [p for p in planets if p.get("name") in main_planet_names]


def _prepare_natal_data(
    birth_date: str,
    birth_time: str,
    latitude: float,
    longitude: float,
    house_system: str
) -> Dict[str, Any]:
    """准备本命盘数据"""
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
    natal_planets = extract_natal_planets({"planets": natal_planets})
    
    return {
        "natal_planets": natal_planets,
        "house_cusps": house_cusps,
        "jd": jd
    }


def _calculate_transit_internal(
    natal_planets: List[Dict[str, Any]],
    target_date: datetime,
    latitude: float,
    longitude: float,
    house_cusps: List[float]
) -> Dict[str, Any]:
    """内部行运计算函数"""
    utc_dt, _ = local_to_utc(
        target_date.year, target_date.month, target_date.day,
        target_date.hour, target_date.minute,
        latitude, longitude
    )
    jd = utc_to_julday(utc_dt)
    
    transit_planets = calculate_transit_planets(jd)
    
    aspects = calculate_transit_aspects(natal_planets, transit_planets)
    
    moon_phase = calculate_moon_phase(jd)
    
    mercury_retro = check_mercury_retrograde(jd)
    
    dimensions = []
    for dim in TransitDimension:
        dim_energy = calculate_dimension_energy(aspects, dim, natal_planets)
        dimensions.append(dim_energy)
    
    overall = calculate_overall_energy(dimensions)
    
    key_events = analyze_key_events(transit_planets, aspects, moon_phase, mercury_retro)
    
    return {
        "target_date": target_date.strftime("%Y-%m-%d %H:%M"),
        "julday": jd,
        "transit_planets": transit_planets,
        "aspects": aspects,
        "aspects_count": len(aspects),
        "moon_phase": moon_phase,
        "mercury_retrograde": mercury_retro,
        "dimensions": dimensions,
        "overall": overall,
        "key_events": key_events
    }


def _calculate_trend_internal(
    natal_planets: List[Dict[str, Any]],
    start_date: datetime,
    latitude: float,
    longitude: float,
    house_system: str
) -> Dict[str, Any]:
    """内部趋势计算函数"""
    trend_data = calculate_7day_trend(
        natal_planets, start_date,
        latitude, longitude, house_system
    )
    
    all_scores = [day["overall_score"] for day in trend_data]
    max_score = max(all_scores)
    min_score = min(all_scores)
    
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
            "avg_score": round(sum(all_scores) / len(all_scores), 1),
            "turning_points": turning_points
        }
    }


@router.post("/calculate", response_model=ApiResponse)
async def calculate_transit(
    request: TransitRequest,
    db: Session = Depends(get_db)
):
    try:
        cache_key = _generate_transit_cache_key(
            action="calculate",
            birth_date=request.birth_date,
            birth_time=request.birth_time,
            latitude=request.latitude,
            longitude=request.longitude,
            house_system=request.house_system,
            target_date=request.target_date
        )
        
        cached = cache_service.get(cache_key)
        if cached:
            return ApiResponse(
                code=200,
                message="获取行运数据成功（缓存）",
                data=cached
            )
        
        natal_data = _prepare_natal_data(
            request.birth_date, request.birth_time,
            request.latitude, request.longitude,
            request.house_system
        )
        natal_planets = natal_data["natal_planets"]
        house_cusps = natal_data["house_cusps"]
        
        if request.target_date:
            target_dt = datetime.strptime(request.target_date, "%Y-%m-%d")
        else:
            target_dt = datetime.now()
        
        transit_data = _calculate_transit_internal(
            natal_planets, target_dt,
            request.latitude, request.longitude, house_cusps
        )
        
        result = {
            "natal_info": {
                "birth_date": request.birth_date,
                "birth_time": request.birth_time,
                "latitude": request.latitude,
                "longitude": request.longitude,
                "house_system": request.house_system,
                "planets_count": len(natal_planets)
            },
            "target_date": target_dt.strftime("%Y-%m-%d"),
            "day_of_week": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][target_dt.weekday()],
            **transit_data
        }
        
        cache_service.set(cache_key, result, ttl=1800)
        
        return ApiResponse(
            code=200,
            message="获取行运数据成功",
            data=result
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"计算行运失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"计算行运失败: {str(e)}")


@router.post("/trend", response_model=ApiResponse)
async def get_7day_trend(
    request: TrendRequest,
    db: Session = Depends(get_db)
):
    try:
        cache_key = _generate_transit_cache_key(
            action="trend",
            birth_date=request.birth_date,
            birth_time=request.birth_time,
            latitude=request.latitude,
            longitude=request.longitude,
            house_system=request.house_system,
            target_date=request.start_date
        )
        
        cached = cache_service.get(cache_key)
        if cached:
            return ApiResponse(
                code=200,
                message="获取7天趋势成功（缓存）",
                data=cached
            )
        
        natal_data = _prepare_natal_data(
            request.birth_date, request.birth_time,
            request.latitude, request.longitude,
            request.house_system
        )
        natal_planets = natal_data["natal_planets"]
        
        if request.start_date:
            start_dt = datetime.strptime(request.start_date, "%Y-%m-%d")
        else:
            start_dt = datetime.now()
        
        trend_result = _calculate_trend_internal(
            natal_planets, start_dt,
            request.latitude, request.longitude,
            request.house_system
        )
        
        result = {
            "natal_info": {
                "birth_date": request.birth_date,
                "birth_time": request.birth_time,
                "latitude": request.latitude,
                "longitude": request.longitude,
                "house_system": request.house_system
            },
            "start_date": start_dt.strftime("%Y-%m-%d"),
            **trend_result
        }
        
        cache_service.set(cache_key, result, ttl=1800)
        
        return ApiResponse(
            code=200,
            message="获取7天趋势成功",
            data=result
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"计算7天趋势失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"计算7天趋势失败: {str(e)}")


@router.post("/interpret", response_model=ApiResponse)
async def get_ai_interpretation(
    request: TransitRequest,
    db: Session = Depends(get_db)
):
    try:
        cache_key = _generate_transit_cache_key(
            action="interpret",
            birth_date=request.birth_date,
            birth_time=request.birth_time,
            latitude=request.latitude,
            longitude=request.longitude,
            house_system=request.house_system,
            target_date=request.target_date
        )
        
        cached = cache_service.get(cache_key)
        if cached:
            return ApiResponse(
                code=200,
                message="获取AI解读成功（缓存）",
                data=cached
            )
        
        natal_data = _prepare_natal_data(
            request.birth_date, request.birth_time,
            request.latitude, request.longitude,
            request.house_system
        )
        natal_planets = natal_data["natal_planets"]
        house_cusps = natal_data["house_cusps"]
        
        if request.target_date:
            target_dt = datetime.strptime(request.target_date, "%Y-%m-%d")
        else:
            target_dt = datetime.now()
        
        transit_data = _calculate_transit_internal(
            natal_planets, target_dt,
            request.latitude, request.longitude, house_cusps
        )
        
        prompt = generate_transit_analysis_prompt(transit_data, natal_planets)
        
        try:
            ai_content = await call_qwen_api(
                prompt=prompt,
                temperature=0.8,
                max_tokens=3000
            )
        except Exception as e:
            logger.warning(f"AI API调用失败，使用备用解读: {str(e)}")
            ai_content = generate_fallback_interpretation(transit_data)
        
        result = {
            "target_date": target_dt.strftime("%Y-%m-%d"),
            "day_of_week": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][target_dt.weekday()],
            "overall_score": transit_data["overall"]["overall_score"],
            "mood": transit_data["overall"]["mood"],
            "mood_label": transit_data["overall"]["mood_label"],
            "interpretation": ai_content,
            "dimensions_summary": [
                {
                    "name": d["name_cn"],
                    "icon": d["icon"],
                    "score": d["score"],
                    "level": d["level"],
                    "level_label": d["level_label"],
                    "color": d["color"]
                }
                for d in transit_data["dimensions"]
            ]
        }
        
        cache_service.set(cache_key, result, ttl=3600)
        
        return ApiResponse(
            code=200,
            message="获取AI解读成功",
            data=result
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取AI解读失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取AI解读失败: {str(e)}")


@router.get("/personal", response_model=ApiResponse)
async def get_personal_transit(
    target_date: Optional[str] = Query(None, description="目标日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        charts = db.query(Chart).filter(
            Chart.user_id == current_user.id,
            Chart.is_deleted == False
        ).order_by(Chart.created_at.desc()).all()
        
        if not charts:
            raise HTTPException(
                status_code=400,
                detail="您还没有保存本命盘数据，请先在星盘查询页面计算并保存您的星盘"
            )
        
        latest_chart = charts[0]
        
        try:
            chart_data = json.loads(latest_chart.chart_data)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"星盘数据解析失败: {str(e)}")
        
        request = TransitRequest(
            birth_date=latest_chart.birth_date,
            birth_time=latest_chart.birth_time,
            latitude=latest_chart.latitude,
            longitude=latest_chart.longitude,
            house_system=latest_chart.house_system or "placidus",
            target_date=target_date
        )
        
        return await calculate_transit(request, db)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取个性化行运失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取个性化行运失败: {str(e)}")


@router.get("/personal/trend", response_model=ApiResponse)
async def get_personal_trend(
    start_date: Optional[str] = Query(None, description="开始日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        charts = db.query(Chart).filter(
            Chart.user_id == current_user.id,
            Chart.is_deleted == False
        ).order_by(Chart.created_at.desc()).all()
        
        if not charts:
            raise HTTPException(
                status_code=400,
                detail="您还没有保存本命盘数据，请先在星盘查询页面计算并保存您的星盘"
            )
        
        latest_chart = charts[0]
        
        request = TrendRequest(
            birth_date=latest_chart.birth_date,
            birth_time=latest_chart.birth_time,
            latitude=latest_chart.latitude,
            longitude=latest_chart.longitude,
            house_system=latest_chart.house_system or "placidus",
            start_date=start_date
        )
        
        return await get_7day_trend(request, db)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取个性化趋势失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取个性化趋势失败: {str(e)}")


@router.get("/cache/status", response_model=ApiResponse)
async def get_cache_status():
    """获取缓存服务状态"""
    return ApiResponse(
        code=200,
        message="缓存状态获取成功",
        data={
            "using_redis": cache_service.is_using_redis,
            "service_available": True
        }
    )
