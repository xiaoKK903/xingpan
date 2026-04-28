from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.database import get_db
from app.models import User, Conversation
from app.schemas import (
    ConversationCreate, 
    ConversationResponse, 
    ApiResponse
)
from app.routers.users import get_current_active_user

router = APIRouter()


@router.get("/", response_model=ApiResponse)
def get_conversations(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(Conversation.updated_at.desc()).offset(skip).limit(limit).all()
    
    total = db.query(Conversation).filter(Conversation.user_id == current_user.id).count()
    
    return ApiResponse(
        code=200,
        message="success",
        data={
            "items": [ConversationResponse.model_validate(c).model_dump() for c in conversations],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    )


@router.get("/{conversation_id}", response_model=ApiResponse)
def get_conversation(
    conversation_id: int,
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
    
    return ApiResponse(
        code=200,
        message="success",
        data=ConversationResponse.model_validate(conversation).model_dump()
    )


@router.post("/", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    conversation_data: ConversationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    new_conversation = Conversation(
        user_id=current_user.id,
        title=conversation_data.title
    )
    db.add(new_conversation)
    db.commit()
    db.refresh(new_conversation)
    
    return ApiResponse(
        code=201,
        message="创建成功",
        data={"conversation": ConversationResponse.model_validate(new_conversation).model_dump()}
    )


@router.put("/{conversation_id}", response_model=ApiResponse)
def update_conversation(
    conversation_id: int,
    conversation_data: ConversationCreate,
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
    
    conversation.title = conversation_data.title
    conversation.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(conversation)
    
    return ApiResponse(
        code=200,
        message="更新成功",
        data={"conversation": ConversationResponse.model_validate(conversation).model_dump()}
    )


@router.delete("/{conversation_id}", response_model=ApiResponse)
def delete_conversation(
    conversation_id: int,
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
    
    db.delete(conversation)
    db.commit()
    
    return ApiResponse(
        code=200,
        message="删除成功",
        data=None
    )
