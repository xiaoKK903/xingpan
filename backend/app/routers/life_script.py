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
    parse_birth_datetime, local_to_utc, utc_to_julday,
    calculate_all_planets, calculate_houses_ex
)
from app.services.life_script_service import get_life_script_analyzer
from app.services.cache_service import get_cache_service

logger = logging.getLogger(__name__)

router = APIRouter()

life_script_analyzer = get_life_script_analyzer()
cache_service = get_cache_service()


class LifeScriptRequest(BaseModel):
    birth_date: str = Field(..., description="出生日期 YYYY-MM-DD")
    birth_time: str = Field(..., description="出生时间 HH:MM")
    latitude: float = Field(..., description="出生地点纬度")
    longitude: float = Field(..., description="出生地点经度")
    house_system: str = Field("placidus", description="宫位系统: placidus/whole_sign")
    target_year: int = Field(..., description="目标年份")


class YearRangeRequest(BaseModel):
    birth_date: str = Field(..., description="出生日期 YYYY-MM-DD")
    birth_time: str = Field(..., description="出生时间 HH:MM")
    latitude: float = Field(..., description="出生地点纬度")
    longitude: float = Field(..., description="出生地点经度")
    house_system: str = Field("placidus", description="宫位系统")
    start_year: int = Field(..., description="开始年份")
    end_year: int = Field(..., description="结束年份")


class KeyYearsRequest(BaseModel):
    birth_date: str = Field(..., description="出生日期 YYYY-MM-DD")
    birth_time: str = Field(..., description="出生时间 HH:MM")
    latitude: float = Field(..., description="出生地点纬度")
    longitude: float = Field(..., description="出生地点经度")
    house_system: str = Field("placidus", description="宫位系统")
    start_age: int = Field(0, description="开始年龄")
    end_age: int = Field(80, description="结束年龄")


def _generate_cache_key(action: str, params: Dict[str, Any]) -> str:
    key_str = json.dumps(params, sort_keys=True, default=str)
    return f"lifescript:{action}:{hashlib.md5(key_str.encode()).hexdigest()}"


@router.post("/analyze", response_model=ApiResponse)
async def analyze_year(
    request: LifeScriptRequest,
    db: Session = Depends(get_db)
):
    """
    分析指定年份的人生剧本（仅星象分析，不生成AI文案）
    
    整合三种推运方法：
    - 行运 (Transit)
    - 法达 (Firdaria)
    - 次限 (Secondary Progressions)
    """
    try:
        cache_key = _generate_cache_key("analyze", {
            "birth_date": request.birth_date,
            "birth_time": request.birth_time,
            "latitude": round(request.latitude, 4),
            "longitude": round(request.longitude, 4),
            "house_system": request.house_system,
            "target_year": request.target_year
        })
        
        cached = cache_service.get(cache_key)
        if cached:
            return ApiResponse(
                code=200,
                message="获取人生剧本分析成功（缓存）",
                data=cached
            )
        
        logger.info(f"分析 {request.target_year} 年人生剧本，出生: {request.birth_date} {request.birth_time}")
        
        analysis = life_script_analyzer.analyze_year(
            birth_date=request.birth_date,
            birth_time=request.birth_time,
            latitude=request.latitude,
            longitude=request.longitude,
            target_year=request.target_year,
            house_system=request.house_system
        )
        
        cache_service.set(cache_key, analysis, ttl=86400)
        
        return ApiResponse(
            code=200,
            message="人生剧本分析完成",
            data=analysis
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分析人生剧本失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"分析人生剧本失败: {str(e)}")


