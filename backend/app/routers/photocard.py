from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import logging
import uuid
import random
import string

from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, PhotocardRecord, SynastryRecord
from app.routers.users import get_current_user, get_current_active_user
from app.schemas import ApiResponse
from app.services.synastry_highlights_service import generate_photocard_design

logger = logging.getLogger(__name__)

router = APIRouter(tags=["合影卡牌"])


def generate_share_code(length: int = 8) -> str:
    """生成分享码"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


class SavePhotocardRequest(BaseModel):
    synastry_record_id: Optional[int] = None
    card_type: str = "default"
    person_a_name: Optional[str] = None
    person_b_name: Optional[str] = None
    highlights: Optional[Dict[str, Any]] = None
    card_design: Optional[Dict[str, Any]] = None
    card_svg: Optional[str] = None
    compatibility_score: Optional[int] = None


class SharePhotocardRequest(BaseModel):
    photocard_id: int


@router.post("/save", response_model=ApiResponse)
async def save_photocard(
    request: SavePhotocardRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """保存合影卡牌"""
    try:
        card_id = f"PC_{uuid.uuid4().hex[:12].upper()}"
        
        synastry_data = None
        highlights = request.highlights
        person_a_name = request.person_a_name or "人物A"
        person_b_name = request.person_b_name or "人物B"
        
        if request.synastry_record_id:
            record = db.query(SynastryRecord).filter(
                SynastryRecord.id == request.synastry_record_id,
                SynastryRecord.user_id == current_user.id,
                SynastryRecord.is_deleted == False
            ).first()
            
            if record:
                person_a_name = record.person_a_name or person_a_name
                person_b_name = record.person_b_name or person_b_name
                
                if record.synastry_data and not request.highlights:
                    try:
                        synastry_data = json.loads(record.synastry_data)
                        from app.services.synastry_highlights_service import extract_synastry_highlights
                        highlights = extract_synastry_highlights(synastry_data)
                    except:
                        pass
        
        card_design = request.card_design
        if not card_design and highlights:
            card_design = generate_photocard_design(
                highlights,
                person_a_name,
                person_b_name,
                request.card_type
            )
        
        primary_highlight = None
        if highlights and highlights.get("highlights"):
            first_highlight = highlights["highlights"][0] if highlights["highlights"] else None
            if first_highlight:
                primary_highlight = f"{first_highlight.get('icon', '')} {first_highlight.get('name', '')}"
        
        new_card = PhotocardRecord(
            user_id=current_user.id,
            synastry_record_id=request.synastry_record_id,
            card_id=card_id,
            card_type=request.card_type,
            card_name=card_design.get("theme_name") if card_design else "星盘合影",
            person_a_name=person_a_name,
            person_b_name=person_b_name,
            rarity=card_design.get("rarity") if card_design else "common",
            is_limited_edition=card_design.get("limited_edition") if card_design else False,
            card_design_data=json.dumps(card_design, ensure_ascii=False) if card_design else None,
            card_svg=request.card_svg,
            compatibility_score=request.compatibility_score,
            primary_highlight=primary_highlight,
            is_saved=True,
            is_deleted=False
        )
        
        db.add(new_card)
        db.commit()
        db.refresh(new_card)
        
        return ApiResponse(
            message="卡牌保存成功",
            data={
                "photocard_id": new_card.id,
                "card_id": new_card.card_id,
                "card_name": new_card.card_name,
                "rarity": new_card.rarity,
                "is_limited_edition": new_card.is_limited_edition,
                "person_a_name": new_card.person_a_name,
                "person_b_name": new_card.person_b_name,
                "created_at": new_card.created_at.isoformat() if new_card.created_at else None
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"保存卡牌失败: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存卡牌失败: {str(e)}"
        )


@router.get("/list", response_model=ApiResponse)
async def get_photocard_list(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取我的卡牌列表"""
    try:
        cards = db.query(PhotocardRecord).filter(
            PhotocardRecord.user_id == current_user.id,
            PhotocardRecord.is_deleted == False
        ).order_by(
            PhotocardRecord.created_at.desc()
        ).offset(skip).limit(limit).all()
        
        total = db.query(PhotocardRecord).filter(
            PhotocardRecord.user_id == current_user.id,
            PhotocardRecord.is_deleted == False
        ).count()
        
        result = []
        for card in cards:
            card_design = None
            if card.card_design_data:
                try:
                    card_design = json.loads(card.card_design_data)
                except:
                    pass
            
            result.append({
                "id": card.id,
                "card_id": card.card_id,
                "card_type": card.card_type,
                "card_name": card.card_name,
                "person_a_name": card.person_a_name,
                "person_b_name": card.person_b_name,
                "rarity": card.rarity,
                "rarity_label": get_rarity_label(card.rarity),
                "is_limited_edition": card.is_limited_edition,
                "compatibility_score": card.compatibility_score,
                "primary_highlight": card.primary_highlight,
                "share_code": card.share_code,
                "share_count": card.share_count,
                "has_svg": bool(card.card_svg),
                "created_at": card.created_at.isoformat() if card.created_at else None
            })
        
        return ApiResponse(
            message="获取成功",
            data={
                "items": result,
                "total": total,
                "skip": skip,
                "limit": limit
            }
        )
        
    except Exception as e:
        logger.error(f"获取卡牌列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取卡牌列表失败: {str(e)}"
        )


