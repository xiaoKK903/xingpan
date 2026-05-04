import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from app.database import get_db
from app.models import User, TopicChallengeStatus, RewardType
from app.schemas import ApiResponse
from app.routers.users import get_current_user, get_current_active_user
from app.services.topic_challenge_service import (
    create_topic_challenge,
    update_topic_challenge,
    get_topic_challenge_by_id,
    get_topic_challenge_by_tag,
    get_active_topic_challenge,
    get_topic_challenge_list,
    participate_in_topic,
    get_topic_leaderboard,
    get_topic_posts,
    settle_topic_rewards,
    claim_topic_reward,
    build_topic_response,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["话题挑战"])


class CreateTopicRequest(BaseModel):
    title: str = Field(..., description="话题标题")
    topic_tag: str = Field(..., description="话题标签，如 #我的星盘缺什么#")
    start_time: datetime = Field(..., description="开始时间")
    end_time: datetime = Field(..., description="结束时间")
    description: Optional[str] = Field(None, description="话题描述")
    banner_image_url: Optional[str] = Field(None, description="横幅图片URL")
    cover_image_url: Optional[str] = Field(None, description="封面图片URL")
    reward_config: Optional[Dict[str, Any]] = Field(None, description="奖励配置")
    max_participants: Optional[int] = Field(None, description="最大参与人数")
    is_featured: bool = Field(False, description="是否精选推荐")
    sort_order: int = Field(0, description="排序顺序")


class UpdateTopicRequest(BaseModel):
    title: Optional[str] = Field(None, description="话题标题")
    description: Optional[str] = Field(None, description="话题描述")
    topic_tag: Optional[str] = Field(None, description="话题标签")
    banner_image_url: Optional[str] = Field(None, description="横幅图片URL")
    cover_image_url: Optional[str] = Field(None, description="封面图片URL")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    status: Optional[str] = Field(None, description="状态: draft, active, ended, archived")
    reward_config: Optional[Dict[str, Any]] = Field(None, description="奖励配置")
    max_participants: Optional[int] = Field(None, description="最大参与人数")
    is_featured: Optional[bool] = Field(None, description="是否精选推荐")
    sort_order: Optional[int] = Field(None, description="排序顺序")


class ParticipateTopicRequest(BaseModel):
    post_id: int = Field(..., description="参与的帖子ID")


