import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from app.database import get_db
from app.models import User, PlazaPostType
from app.schemas import ApiResponse
from app.routers.users import get_current_user, get_current_active_user
from app.services.social_plaza_service import (
    create_plaza_post,
    get_plaza_post_list,
    get_plaza_post_by_id,
    toggle_like,
    check_user_liked,
    send_flower_to_post,
    create_mention,
    respond_to_mention,
    report_post,
    hide_post,
    remove_post,
    get_user_posts,
    delete_user_post,
    get_post_likes,
    get_post_flowers,
    get_post_mentions,
    record_share,
    build_post_response,
    build_post_responses,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["社交广场"])


class CreatePostRequest(BaseModel):
    post_type: str = Field(..., description="内容类型: synastry_card, daily_horoscope, past_life_story, card_draw")
    title: Optional[str] = Field(None, description="标题")
    content: Optional[str] = Field(None, description="内容")
    image_urls: Optional[List[str]] = Field(None, description="图片URL列表")
    related_data: Optional[Dict[str, Any]] = Field(None, description="相关数据")
    synastry_record_id: Optional[int] = Field(None, description="合盘记录ID")
    past_life_record_id: Optional[int] = Field(None, description="前世记录ID")
    photocard_record_id: Optional[int] = Field(None, description="卡牌记录ID")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    topic_challenge_id: Optional[int] = Field(None, description="关联的话题挑战ID")


class SendFlowerRequest(BaseModel):
    gift_id: int = Field(..., description="礼物ID")
    quantity: int = Field(1, description="数量")
    message: Optional[str] = Field(None, description="留言")
    is_anonymous: bool = Field(False, description="是否匿名")


class CreateMentionRequest(BaseModel):
    invitee_id: int = Field(..., description="被邀请用户ID")
    invitation_type: str = Field("synastry", description="邀请类型: synastry, etc.")
    message: Optional[str] = Field(None, description="邀请留言")


class RespondMentionRequest(BaseModel):
    is_accepted: bool = Field(..., description="是否接受")
    decline_reason: Optional[str] = Field(None, description="拒绝原因")


class ReportPostRequest(BaseModel):
    report_category: str = Field(..., description="举报分类")
    report_reason: Optional[str] = Field(None, description="举报原因")


class ShareRecordRequest(BaseModel):
    post_id: Optional[int] = Field(None, description="分享的内容ID")
    share_platform: Optional[str] = Field(None, description="分享平台")
    share_type: str = Field("external", description="分享类型")
    share_url: Optional[str] = Field(None, description="分享链接")
    share_text: Optional[str] = Field(None, description="分享文案")


@router.get("/types", response_model=ApiResponse)
def get_post_types():
    """获取内容类型列表"""
    types = [
        {"key": PlazaPostType.SYNASTRY_CARD.value, "name": "合盘卡牌", "icon": "♊", "description": "分享你的合盘结果"},
        {"key": PlazaPostType.DAILY_HOROSCOPE.value, "name": "今日运势", "icon": "🌟", "description": "分享你的每日星运"},
        {"key": PlazaPostType.PAST_LIFE_STORY.value, "name": "前世今生", "icon": "🌙", "description": "分享你的前世故事"},
        {"key": PlazaPostType.CARD_DRAW.value, "name": "星盘抽卡", "icon": "🎴", "description": "分享你的抽卡结果"},
    ]
    
    return ApiResponse(
        message="获取内容类型成功",
        data={"types": types}
    )


