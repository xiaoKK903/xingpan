"""
前世故事 - 数据服务（记录管理、分页、分享）

修复内容:
1. 假分页: 返回真实的total计数
2. 并发计数: 使用数据库原子操作更新share_count
"""
import logging
import uuid
import random
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError

from app.models import (
    User, Chart, SynastryRecord,
    PastLifeRecord, PastLifeSynastryRecord,
    PastLifeTheme, PastLifeRelationshipType
)

from .config import (
    PAST_LIFE_THEME_CONFIG,
    PAST_LIFE_RELATIONSHIP_CONFIG,
    PAST_LIFE_PRICE,
    PAST_LIFE_SYNASTRY_PRICE
)
from .analysis_service import extract_core_planets, determine_past_life_theme, safe_get

logger = logging.getLogger(__name__)


def generate_share_code() -> str:
    """生成唯一的分享码"""
    timestamp = datetime.now().strftime("%y%m%d%H%M%S")
    random_part = ''.join(random.choices('ABCDEFGHJKLMNPQRSTUVWXYZ23456789', k=6))
    return f"{timestamp}{random_part}"


def get_or_create_past_life_record(
    db: Session,
    user_id: int,
    chart_id: Optional[int] = None,
    chart_data: Optional[Dict[str, Any]] = None,
    name: str = ""
) -> Tuple[Optional[PastLifeRecord], Optional[str]]:
    """
    获取或创建单人前世故事记录
    
    幂等性保障: 同一用户+同一星盘只会创建一条记录
    """
    try:
        if chart_id:
            existing = db.query(PastLifeRecord).filter(
                PastLifeRecord.user_id == user_id,
                PastLifeRecord.chart_id == chart_id,
                PastLifeRecord.is_deleted == False
            ).first()
            if existing:
                return existing, None
        
        record = PastLifeRecord(
            user_id=user_id,
            chart_id=chart_id,
            name=name or "未知",
            theme="adventurer",
            theme_name=PAST_LIFE_THEME_CONFIG["adventurer"]["name"],
            is_paid=False,
            share_count=0,
            is_deleted=False,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        if chart_data:
            planets = extract_core_planets(chart_data)
            theme, theme_info = determine_past_life_theme(planets, chart_data)
            
            record.theme = theme
            record.theme_name = theme_info["theme_name"]
            record.core_planet = theme_info.get("matched_planets", [{}])[0].get("planet") if theme_info.get("matched_planets") else None
            record.core_sign = theme_info.get("matched_planets", [{}])[0].get("sign") if theme_info.get("matched_planets") else None
            record.core_house = theme_info.get("matched_planets", [{}])[0].get("house") if theme_info.get("matched_planets") else None
            record.dominant_element = theme_info.get("dominant_element")
        
        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                record.share_code = generate_share_code()
                db.add(record)
                db.commit()
                db.refresh(record)
                return record, None
            except IntegrityError:
                db.rollback()
                if attempt == max_attempts - 1:
                    logger.error(f"生成唯一分享码失败，超过{max_attempts}次尝试")
                    return None, "生成分享码失败，请重试"
        
        return None, "创建记录失败"
        
    except Exception as e:
        logger.error(f"创建前世记录失败: {e}", exc_info=True)
        db.rollback()
        return None, str(e)


def get_or_create_synastry_past_life_record(
    db: Session,
    user_id: int,
    synastry_record_id: Optional[int] = None,
    synastry_data: Optional[Dict[str, Any]] = None,
    person_a_name: str = "人物A",
    person_b_name: str = "人物B"
) -> Tuple[Optional[PastLifeSynastryRecord], Optional[str]]:
    """
    获取或创建合盘前世关系记录
    
    幂等性保障: 同一用户+同一合盘只会创建一条记录
    """
    try:
        if synastry_record_id:
            existing = db.query(PastLifeSynastryRecord).filter(
                PastLifeSynastryRecord.user_id == user_id,
                PastLifeSynastryRecord.synastry_record_id == synastry_record_id,
                PastLifeSynastryRecord.is_deleted == False
            ).first()
            if existing:
                return existing, None
        
        record = PastLifeSynastryRecord(
            user_id=user_id,
            synastry_record_id=synastry_record_id,
            person_a_name=person_a_name,
            person_b_name=person_b_name,
            relationship_type="stranger",
            relationship_name=PAST_LIFE_RELATIONSHIP_CONFIG["stranger"]["name"],
            is_paid=False,
            share_count=0,
            is_deleted=False,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                record.share_code = generate_share_code()
                db.add(record)
                db.commit()
                db.refresh(record)
                return record, None
            except IntegrityError:
                db.rollback()
                if attempt == max_attempts - 1:
                    logger.error(f"生成唯一分享码失败，超过{max_attempts}次尝试")
                    return None, "生成分享码失败，请重试"
        
        return None, "创建记录失败"
        
    except Exception as e:
        logger.error(f"创建合盘前世记录失败: {e}", exc_info=True)
        db.rollback()
        return None, str(e)


def get_user_past_life_records(
    db: Session,
    user_id: int,
    limit: int = 20,
    offset: int = 0
) -> Tuple[List[PastLifeRecord], int]:
    """
    获取用户的前世记录列表（带真实分页）
    
    返回: (记录列表, 总记录数)
    """
    count_stmt = select(func.count(PastLifeRecord.id)).where(
        PastLifeRecord.user_id == user_id,
        PastLifeRecord.is_deleted == False
    )
    total = db.execute(count_stmt).scalar() or 0
    
    records = db.query(PastLifeRecord).filter(
        PastLifeRecord.user_id == user_id,
        PastLifeRecord.is_deleted == False
    ).order_by(
        PastLifeRecord.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    return records, total


def get_user_synastry_past_life_records(
    db: Session,
    user_id: int,
    limit: int = 20,
    offset: int = 0
) -> Tuple[List[PastLifeSynastryRecord], int]:
    """
    获取用户的合盘前世记录列表（带真实分页）
    
    返回: (记录列表, 总记录数)
    """
    count_stmt = select(func.count(PastLifeSynastryRecord.id)).where(
        PastLifeSynastryRecord.user_id == user_id,
        PastLifeSynastryRecord.is_deleted == False
    )
    total = db.execute(count_stmt).scalar() or 0
    
    records = db.query(PastLifeSynastryRecord).filter(
        PastLifeSynastryRecord.user_id == user_id,
        PastLifeSynastryRecord.is_deleted == False
    ).order_by(
        PastLifeSynastryRecord.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    return records, total


def get_past_life_by_share_code(
    db: Session,
    share_code: str
) -> Optional[Dict[str, Any]]:
    """
    通过分享码获取前世故事（用于分享）
    
    修复: 使用原子操作更新share_count，避免并发问题
    """
    try:
        record = db.query(PastLifeRecord).filter(
            PastLifeRecord.share_code == share_code,
            PastLifeRecord.is_deleted == False
        ).first()
        
        if record:
            db.query(PastLifeRecord).filter(
                PastLifeRecord.id == record.id
            ).update(
                {"share_count": PastLifeRecord.share_count + 1},
                synchronize_session=False
            )
            db.commit()
            db.refresh(record)
            
            theme_config = PAST_LIFE_THEME_CONFIG.get(record.theme, {})
            
            return {
                "type": "single",
                "id": record.id,
                "name": record.name,
                "theme": record.theme,
                "theme_name": record.theme_name,
                "theme_icon": theme_config.get("icon", "✨"),
                "theme_description": theme_config.get("description", ""),
                "basic_story": record.basic_story,
                "basic_story_short": record.basic_story_short,
                "deep_story": record.deep_story if record.is_paid else None,
                "deep_story_details": record.deep_story_details if record.is_paid else None,
                "is_paid": record.is_paid,
                "share_code": record.share_code,
                "share_count": record.share_count,
                "price": PAST_LIFE_PRICE,
                "created_at": record.created_at.isoformat() if record.created_at else None
            }
        
        syn_record = db.query(PastLifeSynastryRecord).filter(
            PastLifeSynastryRecord.share_code == share_code,
            PastLifeSynastryRecord.is_deleted == False
        ).first()
        
        if syn_record:
            db.query(PastLifeSynastryRecord).filter(
                PastLifeSynastryRecord.id == syn_record.id
            ).update(
                {"share_count": PastLifeSynastryRecord.share_count + 1},
                synchronize_session=False
            )
            db.commit()
            db.refresh(syn_record)
            
            rel_config = PAST_LIFE_RELATIONSHIP_CONFIG.get(syn_record.relationship_type, {})
            
            return {
                "type": "synastry",
                "id": syn_record.id,
                "person_a_name": syn_record.person_a_name,
                "person_b_name": syn_record.person_b_name,
                "relationship_type": syn_record.relationship_type,
                "relationship_name": syn_record.relationship_name,
                "relationship_icon": rel_config.get("icon", "✨"),
                "relationship_description": rel_config.get("description", ""),
                "basic_story": syn_record.basic_story,
                "basic_story_short": syn_record.basic_story_short,
                "deep_story": syn_record.deep_story if syn_record.is_paid else None,
                "deep_story_details": syn_record.deep_story_details if syn_record.is_paid else None,
                "is_paid": syn_record.is_paid,
                "share_code": syn_record.share_code,
                "share_count": syn_record.share_count,
                "price": PAST_LIFE_SYNASTRY_PRICE,
                "created_at": syn_record.created_at.isoformat() if syn_record.created_at else None
            }
        
        return None
        
    except Exception as e:
        logger.error(f"通过分享码获取前世故事失败: {e}", exc_info=True)
        return None


def get_single_record_by_id(
    db: Session,
    record_id: int,
    user_id: Optional[int] = None
) -> Optional[PastLifeRecord]:
    """
    根据ID获取单人前世记录（带权限检查）
    """
    query = db.query(PastLifeRecord).filter(
        PastLifeRecord.id == record_id,
        PastLifeRecord.is_deleted == False
    )
    
    if user_id is not None:
        query = query.filter(PastLifeRecord.user_id == user_id)
    
    return query.first()


def get_synastry_record_by_id(
    db: Session,
    record_id: int,
    user_id: Optional[int] = None
) -> Optional[PastLifeSynastryRecord]:
    """
    根据ID获取合盘前世记录（带权限检查）
    """
    query = db.query(PastLifeSynastryRecord).filter(
        PastLifeSynastryRecord.id == record_id,
        PastLifeSynastryRecord.is_deleted == False
    )
    
    if user_id is not None:
        query = query.filter(PastLifeSynastryRecord.user_id == user_id)
    
    return query.first()


def record_to_dict(record: PastLifeRecord) -> Dict[str, Any]:
    """将单人前世记录转换为字典"""
    theme_config = PAST_LIFE_THEME_CONFIG.get(record.theme, {})
    
    return {
        "id": record.id,
        "user_id": record.user_id,
        "chart_id": record.chart_id,
        "name": record.name,
        "theme": record.theme,
        "theme_name": record.theme_name,
        "theme_icon": theme_config.get("icon", "✨"),
        "theme_description": theme_config.get("description", ""),
        "keywords": theme_config.get("keywords", []),
        "core_planet": record.core_planet,
        "core_sign": record.core_sign,
        "core_house": record.core_house,
        "dominant_element": record.dominant_element,
        "basic_story": record.basic_story,
        "basic_story_short": record.basic_story_short,
        "deep_story": record.deep_story if record.is_paid else None,
        "deep_story_details": record.deep_story_details if record.is_paid else None,
        "is_paid": record.is_paid,
        "pay_order_no": record.pay_order_no,
        "share_code": record.share_code,
        "share_count": record.share_count or 0,
        "price": PAST_LIFE_PRICE,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "updated_at": record.updated_at.isoformat() if record.updated_at else None,
    }


def synastry_record_to_dict(record: PastLifeSynastryRecord) -> Dict[str, Any]:
    """将合盘前世记录转换为字典"""
    rel_config = PAST_LIFE_RELATIONSHIP_CONFIG.get(record.relationship_type, {})
    
    return {
        "id": record.id,
        "user_id": record.user_id,
        "synastry_record_id": record.synastry_record_id,
        "person_a_name": record.person_a_name,
        "person_b_name": record.person_b_name,
        "relationship_type": record.relationship_type,
        "relationship_name": record.relationship_name,
        "relationship_icon": rel_config.get("icon", "✨"),
        "relationship_description": rel_config.get("description", ""),
        "keywords": rel_config.get("keywords", []),
        "key_aspect": record.key_aspect,
        "dominant_element": record.dominant_element,
        "basic_story": record.basic_story,
        "basic_story_short": record.basic_story_short,
        "deep_story": record.deep_story if record.is_paid else None,
        "deep_story_details": record.deep_story_details if record.is_paid else None,
        "is_paid": record.is_paid,
        "pay_order_no": record.pay_order_no,
        "share_code": record.share_code,
        "share_count": record.share_count or 0,
        "price": PAST_LIFE_SYNASTRY_PRICE,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "updated_at": record.updated_at.isoformat() if record.updated_at else None,
    }
