from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import logging
import hashlib

from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.database import get_db
from app.models import User, UserPrivateChat, PrivateChatMessage, NetworkConnection, SynastryRecord
from app.routers.users import get_current_user, get_current_active_user
from app.schemas import ApiResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["用户私聊"])


def generate_chat_identifier(user_a_id: int, user_b_id: int) -> str:
    """生成唯一的聊天标识符"""
    min_id = min(user_a_id, user_b_id)
    max_id = max(user_a_id, user_b_id)
    return hashlib.md5(f"{min_id}_{max_id}".encode()).hexdigest()[:16]


class StartChatRequest(BaseModel):
    target_user_id: int
    match_source: Optional[str] = None
    match_source_id: Optional[int] = None
    compatibility_score: Optional[int] = None
    match_type: Optional[str] = None
    initial_message: Optional[str] = None


class SendMessageRequest(BaseModel):
    chat_id: int
    content: str
    message_type: str = "text"


class GetMessagesRequest(BaseModel):
    chat_id: int
    before_id: Optional[int] = None
    limit: int = 50


@router.post("/start", response_model=ApiResponse)
async def start_private_chat(
    request: StartChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """开始用户私聊"""
    try:
        if request.target_user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能与自己聊天"
            )
        
        target_user = db.query(User).filter(
            User.id == request.target_user_id,
            User.is_active == True
        ).first()
        
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="目标用户不存在或已禁用"
            )
        
        chat_identifier = generate_chat_identifier(current_user.id, request.target_user_id)
        
        existing_chat = db.query(UserPrivateChat).filter(
            UserPrivateChat.chat_identifier == chat_identifier
        ).first()
        
        if existing_chat:
            return ApiResponse(
                message="聊天已存在",
                data={
                    "chat_id": existing_chat.id,
                    "chat_identifier": existing_chat.chat_identifier,
                    "target_user_id": existing_chat.user_b_id if existing_chat.user_a_id == current_user.id else existing_chat.user_a_id
                }
            )
        
        user_a_id = min(current_user.id, request.target_user_id)
        user_b_id = max(current_user.id, request.target_user_id)
        
        new_chat = UserPrivateChat(
            user_a_id=user_a_id,
            user_b_id=user_b_id,
            chat_identifier=chat_identifier,
            match_source=request.match_source,
            match_source_id=request.match_source_id,
            match_compatibility_score=request.compatibility_score,
            match_type=request.match_type,
            is_active=True
        )
        
        db.add(new_chat)
        db.flush()
        
        if request.initial_message:
            message = PrivateChatMessage(
                chat_id=new_chat.id,
                sender_id=current_user.id,
                receiver_id=request.target_user_id,
                content=request.initial_message,
                message_type="text",
                is_read=False
            )
            db.add(message)
            
            new_chat.last_message_at = datetime.utcnow()
            new_chat.last_message_content = request.initial_message[:200]
            new_chat.last_message_sender_id = current_user.id
            
            if user_a_id == current_user.id:
                new_chat.unread_count_b = 1
            else:
                new_chat.unread_count_a = 1
        
        db.commit()
        db.refresh(new_chat)
        
        existing_conn = db.query(NetworkConnection).filter(
            NetworkConnection.from_user_id == current_user.id,
            NetworkConnection.to_user_id == request.target_user_id
        ).first()
        
        if existing_conn:
            existing_conn.private_chat_id = new_chat.id
            db.commit()
        
        target_user_name = target_user.username or f"用户{target_user.id}"
        
        return ApiResponse(
            message="聊天已创建",
            data={
                "chat_id": new_chat.id,
                "chat_identifier": new_chat.chat_identifier,
                "target_user": {
                    "id": target_user.id,
                    "name": target_user_name
                },
                "has_initial_message": bool(request.initial_message)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建私聊失败: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建聊天失败: {str(e)}"
        )


@router.post("/send", response_model=ApiResponse)
async def send_message(
    request: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """发送消息"""
    try:
        chat = db.query(UserPrivateChat).filter(
            UserPrivateChat.id == request.chat_id,
            or_(
                UserPrivateChat.user_a_id == current_user.id,
                UserPrivateChat.user_b_id == current_user.id
            )
        ).first()
        
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="聊天不存在或无权限访问"
            )
        
        if not chat.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="聊天已被禁用"
            )
        
        receiver_id = chat.user_b_id if chat.user_a_id == current_user.id else chat.user_a_id
        
        new_message = PrivateChatMessage(
            chat_id=chat.id,
            sender_id=current_user.id,
            receiver_id=receiver_id,
            content=request.content,
            message_type=request.message_type,
            is_read=False
        )
        
        db.add(new_message)
        db.flush()
        
        chat.last_message_at = datetime.utcnow()
        chat.last_message_content = request.content[:200]
        chat.last_message_sender_id = current_user.id
        
        if chat.user_a_id == current_user.id:
            chat.unread_count_b = (chat.unread_count_b or 0) + 1
        else:
            chat.unread_count_a = (chat.unread_count_a or 0) + 1
        
        db.commit()
        db.refresh(new_message)
        
        return ApiResponse(
            message="发送成功",
            data={
                "message_id": new_message.id,
                "chat_id": new_message.chat_id,
                "content": new_message.content,
                "created_at": new_message.created_at.isoformat() if new_message.created_at else None
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"发送消息失败: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发送消息失败: {str(e)}"
        )


@router.get("/list", response_model=ApiResponse)
async def get_chat_list(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取聊天列表"""
    try:
        chats = db.query(UserPrivateChat).filter(
            or_(
                UserPrivateChat.user_a_id == current_user.id,
                UserPrivateChat.user_b_id == current_user.id
            ),
            UserPrivateChat.is_active == True
        ).order_by(
            UserPrivateChat.last_message_at.desc().nulls_last(),
            UserPrivateChat.updated_at.desc()
        ).offset(skip).limit(limit).all()
        
        total = db.query(UserPrivateChat).filter(
            or_(
                UserPrivateChat.user_a_id == current_user.id,
                UserPrivateChat.user_b_id == current_user.id
            ),
            UserPrivateChat.is_active == True
        ).count()
        
        result = []
        for chat in chats:
            is_user_a = chat.user_a_id == current_user.id
            target_user_id = chat.user_b_id if is_user_a else chat.user_a_id
            unread_count = chat.unread_count_b if is_user_a else chat.unread_count_a
            
            target_user = db.query(User).filter(User.id == target_user_id).first()
            target_name = target_user.username if target_user else f"用户{target_user_id}"
            
            result.append({
                "chat_id": chat.id,
                "chat_identifier": chat.chat_identifier,
                "target_user": {
                    "id": target_user_id,
                    "name": target_name
                },
                "match_source": chat.match_source,
                "compatibility_score": chat.match_compatibility_score,
                "match_type": chat.match_type,
                "last_message": {
                    "content": chat.last_message_content,
                    "sender_id": chat.last_message_sender_id,
                    "at": chat.last_message_at.isoformat() if chat.last_message_at else None
                },
                "unread_count": unread_count or 0,
                "created_at": chat.created_at.isoformat() if chat.created_at else None,
                "updated_at": chat.updated_at.isoformat() if chat.updated_at else None
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
        logger.error(f"获取聊天列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取聊天列表失败: {str(e)}"
        )


@router.get("/{chat_id}/messages", response_model=ApiResponse)
async def get_chat_messages(
    chat_id: int,
    before_id: Optional[int] = Query(None, description="获取此ID之前的消息"),
    limit: int = Query(50, ge=1, le=200),
    mark_as_read: bool = Query(True, description="是否标记为已读"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取聊天消息"""
    try:
        chat = db.query(UserPrivateChat).filter(
            UserPrivateChat.id == chat_id,
            or_(
                UserPrivateChat.user_a_id == current_user.id,
                UserPrivateChat.user_b_id == current_user.id
            )
        ).first()
        
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="聊天不存在或无权限访问"
            )
        
        query = db.query(PrivateChatMessage).filter(
            PrivateChatMessage.chat_id == chat_id
        )
        
        if before_id:
            query = query.filter(PrivateChatMessage.id < before_id)
        
        messages = query.order_by(
            PrivateChatMessage.id.desc()
        ).limit(limit).all()
        
        messages = list(reversed(messages))
        
        if mark_as_read:
            is_user_a = chat.user_a_id == current_user.id
            unread_field = "unread_count_b" if is_user_a else "unread_count_a"
            
            unread_messages = db.query(PrivateChatMessage).filter(
                PrivateChatMessage.chat_id == chat_id,
                PrivateChatMessage.receiver_id == current_user.id,
                PrivateChatMessage.is_read == False
            ).all()
            
            for msg in unread_messages:
                msg.is_read = True
                msg.read_at = datetime.utcnow()
            
            if is_user_a:
                chat.unread_count_b = 0
            else:
                chat.unread_count_a = 0
            
            db.commit()
        
        result = []
        for msg in messages:
            result.append({
                "id": msg.id,
                "chat_id": msg.chat_id,
                "sender_id": msg.sender_id,
                "receiver_id": msg.receiver_id,
                "content": msg.content,
                "message_type": msg.message_type,
                "is_read": msg.is_read,
                "is_me": msg.sender_id == current_user.id,
                "created_at": msg.created_at.isoformat() if msg.created_at else None
            })
        
        return ApiResponse(
            message="获取成功",
            data={
                "chat_id": chat_id,
                "messages": result,
                "count": len(result)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取消息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取消息失败: {str(e)}"
        )


@router.post("/{chat_id}/read", response_model=ApiResponse)
async def mark_chat_as_read(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """标记聊天为已读"""
    try:
        chat = db.query(UserPrivateChat).filter(
            UserPrivateChat.id == chat_id,
            or_(
                UserPrivateChat.user_a_id == current_user.id,
                UserPrivateChat.user_b_id == current_user.id
            )
        ).first()
        
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="聊天不存在或无权限访问"
            )
        
        is_user_a = chat.user_a_id == current_user.id
        
        unread_messages = db.query(PrivateChatMessage).filter(
            PrivateChatMessage.chat_id == chat_id,
            PrivateChatMessage.receiver_id == current_user.id,
            PrivateChatMessage.is_read == False
        ).all()
        
        read_count = len(unread_messages)
        
        for msg in unread_messages:
            msg.is_read = True
            msg.read_at = datetime.utcnow()
        
        if is_user_a:
            chat.unread_count_b = 0
        else:
            chat.unread_count_a = 0
        
        db.commit()
        
        return ApiResponse(
            message="已标记为已读",
            data={
                "chat_id": chat_id,
                "marked_count": read_count
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"标记已读失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"标记已读失败: {str(e)}"
        )


@router.get("/unread/count", response_model=ApiResponse)
async def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取未读消息总数"""
    try:
        chats = db.query(UserPrivateChat).filter(
            or_(
                UserPrivateChat.user_a_id == current_user.id,
                UserPrivateChat.user_b_id == current_user.id
            ),
            UserPrivateChat.is_active == True
        ).all()
        
        total_unread = 0
        for chat in chats:
            is_user_a = chat.user_a_id == current_user.id
            unread = chat.unread_count_b if is_user_a else chat.unread_count_a
            total_unread += unread or 0
        
        return ApiResponse(
            message="获取成功",
            data={
                "total_unread": total_unread
            }
        )
        
    except Exception as e:
        logger.error(f"获取未读计数失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取未读计数失败: {str(e)}"
        )