@router.get("/active", response_model=ApiResponse)
def get_active_topic(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """获取当前活跃的话题挑战"""
    topic = get_active_topic_challenge(db)

    if not topic:
        return ApiResponse(
            message="暂无活跃话题",
            data=None
        )

    current_user_id = current_user.id if current_user else None
    topic_response = build_topic_response(
        topic,
        include_participation=True,
        current_user_id=current_user_id,
        db=db
    )

    return ApiResponse(
        message="获取成功",
        data={"topic": topic_response}
    )


@router.get("/list", response_model=ApiResponse)
def get_topic_list(
    status: Optional[str] = Query(None, description="状态筛选: draft, active, ended, archived"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """获取话题挑战列表"""
    topics, total_count = get_topic_challenge_list(
        db=db,
        status=status,
        limit=limit,
        offset=offset,
    )

    current_user_id = current_user.id if current_user else None
    topic_responses = [
        build_topic_response(topic, include_participation=True, current_user_id=current_user_id, db=db)
        for topic in topics
    ]

    return ApiResponse(
        message="获取成功",
        data={
            "topics": topic_responses,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
        }
    )


@router.get("/{topic_id}", response_model=ApiResponse)
def get_topic_detail(
    topic_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """获取话题挑战详情"""
    topic = get_topic_challenge_by_id(db, topic_id)

    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="话题不存在"
        )

    current_user_id = current_user.id if current_user else None
    topic_response = build_topic_response(
        topic,
        include_participation=True,
        current_user_id=current_user_id,
        db=db
    )

    return ApiResponse(
        message="获取成功",
        data={"topic": topic_response}
    )


@router.get("/tag/{topic_tag}", response_model=ApiResponse)
def get_topic_by_tag(
    topic_tag: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """通过话题标签获取话题详情"""
    topic = get_topic_challenge_by_tag(db, topic_tag)

    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="话题不存在"
        )

    current_user_id = current_user.id if current_user else None
    topic_response = build_topic_response(
        topic,
        include_participation=True,
        current_user_id=current_user_id,
        db=db
    )

    return ApiResponse(
        message="获取成功",
        data={"topic": topic_response}
    )


@router.get("/{topic_id}/posts", response_model=ApiResponse)
def get_topic_post_list(
    topic_id: int,
    sort_by: str = Query("latest", description="排序方式: latest, hot"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """获取话题下的帖子列表"""
    topic = get_topic_challenge_by_id(db, topic_id)
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="话题不存在"
        )

    current_user_id = current_user.id if current_user else None

    posts, total_count = get_topic_posts(
        db=db,
        topic_id=topic_id,
        sort_by=sort_by,
        limit=limit,
        offset=offset,
        current_user_id=current_user_id,
    )

    return ApiResponse(
        message="获取成功",
        data={
            "posts": posts,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "sort_by": sort_by,
        }
    )


@router.get("/{topic_id}/leaderboard", response_model=ApiResponse)
def get_leaderboard(
    topic_id: int,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """获取话题排行榜"""
    topic = get_topic_challenge_by_id(db, topic_id)
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="话题不存在"
        )

    leaderboard, total_count = get_topic_leaderboard(
        db=db,
        topic_id=topic_id,
        limit=limit,
        offset=offset,
    )

    my_rank = None
    if current_user:
        for entry in leaderboard:
            if entry["user_id"] == current_user.id:
                my_rank = entry
                break

    return ApiResponse(
        message="获取成功",
        data={
            "leaderboard": leaderboard,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "my_rank": my_rank,
        }
    )


@router.post("/{topic_id}/participate", response_model=ApiResponse)
def participate_topic(
    topic_id: int,
    request: ParticipateTopicRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """参与话题挑战"""
    participation, error = participate_in_topic(
        db=db,
        topic_id=topic_id,
        post_id=request.post_id,
        user_id=current_user.id,
    )

    if not participation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error or "参与失败"
        )

    return ApiResponse(
        message="参与成功",
        data={
            "participation_id": participation.id,
            "topic_id": participation.topic_id,
            "post_id": participation.post_id,
            "hot_score": participation.hot_score,
            "participated_at": participation.participated_at.isoformat() if participation.participated_at else None,
        }
    )


@router.post("/{topic_id}/claim-reward", response_model=ApiResponse)
def claim_reward(
    topic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """领取话题挑战奖励"""
    result, error = claim_topic_reward(
        db=db,
        topic_id=topic_id,
        user_id=current_user.id,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error or "领取失败"
        )

    return ApiResponse(
        message="领取成功",
        data=result
    )


@router.post("/", response_model=ApiResponse)
def create_topic(
    request: CreateTopicRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """创建话题挑战（管理员）"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限执行此操作"
        )

    topic, error = create_topic_challenge(
        db=db,
        title=request.title,
        topic_tag=request.topic_tag,
        start_time=request.start_time,
        end_time=request.end_time,
        description=request.description,
        banner_image_url=request.banner_image_url,
        cover_image_url=request.cover_image_url,
        reward_config=request.reward_config,
        max_participants=request.max_participants,
        is_featured=request.is_featured,
        sort_order=request.sort_order,
        created_by=current_user.id,
    )

    if not topic:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error or "创建失败"
        )

    return ApiResponse(
        message="创建成功",
        data=build_topic_response(topic)
    )


@router.put("/{topic_id}", response_model=ApiResponse)
def update_topic(
    topic_id: int,
    request: UpdateTopicRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新话题挑战（管理员）"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限执行此操作"
        )

    topic, error = update_topic_challenge(
        db=db,
        topic_id=topic_id,
        title=request.title,
        description=request.description,
        topic_tag=request.topic_tag,
        banner_image_url=request.banner_image_url,
        cover_image_url=request.cover_image_url,
        start_time=request.start_time,
        end_time=request.end_time,
        status=request.status,
        reward_config=request.reward_config,
        max_participants=request.max_participants,
        is_featured=request.is_featured,
        sort_order=request.sort_order,
    )

    if not topic:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error or "更新失败"
        )

    return ApiResponse(
        message="更新成功",
        data=build_topic_response(topic)
    )


@router.post("/{topic_id}/settle", response_model=ApiResponse)
def settle_rewards(
    topic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """结算话题奖励（管理员）"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限执行此操作"
        )

    settled_count, error = settle_topic_rewards(db=db, topic_id=topic_id)

    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )

    return ApiResponse(
        message="结算成功",
        data={"settled_count": settled_count}
    )
