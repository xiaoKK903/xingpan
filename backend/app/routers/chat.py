from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.models import User, Conversation, Message
from app.schemas import (
    ChatRequest, 
    ChatResponse, 
    MessageResponse,
    ApiResponse
)
from app.routers.users import get_current_active_user

router = APIRouter()


def generate_ai_response(user_message: str) -> str:
    default_responses = [
        f"收到您的消息：\"{user_message}\"。这是一个测试回复，实际项目中请接入真实的AI服务。",
        "您好！我是AI智能客服助手。请问有什么可以帮助您的吗？",
        "感谢您的咨询。我正在学习中，请稍后再试或联系人工客服。",
    ]
    return default_responses[0]


@router.post("/", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def chat(
    chat_data: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    conversation_id = chat_data.conversation_id
    
    if conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        ).first()
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )
    else:
        conversation = Conversation(
            user_id=current_user.id,
            title=chat_data.message[:50] if len(chat_data.message) > 50 else chat_data.message
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        conversation_id = conversation.id
    
    user_message = Message(
        conversation_id=conversation_id,
        role="user",
        content=chat_data.message
    )
    db.add(user_message)
    
    ai_response_content = generate_ai_response(chat_data.message)
    assistant_message = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=ai_response_content
    )
    db.add(assistant_message)
    
    conversation.updated_at = datetime.utcnow()
    if not conversation.title or conversation.title == "新会话":
        conversation.title = chat_data.message[:50] if len(chat_data.message) > 50 else chat_data.message
    
    db.commit()
    db.refresh(user_message)
    db.refresh(assistant_message)
    
    return ApiResponse(
        code=201,
        message="发送成功",
        data=ChatResponse(
            conversation_id=conversation_id,
            user_message=MessageResponse.model_validate(user_message),
            assistant_message=MessageResponse.model_validate(assistant_message)
        ).model_dump()
    )
