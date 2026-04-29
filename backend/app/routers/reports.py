from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks, Request
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
import json
import io
import traceback
from datetime import datetime

from app.database import get_db
from app.models import User, Chart
from app.routers.users import get_current_user
from app.schemas import ApiResponse, HouseSystemEnum
from app.services.chart_service import (
    ChartService,
    calculate_chart_from_input,
    generate_chart_report,
    get_or_create_chart_data,
    encode_safe_filename,
    build_content_disposition_header,
    generate_report_async
)
from app.report_generator import ReportTemplate

router = APIRouter(tags=["报告生成"])


class ChartReportRequest(BaseModel):
    name: Optional[str] = Field(None, description="姓名/星盘名称")
    birth_date: str = Field(..., description="出生日期 YYYY-MM-DD")
    birth_time: str = Field(..., description="出生时间 HH:MM")
    latitude: float = Field(..., ge=-90, le=90, description="纬度")
    longitude: float = Field(..., ge=-180, le=180, description="经度")
    birth_place: Optional[str] = Field(None, description="出生地点")
    house_system: HouseSystemEnum = Field(
        default=HouseSystemEnum.placidus,
        description="宫位系统: placidus (Placidus分宫制) 或 whole_sign (整宫制)"
    )


class ChartIdRequest(BaseModel):
    chart_id: int = Field(..., description="已保存的星盘ID")
    template: str = Field(default=ReportTemplate.DETAILED, description="报告模板: simple 或 detailed")


@router.get("/templates", response_model=ApiResponse)
def get_available_templates():
    """获取可用的报告模板列表"""
    templates = [
        {
            "id": ReportTemplate.SIMPLE,
            "name": "简洁版",
            "description": "包含基础信息、行星位置表和主要相位，适合快速查看",
            "sections": ["基本信息", "元素分析", "行星位置", "相位分析"]
        },
        {
            "id": ReportTemplate.DETAILED,
            "name": "详细版",
            "description": "包含完整的星盘解读，包括行星详细解读、相位解读和宫位概述",
            "sections": ["基本信息", "元素分析", "行星位置", "行星详细解读", "相位分析", "相位详细解读", "宫位概述"]
        }
    ]
    
    return ApiResponse(
        message="success",
        data={"templates": templates}
    )


