from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
import logging
import time

from app.database import get_db
from app.models import User, Chart
from app.routers.users import get_current_user
from app.schemas import ApiResponse, HouseSystemEnum
from app.services.chart_service import calculate_chart_from_input
from app.services.social_card_service import generate_social_card

logger = logging.getLogger(__name__)

router = APIRouter(tags=["社交破冰助手"])


class SocialCardRequest(BaseModel):
    name: Optional[str] = Field(None, description="姓名/昵称")
    birth_date: Optional[str] = Field(None, description="出生日期 YYYY-MM-DD")
    birth_time: Optional[str] = Field(None, description="出生时间 HH:MM")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="纬度")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="经度")
    birth_place: Optional[str] = Field(None, description="出生地点")
    house_system: Optional[HouseSystemEnum] = Field(
        default=HouseSystemEnum.placidus,
        description="宫位系统: placidus 或 whole_sign"
    )
    chart_id: Optional[int] = Field(None, description="已保存的星盘ID（如果提供则优先使用）")
    chart_data: Optional[Dict[str, Any]] = Field(None, description="已计算的星盘数据（如果提供则直接使用）")


class GenerateTagsRequest(BaseModel):
    chart_data: Optional[Dict[str, Any]] = Field(None, description="已计算的星盘数据")
    birth_date: Optional[str] = Field(None, description="出生日期")
    birth_time: Optional[str] = Field(None, description="出生时间")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="纬度")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="经度")
    house_system: Optional[HouseSystemEnum] = Field(
        default=HouseSystemEnum.placidus,
        description="宫位系统"
    )


@router.get("/health", response_model=ApiResponse)
async def health_check():
    """
    健康检查端点
    """
    logger.info("收到社交破冰助手健康检查请求")
    
    return ApiResponse(
        code=200,
        message="社交破冰助手服务运行正常",
        data={
            "status": "ok",
            "services": [
                "profile_extractor_service",
                "conflict_resolution_service", 
                "social_card_service"
            ],
        }
    )


@router.post("/card", response_model=ApiResponse)
async def generate_social_card_endpoint(
    request: SocialCardRequest
):
    """
    生成社交破冰名片
    
    支持三种方式：
    1. 提供 chart_data：直接使用已计算的星盘数据
    2. 提供 chart_id：从数据库获取已保存的星盘（需要登录）
    3. 提供出生信息：实时计算星盘并生成名片
    
    注意：此接口不需要登录（使用chart_id除外）
    """
    logger.info("收到社交名片生成请求")
    
    start_time = time.time()
    
    try:
        chart_data = None
        name = request.name or "用户"
        
        if request.chart_data:
            logger.info("使用提供的星盘数据")
            chart_data = request.chart_data
        
        elif request.chart_id:
            return ApiResponse(
                code=200,
                message="使用chart_id需要登录，请使用登录接口或提供出生信息",
                data={
                    "success": False,
                    "error": "使用chart_id需要认证",
                    "error_type": "auth_required",
                    "suggestion": "请提供出生信息或登录后使用"
                }
            )
        
        elif request.birth_date and request.birth_time:
            if request.latitude is None or request.longitude is None:
                return ApiResponse(
                    code=200,
                    message="请提供纬度和经度",
                    data={
                        "success": False,
                        "error": "缺少纬度或经度信息",
                        "error_type": "invalid_input"
                    }
                )
            
            logger.info("根据出生信息计算星盘")
            try:
                chart_data = calculate_chart_from_input(
                    birth_date=request.birth_date,
                    birth_time=request.birth_time,
                    latitude=request.latitude,
                    longitude=request.longitude,
                    house_system=request.house_system.value if request.house_system else 'placidus'
                )
            except Exception as e:
                logger.error(f"星盘计算失败: {str(e)}")
                return ApiResponse(
                    code=200,
                    message="星盘计算失败",
                    data={
                        "success": False,
                        "error": f"星盘计算失败: {str(e)}",
                        "error_type": "calculation_error"
                    }
                )
        
        else:
            return ApiResponse(
                code=200,
                message="请提供星盘数据或完整的出生信息",
                data={
                    "success": False,
                    "error": "缺少必要参数：请提供 chart_data 或完整的出生信息",
                    "error_type": "missing_params",
                    "required_fields": [
                        "chart_data",
                        "或: birth_date, birth_time, latitude, longitude"
                    ]
                }
            )
        
        if not chart_data:
            return ApiResponse(
                code=200,
                message="无法获取星盘数据",
                data={
                    "success": False,
                    "error": "星盘数据获取失败",
                    "error_type": "chart_error"
                }
            )
        
        planets = chart_data.get("planets", [])
        if not planets:
            return ApiResponse(
                code=200,
                message="星盘数据不完整",
                data={
                    "success": False,
                    "error": "星盘数据不完整，缺少行星信息",
                    "error_type": "invalid_input"
                }
            )
        
        logger.info(f"开始生成社交名片，用户: {name}")
        result = await generate_social_card(chart_data, name)
        
        if not result.get("success"):
            error_msg = result.get("error", "生成社交名片失败")
            error_type = result.get("error_type", "unknown")
            logger.error(f"社交名片生成失败: {error_type} - {error_msg}")
            return ApiResponse(
                code=200,
                message=error_msg,
                data={
                    "success": False,
                    "error": error_msg,
                    "error_type": error_type
                }
            )
        
        elapsed_time = round(time.time() - start_time, 2)
        result["processing_time_seconds"] = elapsed_time
        
        logger.info(f"社交名片生成成功，耗时: {elapsed_time}秒")
        return ApiResponse(
            code=200,
            message="社交名片生成成功",
            data=result
        )
        
    except Exception as e:
        logger.exception(f"生成社交名片时发生异常: {str(e)}")
        return ApiResponse(
            code=200,
            message="服务暂时不可用",
            data={
                "success": False,
                "error": str(e),
                "error_type": "server_error",
                "suggestion": "请稍后重试或检查网络连接"
            }
        )


