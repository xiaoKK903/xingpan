from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
from app.schemas import ApiResponse, HouseSystemEnum
from app.astro import calculate_chart, parse_birth_datetime, HouseSystem

router = APIRouter()


class ChartRequest(BaseModel):
    name: Optional[str] = Field(None, description="姓名")
    birth_date: str = Field(..., description="出生日期 YYYY-MM-DD")
    birth_time: str = Field(..., description="出生时间 HH:MM")
    latitude: float = Field(39.9, ge=-90, le=90, description="纬度")
    longitude: float = Field(116.4, ge=-180, le=180, description="经度")
    birth_place: Optional[str] = Field(None, description="出生地点")
    house_system: HouseSystemEnum = Field(
        default=HouseSystemEnum.placidus, 
        description="宫位系统: placidus (Placidus分宫制) 或 whole_sign (整宫制)"
    )


@router.post("/calculate", response_model=ApiResponse)
def calculate_astrological_chart(request: ChartRequest):
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
        
        return ApiResponse(
            code=200,
            message="星盘计算成功",
            data={
                "chart": chart_data,
                "name": request.name,
                "birth_place": request.birth_place
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算失败: {str(e)}")


@router.get("/systems", response_model=ApiResponse)
def get_house_systems():
    return ApiResponse(
        code=200,
        message="success",
        data={
            "systems": [
                {
                    "id": "placidus",
                    "name": "Placidus 分宫制",
                    "description": "最常用的宫位系统，根据经纬度计算各宫头位置"
                },
                {
                    "id": "whole_sign",
                    "name": "整宫制",
                    "description": "每个星座完整对应一个宫位，上升点星座为第1宫"
                }
            ]
        }
    )


@router.get("/planets", response_model=ApiResponse)
def get_planets_info():
    from app.astro import PLANET_INFO
    
    planets = []
    for pid, info in PLANET_INFO.items():
        planets.append({
            "id": pid,
            "name": info.get("name"),
            "symbol": info.get("symbol"),
            "ruler_of": info.get("ruler_of", [])
        })
    
    return ApiResponse(
        code=200,
        message="success",
        data={"planets": planets}
    )


@router.get("/zodiac-signs", response_model=ApiResponse)
def get_zodiac_signs():
    from app.astro import ZODIAC_SIGNS, ZODIAC_SYMBOLS, ELEMENTS, QUALITIES, RULING_PLANETS
    
    signs = []
    for i in range(12):
        signs.append({
            "index": i,
            "name": ZODIAC_SIGNS[i],
            "symbol": ZODIAC_SYMBOLS[i],
            "element": ELEMENTS[i],
            "quality": QUALITIES[i],
            "ruling_planet": RULING_PLANETS[i],
            "degree_range": f"{i*30}° - {(i+1)*30}°"
        })
    
    return ApiResponse(
        code=200,
        message="success",
        data={"zodiac_signs": signs}
    )