@router.post("/generate-script", response_model=ApiResponse)
async def generate_life_script(
    request: LifeScriptRequest,
    db: Session = Depends(get_db)
):
    """
    生成指定年份的人生剧本AI文案
    
    调用 DeepSeek API 生成故事化的人生剧本解读
    """
    try:
        cache_key = _generate_cache_key("script", {
            "birth_date": request.birth_date,
            "birth_time": request.birth_time,
            "latitude": round(request.latitude, 4),
            "longitude": round(request.longitude, 4),
            "house_system": request.house_system,
            "target_year": request.target_year
        })
        
        cached = cache_service.get(cache_key)
        if cached:
            return ApiResponse(
                code=200,
                message="获取人生剧本成功（缓存）",
                data=cached
            )
        
        logger.info(f"生成 {request.target_year} 年人生剧本AI文案")
        
        natal_data = life_script_analyzer._prepare_natal_data(
            request.birth_date, request.birth_time,
            request.latitude, request.longitude, request.house_system
        )
        
        analysis = life_script_analyzer.analyze_year(
            birth_date=request.birth_date,
            birth_time=request.birth_time,
            latitude=request.latitude,
            longitude=request.longitude,
            target_year=request.target_year,
            house_system=request.house_system,
            natal_data=natal_data
        )
        
        previous_analysis = None
        next_analysis = None
        
        try:
            previous_analysis = life_script_analyzer.analyze_year(
                birth_date=request.birth_date,
                birth_time=request.birth_time,
                latitude=request.latitude,
                longitude=request.longitude,
                target_year=request.target_year - 1,
                house_system=request.house_system,
                natal_data=natal_data
            )
        except Exception as e:
            logger.warning(f"获取前一年分析失败: {e}")
        
        try:
            next_analysis = life_script_analyzer.analyze_year(
                birth_date=request.birth_date,
                birth_time=request.birth_time,
                latitude=request.latitude,
                longitude=request.longitude,
                target_year=request.target_year + 1,
                house_system=request.house_system,
                natal_data=natal_data
            )
        except Exception as e:
            logger.warning(f"获取后一年分析失败: {e}")
        
        script_result = await life_script_analyzer.generate_life_script(
            analysis=analysis,
            previous_year_analysis=previous_analysis,
            next_year_analysis=next_analysis,
            fast_mode=True
        )
        
        result = {
            "target_year": request.target_year,
            "target_age": analysis.get("target_age"),
            "analysis": analysis,
            "script": script_result
        }
        
        if script_result.get("success"):
            cache_service.set(cache_key, result, ttl=7 * 86400)
            return ApiResponse(
                code=200,
                message="人生剧本生成完成",
                data=result
            )
        else:
            error_type = script_result.get("error_type", "unknown")
            error_msg = script_result.get("error", "未知错误")
            
            user_friendly_messages = {
                "timeout": "AI生成时间过长，请稍后重试。如果问题持续存在，可以尝试在网络较好的环境下操作。",
                "auth": "AI服务认证失败，请联系管理员检查 API 配置。",
                "quota": "AI服务余额不足，请联系管理员充值。",
                "rate_limit": "AI服务请求频率过高，请稍后再试。",
                "network": "网络连接失败，请检查您的网络连接。",
                "empty_response": "AI返回内容为空，请稍后重试。",
                "unknown": f"生成失败: {error_msg}"
            }
            
            user_message = user_friendly_messages.get(error_type, user_friendly_messages["unknown"])
            
            return ApiResponse(
                code=500,
                message=user_message,
                data={
                    "error": error_msg,
                    "error_type": error_type,
                    "analysis": analysis,
                    "can_retry": True
                }
            )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成人生剧本失败: {str(e)}", exc_info=True)
        error_msg = str(e)
        
        if "超时" in error_msg or "timeout" in error_msg.lower():
            raise HTTPException(
                status_code=504,
                detail=f"请求超时: AI服务响应时间过长。请稍后重试。错误详情: {error_msg}"
            )
        elif "连接" in error_msg or "network" in error_msg.lower():
            raise HTTPException(
                status_code=502,
                detail=f"网络连接失败: {error_msg}"
            )
        else:
            raise HTTPException(status_code=500, detail=f"生成人生剧本失败: {error_msg}")


