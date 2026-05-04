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
from app.models import User, StoryCard, SynastryRecord, StoryCardRarity, StoryCardTemplate
from app.routers.users import get_current_user, get_current_active_user
from app.schemas import ApiResponse
from app.services.past_life.story_card_service import (
    generate_story_card,
    get_template_list,
    get_rarity_config,
    generate_share_code
)
from app.services.past_life.config import STORY_CARD_RARITY_CONFIG

logger = logging.getLogger(__name__)

router = APIRouter(tags=["故事卡与故事墙"])


class GenerateStoryCardRequest(BaseModel):
    synastry_record_id: Optional[int] = None
    synastry_data: Optional[Dict[str, Any]] = None
    analysis_data: Optional[Dict[str, Any]] = None
    person_a_name: Optional[str] = None
    person_b_name: Optional[str] = None
    target_user_id: Optional[int] = None
    auto_save: bool = True


class SaveStoryCardRequest(BaseModel):
    synastry_record_id: Optional[int] = None
    story_card_data: Dict[str, Any]
    is_public: bool = False


class MountStoryCardRequest(BaseModel):
    story_card_id: int
    mounted: bool = True


class UpdateStoryCardRequest(BaseModel):
    is_public: Optional[bool] = None
    is_mounted: Optional[bool] = None


def get_rarity_label(rarity: str) -> str:
    labels = {
        "common": "普通",
        "rare": "稀有",
        "epic": "史诗",
        "legendary": "传说"
    }
    return labels.get(rarity, "普通")


def build_story_card_response(card: StoryCard, include_full: bool = False) -> Dict[str, Any]:
    """构建故事卡响应数据"""
    card_metadata = None
    if card.card_metadata:
        try:
            card_metadata = json.loads(card.card_metadata)
        except:
            pass
    
    result = {
        "id": card.id,
        "user_id": card.user_id,
        "synastry_record_id": card.synastry_record_id,
        "past_life_synastry_id": card.past_life_synastry_id,
        
        "card_template": card.card_template,
        "template_name": card.template_name,
        
        "person_a_name": card.person_a_name,
        "person_b_name": card.person_b_name,
        "target_user_id": card.target_user_id,
        
        "headline": card.headline,
        "subheadline": card.subheadline,
        "story_short": card.story_short,
        
        "compatibility_score": card.compatibility_score,
        "match_type": card.match_type,
        "dominant_element": card.dominant_element,
        "key_aspect": card.key_aspect,
        
        "rarity": card.rarity,
        "rarity_name": card.rarity_name or get_rarity_label(card.rarity),
        "rarity_config": STORY_CARD_RARITY_CONFIG.get(card.rarity, {}),
        
        "is_mounted": card.is_mounted,
        "mounted_at": card.mounted_at.isoformat() if card.mounted_at else None,
        "is_public": card.is_public,
        "share_code": card.share_code,
        "share_count": card.share_count,
        
        "metadata": card_metadata,
        
        "created_at": card.created_at.isoformat() if card.created_at else None,
        "updated_at": card.updated_at.isoformat() if card.updated_at else None
    }
    
    if include_full:
        result["story_content"] = card.story_content
    
    return result


