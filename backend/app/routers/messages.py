from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import User, Conversation, Message
from app.schemas import (
    MessageCreate, 
    MessageResponse, 
    ApiResponse
)
from app.routers.users import get_current_active_user

router = APIRouter()


@router.get("/conversation/{conversation_id}", response_model=ApiResponse)
def get_messages_by_conversation(
    conversation_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at.asc()).offset(skip).limit(limit).all()
    
    total = db.query(Message).filter(Message.conversation_id == conversation_id).count()
    
    return ApiResponse(
        code=200,
        message="success",
        data={
            "items": [MessageResponse.model_validate(m).model_dump() for m in messages],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    )


@router.get("/{message_id}", response_model=ApiResponse)
def get_message(
    message_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    message = db.query(Message).join(Conversation).filter(
        Message.id == message_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="消息不存在"
        )
    
    return ApiResponse(
        code=200,
        message="success",
        data=MessageResponse.model_validate(message).model_dump()
    )


@router.post("/", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_message(
    message_data: MessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    conversation = db.query(Conversation).filter(
        Conversation.id == message_data.conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    
    new_message = Message(
        conversation_id=message_data.conversation_id,
        role=message_data.role,
        content=message_data.content
    )
    db.add(new_message)
    conversation.updated_at = new_message.created_at
    db.commit()
    db.refresh(new_message)
    
    return ApiResponse(
        code=201,
        message="创建成功",
        data={"message": MessageResponse.model_validate(new_message).model_dump()}
    )


@router.delete("/{message_id}", response_model=ApiResponse)
def delete_message(
    message_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    message = db.query(Message).join(Conversation).filter(
        Message.id == message_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="消息不存在"
        )
    
    db.delete(message)
    db.commit()
    
    return ApiResponse(
        code=200,
        message="删除成功",
        data=None
    )
