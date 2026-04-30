from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models import User
from app.routers.users import get_current_active_user
from app.services.community_energy_service import (
    CommunityEnergyService,
    get_community_energy_service
)
from app.services.energy_weather_service import (
    EnergyWeatherService,
    get_energy_weather_service
)
from app.services.energy_mission_service import (
    EnergyMissionService,
    get_energy_mission_service
)
from app.services.energy_contribution_service import (
    EnergyContributionService,
    get_energy_contribution_service
)
from app.services.prediction_service import (
    PredictionService,
    get_prediction_service
)
from app.schemas import ApiResponse

router = APIRouter()


class PresenceUpdateRequest(BaseModel):
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    chart_id: Optional[int] = None


class VoteRequest(BaseModel):
    prediction_id: int
    selected_option: str
    confidence: int = 50
    stardust_bet: int = 0


class ContributionRequest(BaseModel):
    contribution_type: str
    scope: str = "global"
    city: Optional[str] = None


@router.get("/weather/current", response_model=ApiResponse)
def get_current_weather(
    scope: str = Query("global", description="范围：global 或 local"),
    city: Optional[str] = Query(None, description="城市名称（当 scope 为 local 时）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取当前能量天气
    
    返回当前社区的能量指数、天气状态、维度能量等信息
    """
    try:
        weather_service = get_energy_weather_service()
        weather_data = weather_service.get_current_weather(db, scope, city)
        
        triggered_missions = weather_service.check_mission_triggers(db, weather_data)
        weather_data["triggered_missions"] = triggered_missions
        
        return ApiResponse(
            code=200,
            message="success",
            data=weather_data
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/weather/history", response_model=ApiResponse)
def get_weather_history(
    scope: str = Query("global", description="范围：global 或 local"),
    city: Optional[str] = Query(None, description="城市名称"),
    hours: int = Query(24, ge=1, le=168, description="历史小时数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取能量天气历史
    """
    try:
        weather_service = get_energy_weather_service()
        history_data = weather_service.get_weather_history(db, scope, city, hours)
        
        return ApiResponse(
            code=200,
            message="success",
            data=history_data
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/weather/forecast", response_model=ApiResponse)
def get_weather_forecast(
    scope: str = Query("global", description="范围：global 或 local"),
    city: Optional[str] = Query(None, description="城市名称"),
    hours: int = Query(6, ge=1, le=24, description="预测小时数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取能量天气预测
    """
    try:
        weather_service = get_energy_weather_service()
        forecast_data = weather_service.get_forecast(db, scope, city, hours)
        
        return ApiResponse(
            code=200,
            message="success",
            data=forecast_data
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/presence/update", response_model=ApiResponse)
def update_presence(
    request: PresenceUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    更新用户在线状态
    
    用于心跳和位置更新
    """
    try:
        community_service = get_community_energy_service()
        presence = community_service.update_user_presence(
            db,
            user_id=current_user.id,
            city=request.city,
            latitude=request.latitude,
            longitude=request.longitude,
            chart_id=request.chart_id
        )
        
        return ApiResponse(
            code=200,
            message="状态已更新",
            data={
                "user_id": presence.user_id,
                "is_online": presence.is_online,
                "last_seen_at": presence.last_seen_at.isoformat() if presence.last_seen_at else None
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/community/online", response_model=ApiResponse)
def get_online_users(
    scope: str = Query("global", description="范围：global 或 local"),
    city: Optional[str] = Query(None, description="城市名称"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取在线用户列表
    """
    try:
        community_service = get_community_energy_service()
        online_users = community_service.get_online_users(db, scope, city)
        
        return ApiResponse(
            code=200,
            message="success",
            data={
                "count": len(online_users),
                "users": online_users
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/missions/active", response_model=ApiResponse)
def get_active_missions(
    limit: int = Query(10, ge=1, le=50, description="限制数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取进行中的能量任务
    """
    try:
        mission_service = get_energy_mission_service()
        missions = mission_service.get_active_missions(db, limit)
        
        return ApiResponse(
            code=200,
            message="success",
            data={
                "count": len(missions),
                "missions": missions
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/missions/upcoming", response_model=ApiResponse)
def get_upcoming_missions(
    hours: int = Query(24, ge=1, le=168, description="未来小时数"),
    limit: int = Query(5, ge=1, le=20, description="限制数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取即将开始的任务
    """
    try:
        mission_service = get_energy_mission_service()
        missions = mission_service.get_upcoming_missions(db, hours, limit)
        
        return ApiResponse(
            code=200,
            message="success",
            data={
                "count": len(missions),
                "missions": missions
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/missions/{mission_id}/join", response_model=ApiResponse)
def join_mission(
    mission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    加入任务
    """
    try:
        mission_service = get_energy_mission_service()
        result = mission_service.join_mission(db, current_user.id, mission_id)
        
        if "error" in result:
            return ApiResponse(
                code=400,
                message=result["error"],
                data=result
            )
        
        return ApiResponse(
            code=200,
            message="已成功加入任务",
            data=result
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/missions/{mission_id}", response_model=ApiResponse)
def get_mission_detail(
    mission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取任务详情
    """
    try:
        mission_service = get_energy_mission_service()
        result = mission_service.get_mission_detail(db, mission_id, current_user.id)
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"]
            )
        
        return ApiResponse(
            code=200,
            message="success",
            data=result
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/contributions/available", response_model=ApiResponse)
def get_available_contributions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取可用的能量贡献类型
    """
    try:
        contribution_service = get_energy_contribution_service()
        contributions = contribution_service.get_available_contributions(db, current_user.id)
        
        return ApiResponse(
            code=200,
            message="success",
            data={
                "count": len(contributions),
                "contributions": contributions
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/contributions", response_model=ApiResponse)
def make_contribution(
    request: ContributionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    注入能量贡献
    """
    try:
        contribution_service = get_energy_contribution_service()
        result = contribution_service.contribute_energy(
            db,
            user_id=current_user.id,
            contribution_type=request.contribution_type,
            scope=request.scope,
            city=request.city
        )
        
        if "error" in result:
            return ApiResponse(
                code=400,
                message=result["error"],
                data=result
            )
        
        return ApiResponse(
            code=200,
            message=result.get("message", "能量注入成功"),
            data=result
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/contributions/my", response_model=ApiResponse)
def get_my_contributions(
    only_active: bool = Query(False, description="只获取活跃的贡献"),
    limit: int = Query(20, ge=1, le=100, description="限制数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取我的能量贡献记录
    """
    try:
        contribution_service = get_energy_contribution_service()
        contributions = contribution_service.get_user_contributions(
            db, current_user.id, only_active, limit
        )
        
        return ApiResponse(
            code=200,
            message="success",
            data={
                "count": len(contributions),
                "contributions": contributions
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/contributions/active", response_model=ApiResponse)
def get_active_contributions(
    scope: str = Query("global", description="范围：global 或 local"),
    city: Optional[str] = Query(None, description="城市名称"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取社区活跃的能量贡献
    """
    try:
        contribution_service = get_energy_contribution_service()
        contributions = contribution_service.get_active_contributions(db, scope, city)
        
        bonus_data = contribution_service.calculate_community_energy_bonus(db, scope, city)
        
        return ApiResponse(
            code=200,
            message="success",
            data={
                "contributions": contributions,
                "bonus": bonus_data
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/predictions/open", response_model=ApiResponse)
def get_open_predictions(
    target_date: Optional[str] = Query(None, description="目标日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取开放投票的预测
    """
    try:
        prediction_service = get_prediction_service()
        predictions = prediction_service.get_open_predictions(db, target_date)
        
        return ApiResponse(
            code=200,
            message="success",
            data={
                "count": len(predictions),
                "predictions": predictions
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/predictions/{prediction_id}", response_model=ApiResponse)
def get_prediction_detail(
    prediction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取预测详情
    """
    try:
        prediction_service = get_prediction_service()
        result = prediction_service.get_prediction_detail(db, prediction_id, current_user.id)
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"]
            )
        
        return ApiResponse(
            code=200,
            message="success",
            data=result
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/predictions/vote", response_model=ApiResponse)
def cast_vote(
    request: VoteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    投票
    """
    try:
        prediction_service = get_prediction_service()
        result = prediction_service.cast_vote(
            db,
            user_id=current_user.id,
            prediction_id=request.prediction_id,
            selected_option=request.selected_option,
            confidence=request.confidence,
            stardust_bet=request.stardust_bet
        )
        
        if "error" in result:
            return ApiResponse(
                code=400,
                message=result["error"],
                data=result
            )
        
        return ApiResponse(
            code=200,
            message=result.get("message", "投票成功"),
            data=result
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/predictions/history/my", response_model=ApiResponse)
def get_my_predictions_history(
    limit: int = Query(20, ge=1, le=100, description="限制数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取我的预测历史
    """
    try:
        prediction_service = get_prediction_service()
        history = prediction_service.get_user_predictions_history(db, current_user.id, limit)
        
        return ApiResponse(
            code=200,
            message="success",
            data={
                "count": len(history),
                "history": history
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