@router.post("/generate", response_model=ApiResponse)
async def generate_new_story_card(
    request: GenerateStoryCardRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    生成故事卡
    可基于合盘记录ID或直接传入合盘数据生成
    """
    try:
        synastry_data = request.synastry_data
        analysis_data = request.analysis_data
        person_a_name = request.person_a_name or "人物A"
        person_b_name = request.person_b_name or "人物B"
        synastry_record_id = request.synastry_record_id
        
        if synastry_record_id and not synastry_data:
            record = db.query(SynastryRecord).filter(
                SynastryRecord.id == synastry_record_id,
                SynastryRecord.is_deleted == False
            ).first()
            
            if not record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="合盘记录不存在"
                )
            
            person_a_name = record.person_a_name or person_a_name
            person_b_name = record.person_b_name or person_b_name
            
            if record.synastry_data:
                try:
                    synastry_data = json.loads(record.synastry_data)
                except:
                    pass
            
            if record.analysis_data:
                try:
                    analysis_data = json.loads(record.analysis_data)
                except:
                    pass
        
        if not synastry_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="缺少合盘数据，请提供 synastry_record_id 或 synastry_data"
            )
        
        result = generate_story_card(
            synastry_data=synastry_data,
            analysis_data=analysis_data,
            person_a_name=person_a_name,
            person_b_name=person_b_name,
            user_id=current_user.id,
            synastry_record_id=synastry_record_id,
            target_user_id=request.target_user_id
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"生成故事卡失败: {result.get('error', '未知错误')}"
            )
        
        story_card_data = result["story_card"]
        
        if request.auto_save:
            new_card = StoryCard(
                user_id=current_user.id,
                synastry_record_id=synastry_record_id,
                card_template=story_card_data.get("card_template", "familiar_strangers"),
                template_name=story_card_data.get("template_name"),
                person_a_name=story_card_data.get("person_a_name"),
                person_b_name=story_card_data.get("person_b_name"),
                target_user_id=request.target_user_id,
                headline=story_card_data.get("headline", ""),
                subheadline=story_card_data.get("subheadline"),
                story_content=story_card_data.get("story_content", ""),
                story_short=story_card_data.get("story_short"),
                compatibility_score=story_card_data.get("compatibility_score"),
                match_type=story_card_data.get("match_type"),
                dominant_element=story_card_data.get("dominant_element"),
                key_aspect=story_card_data.get("key_aspect"),
                rarity=story_card_data.get("rarity", "common"),
                rarity_name=story_card_data.get("rarity_name"),
                is_mounted=False,
                is_public=False,
                share_code=generate_share_code(),
                share_count=0,
                card_metadata=json.dumps({
                    "match_score": story_card_data.get("match_score"),
                    "matched_conditions": story_card_data.get("matched_conditions"),
                    "features": story_card_data.get("features"),
                    "template_icon": story_card_data.get("template_icon")
                }, ensure_ascii=False),
                is_deleted=False
            )
            
            db.add(new_card)
            db.commit()
            db.refresh(new_card)
            
            response_data = build_story_card_response(new_card, include_full=True)
            response_data["match_details"] = result.get("match_details")
        else:
            response_data = story_card_data
            response_data["match_details"] = result.get("match_details")
        
        logger.info(f"生成故事卡成功: 用户={current_user.id}, 模板={story_card_data.get('card_template')}, 稀有度={story_card_data.get('rarity')}")
        
        return ApiResponse(
            message="生成故事卡成功",
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成故事卡失败: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成故事卡失败: {str(e)}"
        )


@router.post("/save", response_model=ApiResponse)
async def save_story_card(
    request: SaveStoryCardRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """保存故事卡到数据库"""
    try:
        card_data = request.story_card_data
        
        new_card = StoryCard(
            user_id=current_user.id,
            synastry_record_id=request.synastry_record_id,
            card_template=card_data.get("card_template", "familiar_strangers"),
            template_name=card_data.get("template_name"),
            person_a_name=card_data.get("person_a_name"),
            person_b_name=card_data.get("person_b_name"),
            target_user_id=card_data.get("target_user_id"),
            headline=card_data.get("headline", ""),
            subheadline=card_data.get("subheadline"),
            story_content=card_data.get("story_content", ""),
            story_short=card_data.get("story_short"),
            compatibility_score=card_data.get("compatibility_score"),
            match_type=card_data.get("match_type"),
            dominant_element=card_data.get("dominant_element"),
            key_aspect=card_data.get("key_aspect"),
            rarity=card_data.get("rarity", "common"),
            rarity_name=card_data.get("rarity_name"),
            is_mounted=False,
            is_public=request.is_public,
            share_code=generate_share_code(),
            share_count=0,
            card_metadata=json.dumps({
                "match_score": card_data.get("match_score"),
                "matched_conditions": card_data.get("matched_conditions"),
                "features": card_data.get("features"),
                "template_icon": card_data.get("template_icon")
            }, ensure_ascii=False) if card_data else None,
            is_deleted=False
        )
        
        db.add(new_card)
        db.commit()
        db.refresh(new_card)
        
        logger.info(f"保存故事卡成功: 用户={current_user.id}, 卡片ID={new_card.id}")
        
        return ApiResponse(
            message="保存故事卡成功",
            data=build_story_card_response(new_card, include_full=True)
        )
        
    except Exception as e:
        logger.error(f"保存故事卡失败: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存故事卡失败: {str(e)}"
        )


@router.post("/mount", response_model=ApiResponse)
async def toggle_mount_story_card(
    request: MountStoryCardRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """挂载/取消挂载故事卡到故事墙"""
    try:
        card = db.query(StoryCard).filter(
            StoryCard.id == request.story_card_id,
            StoryCard.user_id == current_user.id,
            StoryCard.is_deleted == False
        ).first()
        
        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="故事卡不存在或无权限操作"
            )
        
        if request.mounted:
            mounted_count = db.query(StoryCard).filter(
                StoryCard.user_id == current_user.id,
                StoryCard.is_mounted == True,
                StoryCard.is_deleted == False
            ).count()
            
            if mounted_count >= 20:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="故事墙最多挂载20张卡片，请先取消挂载部分卡片"
                )
            
            card.is_mounted = True
            card.mounted_at = datetime.utcnow()
        else:
            card.is_mounted = False
            card.mounted_at = None
        
        db.commit()
        db.refresh(card)
        
        action = "挂载" if request.mounted else "取消挂载"
        logger.info(f"{action}故事卡成功: 用户={current_user.id}, 卡片ID={card.id}")
        
        return ApiResponse(
            message=f"{action}成功",
            data={
                "story_card_id": card.id,
                "is_mounted": card.is_mounted,
                "mounted_at": card.mounted_at.isoformat() if card.mounted_at else None
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"挂载故事卡失败: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"挂载故事卡失败: {str(e)}"
        )


@router.get("/my-cards", response_model=ApiResponse)
async def get_my_story_cards(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    rarity: Optional[str] = Query(None, description="按稀有度筛选: common/rare/epic/legendary"),
    is_mounted: Optional[bool] = Query(None, description="是否已挂载"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取我的故事卡列表"""
    try:
        query = db.query(StoryCard).filter(
            StoryCard.user_id == current_user.id,
            StoryCard.is_deleted == False
        )
        
        if rarity:
            query = query.filter(StoryCard.rarity == rarity)
        
        if is_mounted is not None:
            query = query.filter(StoryCard.is_mounted == is_mounted)
        
        total = query.count()
        
        cards = query.order_by(
            StoryCard.created_at.desc()
        ).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        result = []
        for card in cards:
            result.append(build_story_card_response(card, include_full=False))
        
        return ApiResponse(
            message="获取成功",
            data={
                "items": result,
                "total": total,
                "page": page,
                "page_size": page_size,
                "rarity_filter": rarity,
                "is_mounted_filter": is_mounted
            }
        )
        
    except Exception as e:
        logger.error(f"获取故事卡列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取故事卡列表失败: {str(e)}"
        )


@router.get("/story-wall", response_model=ApiResponse)
async def get_my_story_wall(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取我的故事墙（已挂载的卡片）
    支持访客浏览（未登录用户访问他人主页时）
    """
    try:
        query = db.query(StoryCard).filter(
            StoryCard.user_id == current_user.id,
            StoryCard.is_mounted == True,
            StoryCard.is_deleted == False
        )
        
        total = query.count()
        
        cards = query.order_by(
            StoryCard.mounted_at.desc()
        ).all()
        
        result = []
        for card in cards:
            result.append(build_story_card_response(card, include_full=False))
        
        stats = {
            "total_mounted": total,
            "rarity_distribution": {
                "common": 0,
                "rare": 0,
                "epic": 0,
                "legendary": 0
            }
        }
        
        for card in cards:
            if card.rarity in stats["rarity_distribution"]:
                stats["rarity_distribution"][card.rarity] += 1
        
        return ApiResponse(
            message="获取故事墙成功",
            data={
                "user_id": current_user.id,
                "user_name": current_user.username,
                "cards": result,
                "stats": stats
            }
        )
        
    except Exception as e:
        logger.error(f"获取故事墙失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取故事墙失败: {str(e)}"
        )


@router.get("/story-wall/{user_id}", response_model=ApiResponse)
async def get_user_story_wall(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(lambda: None)
):
    """
    获取其他用户的故事墙（公开访问）
    仅显示已挂载且公开的卡片
    """
    try:
        target_user = db.query(User).filter(User.id == user_id).first()
        
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        query = db.query(StoryCard).filter(
            StoryCard.user_id == user_id,
            StoryCard.is_mounted == True,
            StoryCard.is_deleted == False
        )
        
        is_owner = current_user and current_user.id == user_id
        
        if not is_owner:
            query = query.filter(StoryCard.is_public == True)
        
        total = query.count()
        
        cards = query.order_by(
            StoryCard.mounted_at.desc()
        ).all()
        
        result = []
        for card in cards:
            result.append(build_story_card_response(card, include_full=False))
        
        stats = {
            "total_mounted": total,
            "rarity_distribution": {
                "common": 0,
                "rare": 0,
                "epic": 0,
                "legendary": 0
            }
        }
        
        for card in cards:
            if card.rarity in stats["rarity_distribution"]:
                stats["rarity_distribution"][card.rarity] += 1
        
        return ApiResponse(
            message="获取用户故事墙成功",
            data={
                "user_id": target_user.id,
                "user_name": target_user.username,
                "is_owner": is_owner,
                "cards": result,
                "stats": stats
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户故事墙失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户故事墙失败: {str(e)}"
        )


@router.get("/{story_card_id}", response_model=ApiResponse)
async def get_story_card_detail(
    story_card_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取故事卡详情"""
    try:
        card = db.query(StoryCard).filter(
            StoryCard.id == story_card_id,
            StoryCard.is_deleted == False
        ).first()
        
        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="故事卡不存在"
            )
        
        is_owner = card.user_id == current_user.id
        
        if not is_owner and not card.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限访问此故事卡"
            )
        
        return ApiResponse(
            message="获取成功",
            data=build_story_card_response(card, include_full=True)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取故事卡详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取故事卡详情失败: {str(e)}"
        )


