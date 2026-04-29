from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import json

from app.database import get_db
from app.models import User, Chart
from app.schemas import ChartCreate, ChartUpdate, ChartResponse, ApiResponse
from app.routers.users import get_current_user
from app.astro import calculate_chart, parse_birth_datetime

router = APIRouter(tags=["星盘存档"])


@router.post("", response_model=ApiResponse)
def save_chart(
    chart_data: ChartCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dt = parse_birth_datetime(chart_data.birth_date, chart_data.birth_time)
    
    result = calculate_chart(
        year=dt["year"],
        month=dt["month"],
        day=dt["day"],
        hour=dt["hour"],
        minute=dt["minute"],
        latitude=chart_data.latitude,
        longitude=chart_data.longitude,
        house_system=chart_data.house_system
    )
    
    chart = Chart(
        user_id=current_user.id,
        name=chart_data.name or f"{chart_data.birth_date} {chart_data.birth_time}",
        birth_date=chart_data.birth_date,
        birth_time=chart_data.birth_time,
        birth_place=chart_data.birth_place,
        latitude=chart_data.latitude,
        longitude=chart_data.longitude,
        house_system=chart_data.house_system,
        chart_data=json.dumps(result, ensure_ascii=False, default=str)
    )
    
    db.add(chart)
    db.commit()
    db.refresh(chart)
    
    return ApiResponse(
        message="星盘保存成功",
        data={
            "id": chart.id,
            "created_at": chart.created_at.isoformat()
        }
    )


@router.get("", response_model=ApiResponse)
def get_my_charts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 50
):
    charts = db.query(Chart).filter(
        Chart.user_id == current_user.id,
        Chart.is_deleted == False
    ).order_by(Chart.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for chart in charts:
        result.append({
            "id": chart.id,
            "name": chart.name,
            "birth_date": chart.birth_date,
            "birth_time": chart.birth_time,
            "birth_place": chart.birth_place,
            "latitude": chart.latitude,
            "longitude": chart.longitude,
            "house_system": chart.house_system,
            "created_at": chart.created_at.isoformat(),
            "updated_at": chart.updated_at.isoformat()
        })
    
    return ApiResponse(
        message="success",
        data={"charts": result, "total": len(result)}
    )


@router.get("/{chart_id}", response_model=ApiResponse)
def get_chart_detail(
    chart_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    chart = db.query(Chart).filter(
        Chart.id == chart_id,
        Chart.user_id == current_user.id,
        Chart.is_deleted == False
    ).first()
    
    if not chart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="星盘不存在"
        )
    
    chart_data = None
    try:
        if chart.chart_data:
            chart_data = json.loads(chart.chart_data)
    except Exception as e:
        pass
    
    return ApiResponse(
        message="success",
        data={
            "id": chart.id,
            "name": chart.name,
            "birth_date": chart.birth_date,
            "birth_time": chart.birth_time,
            "birth_place": chart.birth_place,
            "latitude": chart.latitude,
            "longitude": chart.longitude,
            "house_system": chart.house_system,
            "chart_data": chart_data,
            "created_at": chart.created_at.isoformat(),
            "updated_at": chart.updated_at.isoformat()
        }
    )


@router.put("/{chart_id}", response_model=ApiResponse)
def update_chart(
    chart_id: int,
    update_data: ChartUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    chart = db.query(Chart).filter(
        Chart.id == chart_id,
        Chart.user_id == current_user.id,
        Chart.is_deleted == False
    ).first()
    
    if not chart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="星盘不存在"
        )
    
    update_dict = update_data.model_dump(exclude_unset=True)
    
    need_recalculate = any(k in update_dict for k in [
        "birth_date", "birth_time", "latitude", "longitude", "house_system"
    ])
    
    for key, value in update_dict.items():
        if value is not None:
            setattr(chart, key, value)
    
    if need_recalculate:
        dt = parse_birth_datetime(chart.birth_date, chart.birth_time)
        
        result = calculate_chart(
            year=dt["year"],
            month=dt["month"],
            day=dt["day"],
            hour=dt["hour"],
            minute=dt["minute"],
            latitude=chart.latitude,
            longitude=chart.longitude,
            house_system=chart.house_system
        )
        
        chart.chart_data = json.dumps(result, ensure_ascii=False, default=str)
    
    chart.updated_at = datetime.utcnow()
    db.commit()
    
    return ApiResponse(
        message="星盘更新成功",
        data={"id": chart.id}
    )


@router.delete("/{chart_id}", response_model=ApiResponse)
def delete_chart(
    chart_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    chart = db.query(Chart).filter(
        Chart.id == chart_id,
        Chart.user_id == current_user.id,
        Chart.is_deleted == False
    ).first()
    
    if not chart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="星盘不存在"
        )
    
    chart.is_deleted = True
    chart.updated_at = datetime.utcnow()
    db.commit()
    
    return ApiResponse(message="星盘已删除")
