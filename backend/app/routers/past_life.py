from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import logging

from sqlalchemy.orm import Session

from app.schemas import ApiResponse, SynastryPersonInput
from app.database import get_db
from app.models import User, Chart, SynastryRecord
from app.routers.users import get_current_user, get_current_active_user
from app.astro import (
    parse_birth_datetime, local_to_utc, utc_to_julday,
    calculate_all_planets, calculate_houses_ex
)
from app.services.past_life import (
    PAST_LIFE_THEME_CONFIG,
    PAST_LIFE_RELATIONSHIP_CONFIG,
    PAST_LIFE_PRICE,
    PAST_LIFE_SYNASTRY_PRICE,
    extract_core_planets,
    determine_past_life_theme,
    determine_past_life_relationship,
    generate_past_life_story,
    generate_synastry_past_life_story,
    get_or_create_past_life_record,
    get_or_create_synastry_past_life_record,
    create_past_life_order,
    upgrade_to_deep_version,
    get_user_past_life_records,
    get_user_synastry_past_life_records,
    get_past_life_by_share_code,
    get_single_record_by_id,
    get_synastry_record_by_id,
    record_to_dict,
    synastry_record_to_dict,
    process_payment_callback,
    get_order_status,
)
from app.services.synastry_highlights_service import extract_synastry_highlights
from app.synastry import calculate_synastry_chart

logger = logging.getLogger(__name__)

router = APIRouter()


class PastLifeChartRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=100, description="姓名/备注")
    birth_date: str = Field(..., description="出生日期 YYYY-MM-DD")
    birth_time: str = Field(..., description="出生时间 HH:MM")
    birth_place: Optional[str] = Field(None, max_length=100, description="出生地点")
    latitude: float = Field(..., description="纬度")
    longitude: float = Field(..., description="经度")
    house_system: str = Field("placidus", description="宫位系统: placidus/whole_sign")
    chart_id: Optional[int] = Field(None, description="已保存的星盘ID（可选）")


class PastLifeSynastryRequest(BaseModel):
    person_a: SynastryPersonInput = Field(..., description="人物A的星盘信息")
    person_b: SynastryPersonInput = Field(..., description="人物B的星盘信息")
    synastry_record_id: Optional[int] = Field(None, description="已保存的合盘记录ID（可选）")


class OrderCreateRequest(BaseModel):
    record_id: int = Field(..., description="前世记录ID")
    record_type: str = Field("single", description="记录类型: single/synastry")


class OrderCallbackRequest(BaseModel):
    order_no: str = Field(..., description="订单号")
    record_id: int = Field(..., description="前世记录ID")
    record_type: str = Field("single", description="记录类型: single/synastry")


class SingleRecordDetailRequest(BaseModel):
    record_id: int = Field(..., description="前世记录ID")


class SynastryRecordDetailRequest(BaseModel):
    record_id: int = Field(..., description="合盘前世记录ID")


def _calculate_chart_data(
    birth_date: str,
    birth_time: str,
    latitude: float,
    longitude: float,
    house_system: str
) -> Dict[str, Any]:
    """计算星盘数据"""
    birth_dt = parse_birth_datetime(birth_date, birth_time)
    utc_dt, _ = local_to_utc(
        birth_dt["year"], birth_dt["month"], birth_dt["day"],
        birth_dt["hour"], birth_dt["minute"],
        latitude, longitude
    )
    jd = utc_to_julday(utc_dt)
    
    houses_result = calculate_houses_ex(
        jd, latitude, longitude, house_system
    )
    house_cusps = houses_result["house_cusps"]
    
    planets = calculate_all_planets(jd, house_cusps)
    
    main_planet_names = ["太阳", "月亮", "水星", "金星", "火星", "木星", "土星", "天王星", "海王星", "冥王星", "北交点", "南交点"]
    planets = [p for p in planets if p.get("name") in main_planet_names]
    
    sun_sign = {}
    moon_sign = {}
    ascendant = {}
    
    for p in planets:
        if p.get("name") == "太阳":
            zodiac = p.get("zodiac", {})
            sun_sign = {"sign": zodiac.get("sign"), "degree": zodiac.get("degree")}
        elif p.get("name") == "月亮":
            zodiac = p.get("zodiac", {})
            moon_sign = {"sign": zodiac.get("sign"), "degree": zodiac.get("degree")}
    
    ascendant_data = houses_result.get("ascendant", {})
    if ascendant_data:
        ascendant = {"sign": ascendant_data.get("sign"), "degree": ascendant_data.get("degree")}
    
    return {
        "planets": planets,
        "houses": houses_result,
        "sun_sign": sun_sign,
        "moon_sign": moon_sign,
        "ascendant": ascendant,
    }


