from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
import logging
import json

from app.schemas import GroupMatrixCalculateRequest, ApiResponse
from app.services.group_matrix_service import calculate_group_matrix

logger = logging.getLogger(__name__)

router = APIRouter(tags=["多人星盘关系矩阵"])


@router.post("/calculate", response_model=ApiResponse)
def calculate_group_matrix_api(request: GroupMatrixCalculateRequest):
    try:
        members = []
        for m in request.members:
            member_dict = {
                "name": m.name,
                "birth_date": m.birth_date,
                "birth_time": m.birth_time,
                "birth_place": m.birth_place,
                "latitude": m.latitude,
                "longitude": m.longitude,
                "house_system": m.house_system,
                "is_core": m.is_core,
                "weight": m.weight
            }
            members.append(member_dict)
        
        result = calculate_group_matrix(
            group_name=request.group_name,
            members=members,
            group_type=request.group_type,
            description=request.description
        )
        
        logger.info(f"群组矩阵计算完成: {request.group_name}, 成员数量: {len(members)}")
        
        return ApiResponse(
            message="群组关系矩阵计算成功",
            data=result
        )
        
    except Exception as e:
        logger.error(f"群组矩阵计算失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"群组矩阵计算失败: {str(e)}"
        )


@router.post("/simulate-scenario", response_model=ApiResponse)
def simulate_scenario_api(
    matrix_data: dict,
    scenario_type: str = "meeting"
):
    try:
        from app.services.group_matrix_service import (
            simulate_scenario,
            SCENARIO_DEFINITIONS
        )
        
        if scenario_type not in SCENARIO_DEFINITIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的场景类型: {scenario_type}，支持的类型: {list(SCENARIO_DEFINITIONS.keys())}"
            )
        
        members = matrix_data.get("members", [])
        roles = matrix_data.get("roles", [])
        matrix = matrix_data.get("matrix", {})
        
        result = simulate_scenario(scenario_type, members, roles, matrix)
        
        logger.info(f"场景模拟完成: {scenario_type}")
        
        return ApiResponse(
            message="场景模拟成功",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"场景模拟失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"场景模拟失败: {str(e)}"
        )


@router.get("/scenario-types", response_model=ApiResponse)
def get_scenario_types():
    try:
        from app.services.group_matrix_service import SCENARIO_DEFINITIONS
        
        scenarios = []
        for key, value in SCENARIO_DEFINITIONS.items():
            scenarios.append({
                "type": key,
                "name": value["name"],
                "description": value["description"]
            })
        
        return ApiResponse(
            message="获取场景类型成功",
            data={"scenarios": scenarios}
        )
    except Exception as e:
        logger.error(f"获取场景类型失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取场景类型失败: {str(e)}"
        )


@router.get("/role-types", response_model=ApiResponse)
def get_role_types():
    try:
        from app.services.group_matrix_service import ROLE_DEFINITIONS
        
        roles = []
        for key, value in ROLE_DEFINITIONS.items():
            roles.append({
                "type": key,
                "name": value["name"],
                "description": value["description"],
                "icon": value["icon"],
                "color": value["color"]
            })
        
        return ApiResponse(
            message="获取角色类型成功",
            data={"roles": roles}
        )
    except Exception as e:
        logger.error(f"获取角色类型失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取角色类型失败: {str(e)}"
        )