@router.post("/analyze-range", response_model=ApiResponse)
async def analyze_year_range(
    request: YearRangeRequest,
    db: Session = Depends(get_db)
):
    """
    分析指定年份范围内的所有年份（批量星象分析）
    
    用于时间轴预加载和概览显示
    """
    try:
        if request.end_year - request.start_year > 50:
            raise HTTPException(status_code=400, detail="年份范围不能超过50年")
        
        logger.info(f"分析年份范围: {request.start_year} - {request.end_year}")
        
        results = life_script_analyzer.analyze_year_range(
            birth_date=request.birth_date,
            birth_time=request.birth_time,
            latitude=request.latitude,
            longitude=request.longitude,
            start_year=request.start_year,
            end_year=request.end_year,
            house_system=request.house_system
        )
        
        summary = {
            "total_years": len(results),
            "start_year": request.start_year,
            "end_year": request.end_year,
            "key_years": [],
            "yearly_summary": []
        }
        
        for r in results:
            analysis = r.get("analysis", {})
            year_summary = {
                "year": r.get("target_year"),
                "age": r.get("target_age"),
                "intensity": analysis.get("combined_intensity", 5),
                "mood": analysis.get("mood", "neutral"),
                "mood_label": analysis.get("mood_label", "平稳"),
                "is_key_year": analysis.get("is_key_year", False),
                "has_saturn_return": analysis.get("has_saturn_return", False),
                "has_major_transit": analysis.get("has_major_outer_transit", False)
            }
            summary["yearly_summary"].append(year_summary)
            
            if analysis.get("is_key_year", False):
                summary["key_years"].append(year_summary)
        
        summary["key_years"].sort(key=lambda x: x["year"])
        
        return ApiResponse(
            code=200,
            message=f"年份范围分析完成，共 {len(results)} 年",
            data={
                "summary": summary,
                "details": results
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分析年份范围失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"分析年份范围失败: {str(e)}")


@router.post("/key-years", response_model=ApiResponse)
async def get_key_years(
    request: KeyYearsRequest,
    db: Session = Depends(get_db)
):
    """
    获取人生中的关键年份
    
    包括：
    - 土星回归 (Saturn Return)
    - 木星回归 (Jupiter Return)
    - 法达大运起止
    - 外行星重要行运
    """
    try:
        logger.info(f"获取关键年份，年龄范围: {request.start_age} - {request.end_age}")
        
        key_years = life_script_analyzer.get_key_years(
            birth_date=request.birth_date,
            birth_time=request.birth_time,
            latitude=request.latitude,
            longitude=request.longitude,
            house_system=request.house_system,
            start_age=request.start_age,
            end_age=request.end_age
        )
        
        grouped = {
            "saturn_return": [],
            "jupiter_return": [],
            "firdaria_major": [],
            "firdaria_minor": [],
            "outer_planet": [],
            "all": key_years
        }
        
        for ky in key_years:
            t = ky.get("type", "")
            if t == "saturn_return":
                grouped["saturn_return"].append(ky)
            elif t == "jupiter_return":
                grouped["jupiter_return"].append(ky)
            elif t == "firdaria":
                st = ky.get("subtype", "")
                if st == "major_start" or st == "major_mid":
                    grouped["firdaria_major"].append(ky)
                else:
                    grouped["firdaria_minor"].append(ky)
            elif t == "outer_planet":
                grouped["outer_planet"].append(ky)
        
        return ApiResponse(
            code=200,
            message=f"获取关键年份完成，共 {len(key_years)} 个",
            data=grouped
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取关键年份失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取关键年份失败: {str(e)}")


@router.get("/personal/analyze", response_model=ApiResponse)
async def get_personal_analysis(
    target_year: int = Query(..., description="目标年份"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取当前登录用户的人生剧本分析（使用保存的本命盘）
    """
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
        
        request = LifeScriptRequest(
            birth_date=latest_chart.birth_date,
            birth_time=latest_chart.birth_time,
            latitude=latest_chart.latitude,
            longitude=latest_chart.longitude,
            house_system=latest_chart.house_system or "placidus",
            target_year=target_year
        )
        
        return await analyze_year(request, db)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取个性化分析失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取个性化分析失败: {str(e)}")


@router.get("/personal/generate-script", response_model=ApiResponse)
async def get_personal_script(
    target_year: int = Query(..., description="目标年份"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取当前登录用户的人生剧本AI文案（使用保存的本命盘）
    """
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
        
        request = LifeScriptRequest(
            birth_date=latest_chart.birth_date,
            birth_time=latest_chart.birth_time,
            latitude=latest_chart.latitude,
            longitude=latest_chart.longitude,
            house_system=latest_chart.house_system or "placidus",
            target_year=target_year
        )
        
        return await generate_life_script(request, db)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取个性化剧本失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取个性化剧本失败: {str(e)}")
