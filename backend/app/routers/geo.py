from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import requests
import logging
from app.cities_db import CITIES_DB, search_cities_fallback, geocode_fallback

router = APIRouter()
logger = logging.getLogger(__name__)

USER_AGENT = "AstrologyApp/1.0 (astrology-app@example.com)"


class CityResult(BaseModel):
    name: str
    display_name: str
    latitude: float
    longitude: float
    country: Optional[str] = None
    state: Optional[str] = None
    timezone: Optional[str] = None


class GeocodeResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[dict] = None


def search_via_nominatim(query: str, limit: int = 10):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": query,
        "format": "json",
        "limit": limit,
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
        "addressdetails": "1"
    }
    headers = {
        "User-Agent": USER_AGENT
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            results = []
            for item in data:
                address = item.get("address", {})
                country = address.get("country", "")
                state = address.get("state", "")
                if not state:
                    state = address.get("state_district", "")
                
                results.append({
                    "name": item.get("name", ""),
                    "display_name": item.get("display_name", ""),
                    "latitude": float(item.get("lat", 0)),
                    "longitude": float(item.get("lon", 0)),
                    "country": country,
                    "state": state
                })
            return results
    except requests.exceptions.Timeout:
        logger.warning(f"Nominatim search timeout for query: {query}")
    except requests.exceptions.RequestException as e:
        logger.warning(f"Nominatim search error: {e}")
    
    return None


def geocode_via_nominatim(city: str):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": city,
        "format": "json",
        "limit": 1,
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
        "addressdetails": "1"
    }
    headers = {
        "User-Agent": USER_AGENT
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                item = data[0]
                address = item.get("address", {})
                return {
                    "found": True,
                    "city": city,
                    "latitude": float(item.get("lat", 0)),
                    "longitude": float(item.get("lon", 0)),
                    "display_name": item.get("display_name", ""),
                    "country": address.get("country", ""),
                    "state": address.get("state", "")
                }
    except requests.exceptions.Timeout:
        logger.warning(f"Nominatim geocode timeout for city: {city}")
    except requests.exceptions.RequestException as e:
        logger.warning(f"Nominatim geocode error: {e}")
    
    return None


@router.get("/search", response_model=GeocodeResponse)
def search_city(
    query: str = Query(..., min_length=1, max_length=100, description="城市名称（支持中英文）"),
    limit: int = Query(10, ge=1, le=20, description="返回结果数量")
):
    if not query or len(query.strip()) == 0:
        raise HTTPException(status_code=400, detail="请输入城市名称")
    
    results = search_via_nominatim(query, limit)
    
    if not results:
        results = search_cities_fallback(query, limit)
    
    if not results:
        return GeocodeResponse(
            code=404,
            message=f"未找到城市: {query}",
            data={
                "query": query,
                "results": [],
                "from_fallback": True
            }
        )
    
    return GeocodeResponse(
        code=200,
        message=f"找到 {len(results)} 个结果",
        data={
            "query": query,
            "results": results,
            "from_fallback": False if results and results[0].get("timezone") else False
        }
    )


@router.get("/geocode", response_model=GeocodeResponse)
def geocode_city(
    city: str = Query(..., min_length=1, max_length=100, description="城市名称")
):
    if not city or len(city.strip()) == 0:
        raise HTTPException(status_code=400, detail="请输入城市名称")
    
    result = geocode_via_nominatim(city)
    
    if not result or not result.get("found"):
        result = geocode_fallback(city)
    
    if not result or not result.get("found"):
        return GeocodeResponse(
            code=404,
            message=f"未找到城市: {city}。请尝试其他城市名，或手动输入经纬度。",
            data={
                "city": city,
                "found": False
            }
        )
    
    return GeocodeResponse(
        code=200,
        message="success",
        data=result
    )


@router.get("/popular-cities", response_model=GeocodeResponse)
def get_popular_cities():
    cities = []
    popular_names = [
        "北京", "上海", "广州", "深圳", "成都", "杭州", "南京", "武汉",
        "东京", "纽约", "伦敦", "巴黎", "洛杉矶", "香港", "新加坡", "悉尼"
    ]
    
    for name in popular_names:
        if name in CITIES_DB:
            cities.append({
                "name": name,
                "latitude": CITIES_DB[name]["latitude"],
                "longitude": CITIES_DB[name]["longitude"],
                "country": CITIES_DB[name].get("country", ""),
                "state": CITIES_DB[name].get("state", "")
            })
    
    return GeocodeResponse(
        code=200,
        message="success",
        data={
            "cities": cities
        }
    )
