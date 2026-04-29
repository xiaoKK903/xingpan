from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
import logging

from app.schemas import SynastryCalculateRequest, ApiResponse
from app.synastry import calculate_synastry_chart, verify_synastry_calculation

logger = logging.getLogger(__name__)

router = APIRouter(tags=["双人合盘"])


@router.post("/calculate", response_model=ApiResponse)
def calculate_synastry(request: SynastryCalculateRequest):
    try:
        person_a = {
            "name": request.person_a.name or "A",
            "birth_date": request.person_a.birth_date,
            "birth_time": request.person_a.birth_time,
            "birth_place": request.person_a.birth_place,
            "latitude": request.person_a.latitude,
            "longitude": request.person_a.longitude,
            "house_system": request.person_a.house_system
        }
        
        person_b = {
            "name": request.person_b.name or "B",
            "birth_date": request.person_b.birth_date,
            "birth_time": request.person_b.birth_time,
            "birth_place": request.person_b.birth_place,
            "latitude": request.person_b.latitude,
            "longitude": request.person_b.longitude,
            "house_system": request.person_b.house_system
        }
        
        result = calculate_synastry_chart(person_a, person_b)
        
        logger.info(f"合盘计算完成: {person_a['name']} & {person_b['name']}, 相位数量: {result['synastry']['aspect_summary']['total']}")
        
        return ApiResponse(
            message="合盘计算成功",
            data=result
        )
        
    except Exception as e:
        logger.error(f"合盘计算失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"合盘计算失败: {str(e)}"
        )


@router.get("/test", response_model=ApiResponse)
def test_synastry():
    try:
        result = verify_synastry_calculation()
        return ApiResponse(
            message="合盘测试成功",
            data={
                "person_a_sun": result['person_a']['chart']['sun_sign']['sign'],
                "person_b_sun": result['person_b']['chart']['sun_sign']['sign'],
                "aspect_summary": result['synastry']['aspect_summary'],
                "top_aspects": [
                    {
                        "planet_a": a['planet_a'],
                        "planet_b": a['planet_b'],
                        "aspect": a['aspect'],
                        "orb_arcminutes": a['orb_arcminutes']
                    }
                    for a in result['synastry']['aspects'][:5]
                ]
            }
        )
    except Exception as e:
        logger.error(f"合盘测试失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"合盘测试失败: {str(e)}"
        )