@router.get("/posts", response_model=ApiResponse)
def get_posts(
    sort_by: str = Query("latest", description="排序方式: latest, hot"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    post_type: Optional[str] = Query(None, description="内容类型筛选"),
    topic_challenge_id: Optional[int] = Query(None, description="话题挑战ID筛选"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """获取广场内容列表"""
    posts, total_count = get_plaza_post_list(
        db=db,
        sort_by=sort_by,
        limit=limit,
        offset=offset,
        post_type=post_type,
        topic_challenge_id=topic_challenge_id,
    )
    
    current_user_id = current_user.id if current_user else None
    
    posts_response = build_post_responses(db, posts, current_user_id)
    
    return ApiResponse(
        message="获取内容列表成功",
        data={
            "posts": posts_response,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "sort_by": sort_by,
        }
    )


@router.get("/posts/{post_id}", response_model=ApiResponse)
def get_post_detail(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """获取内容详情"""
    post = get_plaza_post_by_id(db, post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="内容不存在或已被删除"
        )
    
    current_user_id = current_user.id if current_user else None
    
    return ApiResponse(
        message="获取内容详情成功",
        data=build_post_response(db, post, current_user_id)
    )


@router.post("/posts", response_model=ApiResponse)
def create_post(
    request: CreatePostRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """发布内容"""
    valid_types = [t.value for t in PlazaPostType]
    if request.post_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的内容类型，可选: {', '.join(valid_types)}"
        )
    
    post, error = create_plaza_post(
        db=db,
        user_id=current_user.id,
        post_type=request.post_type,
        title=request.title,
        content=request.content,
        image_urls=request.image_urls,
        related_data=request.related_data,
        synastry_record_id=request.synastry_record_id,
        past_life_record_id=request.past_life_record_id,
        photocard_record_id=request.photocard_record_id,
        tags=request.tags,
        topic_challenge_id=request.topic_challenge_id,
    )
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error or "发布失败"
        )
    
    return ApiResponse(
        message="发布成功",
        data=build_post_response(db, post, current_user.id)
    )


@router.delete("/posts/{post_id}", response_model=ApiResponse)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除自己发布的内容"""
    success, message = delete_user_post(db, post_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return ApiResponse(message=message, data=None)


@router.post("/posts/{post_id}/like", response_model=ApiResponse)
def like_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """点赞/取消点赞"""
    is_liked, like_count, message = toggle_like(db, post_id, current_user.id)
    
    if message != "success":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return ApiResponse(
        message="操作成功",
        data={
            "is_liked": is_liked,
            "like_count": like_count,
        }
    )


@router.get("/posts/{post_id}/likes", response_model=ApiResponse)
def get_post_likes_list(
    post_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """获取点赞列表"""
    likes = get_post_likes(db, post_id, limit, offset)
    
    return ApiResponse(
        message="获取点赞列表成功",
        data={"likes": likes}
    )


@router.post("/posts/{post_id}/flower", response_model=ApiResponse)
def send_flower(
    post_id: int,
    request: SendFlowerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """送花"""
    flower_gift, error = send_flower_to_post(
        db=db,
        post_id=post_id,
        sender_id=current_user.id,
        gift_id=request.gift_id,
        quantity=request.quantity,
        message=request.message,
        is_anonymous=request.is_anonymous,
    )
    
    if not flower_gift:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error or "送花失败"
        )
    
    return ApiResponse(
        message="送花成功",
        data={
            "id": flower_gift.id,
            "gift_name": flower_gift.gift_name,
            "quantity": flower_gift.quantity,
            "is_anonymous": flower_gift.is_anonymous,
        }
    )


@router.get("/posts/{post_id}/flowers", response_model=ApiResponse)
def get_post_flowers_list(
    post_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """获取送花列表"""
    flowers = get_post_flowers(db, post_id, limit, offset)
    
    return ApiResponse(
        message="获取送花列表成功",
        data={"flowers": flowers}
    )


@router.post("/posts/{post_id}/mention", response_model=ApiResponse)
def create_post_mention(
    post_id: int,
    request: CreateMentionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """@好友邀请合盘"""
    mention, error = create_mention(
        db=db,
        post_id=post_id,
        inviter_id=current_user.id,
        invitee_id=request.invitee_id,
        invitation_type=request.invitation_type,
        message=request.message,
    )
    
    if not mention:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error or "邀请失败"
        )
    
    return ApiResponse(
        message="邀请已发送",
        data={
            "id": mention.id,
            "invitee_id": mention.invitee_id,
            "invitation_type": mention.invitation_type,
            "message": mention.message,
            "is_accepted": mention.is_accepted,
        }
    )


@router.get("/posts/{post_id}/mentions", response_model=ApiResponse)
def get_post_mentions_list(
    post_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """获取@好友列表"""
    mentions = get_post_mentions(db, post_id, limit, offset)
    
    return ApiResponse(
        message="获取邀请列表成功",
        data={"mentions": mentions}
    )


@router.put("/mentions/{mention_id}/respond", response_model=ApiResponse)
def respond_to_post_mention(
    mention_id: int,
    request: RespondMentionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """回应邀请"""
    mention, error = respond_to_mention(
        db=db,
        mention_id=mention_id,
        user_id=current_user.id,
        is_accepted=request.is_accepted,
        decline_reason=request.decline_reason,
    )
    
    if not mention:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error or "操作失败"
        )
    
    return ApiResponse(
        message="操作成功",
        data={
            "id": mention.id,
            "is_accepted": mention.is_accepted,
        }
    )


@router.post("/posts/{post_id}/report", response_model=ApiResponse)
def report_post_content(
    post_id: int,
    request: ReportPostRequest,
    request_obj: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """举报内容"""
    reporter_id = current_user.id if current_user else None
    reporter_ip = request_obj.client.host if request_obj.client else None
    
    report, error = report_post(
        db=db,
        post_id=post_id,
        reporter_id=reporter_id,
        report_category=request.report_category,
        report_reason=request.report_reason,
        reporter_ip=reporter_ip,
    )
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error or "举报失败"
        )
    
    return ApiResponse(
        message="举报已提交，感谢您的反馈",
        data={"report_id": report.id}
    )


@router.get("/my/posts", response_model=ApiResponse)
def get_my_posts(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取我的发布记录"""
    posts, total_count = get_user_posts(db, current_user.id, limit, offset)
    
    posts_response = build_post_responses(db, posts, current_user.id)
    
    return ApiResponse(
        message="获取我的发布成功",
        data={
            "posts": posts_response,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
        }
    )


@router.post("/share", response_model=ApiResponse)
def record_share_action(
    request: ShareRecordRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """记录分享行为"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先登录"
        )
    
    share = record_share(
        db=db,
        user_id=current_user.id,
        post_id=request.post_id,
        share_platform=request.share_platform,
        share_type=request.share_type,
        share_url=request.share_url,
        share_text=request.share_text,
    )
    
    return ApiResponse(
        message="分享记录已保存",
        data={"share_id": share.id}
    )


@router.put("/admin/posts/{post_id}/hide", response_model=ApiResponse)
def hide_post_admin(
    post_id: int,
    hide_reason: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """管理员隐藏内容"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限执行此操作"
        )
    
    post, error = hide_post(db, post_id, current_user.id, hide_reason)
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error or "操作失败"
        )
    
    return ApiResponse(
        message="内容已隐藏",
        data={"post_id": post.id, "status": post.status}
    )


@router.put("/admin/posts/{post_id}/remove", response_model=ApiResponse)
def remove_post_admin(
    post_id: int,
    hide_reason: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """管理员下架内容"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限执行此操作"
        )
    
    post, error = remove_post(db, post_id, current_user.id, hide_reason)
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error or "操作失败"
        )
    
    return ApiResponse(
        message="内容已下架",
        data={"post_id": post.id, "status": post.status}
    )
