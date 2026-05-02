from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from app.database import get_db
from app.models import User
from app.routers.users import get_current_user, get_current_active_user
from app.schemas import (
    ApiResponse, PaymentOrderCreate, PaymentOrderResponse,
    PaymentSimulateRequest
)
from app.services.payment_service import (
    create_payment_order, get_order_by_no,
    get_order_by_id, get_user_orders,
    simulate_payment, cancel_order, refund_order,
    get_order_payment_info, get_payment_statistics,
    process_expired_orders
)

router = APIRouter(tags=["支付系统"])


@router.post("/order/create", response_model=ApiResponse)
def create_order(
    request: PaymentOrderCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    order, error = create_payment_order(
        db=db,
        user_id=current_user.id,
        payment_type=request.payment_type,
        amount=request.amount,
        related_type=request.related_type,
        related_id=request.related_id,
        payment_method=request.payment_method
    )
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error or "创建订单失败"
        )
    
    order_response = PaymentOrderResponse.model_validate(order).model_dump()
    order_response["payment_url"] = f"/api/payment/sandbox/pay?order_no={order.order_no}" if order.is_sandbox else None
    
    return ApiResponse(
        message="订单创建成功",
        data=order_response
    )


@router.get("/order/{order_no}", response_model=ApiResponse)
def get_order(
    order_no: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    order = get_order_by_no(db, order_no)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )
    
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权查看此订单"
        )
    
    order_response = PaymentOrderResponse.model_validate(order).model_dump()
    if order.is_sandbox and order.status == "pending":
        order_response["payment_url"] = f"/api/payment/sandbox/pay?order_no={order.order_no}"
    
    return ApiResponse(
        message="success",
        data=order_response
    )


@router.get("/orders", response_model=ApiResponse)
def get_my_orders(
    status: Optional[str] = Query(None, description="订单状态筛选"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    orders = get_user_orders(db, current_user.id, status, limit, offset)
    
    orders_response = [
        PaymentOrderResponse.model_validate(o).model_dump()
        for o in orders
    ]
    
    return ApiResponse(
        message="success",
        data={
            "orders": orders_response,
            "total": len(orders_response)
        }
    )


@router.post("/order/{order_no}/cancel", response_model=ApiResponse)
def cancel_my_order(
    order_no: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    success, message = cancel_order(db, order_no, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return ApiResponse(message=message, data=None)


@router.get("/sandbox/pay", response_class=HTMLResponse)
def sandbox_payment_page(
    order_no: str = Query(..., description="订单号"),
    db: Session = Depends(get_db)
):
    order = get_order_by_no(db, order_no)
    
    if not order:
        return HTMLResponse(content="<html><body><h1>订单不存在</h1></body></html>", status_code=404)
    
    if order.status != "pending":
        return HTMLResponse(content=f"""
        <html>
        <head><title>支付结果</title></head>
        <body>
            <h1>订单状态: {order.status}</h1>
            <p>订单号: {order.order_no}</p>
            <p>金额: ¥{order.final_amount / 100:.2f}</p>
        </body>
        </html>
        """)
    
    amount_yuan = order.final_amount / 100
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>沙箱模拟支付</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
            .card {{ border: 1px solid #ddd; border-radius: 8px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #333; }}
            .amount {{ font-size: 32px; color: #e53e3e; font-weight: bold; margin: 20px 0; }}
            .btn-group {{ margin-top: 30px; }}
            button {{ padding: 12px 30px; font-size: 16px; border: none; border-radius: 4px; cursor: pointer; margin-right: 10px; }}
            .btn-success {{ background: #38a169; color: white; }}
            .btn-fail {{ background: #e53e3e; color: white; }}
            .btn-success:hover {{ background: #2f855a; }}
            .btn-fail:hover {{ background: #c53030; }}
            .info {{ background: #f7fafc; padding: 15px; border-radius: 4px; margin: 15px 0; }}
            .warning {{ background: #fffaf0; padding: 15px; border-radius: 4px; margin: 15px 0; border-left: 4px solid #ed8936; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🔒 沙箱模拟支付</h1>
            <div class="info">
                <p><strong>订单号:</strong> {order.order_no}</p>
                <p><strong>支付类型:</strong> {order.payment_type}</p>
                <p><strong>环境:</strong> 沙箱测试 (Sandbox)</p>
            </div>
            <div class="amount">¥ {amount_yuan:.2f}</div>
            <div class="warning">
                <strong>⚠️ 这是模拟支付环境</strong><br>
                点击以下按钮模拟支付成功或失败，不会产生真实支付。
            </div>
            <div class="btn-group">
                <button class="btn-success" onclick="simulatePayment(true)">✅ 模拟支付成功</button>
                <button class="btn-fail" onclick="simulatePayment(false)">❌ 模拟支付失败</button>
            </div>
        </div>
        
        <script>
            async function simulatePayment(success) {{
                try {{
                    const response = await fetch('/api/payment/sandbox/simulate', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify({{
                            order_no: '{order.order_no}',
                            success: success
                        }})
                    }});
                    
                    const result = await response.json();
                    
                    if (result.code === 200) {{
                        alert(success ? '✅ 支付成功！' : '❌ 支付失败');
                        window.location.reload();
                    }} else {{
                        alert('操作失败: ' + (result.detail || result.message));
                    }}
                }} catch (error) {{
                    alert('请求出错: ' + error.message);
                }}
            }}
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)


@router.post("/sandbox/simulate", response_model=ApiResponse)
def simulate_sandbox_payment(
    request: PaymentSimulateRequest,
    db: Session = Depends(get_db)
):
    order, error = simulate_payment(
        db=db,
        order_no=request.order_no,
        success=request.success
    )
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error or "模拟支付失败"
        )
    
    return ApiResponse(
        message="模拟支付完成",
        data={
            "order_no": order.order_no,
            "status": order.status,
            "paid_at": order.paid_at.isoformat() if order.paid_at else None
        }
    )


@router.get("/sandbox/quick-pay/{order_no}", response_model=ApiResponse)
def quick_sandbox_payment(
    order_no: str,
    success: bool = Query(True, description="是否成功"),
    db: Session = Depends(get_db)
):
    order, error = simulate_payment(
        db=db,
        order_no=order_no,
        success=success
    )
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error or "模拟支付失败"
        )
    
    return ApiResponse(
        message="快速模拟支付完成",
        data={
            "order_no": order.order_no,
            "status": order.status,
            "paid_at": order.paid_at.isoformat() if order.paid_at else None
        }
    )


@router.get("/statistics", response_model=ApiResponse)
def get_my_payment_statistics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    stats = get_payment_statistics(db, current_user.id)
    
    return ApiResponse(
        message="success",
        data=stats
    )


@router.post("/admin/process-expired", response_model=ApiResponse)
def admin_process_expired_orders(
    db: Session = Depends(get_db)
):
    count = process_expired_orders(db)
    
    return ApiResponse(
        message=f"已处理 {count} 个过期订单",
        data={"processed_count": count}
    )