@router.post("/tags", response_model=ApiResponse)
async def extract_personality_tags(
    request: GenerateTagsRequest
):
    """
    提取性格标签矩阵
    
    此接口专注于提取星盘的性格标签，不调用AI生成文案
    """
    logger.info("收到性格标签提取请求")
    
    try:
        from app.services.profile_extractor_service import extract_tag_matrix
        
        chart_data = None
        
        if request.chart_data:
            chart_data = request.chart_data
        elif request.birth_date and request.birth_time:
            if request.latitude is None or request.longitude is None:
                return ApiResponse(
                    code=200,
                    message="请提供纬度和经度",
                    data={
                        "success": False,
                        "error": "缺少纬度或经度信息",
                        "error_type": "invalid_input"
                    }
                )
            
            chart_data = calculate_chart_from_input(
                birth_date=request.birth_date,
                birth_time=request.birth_time,
                latitude=request.latitude,
                longitude=request.longitude,
                house_system=request.house_system.value if request.house_system else 'placidus'
            )
        else:
            return ApiResponse(
                code=200,
                message="请提供星盘数据或出生信息",
                data={
                    "success": False,
                    "error": "缺少必要参数",
                    "error_type": "missing_params"
                }
            )
        
        if not chart_data:
            return ApiResponse(
                code=200,
                message="无法获取星盘数据",
                data={
                    "success": False,
                    "error": "星盘数据获取失败",
                    "error_type": "chart_error"
                }
            )
        
        result = extract_tag_matrix(chart_data)
        
        logger.info(f"性格标签提取完成，共 {result.get('tags_count', 0)} 个标签")
        return ApiResponse(
            code=200,
            message="性格标签提取成功",
            data={
                "success": True,
                "tag_matrix": result
            }
        )
        
    except Exception as e:
        logger.exception(f"提取性格标签时发生异常: {str(e)}")
        return ApiResponse(
            code=200,
            message="提取性格标签失败",
            data={
                "success": False,
                "error": str(e),
                "error_type": "server_error"
            }
        )


@router.post("/conflicts", response_model=ApiResponse)
async def analyze_conflicts(
    request: GenerateTagsRequest
):
    """
    分析性格对冲配置
    
    检测星盘中的性格对冲并提供整合描述
    """
    logger.info("收到性格对冲分析请求")
    
    try:
        from app.services.profile_extractor_service import extract_tag_matrix
        from app.services.conflict_resolution_service import generate_conflict_aware_personality
        
        chart_data = None
        
        if request.chart_data:
            chart_data = request.chart_data
        elif request.birth_date and request.birth_time:
            if request.latitude is None or request.longitude is None:
                return ApiResponse(
                    code=200,
                    message="请提供纬度和经度",
                    data={
                        "success": False,
                        "error": "缺少纬度或经度信息",
                        "error_type": "invalid_input"
                    }
                )
            
            chart_data = calculate_chart_from_input(
                birth_date=request.birth_date,
                birth_time=request.birth_time,
                latitude=request.latitude,
                longitude=request.longitude,
                house_system=request.house_system.value if request.house_system else 'placidus'
            )
        else:
            return ApiResponse(
                code=200,
                message="请提供星盘数据或出生信息",
                data={
                    "success": False,
                    "error": "缺少必要参数",
                    "error_type": "missing_params"
                }
            )
        
        if not chart_data:
            return ApiResponse(
                code=200,
                message="无法获取星盘数据",
                data={
                    "success": False,
                    "error": "星盘数据获取失败",
                    "error_type": "chart_error"
                }
            )
        
        tag_matrix = extract_tag_matrix(chart_data)
        result = generate_conflict_aware_personality(chart_data, tag_matrix)
        
        conflict_count = result.get("conflicts_detected", {}).get("total_count", 0)
        logger.info(f"性格对冲分析完成，检测到 {conflict_count} 个对冲")
        
        return ApiResponse(
            code=200,
            message="性格对冲分析成功",
            data={
                "success": True,
                "conflict_analysis": result
            }
        )
        
    except Exception as e:
        logger.exception(f"分析性格对冲时发生异常: {str(e)}")
        return ApiResponse(
            code=200,
            message="分析性格对冲失败",
            data={
                "success": False,
                "error": str(e),
                "error_type": "server_error"
            }
        )