@router.post("/analyze", response_model=ApiResponse)
async def analyze_past_life(
    request: PastLifeChartRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    分析前世主题（不生成AI故事）
    
    基于星盘数据确定前世主题类型
    """
    try:
        user_id = current_user.id if current_user else None
        chart_data = None
        
        if request.chart_id and current_user:
            chart = db.query(Chart).filter(
                Chart.id == request.chart_id,
                Chart.user_id == current_user.id,
                Chart.is_deleted == False
            ).first()
            if chart:
                try:
                    chart_data = json.loads(chart.chart_data)
                except Exception:
                    pass
        
        if not chart_data:
            chart_data = _calculate_chart_data(
                birth_date=request.birth_date,
                birth_time=request.birth_time,
                latitude=request.latitude,
                longitude=request.longitude,
                house_system=request.house_system
            )
        
        planets = extract_core_planets(chart_data)
        theme, theme_info = determine_past_life_theme(planets, chart_data)
        
        theme_config = PAST_LIFE_THEME_CONFIG.get(theme, PAST_LIFE_THEME_CONFIG["adventurer"])
        
        sun_sign = chart_data.get("sun_sign", {}).get("sign", "未知")
        moon_sign = chart_data.get("moon_sign", {}).get("sign", "未知")
        ascendant = chart_data.get("ascendant", {}).get("sign", "未知")
        
        return ApiResponse(
            code=200,
            message="前世主题分析完成",
            data={
                "theme": theme,
                "theme_name": theme_config["name"],
                "theme_icon": theme_config["icon"],
                "theme_description": theme_config["description"],
                "keywords": theme_config["keywords"],
                "theme_score": theme_info.get("score", 0),
                "matched_planets": theme_info.get("matched_planets", []),
                "all_planets": planets,
                "sun_sign": sun_sign,
                "moon_sign": moon_sign,
                "ascendant": ascendant,
                "price": PAST_LIFE_PRICE,
                "deep_version_price": PAST_LIFE_PRICE,
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"分析前世主题失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.post("/generate", response_model=ApiResponse)
async def generate_past_life(
    request: PastLifeChartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    生成前世故事（基础版，免费）
    
    生成精简版的前世故事摘要，适合快速预览
    """
    try:
        logger.info(f"生成前世故事，用户: {current_user.username}")
        
        chart_data = None
        chart_id = request.chart_id
        
        if chart_id:
            chart = db.query(Chart).filter(
                Chart.id == chart_id,
                Chart.user_id == current_user.id,
                Chart.is_deleted == False
            ).first()
            if chart:
                try:
                    chart_data = json.loads(chart.chart_data)
                except Exception:
                    pass
        
        if not chart_data:
            chart_data = _calculate_chart_data(
                birth_date=request.birth_date,
                birth_time=request.birth_time,
                latitude=request.latitude,
                longitude=request.longitude,
                house_system=request.house_system
            )
        
        record, error = get_or_create_past_life_record(
            db=db,
            user_id=current_user.id,
            chart_id=chart_id,
            chart_data=chart_data,
            name=request.name or current_user.username
        )
        
        if not record:
            raise HTTPException(status_code=500, detail=error or "创建前世记录失败")
        
        if record.basic_story:
            return ApiResponse(
                code=200,
                message="获取前世故事成功",
                data=record_to_dict(record)
            )
        
        planets = extract_core_planets(chart_data)
        theme, _ = determine_past_life_theme(planets, chart_data)
        
        story_result = await generate_past_life_story(
            theme=theme,
            planets=planets,
            chart_data=chart_data,
            is_deep=False,
            name=request.name or current_user.username
        )
        
        if not story_result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=story_result.get("error", "生成故事失败")
            )
        
        record.basic_story = story_result["story"]
        record.basic_story_short = story_result["short_story"]
        db.commit()
        db.refresh(record)
        
        return ApiResponse(
            code=200,
            message="前世故事生成完成",
            data=record_to_dict(record)
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成前世故事失败: {str(e)}", exc_info=True)
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
            raise HTTPException(status_code=500, detail=f"生成前世故事失败: {error_msg}")


@router.post("/synastry/analyze", response_model=ApiResponse)
async def analyze_synastry_past_life(
    request: PastLifeSynastryRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    分析合盘前世关系主题（不生成AI故事）
    """
    try:
        synastry_data = None
        
        if request.synastry_record_id and current_user:
            syn_record = db.query(SynastryRecord).filter(
                SynastryRecord.id == request.synastry_record_id,
                SynastryRecord.user_id == current_user.id,
                SynastryRecord.is_deleted == False
            ).first()
            if syn_record:
                try:
                    synastry_data = json.loads(syn_record.synastry_data)
                except Exception:
                    pass
        
        if not synastry_data:
            person_a = request.person_a
            person_b = request.person_b
            
            synastry_data = calculate_synastry_chart(
                {
                    "name": person_a.name or "人物A",
                    "birth_date": person_a.birth_date,
                    "birth_time": person_a.birth_time,
                    "latitude": person_a.latitude,
                    "longitude": person_a.longitude,
                    "house_system": person_a.house_system
                },
                {
                    "name": person_b.name or "人物B",
                    "birth_date": person_b.birth_date,
                    "birth_time": person_b.birth_time,
                    "latitude": person_b.latitude,
                    "longitude": person_b.longitude,
                    "house_system": person_b.house_system
                }
            )
        
        highlights = extract_synastry_highlights(synastry_data)
        relationship_type, rel_info = determine_past_life_relationship(highlights)
        
        rel_config = PAST_LIFE_RELATIONSHIP_CONFIG.get(
            relationship_type, 
            PAST_LIFE_RELATIONSHIP_CONFIG["stranger"]
        )
        
        return ApiResponse(
            code=200,
            message="合盘前世关系分析完成",
            data={
                "relationship_type": relationship_type,
                "relationship_name": rel_config["name"],
                "relationship_icon": rel_config["icon"],
                "relationship_description": rel_config["description"],
                "keywords": rel_config["keywords"],
                "relationship_score": rel_info.get("score", 0),
                "highlights": highlights.get("highlights", [])[:3],
                "overall_theme": highlights.get("overall_theme", {}),
                "price": PAST_LIFE_SYNASTRY_PRICE,
                "deep_version_price": PAST_LIFE_SYNASTRY_PRICE,
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"分析合盘前世关系失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.post("/synastry/generate", response_model=ApiResponse)
async def generate_synastry_past_life(
    request: PastLifeSynastryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    生成合盘前世关系故事（基础版，免费）
    """
    try:
        logger.info(f"生成合盘前世故事，用户: {current_user.username}")
        
        synastry_data = None
        synastry_record_id = request.synastry_record_id
        name_a = request.person_a.name or "人物A"
        name_b = request.person_b.name or "人物B"
        
        if synastry_record_id:
            syn_record = db.query(SynastryRecord).filter(
                SynastryRecord.id == synastry_record_id,
                SynastryRecord.user_id == current_user.id,
                SynastryRecord.is_deleted == False
            ).first()
            if syn_record:
                try:
                    synastry_data = json.loads(syn_record.synastry_data)
                    name_a = syn_record.person_a_name or name_a
                    name_b = syn_record.person_b_name or name_b
                except Exception:
                    pass
        
        if not synastry_data:
            person_a = request.person_a
            person_b = request.person_b
            
            synastry_data = calculate_synastry_chart(
                {
                    "name": name_a,
                    "birth_date": person_a.birth_date,
                    "birth_time": person_a.birth_time,
                    "latitude": person_a.latitude,
                    "longitude": person_a.longitude,
                    "house_system": person_a.house_system
                },
                {
                    "name": name_b,
                    "birth_date": person_b.birth_date,
                    "birth_time": person_b.birth_time,
                    "latitude": person_b.latitude,
                    "longitude": person_b.longitude,
                    "house_system": person_b.house_system
                }
            )
        
        record, error = get_or_create_synastry_past_life_record(
            db=db,
            user_id=current_user.id,
            synastry_record_id=synastry_record_id,
            person_a_name=name_a,
            person_b_name=name_b
        )
        
        if not record:
            raise HTTPException(status_code=500, detail=error or "创建合盘前世记录失败")
        
        if record.basic_story:
            return ApiResponse(
                code=200,
                message="获取合盘前世故事成功",
                data=synastry_record_to_dict(record)
            )
        
        highlights = extract_synastry_highlights(synastry_data)
        relationship_type, _ = determine_past_life_relationship(highlights)
        
        person_a_data = {
            "name": name_a,
            "sun_sign": synastry_data.get("person_a", {}).get("chart", {}).get("sun_sign", {}).get("sign", "未知")
        }
        person_b_data = {
            "name": name_b,
            "sun_sign": synastry_data.get("person_b", {}).get("chart", {}).get("sun_sign", {}).get("sign", "未知")
        }
        
        story_result = await generate_synastry_past_life_story(
            relationship_type=relationship_type,
            person_a=person_a_data,
            person_b=person_b_data,
            synastry_highlights=highlights,
            is_deep=False
        )
        
        if not story_result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=story_result.get("error", "生成故事失败")
            )
        
        record.relationship_type = relationship_type
        rel_config = PAST_LIFE_RELATIONSHIP_CONFIG.get(relationship_type, {})
        record.relationship_name = rel_config.get("name", "")
        record.basic_story = story_result["story"]
        record.basic_story_short = story_result["short_story"]
        db.commit()
        db.refresh(record)
        
        return ApiResponse(
            code=200,
            message="合盘前世故事生成完成",
            data=synastry_record_to_dict(record)
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成合盘前世故事失败: {str(e)}", exc_info=True)
        error_msg = str(e)
        
        if "超时" in error_msg or "timeout" in error_msg.lower():
            raise HTTPException(
                status_code=504,
                detail=f"请求超时: AI服务响应时间过长。请稍后重试。错误详情: {error_msg}"
            )
        else:
            raise HTTPException(status_code=500, detail=f"生成合盘前世故事失败: {error_msg}")


@router.get("/detail/{record_id}", response_model=ApiResponse)
def get_single_record_detail(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取单人前世记录详情
    """
    try:
        record = get_single_record_by_id(db, record_id, current_user.id)
        
        if not record:
            raise HTTPException(status_code=404, detail="记录不存在或无权限")
        
        return ApiResponse(
            code=200,
            message="success",
            data=record_to_dict(record)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取前世记录详情失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get("/synastry/detail/{record_id}", response_model=ApiResponse)
def get_synastry_record_detail(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取合盘前世记录详情
    """
    try:
        record = get_synastry_record_by_id(db, record_id, current_user.id)
        
        if not record:
            raise HTTPException(status_code=404, detail="记录不存在或无权限")
        
        return ApiResponse(
            code=200,
            message="success",
            data=synastry_record_to_dict(record)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取合盘前世记录详情失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.post("/order/create", response_model=ApiResponse)
def create_deep_version_order(
    request: OrderCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    创建深度版订单
    
    生成9.9元的支付订单，用于解锁深度版前世故事
    
    幂等性保障: 同一记录不会重复创建订单
    """
    try:
        order, error = create_past_life_order(
            db=db,
            user_id=current_user.id,
            record_type=request.record_type,
            record_id=request.record_id
        )
        
        if not order:
            raise HTTPException(status_code=400, detail=error or "创建订单失败")
        
        return ApiResponse(
            code=200,
            message="订单创建成功",
            data={
                "order_no": order.order_no,
                "amount": order.amount,
                "final_amount": order.final_amount,
                "status": order.status.value if hasattr(order.status, 'value') else str(order.status),
                "is_sandbox": order.is_sandbox,
                "payment_url": f"/api/payment/sandbox/pay?order_no={order.order_no}" if order.is_sandbox else None,
                "created_at": order.created_at.isoformat() if order.created_at else None,
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建深度版订单失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建订单失败: {str(e)}")


@router.get("/order/status/{order_no}", response_model=ApiResponse)
def get_payment_order_status(
    order_no: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取订单状态
    """
    try:
        status_data, error = get_order_status(db, order_no, current_user.id)
        
        if error:
            raise HTTPException(status_code=404, detail=error)
        
        return ApiResponse(
            code=200,
            message="success",
            data=status_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取订单状态失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.post("/order/upgrade", response_model=ApiResponse)
def upgrade_with_order(
    request: OrderCallbackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    订单支付成功后升级到深度版
    
    用于沙盒环境的模拟支付回调
    
    幂等性保障: 已升级的记录不会重复处理
    """
    try:
        success, error, result_data = process_payment_callback(
            db=db,
            order_no=request.order_no,
            success=True
        )
        
        if not success:
            raise HTTPException(status_code=400, detail=error or "升级失败")
        
        if result_data:
            return ApiResponse(
                code=200,
                message="升级到深度版成功",
                data=result_data
            )
        
        if request.record_type == "synastry":
            record = get_synastry_record_by_id(db, request.record_id, current_user.id)
            if record:
                return ApiResponse(
                    code=200,
                    message="升级到深度版成功",
                    data=synastry_record_to_dict(record)
                )
        else:
            record = get_single_record_by_id(db, request.record_id, current_user.id)
            if record:
                return ApiResponse(
                    code=200,
                    message="升级到深度版成功",
                    data=record_to_dict(record)
                )
        
        raise HTTPException(status_code=404, detail="记录不存在")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"升级到深度版失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"升级失败: {str(e)}")


@router.post("/generate-deep", response_model=ApiResponse)
async def generate_deep_version(
    request: PastLifeChartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    生成深度版前世故事
    
    注意：此接口需要用户已购买深度版权限
    """
    try:
        record, error = get_or_create_past_life_record(
            db=db,
            user_id=current_user.id,
            chart_id=request.chart_id,
            name=request.name or current_user.username
        )
        
        if not record:
            raise HTTPException(status_code=400, detail=error or "获取记录失败")
        
        if not record.is_paid:
            raise HTTPException(
                status_code=403,
                detail="请先购买深度版权限"
            )
        
        if record.deep_story:
            return ApiResponse(
                code=200,
                message="获取深度版故事成功",
                data=record_to_dict(record)
            )
        
        chart_data = None
        if request.chart_id:
            chart = db.query(Chart).filter(
                Chart.id == request.chart_id,
                Chart.user_id == current_user.id
            ).first()
            if chart:
                try:
                    chart_data = json.loads(chart.chart_data)
                except Exception:
                    pass
        
        if not chart_data:
            chart_data = _calculate_chart_data(
                birth_date=request.birth_date,
                birth_time=request.birth_time,
                latitude=request.latitude,
                longitude=request.longitude,
                house_system=request.house_system
            )
        
        planets = extract_core_planets(chart_data)
        theme = record.theme or "adventurer"
        
        story_result = await generate_past_life_story(
            theme=theme,
            planets=planets,
            chart_data=chart_data,
            is_deep=True,
            name=request.name or current_user.username
        )
        
        if not story_result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=story_result.get("error", "生成故事失败")
            )
        
        record.deep_story = story_result["story"]
        db.commit()
        db.refresh(record)
        
        return ApiResponse(
            code=200,
            message="深度版故事生成完成",
            data=record_to_dict(record)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成深度版前世故事失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@router.get("/my-records", response_model=ApiResponse)
def get_my_records(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取我的前世故事记录列表（真实分页）
    
    返回真实的total计数，支持分页功能
    """
    try:
        records, total = get_user_past_life_records(db, current_user.id, limit, offset)
        
        records_list = [record_to_dict(r) for r in records]
        
        return ApiResponse(
            code=200,
            message="success",
            data={
                "records": records_list,
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": (offset + limit) < total,
            }
        )
        
    except Exception as e:
        logger.error(f"获取前世记录失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get("/my-synastry-records", response_model=ApiResponse)
def get_my_synastry_records(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取我的合盘前世故事记录列表（真实分页）
    
    返回真实的total计数，支持分页功能
    """
    try:
        records, total = get_user_synastry_past_life_records(db, current_user.id, limit, offset)
        
        records_list = [synastry_record_to_dict(r) for r in records]
        
        return ApiResponse(
            code=200,
            message="success",
            data={
                "records": records_list,
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": (offset + limit) < total,
            }
        )
        
    except Exception as e:
        logger.error(f"获取合盘前世记录失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get("/share/{share_code}", response_model=ApiResponse)
def get_shared_story(
    share_code: str,
    db: Session = Depends(get_db)
):
    """
    通过分享码获取前世故事（公开分享接口）
    
    用于用户分享给他人查看
    
    并发安全: 使用数据库原子操作更新share_count
    """
    try:
        shared_data = get_past_life_by_share_code(db, share_code)
        
        if not shared_data:
            raise HTTPException(status_code=404, detail="分享链接不存在或已失效")
        
        return ApiResponse(
            code=200,
            message="success",
            data=shared_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取分享故事失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get("/themes", response_model=ApiResponse)
def get_all_themes():
    """
    获取所有前世主题配置
    """
    themes = []
    for key, config in PAST_LIFE_THEME_CONFIG.items():
        themes.append({
            "key": key,
            "name": config["name"],
            "icon": config["icon"],
            "description": config["description"],
            "keywords": config["keywords"],
        })
    
    return ApiResponse(
        code=200,
        message="success",
        data={
            "themes": themes,
            "price": PAST_LIFE_PRICE,
        }
    )


@router.get("/relationship-types", response_model=ApiResponse)
def get_all_relationship_types():
    """
    获取所有前世关系类型配置
    """
    relationships = []
    for key, config in PAST_LIFE_RELATIONSHIP_CONFIG.items():
        relationships.append({
            "key": key,
            "name": config["name"],
            "icon": config["icon"],
            "description": config["description"],
            "keywords": config["keywords"],
        })
    
    return ApiResponse(
        code=200,
        message="success",
        data={
            "relationships": relationships,
            "price": PAST_LIFE_SYNASTRY_PRICE,
        }
    )
