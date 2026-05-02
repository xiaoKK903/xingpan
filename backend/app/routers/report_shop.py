from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import json

from app.database import get_db
from app.models import User
from app.routers.users import get_current_user, get_current_active_user
from app.schemas import (
    ApiResponse, ReportProductResponse, ReportPurchaseRequest,
    UserReportPurchaseResponse
)
from app.services.report_service import (
    init_report_products, get_active_report_products,
    get_report_product_by_id, purchase_report,
    get_user_purchased_reports, get_report_purchase_by_id,
    view_report, check_report_access, get_report_statistics
)
from app.services.vip_service import (
    check_vip_status, get_free_reports_remaining
)

router = APIRouter(tags=["付费报告"])


def init_report_data(db: Session):
    init_report_products(db)


def safe_model_validate_product(p) -> dict:
    """安全地将 ReportProduct 模型转换为字典，处理 JSON 字符串字段"""
    sections_included_list = None
    if p.sections_included:
        try:
            sections_included_list = json.loads(p.sections_included)
        except (json.JSONDecodeError, TypeError):
            sections_included_list = []
    
    return {
        "id": p.id,
        "product_key": p.product_key,
        "name": p.name,
        "description": p.description,
        "product_type": p.product_type,
        "price": p.price,
        "original_price": p.original_price,
        "currency_type": p.currency_type,
        "report_template": p.report_template,
        "sections_included": sections_included_list,
        "is_active": p.is_active,
        "sort_order": p.sort_order,
        "icon_url": p.icon_url,
        "preview_image_url": p.preview_image_url
    }


def safe_model_validate_purchase(p) -> dict:
    """安全地将 UserReportPurchase 模型转换为字典，处理 JSON 字符串字段"""
    report_data_dict = None
    if p.report_data:
        try:
            report_data_dict = json.loads(p.report_data)
        except (json.JSONDecodeError, TypeError):
            report_data_dict = {}
    
    return {
        "id": p.id,
        "purchase_no": p.purchase_no,
        "user_id": p.user_id,
        "product_id": p.product_id,
        "product_key": p.product_key,
        "product_name": p.product_name,
        "price_paid": p.price_paid,
        "currency_type": p.currency_type,
        "is_free_vip": p.is_free_vip,
        "chart_id": p.chart_id,
        "synastry_record_id": p.synastry_record_id,
        "group_matrix_id": p.group_matrix_id,
        "report_data": report_data_dict,
        "report_pdf_url": p.report_pdf_url,
        "view_count": p.view_count if p.view_count else 0,
        "last_viewed_at": p.last_viewed_at,
        "is_active": p.is_active,
        "created_at": p.created_at
    }


@router.get("/shop", response_model=ApiResponse)
def get_report_shop(
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    init_report_data(db)
    
    products = get_active_report_products(db)
    
    products_response = []
    for p in products:
        p_dict = safe_model_validate_product(p)
        products_response.append(p_dict)
    
    user_vip_data = None
    free_reports_remaining = 0
    
    if current_user:
        is_vip, user_vip = check_vip_status(db, current_user.id)
        if is_vip:
            user_vip_data = {
                "is_vip": True,
                "plan_type": user_vip.plan_type
            }
            free_reports_remaining = get_free_reports_remaining(db, current_user.id)
    
    return ApiResponse(
        message="success",
        data={
            "products": products_response,
            "user_vip": user_vip_data,
            "free_reports_remaining": free_reports_remaining
        }
    )


@router.post("/purchase", response_model=ApiResponse)
def purchase_report_product(
    request: ReportPurchaseRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    init_report_data(db)
    
    purchase, error = purchase_report(
        db=db,
        user_id=current_user.id,
        product_id=request.product_id,
        chart_id=request.chart_id,
        synastry_record_id=request.synastry_record_id,
        group_matrix_id=request.group_matrix_id,
        use_free_vip=request.use_free_vip
    )
    
    if not purchase:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error or "购买失败"
        )
    
    purchase_response = safe_model_validate_purchase(purchase)
    
    return ApiResponse(
        message="报告购买成功",
        data=purchase_response
    )


@router.get("/purchased", response_model=ApiResponse)
def get_my_purchased_reports(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    reports = get_user_purchased_reports(db, current_user.id, limit, offset)
    
    reports_response = []
    for r in reports:
        r_dict = safe_model_validate_purchase(r)
        reports_response.append(r_dict)
    
    return ApiResponse(
        message="success",
        data={
            "reports": reports_response,
            "total": len(reports_response)
        }
    )


@router.get("/view/{purchase_id}", response_model=ApiResponse)
def view_purchased_report(
    purchase_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    report_data, error = view_report(
        db=db,
        purchase_id=purchase_id,
        user_id=current_user.id
    )
    
    if report_data is None and error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error
        )
    
    purchase = get_report_purchase_by_id(db, purchase_id, current_user.id)
    
    return ApiResponse(
        message="success",
        data={
            "purchase_id": purchase_id,
            "product_name": purchase.product_name if purchase else None,
            "product_key": purchase.product_key if purchase else None,
            "view_count": purchase.view_count if purchase else 0,
            "report_data": report_data
        }
    )


@router.get("/check-access", response_model=ApiResponse)
def check_my_report_access(
    product_key: str = Query(..., description="报告产品key"),
    chart_id: Optional[int] = Query(None, description="星盘ID"),
    synastry_record_id: Optional[int] = Query(None, description="合盘记录ID"),
    group_matrix_id: Optional[int] = Query(None, description="群组矩阵ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    has_access, purchase = check_report_access(
        db=db,
        user_id=current_user.id,
        product_key=product_key,
        chart_id=chart_id,
        synastry_record_id=synastry_record_id,
        group_matrix_id=group_matrix_id
    )
    
    purchase_data = None
    if purchase:
        purchase_data = safe_model_validate_purchase(purchase)
    
    return ApiResponse(
        message="success",
        data={
            "has_access": has_access,
            "purchase": purchase_data
        }
    )


@router.get("/statistics", response_model=ApiResponse)
def get_my_report_statistics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    stats = get_report_statistics(db, current_user.id)
    
    is_vip, _ = check_vip_status(db, current_user.id)
    free_reports_remaining = 0
    if is_vip:
        free_reports_remaining = get_free_reports_remaining(db, current_user.id)
    
    stats["free_reports_remaining"] = free_reports_remaining
    stats["is_vip"] = is_vip
    
    return ApiResponse(
        message="success",
        data=stats
    )


@router.post("/init-data", response_model=ApiResponse)
def initialize_report_data(
    db: Session = Depends(get_db)
):
    init_report_data(db)
    
    products_count = db.query(__import__('app.models', fromlist=['ReportProduct']).ReportProduct).count()
    
    return ApiResponse(
        message="报告数据初始化完成",
        data={"products_count": products_count}
    )
