from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
import logging
import os

from app.database import get_db
from app.models import User, Chart
from app.routers.users import get_current_user
from app.schemas import ApiResponse, HouseSystemEnum
from app.services.chart_service import calculate_chart_from_input, get_or_create_chart_data
from app.services.ai_service import generate_ai_interpretation
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["AI解读"])


class AIInterpretationRequest(BaseModel):
    name: Optional[str] = Field(None, description="姓名/星盘名称")
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


class AIInterpretationResponse(BaseModel):
    success: bool
    content: Optional[str] = None
    sections: Optional[Dict[str, str]] = None
    error: Optional[str] = None
    error_type: Optional[str] = None


@router.get("/health", response_model=ApiResponse)
async def health_check():
    """
    健康检查端点 - 用于验证服务是否正常运行
    """
    logger.info("收到AI健康检查请求")
    
    api_key_status = "已配置" if settings.DASHSCOPE_API_KEY else "未配置"
    api_key_prefix = settings.DASHSCOPE_API_KEY[:10] + "..." if settings.DASHSCOPE_API_KEY and len(settings.DASHSCOPE_API_KEY) > 10 else None
    
    return ApiResponse(
        code=200,
        message="AI解读服务运行正常",
        data={
            "status": "ok",
            "api_key_configured": settings.DASHSCOPE_API_KEY is not None,
            "api_key_status": api_key_status,
            "api_key_prefix": api_key_prefix,
            "model": settings.QWEN_MODEL,
            "env_file_loaded": True
        }
    )


@router.post("/test", response_model=ApiResponse)
async def test_endpoint(request_data: Optional[Dict[str, Any]] = None):
    """
    测试端点 - 用于验证前后端通信是否正常
    """
    logger.info(f"收到测试请求，数据: {request_data}")
    
    return ApiResponse(
        code=200,
        message="测试成功",
        data={
            "success": True,
            "message": "后端服务正常接收请求",
            "received_data": request_data,
            "timestamp": "测试时间"
        }
    )


@router.post("/interpret", response_model=ApiResponse)
async def generate_interpretation(
    request: AIInterpretationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    基于星盘配置生成AI解读
    
    支持三种方式：
    1. 提供 chart_data：直接使用已计算的星盘数据
    2. 提供 chart_id：从数据库获取已保存的星盘
    3. 提供出生信息：实时计算星盘并解读
    """
    logger.info(f"用户 {current_user.username} 请求生成AI解读")
    
    try:
        chart_data = None
        name = request.name or "用户"
        
        if request.chart_data:
            logger.info("使用提供的星盘数据")
            chart_data = request.chart_data
        elif request.chart_id:
            logger.info(f"从数据库获取星盘 ID={request.chart_id}")
            result = get_or_create_chart_data(db, request.chart_id, current_user.id)
            if result[0] is None:
                return ApiResponse(
                    code=200,
                    message="星盘不存在或无权限访问",
                    data={
                        "success": False,
                        "error": "星盘不存在或无权限访问",
                        "error_type": "not_found"
                    }
                )
            chart_data, chart_record = result
            if chart_record and chart_record.name:
                name = chart_record.name
        elif request.birth_date and request.birth_time:
            if request.latitude is None or request.longitude is None:
                return ApiResponse(
                    code=200,
                    message="请提供纬度和经度",
                    data={
                        "success": False,
                        "error": "请提供纬度和经度",
                        "error_type": "invalid_input"
                    }
                )
            
            logger.info("根据出生信息计算星盘")
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
                message="请提供 chart_data、chart_id 或完整的出生信息",
                data={
                    "success": False,
                    "error": "请提供 chart_data、chart_id 或完整的出生信息",
                    "error_type": "invalid_input"
                }
            )
        
        if not chart_data:
            return ApiResponse(
                code=200,
                message="无法获取星盘数据",
                data={
                    "success": False,
                    "error": "无法获取星盘数据",
                    "error_type": "chart_error"
                }
            )
        
        logger.info("开始调用AI服务生成解读")
        result = await generate_ai_interpretation(chart_data, name)
        
        if not result.get("success"):
            error_msg = result.get("error", "AI解读生成失败")
            error_type = result.get("error_type", "unknown")
            logger.error(f"AI解读生成失败: {error_type} - {error_msg}")
            return ApiResponse(
                code=200,
                message=error_msg,
                data={
                    "success": False,
                    "error": error_msg,
                    "error_type": error_type
                }
            )
        
        logger.info("AI解读生成成功")
        return ApiResponse(
            code=200,
            message="AI解读生成成功",
            data={
                "success": True,
                "content": result.get("content"),
                "sections": result.get("sections")
            }
        )
        
    except Exception as e:
        logger.exception(f"生成AI解读时发生异常: {str(e)}")
        return ApiResponse(
            code=200,
            message=str(e),
            data={
                "success": False,
                "error": str(e),
                "error_type": "server_error"
            }
        )


@router.post("/interpret/direct", response_model=ApiResponse)
async def generate_interpretation_direct(
    request: AIInterpretationRequest
):
    """
    无需登录，直接基于星盘配置生成AI解读
    
    支持两种方式：
    1. 提供 chart_data：直接使用已计算的星盘数据
    2. 提供出生信息：实时计算星盘并解读
    
    注意：此接口不需要登录
    """
    logger.info("收到公开AI解读请求")
    
    try:
        chart_data = None
        name = request.name or "用户"
        
        if request.chart_data:
            logger.info("使用提供的星盘数据")
            chart_data = request.chart_data
        elif request.birth_date and request.birth_time:
            if request.latitude is None or request.longitude is None:
                return ApiResponse(
                    code=200,
                    message="请提供纬度和经度",
                    data={
                        "success": False,
                        "error": "请提供纬度和经度",
                        "error_type": "invalid_input"
                    }
                )
            
            logger.info("根据出生信息计算星盘")
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
                message="请提供 chart_data 或完整的出生信息",
                data={
                    "success": False,
                    "error": "请提供 chart_data 或完整的出生信息",
                    "error_type": "invalid_input"
                }
            )
        
        if not chart_data:
            return ApiResponse(
                code=200,
                message="无法获取星盘数据",
                data={
                    "success": False,
                    "error": "无法获取星盘数据",
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
        
        logger.info(f"星盘数据验证通过，行星数量: {len(planets)}")
        logger.info("开始调用AI服务生成解读")
        
        result = await generate_ai_interpretation(chart_data, name)
        
        if not result.get("success"):
            error_msg = result.get("error", "AI解读生成失败")
            error_type = result.get("error_type", "unknown")
            logger.error(f"AI解读生成失败: {error_type} - {error_msg}")
            return ApiResponse(
                code=200,
                message=error_msg,
                data={
                    "success": False,
                    "error": error_msg,
                    "error_type": error_type
                }
            )
        
        logger.info("AI解读生成成功")
        return ApiResponse(
            code=200,
            message="AI解读生成成功",
            data={
                "success": True,
                "content": result.get("content"),
                "sections": result.get("sections")
            }
        )
        
    except Exception as e:
        logger.exception(f"生成AI解读时发生异常: {str(e)}")
        return ApiResponse(
            code=200,
            message=str(e),
            data={
                "success": False,
                "error": str(e),
                "error_type": "server_error"
            }
        )
