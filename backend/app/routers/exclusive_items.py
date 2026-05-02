from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from app.schemas import ApiResponse
from app.database import get_db
from app.models import (
    User,
    ExclusiveItem,
    UserInventory,
)
from app.routers.users import get_current_user, get_current_user_optional
from app.services.exclusive_item_service import (
    get_exclusive_item_service,
    ExclusiveItemService,
    ItemType,
    ItemRarity,
    RARITY_CONFIG
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["专属物品商城"])


class PurchaseItemRequest(BaseModel):
    item_id: int = Field(..., description="物品ID")
    use_currency: str = Field("point", description="使用的货币: point(高阶星尘), fragment(星元碎片)")


@router.get("/items", response_model=ApiResponse)
async def get_available_items(
    item_type: Optional[str] = Query(None, description="物品类型: pendant, frame, effect, title, booster"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    获取可兑换的物品列表
    
    物品类型：
    - pendant: 挂坠
    - frame: 头像框
    - effect: 特效
    - title: 称号
    - booster: 增益道具
    """
    try:
        service = get_exclusive_item_service()
        items = service.get_available_items(db, item_type)
        
        user_assets = None
        if current_user:
            user_assets = {
                "stardust_point_balance": current_user.stardust_point_balance or 0,
                "stardust_fragment_balance": current_user.stardust_fragment_balance or 0
            }
        
        return ApiResponse(
            message="获取物品列表成功",
            data={
                "items": items,
                "count": len(items),
                "item_type_filter": item_type,
                "user_assets": user_assets,
                "rarity_config": RARITY_CONFIG
            }
        )
        
    except Exception as e:
        logger.error(f"获取物品列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取物品列表失败: {str(e)}"
        )


@router.get("/items/init", response_model=ApiResponse)
async def initialize_default_items(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    初始化默认物品（管理员操作）
    """
    try:
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="仅管理员可执行此操作"
            )
        
        service = get_exclusive_item_service()
        items = service.initialize_default_items(db)
        
        return ApiResponse(
            message=f"初始化默认物品成功，共 {len(items)} 个",
            data={
                "items": items,
                "count": len(items)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"初始化默认物品失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"初始化失败: {str(e)}"
        )


@router.get("/items/{item_id}", response_model=ApiResponse)
async def get_item_detail(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    获取物品详情
    """
    try:
        service = get_exclusive_item_service()
        item = service.get_item_detail(db, item_id)
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="物品不存在"
            )
        
        user_owned = None
        if current_user:
            user_inventory = db.query(UserInventory).filter(
                UserInventory.user_id == current_user.id,
                UserInventory.item_id == item_id
            ).first()
            
            if user_inventory:
                user_owned = {
                    "id": user_inventory.id,
                    "quantity": user_inventory.quantity,
                    "is_equipped": user_inventory.is_equipped,
                    "equipped_at": user_inventory.equipped_at.isoformat() if user_inventory.equipped_at else None,
                    "acquired_at": user_inventory.acquired_at.isoformat() if user_inventory.acquired_at else None
                }
        
        return ApiResponse(
            message="获取物品详情成功",
            data={
                "item": item,
                "user_owned": user_owned
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取物品详情失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取物品详情失败: {str(e)}"
        )


@router.post("/items/purchase", response_model=ApiResponse)
async def purchase_item(
    request: PurchaseItemRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    购买/兑换物品
    
    支持使用：
    - point: 高阶星尘（推荐）
    - fragment: 星元碎片
    
    高阶星尘可通过竞猜奖励获得，形成经济闭环
    """
    try:
        service = get_exclusive_item_service()
        
        result = service.purchase_item(
            db=db,
            user_id=current_user.id,
            item_id=request.item_id,
            use_currency=request.use_currency
        )
        
        if not result.get("success"):
            return ApiResponse(
                message=result.get("error", "购买失败"),
                code=400,
                data={
                    "success": False,
                    "error_code": result.get("error_code"),
                    "error": result.get("error")
                }
            )
        
        db.refresh(current_user)
        
        return ApiResponse(
            message=result.get("message", "购买成功！"),
            data={
                "success": True,
                "inventory": result.get("inventory"),
                "transaction": result.get("transaction"),
                "new_balance": {
                    "stardust_point_balance": current_user.stardust_point_balance or 0,
                    "stardust_fragment_balance": current_user.stardust_fragment_balance or 0
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"购买物品失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"购买失败: {str(e)}"
        )


@router.get("/my-inventory", response_model=ApiResponse)
async def get_my_inventory(
    item_type: Optional[str] = Query(None, description="物品类型过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取我的物品库存
    """
    try:
        service = get_exclusive_item_service()
        inventory = service.get_user_inventory(db, current_user.id, item_type)
        
        equipped_count = sum(1 for item in inventory if item.get("is_equipped"))
        
        return ApiResponse(
            message="获取库存成功",
            data={
                "inventory": inventory,
                "count": len(inventory),
                "equipped_count": equipped_count,
                "item_type_filter": item_type
            }
        )
        
    except Exception as e:
        logger.error(f"获取库存失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取库存失败: {str(e)}"
        )


@router.post("/my-inventory/equip/{inventory_id}", response_model=ApiResponse)
async def equip_item(
    inventory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    装备/使用物品
    
    挂坠和头像框会自动卸下同类型已装备的物品
    增益道具使用后会消耗
    """
    try:
        service = get_exclusive_item_service()
        result = service.equip_item(db, current_user.id, inventory_id)
        
        if not result.get("success"):
            return ApiResponse(
                message=result.get("error", "装备失败"),
                code=400,
                data={
                    "success": False,
                    "error_code": result.get("error_code"),
                    "error": result.get("error")
                }
            )
        
        return ApiResponse(
            message=result.get("message", "装备成功！"),
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"装备物品失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"装备失败: {str(e)}"
        )


@router.post("/my-inventory/unequip/{inventory_id}", response_model=ApiResponse)
async def unequip_item(
    inventory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    卸下物品
    """
    try:
        service = get_exclusive_item_service()
        result = service.unequip_item(db, current_user.id, inventory_id)
        
        if not result.get("success"):
            return ApiResponse(
                message=result.get("error", "卸下失败"),
                code=400,
                data={
                    "success": False,
                    "error_code": result.get("error_code"),
                    "error": result.get("error")
                }
            )
        
        return ApiResponse(
            message=result.get("message", "卸下成功！"),
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"卸下物品失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"卸下失败: {str(e)}"
        )


@router.get("/my-bonuses", response_model=ApiResponse)
async def get_my_equipped_bonuses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取我的装备加成效果
    
    包括：
    - 总能量场权重加成
    - 各元素炼化加成
    - 通用炼化加成
    - 已装备物品详情
    """
    try:
        service = get_exclusive_item_service()
        bonuses = service.get_user_equipped_bonuses(db, current_user.id)
        energy_weight = service.get_user_energy_weight(db, current_user.id)
        
        return ApiResponse(
            message="获取装备加成成功",
            data={
                "base_energy_weight": 1.0,
                "total_energy_weight": energy_weight,
                "weight_bonus": energy_weight - 1.0,
                "element_bonuses": bonuses["element_bonuses"],
                "universal_bonus": bonuses["universal_bonus"],
                "equipped_items": bonuses["equipped_items"],
                "equipped_count": len(bonuses["equipped_items"])
            }
        )
        
    except Exception as e:
        logger.error(f"获取装备加成失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取装备加成失败: {str(e)}"
        )


@router.get("/calculate-refine-bonus", response_model=ApiResponse)
async def calculate_refine_bonus(
    element: str = Query(..., description="元素类型: fire, earth, air, water"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    计算炼化时的能量加成
    
    基于用户装备的物品计算额外能量倍数
    """
    try:
        service = get_exclusive_item_service()
        bonus_multiplier = service.calculate_refine_energy_bonus(db, current_user.id, element)
        
        element_names = {
            "fire": "火象",
            "earth": "土象",
            "air": "风象",
            "water": "水象"
        }
        
        return ApiResponse(
            message=f"计算 {element_names.get(element, element)} 炼化加成成功",
            data={
                "element": element,
                "element_name": element_names.get(element, element),
                "base_multiplier": 1.0,
                "bonus_multiplier": bonus_multiplier,
                "total_bonus": bonus_multiplier - 1.0,
                "example": {
                    "base_energy": 100,
                    "energy_with_bonus": 100 * bonus_multiplier,
                    "bonus_energy": 100 * (bonus_multiplier - 1.0)
                }
            }
        )
        
    except Exception as e:
        logger.error(f"计算炼化加成失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"计算炼化加成失败: {str(e)}"
        )


@router.get("/economy-overview", response_model=ApiResponse)
async def get_economy_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取经济系统概览
    
    展示完整的经济闭环：
    1. 我的资产（高阶星尘、星元碎片、预言券）
    2. 我的装备加成
    3. 资产获取途径说明
    4. 资产使用场景说明
    """
    try:
        from app.models import ProphecyTicket
        from sqlalchemy import func
        from datetime import datetime
        
        valid_tickets = db.query(func.count(ProphecyTicket.id)).filter(
            ProphecyTicket.user_id == current_user.id,
            ProphecyTicket.is_used == False,
            ProphecyTicket.valid_until > datetime.utcnow()
        ).scalar() or 0
        
        service = get_exclusive_item_service()
        bonuses = service.get_user_equipped_bonuses(db, current_user.id)
        energy_weight = service.get_user_energy_weight(db, current_user.id)
        
        return ApiResponse(
            message="获取经济系统概览成功",
            data={
                "my_assets": {
                    "stardust_point": {
                        "name": "高阶星尘",
                        "balance": current_user.stardust_point_balance or 0,
                        "description": "可兑换专属挂件、头像框等稀有物品",
                        "acquisition_methods": [
                            "竞猜获胜奖励",
                            "特殊活动奖励",
                            "成就达成"
                        ],
                        "usage_scenarios": [
                            "兑换专属挂坠",
                            "兑换头像框",
                            "兑换称号",
                            "购买增益道具"
                        ]
                    },
                    "stardust_fragment": {
                        "name": "星元碎片",
                        "balance": current_user.stardust_fragment_balance or 0,
                        "description": "用于星能共鸣池炼化、日常任务",
                        "acquisition_methods": [
                            "每日任务",
                            "能量气象站任务",
                            "竞猜奖励",
                            "广场互动"
                        ],
                        "usage_scenarios": [
                            "星能共鸣池炼化",
                            "额外投票次数",
                            "部分物品兑换"
                        ]
                    },
                    "prophecy_ticket": {
                        "name": "预言券",
                        "balance": valid_tickets,
                        "description": "用于特殊竞猜场次",
                        "acquisition_methods": [
                            "共鸣池升级奖励",
                            "特殊竞猜奖励"
                        ],
                        "usage_scenarios": [
                            "特殊场次投票",
                            "高级竞猜参与"
                        ]
                    }
                },
                "current_bonuses": {
                    "energy_weight": energy_weight,
                    "weight_bonus": energy_weight - 1.0,
                    "element_bonuses": bonuses["element_bonuses"],
                    "universal_bonus": bonuses["universal_bonus"],
                    "equipped_count": len(bonuses["equipped_items"])
                },
                "economy_loop": {
                    "description": "站内经济闭环",
                    "steps": [
                        {
                            "step": 1,
                            "action": "参与竞猜",
                            "reward": "获得高阶星尘奖励"
                        },
                        {
                            "step": 2,
                            "action": "使用高阶星尘",
                            "result": "兑换专属挂坠、头像框"
                        },
                        {
                            "step": 3,
                            "action": "装备物品",
                            "effect": "获得炼化能量加成、权重加成"
                        },
                        {
                            "step": 4,
                            "action": "炼化注入",
                            "result": "提升共鸣池等级，获得更多预言券"
                        },
                        {
                            "step": 5,
                            "action": "使用预言券",
                            "result": "参与更多竞猜，形成闭环"
                        }
                    ]
                }
            }
        )
        
    except Exception as e:
        logger.error(f"获取经济概览失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取经济概览失败: {str(e)}"
        )
