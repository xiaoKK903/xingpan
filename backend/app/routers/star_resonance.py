from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from sqlalchemy.orm import Session

from app.schemas import ApiResponse
from app.database import get_db
from app.models import (
    User,
    Chart,
    StarDustTransaction
)
from app.routers.users import get_current_user, get_current_user_optional
from app.services.star_resonance_service import (
    star_resonance_service,
    ELEMENT_INFO_SERIALIZABLE,
    TIER_CONFIG_SERIALIZABLE,
    BASE_FRAGMENT_COST,
    ElementType,
    ResonanceTier
)
from app.services.websocket_manager import websocket_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["星能共鸣池"])


class RefineRequest(BaseModel):
    fragment_amount: int = Field(..., ge=BASE_FRAGMENT_COST, description="使用的星元碎片数量")
    selected_planet_name: Optional[str] = Field(None, description="选择的强势行星名称，为空则自动选择最强")


class ContributeRequest(BaseModel):
    fragment_amount: int = Field(..., ge=BASE_FRAGMENT_COST, description="使用的星元碎片数量")
    selected_planet_name: Optional[str] = Field(None, description="选择的强势行星名称")


@router.get("/status", response_model=ApiResponse)
async def get_pool_status(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    try:
        pool_status = star_resonance_service.get_pool_status(db)
        
        element_dist_dict = {}
        for elem_key, energy in pool_status.element_distribution.items():
            info = ELEMENT_INFO_SERIALIZABLE.get(elem_key, {})
            element_dist_dict[elem_key] = {
                "name": info.get("name_cn", ""),
                "energy": round(float(energy), 2),
                "color": info.get("color", "#1F2937"),
                "signs": info.get("signs", []),
                "effects": info.get("effects", {})
            }
        
        user_assets = None
        if current_user:
            user_assets = {
                "stardust_fragment_balance": current_user.stardust_fragment_balance or 0,
                "stardust_point_balance": current_user.stardust_point_balance or 0
            }
        
        return ApiResponse(
            message="获取能量池状态成功",
            data={
                "current_tier": pool_status.current_tier,
                "current_tier_name": TIER_CONFIG_SERIALIZABLE.get(pool_status.current_tier, {}).get("name_cn", "未知"),
                "current_energy": round(float(pool_status.current_energy), 2),
                "tier_progress": round(float(pool_status.tier_progress), 4),
                "element_distribution": element_dist_dict,
                "nebula": {
                    "color": pool_status.nebula_color,
                    "intensity": float(pool_status.nebula_intensity)
                },
                "active_effects": pool_status.active_effects,
                "next_tier": pool_status.next_tier,
                "tickets_pending": pool_status.tickets_pending,
                "tier_config": TIER_CONFIG_SERIALIZABLE,
                "user_assets": user_assets,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"获取能量池状态失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取能量池状态失败: {str(e)}"
        )


@router.get("/my-strong-planets", response_model=ApiResponse)
async def get_my_strong_planets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        chart_data = star_resonance_service.get_user_chart(db, current_user.id)
        
        if not chart_data:
            return ApiResponse(
                message="未找到您的星盘数据",
                data={
                    "has_chart": False,
                    "strong_planets": [],
                    "element_distribution": {}
                }
            )
        
        strong_planets = star_resonance_service.analyze_strong_planets(chart_data)
        
        planets_list = []
        for planet in strong_planets:
            elem_info = ELEMENT_INFO_SERIALIZABLE.get(planet.element.value, {})
            planets_list.append({
                "name": planet.name,
                "sign": planet.sign,
                "element": planet.element.value,
                "element_name": elem_info.get("name_cn", ""),
                "element_color": elem_info.get("color", "#1F2937"),
                "dignity_score": planet.dignity_score,
                "weight": planet.weight,
                "multiplier": round(planet.multiplier, 2),
                "is_stellium": planet.is_stellium
            })
        
        from app.services.profile_extractor_service import extract_element_distribution
        element_data = extract_element_distribution(chart_data.get("planets", []))
        
        element_dist = {}
        elem_type_map = {
            "火": "fire",
            "土": "earth",
            "风": "air",
            "水": "water"
        }
        for elem_key in ["火", "土", "风", "水"]:
            elem_value = elem_type_map.get(elem_key)
            if elem_value:
                elem_info = ELEMENT_INFO_SERIALIZABLE.get(elem_value, {})
                count = element_data.get("count", {}).get(elem_key, 0)
                weighted = element_data.get("weighted_score", {}).get(elem_key, 0.0)
                percentage = element_data.get("percentage", {}).get(elem_key, 0.0)
                
                element_dist[elem_value] = {
                    "name": elem_info.get("name_cn", ""),
                    "color": elem_info.get("color", "#1F2937"),
                    "count": count,
                    "weighted_score": float(weighted) if weighted else 0.0,
                    "percentage": float(percentage) if percentage else 0.0
                }
        
        return ApiResponse(
            message="获取强势行星成功",
            data={
                "has_chart": True,
                "strong_planets": planets_list,
                "element_distribution": element_dist,
                "base_fragment_cost": BASE_FRAGMENT_COST
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取强势行星失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取强势行星失败: {str(e)}"
        )


@router.post("/refine", response_model=ApiResponse)
async def refine_energy_preview(
    request: RefineRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        refine_result = star_resonance_service.refine_energy(
            db=db,
            user_id=current_user.id,
            fragment_amount=request.fragment_amount,
            selected_planet_name=request.selected_planet_name
        )
        
        if not refine_result.success:
            return ApiResponse(
                message=refine_result.error_message or "炼化预览失败",
                code=400,
                data={
                    "success": False,
                    "error": refine_result.error_message
                }
            )
        
        selected_planet = None
        if refine_result.selected_planet:
            elem_info = ELEMENT_INFO_SERIALIZABLE.get(refine_result.selected_planet.element.value, {})
            selected_planet = {
                "name": refine_result.selected_planet.name,
                "sign": refine_result.selected_planet.sign,
                "element": refine_result.selected_planet.element.value,
                "element_name": elem_info.get("name_cn", ""),
                "element_color": elem_info.get("color", "#1F2937"),
                "dignity_score": refine_result.selected_planet.dignity_score,
                "multiplier": round(refine_result.selected_planet.multiplier, 2),
                "is_stellium": refine_result.selected_planet.is_stellium
            }
        
        all_planets = []
        for planet in refine_result.strong_planets:
            elem_info = ELEMENT_INFO_SERIALIZABLE.get(planet.element.value, {})
            all_planets.append({
                "name": planet.name,
                "sign": planet.sign,
                "element": planet.element.value,
                "element_name": elem_info.get("name_cn", ""),
                "dignity_score": planet.dignity_score,
                "multiplier": round(planet.multiplier, 2)
            })
        
        element_effects = {}
        if refine_result.element:
            element_effects = ELEMENT_INFO_SERIALIZABLE.get(refine_result.element.value, {}).get("effects", {})
        
        return ApiResponse(
            message="炼化预览成功",
            data={
                "success": True,
                "selected_planet": selected_planet,
                "all_strong_planets": all_planets,
                "fragment_cost": refine_result.fragment_cost,
                "base_energy": round(refine_result.base_energy, 2),
                "total_energy": round(refine_result.total_energy, 2),
                "element": refine_result.element.value if refine_result.element else None,
                "element_name": ELEMENT_INFO_SERIALIZABLE.get(refine_result.element.value, {}).get("name_cn") if refine_result.element else None,
                "multiplier": round(refine_result.multiplier, 2),
                "element_effects": element_effects,
                "current_balance": current_user.stardust_fragment_balance or 0
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"炼化预览失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"炼化预览失败: {str(e)}"
        )


@router.post("/contribute", response_model=ApiResponse)
async def contribute_energy(
    request: ContributeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        refine_result = star_resonance_service.refine_energy(
            db=db,
            user_id=current_user.id,
            fragment_amount=request.fragment_amount,
            selected_planet_name=request.selected_planet_name
        )
        
        if not refine_result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "REFINE_FAILED",
                    "message": refine_result.error_message or "炼化失败"
                }
            )
        
        result = star_resonance_service.contribute_to_pool(
            db=db,
            user_id=current_user.id,
            refine_result=refine_result
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "注入失败")
            )
        
        try:
            contribution = result.get("contribution", {})
            await websocket_manager.broadcast(
                message_type="resonance_contributed",
                data={
                    "user_id": current_user.id,
                    "username": current_user.username,
                    "element": contribution.get("element"),
                    "element_name": contribution.get("element_name"),
                    "planet_name": contribution.get("planet_name"),
                    "planet_sign": contribution.get("planet_sign"),
                    "total_energy": contribution.get("total_energy"),
                    "fragment_cost": contribution.get("fragment_cost"),
                    "tickets_awarded": result.get("tickets_awarded", 0),
                    "pool_status": result.get("pool_status"),
                    "message": f"{current_user.username} 注入了 {contribution.get('element_name')} 能量！"
                },
                channel="global"
            )
        except Exception as e:
            logger.warning(f"WebSocket 广播失败: {e}")
        
        return ApiResponse(
            message=result.get("message", "能量注入成功"),
            data={
                "success": True,
                "contribution": result.get("contribution"),
                "pool_status": result.get("pool_status"),
                "tickets_awarded": result.get("tickets_awarded", 0),
                "transaction": result.get("transaction"),
                "new_balance": current_user.stardust_fragment_balance or 0
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"注入能量失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注入能量失败: {str(e)}"
        )


@router.get("/my-tickets", response_model=ApiResponse)
async def get_my_tickets(
    only_valid: bool = Query(True, description="只获取有效的预言券"),
    limit: int = Query(20, ge=1, le=100, description="限制数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        tickets = star_resonance_service.get_user_tickets(
            db=db,
            user_id=current_user.id,
            only_valid=only_valid
        )
        
        return ApiResponse(
            message="获取预言券成功",
            data={
                "tickets": tickets[:limit],
                "count": len(tickets),
                "only_valid": only_valid
            }
        )
        
    except Exception as e:
        logger.error(f"获取预言券失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取预言券失败: {str(e)}"
        )


@router.get("/recent-contributions", response_model=ApiResponse)
async def get_recent_contributions(
    limit: int = Query(20, ge=1, le=100, description="限制数量"),
    db: Session = Depends(get_db)
):
    try:
        contributions = star_resonance_service.get_recent_contributions(
            db=db,
            limit=limit
        )
        
        return ApiResponse(
            message="获取注入记录成功",
            data={
                "contributions": contributions,
                "count": len(contributions)
            }
        )
        
    except Exception as e:
        logger.error(f"获取注入记录失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取注入记录失败: {str(e)}"
        )


@router.get("/element-info", response_model=ApiResponse)
async def get_element_info():
    try:
        info = star_resonance_service.get_element_and_tier_info()
        
        return ApiResponse(
            message="获取元素信息成功",
            data={
                "elements": info.get("elements", {}),
                "tier_config": info.get("tier_config", {})
            }
        )
        
    except Exception as e:
        logger.error(f"获取元素信息失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取元素信息失败: {str(e)}"
        )


@router.post("/init-demo", response_model=ApiResponse)
async def init_demo_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        from app.models import (
            ResonancePoolSnapshot,
            ResonanceContribution,
            ProphecyTicket,
            StarDustTransaction
        )
        from sqlalchemy import text
        
        try:
            db.execute(text("SELECT 1 FROM resonance_pool_snapshots LIMIT 1"))
            db.commit()
        except Exception:
            db.rollback()
            try:
                db.execute(text("""
                    CREATE TABLE IF NOT EXISTS resonance_pool_snapshots (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        total_energy FLOAT DEFAULT 0.0,
                        current_tier VARCHAR(20) DEFAULT 'dormant',
                        tier_progress FLOAT DEFAULT 0.0,
                        element_distribution TEXT,
                        nebula_color VARCHAR(20) DEFAULT '#1F2937',
                        nebula_intensity FLOAT DEFAULT 0.1,
                        active_effects TEXT,
                        snapshot_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                db.execute(text("""
                    CREATE TABLE IF NOT EXISTS resonance_contributions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        element VARCHAR(20),
                        planet_name VARCHAR(50),
                        planet_sign VARCHAR(50),
                        fragment_cost INTEGER DEFAULT 0,
                        base_energy FLOAT DEFAULT 0.0,
                        total_energy FLOAT DEFAULT 0.0,
                        energy_multiplier FLOAT DEFAULT 1.0,
                        dignity_score INTEGER DEFAULT 0,
                        is_stellium BOOLEAN DEFAULT FALSE,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                db.execute(text("""
                    CREATE TABLE IF NOT EXISTS prophecy_tickets (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        ticket_type VARCHAR(50) DEFAULT 'resonance_reward',
                        source_snapshot_id INTEGER,
                        is_used BOOLEAN DEFAULT FALSE,
                        used_at DATETIME,
                        used_for VARCHAR(100),
                        valid_from DATETIME,
                        valid_until DATETIME,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                db.commit()
                logger.info("创建了共振池相关表")
            except Exception as create_err:
                logger.warning(f"创建表失败（可能已存在）: {create_err}")
                db.rollback()
        
        latest_snapshot = db.query(ResonancePoolSnapshot).order_by(
            ResonancePoolSnapshot.snapshot_at.desc()
        ).first()
        
        if not latest_snapshot:
            now = datetime.utcnow()
            element_dist = {
                "fire": 500.0,
                "earth": 300.0,
                "air": 400.0,
                "water": 350.0
            }
            total_energy = sum(element_dist.values())
            
            initial_snapshot = ResonancePoolSnapshot(
                total_energy=total_energy,
                current_tier="dormant",
                tier_progress=total_energy / 1000.0 if total_energy < 1000 else 1.0,
                element_distribution=json.dumps(element_dist, ensure_ascii=False),
                nebula_color="#1F2937",
                nebula_intensity=0.1,
                active_effects=json.dumps({
                    "fire": {"name": "火象", "energy": 500.0, "ratio": 32.26},
                    "earth": {"name": "土象", "energy": 300.0, "ratio": 19.35},
                    "air": {"name": "风象", "energy": 400.0, "ratio": 25.81},
                    "water": {"name": "水象", "energy": 350.0, "ratio": 22.58},
                    "dominant": "fire"
                }, ensure_ascii=False),
                snapshot_at=now,
                created_at=now
            )
            db.add(initial_snapshot)
            db.flush()
            
            demo_contributions = [
                {
                    "user_id": current_user.id,
                    "element": "fire",
                    "planet_name": "太阳",
                    "planet_sign": "狮子座",
                    "fragment_cost": 50,
                    "base_energy": 50.0,
                    "total_energy": 85.0,
                    "energy_multiplier": 1.7,
                    "dignity_score": 5,
                    "is_stellium": False,
                    "created_at": now - timedelta(hours=2)
                },
                {
                    "user_id": current_user.id,
                    "element": "water",
                    "planet_name": "月亮",
                    "planet_sign": "巨蟹座",
                    "fragment_cost": 30,
                    "base_energy": 30.0,
                    "total_energy": 54.0,
                    "energy_multiplier": 1.8,
                    "dignity_score": 5,
                    "is_stellium": False,
                    "created_at": now - timedelta(hours=1)
                }
            ]
            
            for contrib_data in demo_contributions:
                contrib = ResonanceContribution(
                    user_id=contrib_data["user_id"],
                    element=contrib_data["element"],
                    planet_name=contrib_data["planet_name"],
                    planet_sign=contrib_data["planet_sign"],
                    fragment_cost=contrib_data["fragment_cost"],
                    base_energy=contrib_data["base_energy"],
                    total_energy=contrib_data["total_energy"],
                    energy_multiplier=contrib_data["energy_multiplier"],
                    dignity_score=contrib_data["dignity_score"],
                    is_stellium=contrib_data["is_stellium"],
                    is_active=True,
                    created_at=contrib_data["created_at"]
                )
                db.add(contrib)
            
            db.flush()
            
            for i in range(3):
                ticket = ProphecyTicket(
                    user_id=current_user.id,
                    ticket_type="demo_initial",
                    source_snapshot_id=initial_snapshot.id,
                    is_used=False,
                    valid_from=now,
                    valid_until=now + timedelta(days=30),
                    created_at=now
                )
                db.add(ticket)
            
            db.commit()
            logger.info(f"为用户 {current_user.id} 创建了演示数据")
        
        if (current_user.stardust_fragment_balance or 0) < 500:
            balance_before = current_user.stardust_fragment_balance or 0
            current_user.stardust_fragment_balance = 1000
            
            transaction = StarDustTransaction(
                user_id=current_user.id,
                transaction_type="demo_reward",
                currency_type="fragment",
                amount=1000 - balance_before,
                balance_before=balance_before,
                balance_after=1000,
                description="演示初始奖励 - 星元碎片",
                created_at=datetime.utcnow()
            )
            db.add(transaction)
            db.commit()
        
        pool_status = star_resonance_service.get_pool_status(db)
        
        element_dist_dict = {}
        for elem_key, energy in pool_status.element_distribution.items():
            info = ELEMENT_INFO_SERIALIZABLE.get(elem_key, {})
            element_dist_dict[elem_key] = {
                "name": info.get("name_cn", ""),
                "energy": round(float(energy), 2),
                "color": info.get("color", "#1F2937"),
                "signs": info.get("signs", []),
                "effects": info.get("effects", {})
            }
        
        return ApiResponse(
            message="演示数据初始化成功！",
            data={
                "success": True,
                "message": "已为您初始化演示数据",
                "user_fragments": current_user.stardust_fragment_balance,
                "pool_status": {
                    "current_tier": pool_status.current_tier,
                    "current_tier_name": TIER_CONFIG_SERIALIZABLE.get(pool_status.current_tier, {}).get("name_cn", "未知"),
                    "current_energy": round(float(pool_status.current_energy), 2),
                    "tier_progress": round(float(pool_status.tier_progress), 4),
                    "element_distribution": element_dist_dict,
                    "nebula": {
                        "color": pool_status.nebula_color,
                        "intensity": float(pool_status.nebula_intensity)
                    }
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"初始化演示数据失败: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"初始化失败: {str(e)}"
        )


@router.post("/demo-contribute", response_model=ApiResponse)
async def demo_contribute(
    element: str = Query(..., description="元素类型: fire, earth, air, water"),
    fragment_amount: int = Query(20, ge=10, le=500, description="碎片数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        planet_map = {
            "fire": {"name": "太阳", "sign": "狮子座", "multiplier": 1.7, "dignity_score": 5},
            "earth": {"name": "金星", "sign": "金牛座", "multiplier": 1.5, "dignity_score": 5},
            "air": {"name": "水星", "sign": "双子座", "multiplier": 1.6, "dignity_score": 4},
            "water": {"name": "月亮", "sign": "巨蟹座", "multiplier": 1.8, "dignity_score": 5}
        }
        
        planet_info = planet_map.get(element, planet_map["fire"])
        
        from app.models import ResonancePoolSnapshot, ResonanceContribution, ProphecyTicket, StarDustTransaction
        from datetime import datetime, timedelta
        
        db.begin_nested()
        
        try:
            if (current_user.stardust_fragment_balance or 0) < fragment_amount:
                db.rollback()
                return ApiResponse(
                    message="星元碎片不足",
                    code=400,
                    data={"success": False, "error": f"当前余额: {current_user.stardust_fragment_balance or 0}"}
                )
            
            balance_before = current_user.stardust_fragment_balance or 0
            balance_after = balance_before - fragment_amount
            
            transaction = StarDustTransaction(
                user_id=current_user.id,
                transaction_type="demo_contribution",
                currency_type="fragment",
                amount=-fragment_amount,
                balance_before=balance_before,
                balance_after=balance_after,
                description=f"演示注入 - {planet_info['name']}在{planet_info['sign']}",
                created_at=datetime.utcnow()
            )
            db.add(transaction)
            
            current_user.stardust_fragment_balance = balance_after
            
            base_energy = float(fragment_amount)
            total_energy = base_energy * planet_info["multiplier"]
            
            latest_snapshot = db.query(ResonancePoolSnapshot).order_by(
                ResonancePoolSnapshot.snapshot_at.desc()
            ).with_for_update().first()
            
            if latest_snapshot:
                element_dist = json.loads(latest_snapshot.element_distribution) if latest_snapshot.element_distribution else {}
            else:
                element_dist = {"fire": 0.0, "earth": 0.0, "air": 0.0, "water": 0.0}
            
            element_dist[element] = float(element_dist.get(element, 0.0)) + total_energy
            total_energy_new = sum(element_dist.values())
            
            tier_order = ["dormant", "awakening", "glowing", "radiant", "transcendent"]
            tier_configs = TIER_CONFIG_SERIALIZABLE
            
            current_tier = "dormant"
            for tier in reversed(tier_order):
                config = tier_configs.get(tier, {})
                if total_energy_new >= config.get("min_energy", 0):
                    current_tier = tier
                    break
            
            current_config = tier_configs.get(current_tier, {})
            progress_min = current_config.get("min_energy", 0)
            progress_max = current_config.get("max_energy", 1000)
            tier_progress = 0.0
            if progress_max > progress_min:
                tier_progress = (total_energy_new - progress_min) / (progress_max - progress_min)
                tier_progress = min(max(tier_progress, 0.0), 1.0)
            
            nebula_color = "#1F2937"
            total = total_energy_new
            if total > 0:
                r_total = 0.0
                g_total = 0.0
                b_total = 0.0
                color_map = {
                    "fire": (239, 68, 68),
                    "earth": (132, 204, 22),
                    "air": (59, 130, 246),
                    "water": (139, 92, 246)
                }
                for elem, energy in element_dist.items():
                    if energy > 0:
                        ratio = energy / total
                        r, g, b = color_map.get(elem, (31, 41, 55))
                        r_total += r * ratio
                        g_total += g * ratio
                        b_total += b * ratio
                
                if r_total > 0 or g_total > 0 or b_total > 0:
                    final_r = int(round(r_total))
                    final_g = int(round(g_total))
                    final_b = int(round(b_total))
                    final_r = max(0, min(255, final_r))
                    final_g = max(0, min(255, final_g))
                    final_b = max(0, min(255, final_b))
                    nebula_color = f"#{final_r:02x}{final_g:02x}{final_b:02x}"
            
            now = datetime.utcnow()
            new_snapshot = ResonancePoolSnapshot(
                total_energy=total_energy_new,
                current_tier=current_tier,
                tier_progress=tier_progress,
                element_distribution=json.dumps(element_dist, ensure_ascii=False),
                nebula_color=nebula_color,
                nebula_intensity=current_config.get("nebula_intensity", 0.1),
                active_effects=json.dumps({}, ensure_ascii=False),
                snapshot_at=now,
                created_at=now
            )
            db.add(new_snapshot)
            db.flush()
            
            contribution = ResonanceContribution(
                user_id=current_user.id,
                element=element,
                planet_name=planet_info["name"],
                planet_sign=planet_info["sign"],
                fragment_cost=fragment_amount,
                base_energy=base_energy,
                total_energy=total_energy,
                energy_multiplier=planet_info["multiplier"],
                dignity_score=planet_info["dignity_score"],
                is_stellium=False,
                is_active=True,
                created_at=now
            )
            db.add(contribution)
            db.flush()
            
            tickets_awarded = 0
            prev_snapshot = db.query(ResonancePoolSnapshot).order_by(
                ResonancePoolSnapshot.snapshot_at.desc()
            ).offset(1).first()
            
            if prev_snapshot:
                try:
                    prev_idx = tier_order.index(prev_snapshot.current_tier)
                    current_idx = tier_order.index(current_tier)
                    
                    if current_idx > prev_idx:
                        for i in range(prev_idx + 1, current_idx + 1):
                            tier = tier_order[i]
                            config = tier_configs.get(tier, {})
                            ticket_count = config.get("ticket_reward", 0)
                            
                            if ticket_count > 0:
                                existing = db.query(ProphecyTicket).filter(
                                    ProphecyTicket.user_id == current_user.id,
                                    ProphecyTicket.source_snapshot_id == new_snapshot.id,
                                    ProphecyTicket.ticket_type == f"tier_{tier}"
                                ).first()
                                
                                if not existing:
                                    for _ in range(ticket_count):
                                        ticket = ProphecyTicket(
                                            user_id=current_user.id,
                                            ticket_type=f"tier_{tier}",
                                            source_snapshot_id=new_snapshot.id,
                                            is_used=False,
                                            valid_from=now,
                                            valid_until=now + timedelta(days=30),
                                            created_at=now
                                        )
                                        db.add(ticket)
                                    tickets_awarded += ticket_count
                except Exception as e:
                    logger.warning(f"发放预言券时出错: {e}")
            
            db.commit()
            
            elem_info = ELEMENT_INFO_SERIALIZABLE.get(element, {})
            
            return ApiResponse(
                message=f"能量注入成功！{f'获得 {tickets_awarded} 张预言券' if tickets_awarded > 0 else ''}",
                data={
                    "success": True,
                    "contribution": {
                        "element": element,
                        "element_name": elem_info.get("name_cn", ""),
                        "planet_name": planet_info["name"],
                        "planet_sign": planet_info["sign"],
                        "fragment_cost": fragment_amount,
                        "base_energy": round(base_energy, 2),
                        "total_energy": round(total_energy, 2),
                        "multiplier": planet_info["multiplier"]
                    },
                    "pool_status": {
                        "current_tier": current_tier,
                        "current_tier_name": current_config.get("name_cn", "未知"),
                        "current_energy": round(total_energy_new, 2),
                        "tier_progress": round(tier_progress, 4),
                        "element_distribution": element_dist,
                        "nebula": {
                            "color": nebula_color,
                            "intensity": current_config.get("nebula_intensity", 0.1)
                        }
                    },
                    "tickets_awarded": tickets_awarded,
                    "new_balance": balance_after
                }
            )
            
        except Exception as inner_err:
            db.rollback()
            raise inner_err
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"演示注入失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注入失败: {str(e)}"
        )


@router.get("/nebula-color", response_model=ApiResponse)
async def calculate_nebula_color(
    fire: float = Query(0.0, ge=0),
    earth: float = Query(0.0, ge=0),
    air: float = Query(0.0, ge=0),
    water: float = Query(0.0, ge=0)
):
    try:
        element_dist = {
            "fire": fire,
            "earth": earth,
            "air": air,
            "water": water
        }
        
        total = sum(element_dist.values())
        
        if total <= 0:
            return ApiResponse(
                message="无能量数据",
                data={
                    "color": "#1F2937",
                    "hex": "#1F2937",
                    "rgb": {"r": 31, "g": 41, "b": 55},
                    "element_ratios": {},
                    "dominant_element": None
                }
            )
        
        color_map = {
            "fire": (239, 68, 68),
            "earth": (132, 204, 22),
            "air": (59, 130, 246),
            "water": (139, 92, 246)
        }
        
        r_total = 0.0
        g_total = 0.0
        b_total = 0.0
        
        element_ratios = {}
        max_ratio = 0.0
        dominant_element = None
        
        for elem, energy in element_dist.items():
            if energy > 0:
                ratio = energy / total
                element_ratios[elem] = round(ratio * 100, 2)
                
                if ratio > max_ratio:
                    max_ratio = ratio
                    dominant_element = elem
                
                r, g, b = color_map.get(elem, (31, 41, 55))
                r_total += r * ratio
                g_total += g * ratio
                b_total += b * ratio
        
        final_r = int(round(r_total))
        final_g = int(round(g_total))
        final_b = int(round(b_total))
        
        final_r = max(0, min(255, final_r))
        final_g = max(0, min(255, final_g))
        final_b = max(0, min(255, final_b))
        
        hex_color = f"#{final_r:02x}{final_g:02x}{final_b:02x}"
        
        return ApiResponse(
            message="计算星云颜色成功",
            data={
                "color": hex_color,
                "hex": hex_color,
                "rgb": {"r": final_r, "g": final_g, "b": final_b},
                "element_ratios": element_ratios,
                "dominant_element": dominant_element,
                "dominant_element_name": ELEMENT_INFO_SERIALIZABLE.get(dominant_element, {}).get("name_cn") if dominant_element else None,
                "total_energy": total
            }
        )
        
    except Exception as e:
        logger.error(f"计算星云颜色失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"计算失败: {str(e)}"
        )