@router.get("/interpretation/{chart_id}", response_model=ApiResponse)
def get_chart_interpretation(
    chart_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取已保存星盘的解读数据"""
    try:
        chart_data, chart = get_or_create_chart_data(db, chart_id, current_user.id)
        
        if not chart_data or not chart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="星盘不存在"
            )
        
        interpretation = ChartService.generate_interpretation(chart_data)
        
        return ApiResponse(
            message="success",
            data={
                "chart_id": chart_id,
                "chart_name": chart.name,
                "interpretation": interpretation
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取解读数据失败: {str(e)}"
        )


@router.get("/pdf/{chart_id}")
async def generate_pdf_report(
    chart_id: int,
    template: str = Query(default=ReportTemplate.DETAILED, description="报告模板: simple 或 detailed"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    为已保存的星盘生成 PDF 报告
    
    支持异步生成，避免阻塞事件循环
    """
    try:
        chart_data, chart = get_or_create_chart_data(db, chart_id, current_user.id)
        
        if not chart_data or not chart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="星盘不存在"
            )
        
        if template not in [ReportTemplate.SIMPLE, ReportTemplate.DETAILED]:
            template = ReportTemplate.DETAILED
        
        pdf_buffer, filename = await generate_report_async(
            chart_data=chart_data,
            name=chart.name or '星盘',
            birth_date=chart.birth_date,
            birth_time=chart.birth_time,
            birth_place=chart.birth_place or '',
            latitude=chart.latitude,
            longitude=chart.longitude,
            template=template
        )
        
        content_disposition = build_content_disposition_header(filename)
        
        return StreamingResponse(
            io.BytesIO(pdf_buffer.getvalue()),
            media_type="application/pdf",
            headers={
                "Content-Disposition": content_disposition,
                "Content-Length": str(len(pdf_buffer.getvalue())),
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"PDF 生成错误: {error_trace}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"报告生成失败: {str(e)}"
        )


@router.post("/pdf/generate")
async def generate_pdf_direct(
    request: ChartReportRequest,
    template: str = Query(default=ReportTemplate.DETAILED, description="报告模板: simple 或 detailed"),
    current_user: User = Depends(get_current_user)
):
    """
    直接生成 PDF 报告（无需预先保存星盘）
    
    接收星盘参数，直接计算并生成 PDF 报告
    """
    try:
        if template not in [ReportTemplate.SIMPLE, ReportTemplate.DETAILED]:
            template = ReportTemplate.DETAILED
        
        chart_data = calculate_chart_from_input(
            birth_date=request.birth_date,
            birth_time=request.birth_time,
            latitude=request.latitude,
            longitude=request.longitude,
            house_system=request.house_system.value
        )
        
        pdf_buffer, filename = await generate_report_async(
            chart_data=chart_data,
            name=request.name or '星盘',
            birth_date=request.birth_date,
            birth_time=request.birth_time,
            birth_place=request.birth_place or '',
            latitude=request.latitude,
            longitude=request.longitude,
            template=template
        )
        
        content_disposition = build_content_disposition_header(filename)
        
        return StreamingResponse(
            io.BytesIO(pdf_buffer.getvalue()),
            media_type="application/pdf",
            headers={
                "Content-Disposition": content_disposition,
                "Content-Length": str(len(pdf_buffer.getvalue())),
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"直接生成 PDF 错误: {error_trace}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"报告生成失败: {str(e)}"
        )


@router.post("/interpretation/generate", response_model=ApiResponse)
def generate_interpretation_direct(
    request: ChartReportRequest
):
    """
    直接生成星盘解读数据（无需预先保存星盘）
    
    接收星盘参数，直接计算并返回解读数据
    """
    try:
        chart_data = calculate_chart_from_input(
            birth_date=request.birth_date,
            birth_time=request.birth_time,
            latitude=request.latitude,
            longitude=request.longitude,
            house_system=request.house_system.value
        )
        
        interpretation = ChartService.generate_interpretation(chart_data)
        
        return ApiResponse(
            message="success",
            data={
                "chart_name": request.name or '星盘',
                "chart_data": chart_data,
                "interpretation": interpretation
            }
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成解读失败: {str(e)}"
        )


@router.post("/pdf/async", response_model=ApiResponse)
async def generate_pdf_async_task(
    request: ChartReportRequest,
    background_tasks: BackgroundTasks,
    template: str = Query(default=ReportTemplate.DETAILED, description="报告模板: simple 或 detailed"),
    current_user: User = Depends(get_current_user)
):
    """
    异步 PDF 报告生成（适用于大报告）
    
    立即返回任务ID，后台生成完成后可通过其他接口获取
    注意：当前版本为简化实现，实际生产环境可结合 Redis/Celery
    """
    import uuid
    
    task_id = str(uuid.uuid4())
    
    try:
        chart_data = calculate_chart_from_input(
            birth_date=request.birth_date,
            birth_time=request.birth_time,
            latitude=request.latitude,
            longitude=request.longitude,
            house_system=request.house_system.value
        )
        
        pdf_buffer, filename = await generate_report_async(
            chart_data=chart_data,
            name=request.name or '星盘',
            birth_date=request.birth_date,
            birth_time=request.birth_time,
            birth_place=request.birth_place or '',
            latitude=request.latitude,
            longitude=request.longitude,
            template=template
        )
        
        return ApiResponse(
            message="报告生成成功",
            data={
                "task_id": task_id,
                "status": "completed",
                "filename": encode_safe_filename(filename),
                "file_size": len(pdf_buffer.getvalue())
            }
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"异步 PDF 生成错误: {error_trace}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"报告生成失败: {str(e)}"
        )


@router.post("/pdf/generate-with-interpretation", response_model=ApiResponse)
async def generate_pdf_with_interpretation(
    request: ChartReportRequest,
    template: str = Query(default=ReportTemplate.DETAILED, description="报告模板: simple 或 detailed"),
    current_user: User = Depends(get_current_user)
):
    """
    生成 PDF 报告并同时返回解读数据
    
    适合需要同时展示解读和下载 PDF 的场景
    """
    try:
        chart_data = calculate_chart_from_input(
            birth_date=request.birth_date,
            birth_time=request.birth_time,
            latitude=request.latitude,
            longitude=request.longitude,
            house_system=request.house_system.value
        )
        
        interpretation = ChartService.generate_interpretation(chart_data)
        
        pdf_buffer, filename = await generate_report_async(
            chart_data=chart_data,
            name=request.name or '星盘',
            birth_date=request.birth_date,
            birth_time=request.birth_time,
            birth_place=request.birth_place or '',
            latitude=request.latitude,
            longitude=request.longitude,
            template=template
        )
        
        import base64
        pdf_base64 = base64.b64encode(pdf_buffer.getvalue()).decode('utf-8')
        
        return ApiResponse(
            message="报告生成成功",
            data={
                "chart_name": request.name or '星盘',
                "interpretation": interpretation,
                "pdf_base64": pdf_base64,
                "filename": encode_safe_filename(filename),
                "file_size": len(pdf_buffer.getvalue())
            }
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"生成 PDF 带解读错误: {error_trace}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"报告生成失败: {str(e)}"
        )
