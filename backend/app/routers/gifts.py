from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from app.database import get_db
from app.models import User
from app.routers.users import get_current_user, get_current_active_user
from app.schemas import (
    ApiResponse, GiftResponse, GiftSendRequest,
    GiftTransactionResponse, UserGiftDisplayResponse
)
from app.services.gift_service import (
    init_default_gifts, get_active_gifts,
    get_gift_by_id, send_gift,
    get_user_received_gifts, get_user_sent_gifts,
    display_gift_on_profile, remove_gift_from_display,
    get_user_displayed_gifts, set_gift_featured,
    get_gift_statistics
)

router = APIRouter(tags=["虚拟礼物"])


def init_gift_data(db: Session):
    init_default_gifts(db)


@router.get("/shop", response_model=ApiResponse)
def get_gift_shop(
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    init_gift_data(db)
    
    gifts = get_active_gifts(db)
    
    gifts_response = [
        GiftResponse.model_validate(g).model_dump()
        for g in gifts
    ]
    
    user_balance = None
    if current_user:
        user_balance = {
            "stardust_points": current_user.stardust_point_balance,
            "stardust_fragments": current_user.stardust_fragment_balance
        }
    
    return ApiResponse(
        message="success",
        data={
            "gifts": gifts_response,
            "user_balance": user_balance
        }
    )


@router.post("/send", response_model=ApiResponse)
def send_gift_to_user(
    request: GiftSendRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    init_gift_data(db)
    
    receiver_id = request.receiver_id
    
    if receiver_id is None and request.receiver_identifier:
        identifier = request.receiver_identifier.strip()
        try:
            receiver_id = int(identifier)
        except ValueError:
            receiver = db.query(User).filter(User.username == identifier).first()
            if not receiver:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"未找到用户: {identifier}"
                )
            receiver_id = receiver.id
    
    if receiver_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请指定接收用户"
        )
    
    transaction, error = send_gift(
        db=db,
        sender_id=current_user.id,
        receiver_id=receiver_id,
        gift_id=request.gift_id,
        quantity=request.quantity,
        message=request.message,
        is_anonymous=request.is_anonymous
    )
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error or "赠送失败"
        )
    
    transaction_response = GiftTransactionResponse.model_validate(transaction).model_dump()
    transaction_response["sender_name"] = current_user.username if not transaction.is_anonymous else None
    
    receiver = db.query(User).filter(User.id == transaction.receiver_id).first()
    if receiver:
        transaction_response["receiver_name"] = receiver.username
    
    return ApiResponse(
        message="礼物赠送成功",
        data=transaction_response
    )


@router.get("/received", response_model=ApiResponse)
def get_my_received_gifts(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    gifts = get_user_received_gifts(db, current_user.id, limit, offset)
    
    gifts_response = []
    for g in gifts:
        g_dict = GiftTransactionResponse.model_validate(g).model_dump()
        
        if not g.is_anonymous:
            sender = db.query(User).filter(User.id == g.sender_id).first()
            if sender:
                g_dict["sender_name"] = sender.username
        
        g_dict["receiver_name"] = current_user.username
        gifts_response.append(g_dict)
    
    return ApiResponse(
        message="success",
        data={
            "gifts": gifts_response,
            "total": len(gifts_response)
        }
    )


@router.get("/sent", response_model=ApiResponse)
def get_my_sent_gifts(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    gifts = get_user_sent_gifts(db, current_user.id, limit, offset)
    
    gifts_response = []
    for g in gifts:
        g_dict = GiftTransactionResponse.model_validate(g).model_dump()
        g_dict["sender_name"] = current_user.username if not g.is_anonymous else None
        
        receiver = db.query(User).filter(User.id == g.receiver_id).first()
        if receiver:
            g_dict["receiver_name"] = receiver.username
        
        gifts_response.append(g_dict)
    
    return ApiResponse(
        message="success",
        data={
            "gifts": gifts_response,
            "total": len(gifts_response)
        }
    )


@router.get("/displayed", response_model=ApiResponse)
def get_my_displayed_gifts(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    displayed = get_user_displayed_gifts(db, current_user.id)
    
    displayed_response = [
        UserGiftDisplayResponse.model_validate(d).model_dump()
        for d in displayed
    ]
    
    return ApiResponse(
        message="success",
        data={"displayed_gifts": displayed_response}
    )


@router.post("/display/{transaction_id}", response_model=ApiResponse)
def display_gift(
    transaction_id: int,
    is_featured: bool = Query(False, description="是否设为精选展示"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    display, error = display_gift_on_profile(
        db=db,
        user_id=current_user.id,
        gift_transaction_id=transaction_id,
        is_featured=is_featured
    )
    
    if not display:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error or "展示失败"
        )
    
    return ApiResponse(
        message="礼物已添加到展示",
        data=UserGiftDisplayResponse.model_validate(display).model_dump()
    )


@router.delete("/display/{display_id}", response_model=ApiResponse)
def remove_displayed_gift(
    display_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    success, message = remove_gift_from_display(
        db=db,
        user_id=current_user.id,
        display_id=display_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return ApiResponse(message=message, data=None)


@router.put("/display/{display_id}/featured", response_model=ApiResponse)
def set_featured_gift(
    display_id: int,
    is_featured: bool = Query(True, description="是否设为精选"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    success, message = set_gift_featured(
        db=db,
        user_id=current_user.id,
        display_id=display_id,
        is_featured=is_featured
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return ApiResponse(message=message, data=None)


@router.get("/statistics", response_model=ApiResponse)
def get_my_gift_statistics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    stats = get_gift_statistics(db, current_user.id)
    
    return ApiResponse(
        message="success",
        data=stats
    )


@router.get("/user/{user_id}/displayed", response_model=ApiResponse)
def get_user_public_displayed_gifts(
    user_id: int,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_user = db.query(User).filter(User.id == user_id).first()
    
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    displayed = get_user_displayed_gifts(db, user_id)
    
    displayed_response = []
    for d in displayed:
        d_dict = UserGiftDisplayResponse.model_validate(d).model_dump()
        if d.is_featured:
            displayed_response.insert(0, d_dict)
        else:
            displayed_response.append(d_dict)
    
    return ApiResponse(
        message="success",
        data={
            "user_id": user_id,
            "username": target_user.username,
            "displayed_gifts": displayed_response
        }
    )


@router.post("/init-data", response_model=ApiResponse)
def initialize_gift_data(
    db: Session = Depends(get_db)
):
    init_gift_data(db)
    
    gifts_count = db.query(__import__('app.models', fromlist=['Gift']).Gift).count()
    
    return ApiResponse(
        message="礼物数据初始化完成",
        data={"gifts_count": gifts_count}
    )