@router.put("/{story_card_id}", response_model=ApiResponse)
async def update_story_card(
    story_card_id: int,
    request: UpdateStoryCardRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新故事卡信息"""
    try:
        card = db.query(StoryCard).filter(
            StoryCard.id == story_card_id,
            StoryCard.user_id == current_user.id,
            StoryCard.is_deleted == False
        ).first()
        
        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="故事卡不存在或无权限操作"
            )
        
        if request.is_public is not None:
            card.is_public = request.is_public
        
        if request.is_mounted is not None:
            if request.is_mounted:
                mounted_count = db.query(StoryCard).filter(
                    StoryCard.user_id == current_user.id,
                    StoryCard.is_mounted == True,
                    StoryCard.id != story_card_id,
                    StoryCard.is_deleted == False
                ).count()
                
                if mounted_count >= 20:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="故事墙最多挂载20张卡片"
                    )
                
                card.is_mounted = True
                card.mounted_at = datetime.utcnow()
            else:
                card.is_mounted = False
                card.mounted_at = None
        
        db.commit()
        db.refresh(card)
        
        return ApiResponse(
            message="更新成功",
            data=build_story_card_response(card, include_full=True)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新故事卡失败: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新故事卡失败: {str(e)}"
        )


@router.post("/{story_card_id}/share", response_model=ApiResponse)
async def share_story_card(
    story_card_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """分享故事卡，生成/获取分享链接"""
    try:
        card = db.query(StoryCard).filter(
            StoryCard.id == story_card_id,
            StoryCard.user_id == current_user.id,
            StoryCard.is_deleted == False
        ).first()
        
        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="故事卡不存在或无权限操作"
            )
        
        if not card.share_code:
            for _ in range(10):
                share_code = generate_share_code()
                existing = db.query(StoryCard).filter(
                    StoryCard.share_code == share_code
                ).first()
                if not existing:
                    card.share_code = share_code
                    break
        
        card.share_count = (card.share_count or 0) + 1
        card.is_public = True
        db.commit()
        db.refresh(card)
        
        share_url = f"/story-card/share/{card.share_code}"
        
        return ApiResponse(
            message="分享成功",
            data={
                "story_card_id": card.id,
                "share_code": card.share_code,
                "share_url": share_url,
                "share_count": card.share_count,
                "is_public": card.is_public
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分享故事卡失败: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分享故事卡失败: {str(e)}"
        )


@router.get("/share/{share_code}", response_model=ApiResponse)
async def get_shared_story_card(
    share_code: str,
    db: Session = Depends(get_db)
):
    """通过分享码获取故事卡（公开访问）"""
    try:
        card = db.query(StoryCard).filter(
            StoryCard.share_code == share_code,
            StoryCard.is_deleted == False
        ).first()
        
        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分享链接无效或已过期"
            )
        
        if not card.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="此故事卡未公开"
            )
        
        creator = db.query(User).filter(User.id == card.user_id).first()
        creator_name = creator.username if creator else None
        
        result = build_story_card_response(card, include_full=True)
        result["creator_name"] = creator_name
        
        return ApiResponse(
            message="获取成功",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取分享故事卡失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取分享故事卡失败: {str(e)}"
        )


@router.delete("/{story_card_id}", response_model=ApiResponse)
async def delete_story_card(
    story_card_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除故事卡"""
    try:
        card = db.query(StoryCard).filter(
            StoryCard.id == story_card_id,
            StoryCard.user_id == current_user.id
        ).first()
        
        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="故事卡不存在或无权限删除"
            )
        
        card.is_deleted = True
        db.commit()
        
        logger.info(f"删除故事卡成功: 用户={current_user.id}, 卡片ID={card.id}")
        
        return ApiResponse(
            message="删除成功",
            data={"deleted": True, "story_card_id": story_card_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除故事卡失败: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除故事卡失败: {str(e)}"
        )


@router.get("/templates/list", response_model=ApiResponse)
async def get_story_card_templates():
    """获取所有故事卡模板列表"""
    try:
        templates = get_template_list()
        
        return ApiResponse(
            message="获取成功",
            data={
                "templates": templates,
                "total": len(templates)
            }
        )
        
    except Exception as e:
        logger.error(f"获取模板列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取模板列表失败: {str(e)}"
        )


@router.get("/rarity/config", response_model=ApiResponse)
async def get_story_card_rarity_config():
    """获取稀有度配置"""
    try:
        config = get_rarity_config()
        
        return ApiResponse(
            message="获取成功",
            data=config
        )
        
    except Exception as e:
        logger.error(f"获取稀有度配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取稀有度配置失败: {str(e)}"
        )
