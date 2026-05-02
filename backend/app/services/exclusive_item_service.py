import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.models import (
    User,
    ExclusiveItem,
    UserInventory,
    StarDustTransaction,
    ResonanceContribution,
    Avatar,
    AvatarInventory
)

logger = logging.getLogger(__name__)


class ItemType(str, Enum):
    PENDANT = "pendant"
    FRAME = "frame"
    EFFECT = "effect"
    TITLE = "title"
    BOOSTER = "booster"


class ItemRarity(str, Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


RARITY_CONFIG = {
    ItemRarity.COMMON: {
        "name": "普通",
        "color": "#9CA3AF",
        "glow_color": "#D1D5DB"
    },
    ItemRarity.UNCOMMON: {
        "name": "优秀",
        "color": "#10B981",
        "glow_color": "#6EE7B7"
    },
    ItemRarity.RARE: {
        "name": "稀有",
        "color": "#3B82F6",
        "glow_color": "#93C5FD"
    },
    ItemRarity.EPIC: {
        "name": "史诗",
        "color": "#8B5CF6",
        "glow_color": "#C4B5FD"
    },
    ItemRarity.LEGENDARY: {
        "name": "传说",
        "color": "#F59E0B",
        "glow_color": "#FCD34D"
    }
}


DEFAULT_EXCLUSIVE_ITEMS = [
    {
        "item_key": "pendant_fire_essence",
        "item_name": "火象精华挂坠",
        "item_type": ItemType.PENDANT,
        "description": "蕴含火象星座能量的神秘挂坠，佩戴后可提升炼化时火象行星的能量加成",
        "rarity": ItemRarity.RARE,
        "cost_points": 500,
        "cost_fragments": 0,
        "effect_type": "energy_bonus",
        "effect_data": json.dumps({
            "element": "fire",
            "energy_multiplier_bonus": 0.2,
            "description": "火象行星炼化能量 +20%"
        }),
        "energy_weight_bonus": 0.1
    },
    {
        "item_key": "pendant_earth_essence",
        "item_name": "土象精华挂坠",
        "item_type": ItemType.PENDANT,
        "description": "蕴含土象星座能量的神秘挂坠，佩戴后可提升炼化时土象行星的能量加成",
        "rarity": ItemRarity.RARE,
        "cost_points": 500,
        "cost_fragments": 0,
        "effect_type": "energy_bonus",
        "effect_data": json.dumps({
            "element": "earth",
            "energy_multiplier_bonus": 0.2,
            "description": "土象行星炼化能量 +20%"
        }),
        "energy_weight_bonus": 0.1
    },
    {
        "item_key": "pendant_air_essence",
        "item_name": "风象精华挂坠",
        "item_type": ItemType.PENDANT,
        "description": "蕴含风象星座能量的神秘挂坠，佩戴后可提升炼化时风象行星的能量加成",
        "rarity": ItemRarity.RARE,
        "cost_points": 500,
        "cost_fragments": 0,
        "effect_type": "energy_bonus",
        "effect_data": json.dumps({
            "element": "air",
            "energy_multiplier_bonus": 0.2,
            "description": "风象行星炼化能量 +20%"
        }),
        "energy_weight_bonus": 0.1
    },
    {
        "item_key": "pendant_water_essence",
        "item_name": "水象精华挂坠",
        "item_type": ItemType.PENDANT,
        "description": "蕴含水象星座能量的神秘挂坠，佩戴后可提升炼化时水象行星的能量加成",
        "rarity": ItemRarity.RARE,
        "cost_points": 500,
        "cost_fragments": 0,
        "effect_type": "energy_bonus",
        "effect_data": json.dumps({
            "element": "water",
            "energy_multiplier_bonus": 0.2,
            "description": "水象行星炼化能量 +20%"
        }),
        "energy_weight_bonus": 0.1
    },
    {
        "item_key": "frame_golden_aura",
        "item_name": "金色光环头像框",
        "item_type": ItemType.FRAME,
        "description": "闪耀着金色光芒的专属头像框，彰显尊贵身份",
        "rarity": ItemRarity.EPIC,
        "cost_points": 1000,
        "cost_fragments": 0,
        "effect_type": "cosmetic",
        "effect_data": json.dumps({
            "frame_color": "#F59E0B",
            "glow_effect": "pulse",
            "description": "金色光环特效"
        }),
        "energy_weight_bonus": 0.05
    },
    {
        "item_key": "frame_cosmic_nebula",
        "item_name": "宇宙星云头像框",
        "item_type": ItemType.FRAME,
        "description": "深邃宇宙星云特效头像框，如梦似幻",
        "rarity": ItemRarity.LEGENDARY,
        "cost_points": 2500,
        "cost_fragments": 0,
        "effect_type": "cosmetic",
        "effect_data": json.dumps({
            "frame_color": "#8B5CF6",
            "glow_effect": "nebula_rotate",
            "description": "宇宙星云旋转特效"
        }),
        "energy_weight_bonus": 0.15
    },
    {
        "item_key": "title_star_master",
        "item_name": "星象大师称号",
        "item_type": ItemType.TITLE,
        "description": "获得「星象大师」专属称号，展示于个人资料页",
        "rarity": ItemRarity.EPIC,
        "cost_points": 800,
        "cost_fragments": 0,
        "effect_type": "cosmetic",
        "effect_data": json.dumps({
            "title_text": "星象大师",
            "title_color": "#3B82F6",
            "description": "专属称号展示"
        }),
        "energy_weight_bonus": 0.0
    },
    {
        "item_key": "booster_daily_double",
        "item_name": "每日双倍能量卡",
        "item_type": ItemType.BOOSTER,
        "description": "使用后当天第一次炼化可获得双倍能量",
        "rarity": ItemRarity.UNCOMMON,
        "cost_points": 200,
        "cost_fragments": 0,
        "effect_type": "temporary_boost",
        "effect_data": json.dumps({
            "boost_type": "double_energy",
            "duration_type": "daily",
            "uses_remaining": 1,
            "description": "单次双倍能量加成"
        }),
        "energy_weight_bonus": 0.0,
        "is_limited": True,
        "max_per_user": 5
    },
    {
        "item_key": "pendant_cosmic_core",
        "item_name": "宇宙核心挂坠",
        "item_type": ItemType.PENDANT,
        "description": "传说级挂坠，蕴含宇宙原始能量，所有元素炼化均获得额外加成",
        "rarity": ItemRarity.LEGENDARY,
        "cost_points": 5000,
        "cost_fragments": 0,
        "effect_type": "universal_energy_bonus",
        "effect_data": json.dumps({
            "element": "all",
            "energy_multiplier_bonus": 0.3,
            "description": "所有元素炼化能量 +30%"
        }),
        "energy_weight_bonus": 0.25
    }
]


class ExclusiveItemService:
    """
    专属物品服务
    
    核心功能：
    - 高阶星尘兑换专属物品
    - 物品库存管理
    - 物品效果应用
    - 能量场权重加成
    """
    
    _instance: Optional['ExclusiveItemService'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def initialize_default_items(self, db: Session) -> List[Dict[str, Any]]:
        """
        初始化默认专属物品
        """
        created_items = []
        
        for item_data in DEFAULT_EXCLUSIVE_ITEMS:
            existing = db.query(ExclusiveItem).filter(
                ExclusiveItem.item_key == item_data["item_key"]
            ).first()
            
            if existing:
                created_items.append(self._item_to_dict(existing))
                continue
            
            item = ExclusiveItem(
                item_key=item_data["item_key"],
                item_name=item_data["item_name"],
                item_type=item_data["item_type"],
                description=item_data["description"],
                rarity=item_data["rarity"],
                cost_points=item_data["cost_points"],
                cost_fragments=item_data["cost_fragments"],
                effect_type=item_data["effect_type"],
                effect_data=item_data.get("effect_data"),
                energy_weight_bonus=item_data.get("energy_weight_bonus", 0.0),
                is_active=True,
                is_limited=item_data.get("is_limited", False),
                stock_remaining=item_data.get("stock_remaining"),
                max_per_user=item_data.get("max_per_user", 1),
                available_from=item_data.get("available_from"),
                available_until=item_data.get("available_until")
            )
            
            db.add(item)
            db.commit()
            db.refresh(item)
            
            created_items.append(self._item_to_dict(item))
            logger.info(f"创建默认物品: {item_data['item_key']}")
        
        return created_items
    
    def get_available_items(self, db: Session, item_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取可兑换的物品列表
        """
        now = datetime.utcnow()
        
        query = db.query(ExclusiveItem).filter(
            ExclusiveItem.is_active == True
        )
        
        if item_type:
            query = query.filter(ExclusiveItem.item_type == item_type)
        
        query = query.filter(
            or_(
                ExclusiveItem.available_from == None,
                ExclusiveItem.available_from <= now
            ),
            or_(
                ExclusiveItem.available_until == None,
                ExclusiveItem.available_until > now
            )
        )
        
        items = query.order_by(
            ExclusiveItem.rarity.desc(),
            ExclusiveItem.cost_points.asc()
        ).all()
        
        return [self._item_to_dict(item) for item in items]
    
    def get_item_detail(self, db: Session, item_id: int) -> Optional[Dict[str, Any]]:
        """
        获取物品详情
        """
        item = db.query(ExclusiveItem).filter(
            ExclusiveItem.id == item_id
        ).first()
        
        if not item:
            return None
        
        return self._item_to_dict(item)
    
    def purchase_item(
        self,
        db: Session,
        user_id: int,
        item_id: int,
        use_currency: str = "point"
    ) -> Dict[str, Any]:
        """
        购买/兑换物品
        
        支持使用高阶星尘（point）或星元碎片（fragment）购买
        """
        item = db.query(ExclusiveItem).filter(
            ExclusiveItem.id == item_id
        ).first()
        
        if not item:
            return {
                "success": False,
                "error_code": "ITEM_NOT_FOUND",
                "error": "物品不存在"
            }
        
        if not item.is_active:
            return {
                "success": False,
                "error_code": "ITEM_INACTIVE",
                "error": "物品已下架"
            }
        
        now = datetime.utcnow()
        
        if item.available_from and item.available_from > now:
            return {
                "success": False,
                "error_code": "NOT_AVAILABLE_YET",
                "error": "物品尚未开放兑换"
            }
        
        if item.available_until and item.available_until <= now:
            return {
                "success": False,
                "error_code": "EXPIRED",
                "error": "物品已过期"
            }
        
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return {
                "success": False,
                "error_code": "USER_NOT_FOUND",
                "error": "用户不存在"
            }
        
        user_owned_count = db.query(func.count(UserInventory.id)).filter(
            UserInventory.user_id == user_id,
            UserInventory.item_id == item_id
        ).scalar() or 0
        
        max_per_user = item.max_per_user or 1
        if user_owned_count >= max_per_user:
            return {
                "success": False,
                "error_code": "MAX_LIMIT_EXCEEDED",
                "error": f"已达到购买上限 ({max_per_user}个)"
            }
        
        if item.is_limited and item.stock_remaining is not None and item.stock_remaining <= 0:
            return {
                "success": False,
                "error_code": "OUT_OF_STOCK",
                "error": "物品已售罄"
            }
        
        if use_currency == "point":
            cost = item.cost_points or 0
            balance = user.stardust_point_balance or 0
            currency_type = "point"
        elif use_currency == "fragment":
            cost = item.cost_fragments or 0
            balance = user.stardust_fragment_balance or 0
            currency_type = "fragment"
        else:
            return {
                "success": False,
                "error_code": "INVALID_CURRENCY",
                "error": "不支持的支付方式"
            }
        
        if cost <= 0:
            return {
                "success": False,
                "error_code": "FREE_ITEM",
                "error": "该物品暂不支持兑换"
            }
        
        if balance < cost:
            currency_name = "高阶星尘" if use_currency == "point" else "星元碎片"
            return {
                "success": False,
                "error_code": "INSUFFICIENT_BALANCE",
                "error": f"{currency_name}不足，需要 {cost}，当前 {balance}"
            }
        
        db.begin_nested()
        
        try:
            if use_currency == "point":
                user.stardust_point_balance = balance - cost
            else:
                user.stardust_fragment_balance = balance - cost
            
            transaction = StarDustTransaction(
                user_id=user_id,
                transaction_type="item_purchase",
                currency_type=currency_type,
                amount=-cost,
                balance_before=balance,
                balance_after=balance - cost,
                related_type="item",
                related_id=str(item_id),
                description=f"兑换物品: {item.item_name}",
                created_at=now
            )
            db.add(transaction)
            
            inventory = UserInventory(
                user_id=user_id,
                item_id=item_id,
                quantity=1,
                is_equipped=False,
                acquired_at=now,
                acquired_source="purchase",
                cost_points_spent=item.cost_points if use_currency == "point" else 0,
                cost_fragments_spent=item.cost_fragments if use_currency == "fragment" else 0
            )
            
            if item.item_type == ItemType.BOOSTER:
                effect_data = json.loads(item.effect_data) if item.effect_data else {}
                uses_remaining = effect_data.get("uses_remaining", 1)
                inventory.expires_at = now + timedelta(days=30)
            
            db.add(inventory)
            
            if item.is_limited and item.stock_remaining is not None:
                item.stock_remaining -= 1
            
            db.commit()
            db.refresh(inventory)
            
            logger.info(f"用户 {user_id} 兑换物品: {item.item_key}, 花费: {cost} {currency_type}")
            
            return {
                "success": True,
                "message": "兑换成功！",
                "inventory": self._inventory_to_dict(inventory, item),
                "transaction": {
                    "id": transaction.id,
                    "amount": cost,
                    "currency_type": currency_type,
                    "description": transaction.description
                }
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"兑换物品失败: {e}")
            return {
                "success": False,
                "error_code": "PURCHASE_FAILED",
                "error": str(e)
            }
    
    def get_user_inventory(
        self,
        db: Session,
        user_id: int,
        item_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取用户物品库存
        """
        query = db.query(UserInventory).options(
            joinedload(UserInventory.item)
        ).filter(
            UserInventory.user_id == user_id
        )
        
        if item_type:
            query = query.join(ExclusiveItem).filter(
                ExclusiveItem.item_type == item_type
            )
        
        inventory_items = query.order_by(
            UserInventory.acquired_at.desc()
        ).all()
        
        result = []
        for inv in inventory_items:
            item = db.query(ExclusiveItem).filter(
                ExclusiveItem.id == inv.item_id
            ).first()
            if item:
                result.append(self._inventory_to_dict(inv, item))
        
        return result
    
    def equip_item(
        self,
        db: Session,
        user_id: int,
        inventory_id: int
    ) -> Dict[str, Any]:
        """
        装备/使用物品
        """
        inventory = db.query(UserInventory).filter(
            UserInventory.id == inventory_id,
            UserInventory.user_id == user_id
        ).first()
        
        if not inventory:
            return {
                "success": False,
                "error_code": "INVENTORY_NOT_FOUND",
                "error": "物品不存在"
            }
        
        item = db.query(ExclusiveItem).filter(
            ExclusiveItem.id == inventory.item_id
        ).first()
        
        if not item:
            return {
                "success": False,
                "error_code": "ITEM_NOT_FOUND",
                "error": "物品不存在"
            }
        
        if item.item_type == ItemType.BOOSTER:
            return self._use_booster_item(db, user_id, inventory, item)
        
        db.begin_nested()
        
        try:
            if item.item_type in [ItemType.PENDANT, ItemType.FRAME]:
                existing_equipped = db.query(UserInventory).filter(
                    UserInventory.user_id == user_id,
                    UserInventory.is_equipped == True
                ).join(ExclusiveItem).filter(
                    ExclusiveItem.item_type == item.item_type
                ).all()
                
                for eq in existing_equipped:
                    eq.is_equipped = False
            
            inventory.is_equipped = True
            inventory.equipped_at = datetime.utcnow()
            
            db.commit()
            db.refresh(inventory)
            
            return {
                "success": True,
                "message": f"已装备: {item.item_name}",
                "inventory": self._inventory_to_dict(inventory, item)
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"装备物品失败: {e}")
            return {
                "success": False,
                "error_code": "EQUIP_FAILED",
                "error": str(e)
            }
    
    def _use_booster_item(
        self,
        db: Session,
        user_id: int,
        inventory: UserInventory,
        item: ExclusiveItem
    ) -> Dict[str, Any]:
        """
        使用消耗型道具
        """
        effect_data = json.loads(item.effect_data) if item.effect_data else {}
        boost_type = effect_data.get("boost_type")
        
        if boost_type == "double_energy":
            inventory.quantity -= 1
            
            if inventory.quantity <= 0:
                inventory.is_equipped = False
                db.delete(inventory)
            else:
                inventory.is_equipped = True
                inventory.equipped_at = datetime.utcnow()
            
            db.commit()
            
            return {
                "success": True,
                "message": "已激活双倍能量卡，下次炼化将获得双倍能量！",
                "boost_active": True,
                "inventory": self._inventory_to_dict(inventory, item) if inventory.quantity > 0 else None
            }
        
        return {
            "success": False,
            "error_code": "UNKNOWN_BOOSTER",
            "error": "未知的道具类型"
        }
    
    def unequip_item(
        self,
        db: Session,
        user_id: int,
        inventory_id: int
    ) -> Dict[str, Any]:
        """
        卸下物品
        """
        inventory = db.query(UserInventory).filter(
            UserInventory.id == inventory_id,
            UserInventory.user_id == user_id
        ).first()
        
        if not inventory:
            return {
                "success": False,
                "error_code": "INVENTORY_NOT_FOUND",
                "error": "物品不存在"
            }
        
        item = db.query(ExclusiveItem).filter(
            ExclusiveItem.id == inventory.item_id
        ).first()
        
        inventory.is_equipped = False
        
        db.commit()
        db.refresh(inventory)
        
        return {
            "success": True,
            "message": f"已卸下: {item.item_name if item else ''}",
            "inventory": self._inventory_to_dict(inventory, item)
        }
    
    def get_user_equipped_bonuses(
        self,
        db: Session,
        user_id: int
    ) -> Dict[str, Any]:
        """
        获取用户当前装备的物品加成效果
        
        用于计算炼化时的能量加成和权重加成
        """
        equipped_items = db.query(UserInventory).filter(
            UserInventory.user_id == user_id,
            UserInventory.is_equipped == True
        ).all()
        
        total_weight_bonus = 0.0
        element_bonuses = {}
        universal_bonus = 0.0
        
        item_details = []
        
        for inv in equipped_items:
            item = db.query(ExclusiveItem).filter(
                ExclusiveItem.id == inv.item_id
            ).first()
            
            if not item:
                continue
            
            total_weight_bonus += item.energy_weight_bonus or 0.0
            
            effect_data = json.loads(item.effect_data) if item.effect_data else {}
            
            if item.effect_type == "energy_bonus":
                element = effect_data.get("element")
                bonus = effect_data.get("energy_multiplier_bonus", 0.0)
                if element:
                    element_bonuses[element] = element_bonuses.get(element, 0.0) + bonus
            
            elif item.effect_type == "universal_energy_bonus":
                bonus = effect_data.get("energy_multiplier_bonus", 0.0)
                universal_bonus += bonus
            
            item_details.append({
                "item_key": item.item_key,
                "item_name": item.item_name,
                "item_type": item.item_type,
                "rarity": item.rarity,
                "weight_bonus": item.energy_weight_bonus,
                "effects": effect_data
            })
        
        return {
            "total_weight_bonus": round(total_weight_bonus, 4),
            "element_bonuses": element_bonuses,
            "universal_bonus": round(universal_bonus, 4),
            "equipped_items": item_details
        }
    
    def get_user_energy_weight(
        self,
        db: Session,
        user_id: int
    ) -> float:
        """
        获取用户的能量场权重
        
        基础权重 1.0 + 装备物品加成
        """
        base_weight = 1.0
        
        bonuses = self.get_user_equipped_bonuses(db, user_id)
        total_weight = base_weight + bonuses["total_weight_bonus"]
        
        return round(total_weight, 4)
    
    def calculate_refine_energy_bonus(
        self,
        db: Session,
        user_id: int,
        element: str
    ) -> float:
        """
        计算炼化时的能量加成
        
        基于用户装备的物品计算额外能量倍数
        """
        bonuses = self.get_user_equipped_bonuses(db, user_id)
        
        total_bonus = bonuses["universal_bonus"]
        
        if element in bonuses["element_bonuses"]:
            total_bonus += bonuses["element_bonuses"][element]
        
        return round(1.0 + total_bonus, 4)
    
    def _item_to_dict(self, item: ExclusiveItem) -> Dict[str, Any]:
        rarity_config = RARITY_CONFIG.get(item.rarity, RARITY_CONFIG[ItemRarity.COMMON])
        
        return {
            "id": item.id,
            "item_key": item.item_key,
            "item_name": item.item_name,
            "item_type": item.item_type,
            "description": item.description,
            "rarity": item.rarity,
            "rarity_name": rarity_config["name"],
            "rarity_color": rarity_config["color"],
            "rarity_glow_color": rarity_config["glow_color"],
            "cost_points": item.cost_points or 0,
            "cost_fragments": item.cost_fragments or 0,
            "effect_type": item.effect_type,
            "effect_data": json.loads(item.effect_data) if item.effect_data else {},
            "energy_weight_bonus": item.energy_weight_bonus or 0.0,
            "is_active": item.is_active,
            "is_limited": item.is_limited,
            "stock_remaining": item.stock_remaining,
            "max_per_user": item.max_per_user,
            "available_from": item.available_from.isoformat() if item.available_from else None,
            "available_until": item.available_until.isoformat() if item.available_until else None,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "updated_at": item.updated_at.isoformat() if item.updated_at else None
        }
    
    def _inventory_to_dict(self, inv: UserInventory, item: Optional[ExclusiveItem] = None) -> Dict[str, Any]:
        result = {
            "id": inv.id,
            "user_id": inv.user_id,
            "item_id": inv.item_id,
            "quantity": inv.quantity,
            "is_equipped": inv.is_equipped,
            "equipped_at": inv.equipped_at.isoformat() if inv.equipped_at else None,
            "acquired_at": inv.acquired_at.isoformat() if inv.acquired_at else None,
            "acquired_source": inv.acquired_source,
            "cost_points_spent": inv.cost_points_spent or 0,
            "cost_fragments_spent": inv.cost_fragments_spent or 0,
            "expires_at": inv.expires_at.isoformat() if inv.expires_at else None
        }
        
        if item:
            result["item"] = self._item_to_dict(item)
        
        return result


exclusive_item_service = ExclusiveItemService()


def get_exclusive_item_service() -> ExclusiveItemService:
    return exclusive_item_service