@router.get("/{photocard_id}", response_model=ApiResponse)
async def get_photocard_detail(
    photocard_id: int,
    include_svg: bool = Query(False, description="是否包含SVG数据"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取卡牌详情"""
    try:
        card = db.query(PhotocardRecord).filter(
            PhotocardRecord.id == photocard_id,
            PhotocardRecord.user_id == current_user.id,
            PhotocardRecord.is_deleted == False
        ).first()
        
        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="卡牌不存在或无权限访问"
            )
        
        card_design = None
        if card.card_design_data:
            try:
                card_design = json.loads(card.card_design_data)
            except:
                pass
        
        result = {
            "id": card.id,
            "card_id": card.card_id,
            "card_type": card.card_type,
            "card_name": card.card_name,
            "person_a_name": card.person_a_name,
            "person_b_name": card.person_b_name,
            "rarity": card.rarity,
            "rarity_label": get_rarity_label(card.rarity),
            "is_limited_edition": card.is_limited_edition,
            "compatibility_score": card.compatibility_score,
            "primary_highlight": card.primary_highlight,
            "share_code": card.share_code,
            "share_count": card.share_count,
            "design": card_design,
            "created_at": card.created_at.isoformat() if card.created_at else None
        }
        
        if include_svg and card.card_svg:
            result["card_svg"] = card.card_svg
        
        return ApiResponse(
            message="获取成功",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取卡牌详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取卡牌详情失败: {str(e)}"
        )


@router.post("/share", response_model=ApiResponse)
async def share_photocard(
    request: SharePhotocardRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """分享卡牌，生成分享码"""
    try:
        card = db.query(PhotocardRecord).filter(
            PhotocardRecord.id == request.photocard_id,
            PhotocardRecord.user_id == current_user.id,
            PhotocardRecord.is_deleted == False
        ).first()
        
        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="卡牌不存在或无权限访问"
            )
        
        if not card.share_code:
            for _ in range(10):
                share_code = generate_share_code(8)
                existing = db.query(PhotocardRecord).filter(
                    PhotocardRecord.share_code == share_code
                ).first()
                if not existing:
                    card.share_code = share_code
                    break
        
        card.share_count = (card.share_count or 0) + 1
        db.commit()
        db.refresh(card)
        
        share_url = f"/photocard/share/{card.share_code}"
        
        return ApiResponse(
            message="分享成功",
            data={
                "photocard_id": card.id,
                "share_code": card.share_code,
                "share_url": share_url,
                "share_count": card.share_count
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分享卡牌失败: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分享卡牌失败: {str(e)}"
        )


@router.get("/share/{share_code}", response_model=ApiResponse)
async def get_shared_photocard(
    share_code: str,
    db: Session = Depends(get_db)
):
    """通过分享码获取卡牌（公开访问）"""
    try:
        card = db.query(PhotocardRecord).filter(
            PhotocardRecord.share_code == share_code,
            PhotocardRecord.is_deleted == False
        ).first()
        
        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分享链接无效或已过期"
            )
        
        card_design = None
        if card.card_design_data:
            try:
                card_design = json.loads(card.card_design_data)
            except:
                pass
        
        creator = db.query(User).filter(User.id == card.user_id).first()
        creator_name = creator.username if creator else None
        
        result = {
            "card_id": card.card_id,
            "card_name": card.card_name,
            "person_a_name": card.person_a_name,
            "person_b_name": card.person_b_name,
            "rarity": card.rarity,
            "rarity_label": get_rarity_label(card.rarity),
            "is_limited_edition": card.is_limited_edition,
            "compatibility_score": card.compatibility_score,
            "primary_highlight": card.primary_highlight,
            "design": card_design,
            "card_svg": card.card_svg,
            "share_count": card.share_count,
            "creator_name": creator_name,
            "created_at": card.created_at.isoformat() if card.created_at else None
        }
        
        return ApiResponse(
            message="获取成功",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取分享卡牌失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取分享卡牌失败: {str(e)}"
        )


@router.delete("/{photocard_id}", response_model=ApiResponse)
async def delete_photocard(
    photocard_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除卡牌"""
    try:
        card = db.query(PhotocardRecord).filter(
            PhotocardRecord.id == photocard_id,
            PhotocardRecord.user_id == current_user.id
        ).first()
        
        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="卡牌不存在或无权限删除"
            )
        
        card.is_deleted = True
        db.commit()
        
        return ApiResponse(
            message="删除成功",
            data={"deleted": True}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除卡牌失败: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除卡牌失败: {str(e)}"
        )


def get_rarity_label(rarity: str) -> str:
    labels = {
        "common": "普通",
        "rare": "稀有",
        "epic": "史诗",
        "legendary": "传说"
    }
    return labels.get(rarity, "普通")
