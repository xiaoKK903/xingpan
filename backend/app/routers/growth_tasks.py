import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.database import get_db
from app.models import User
from app.routers.users import get_current_user, get_current_active_user
from app.schemas import ApiResponse
from app.services.growth_task_service import (
    get_growth_task_service,
    GrowthTaskService,
)
from app.models import GrowthTaskType

logger = logging.getLogger(__name__)
router = APIRouter(tags=["成长任务"])


def init_growth_tasks_data(db: Session):
    """初始化成长任务数据"""
    service = get_growth_task_service()
    service.initialize_default_tasks(db)


@router.get("/tasks", response_model=ApiResponse)
def get_growth_tasks(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    获取用户的成长任务列表
    """
    try:
        init_growth_tasks_data(db)
        
        service = get_growth_task_service()
        tasks = service.get_user_tasks(db, current_user.id, include_completed=True)
        
        completed_count = sum(1 for t in tasks if t.get("status") in ["completed", "claimed"])
        total_count = len(tasks)
        
        return ApiResponse(
            message="success",
            data={
                "tasks": tasks,
                "total_count": total_count,
                "completed_count": completed_count,
                "progress_percent": round((completed_count / total_count) * 100, 1) if total_count > 0 else 0
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取成长任务列表异常: 用户ID={current_user.id}, 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="获取成长任务列表失败，请稍后重试",
            data=None
        )


@router.get("/popup-status", response_model=ApiResponse)
def get_popup_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    获取首次登录弹窗状态
    """
    try:
        init_growth_tasks_data(db)
        
        service = get_growth_task_service()
        result = service.check_first_login_popup(db, current_user.id)
        
        if not result.get("success"):
            return ApiResponse(
                code=400,
                message=result.get("error", "获取弹窗状态失败"),
                data=None
            )
        
        return ApiResponse(
            message="success",
            data=result.get("data")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取弹窗状态异常: 用户ID={current_user.id}, 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="获取弹窗状态失败，请稍后重试",
            data=None
        )


@router.post("/popup-mark-seen", response_model=ApiResponse)
def mark_popup_seen(
    is_dismissed: bool = Query(False, description="是否是关闭弹窗"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    标记弹窗已显示
    """
    try:
        service = get_growth_task_service()
        result = service.mark_popup_seen(
            db, current_user.id,
            is_dismissed=is_dismissed
        )
        
        if not result.get("success"):
            return ApiResponse(
                code=400,
                message=result.get("error", "标记弹窗状态失败"),
                data=None
            )
        
        logger.info(f"用户 {current_user.id} 标记成长任务弹窗已显示, is_dismissed={is_dismissed}")
        
        return ApiResponse(
            message="success",
            data=result.get("data")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"标记弹窗状态异常: 用户ID={current_user.id}, 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="标记弹窗状态失败，请稍后重试",
            data=None
        )


@router.post("/claim-reward/{task_id}", response_model=ApiResponse)
def claim_task_reward(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    手动领取任务奖励
    """
    try:
        service = get_growth_task_service()
        result = service.claim_task_reward(db, current_user.id, task_id)
        
        if not result.get("success"):
            error_code = result.get("code", "CLAIM_FAILED")
            return ApiResponse(
                code=400,
                message=result.get("error", "领取奖励失败"),
                data={"error_code": error_code}
            )
        
        logger.info(f"用户 {current_user.id} 领取任务奖励成功, task_id={task_id}")
        
        return ApiResponse(
            message="奖励领取成功",
            data=result.get("data")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"领取任务奖励异常: 用户ID={current_user.id}, task_id={task_id}, 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="领取奖励失败，请稍后重试",
            data=None
        )


@router.post("/trigger-task", response_model=ApiResponse)
def trigger_task_completion(
    task_type: str = Query(..., description="任务类型"),
    chart_id: Optional[int] = Query(None, description="星盘ID（完善星盘任务用）"),
    synastry_record_id: Optional[int] = Query(None, description="合盘记录ID（双人合盘任务用）"),
    group_matrix_id: Optional[int] = Query(None, description="群组矩阵ID（加入群组任务用）"),
    share_log_id: Optional[int] = Query(None, description="分享日志ID（首次分享任务用）"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    触发任务完成检测
    
    这个接口应该在用户完成特定操作后被调用：
    - 创建星盘后：task_type=complete_chart
    - 完成合盘后：task_type=complete_synastry
    - 加入群组后：task_type=join_group
    - 签到后：task_type=daily_checkin
    - 分享后：task_type=first_share
    """
    try:
        init_growth_tasks_data(db)
        
        service = get_growth_task_service()
        
        kwargs = {}
        if chart_id:
            kwargs["chart_id"] = chart_id
        if synastry_record_id:
            kwargs["synastry_record_id"] = synastry_record_id
        if group_matrix_id:
            kwargs["group_matrix_id"] = group_matrix_id
        if share_log_id:
            kwargs["share_log_id"] = share_log_id
        
        result = service.check_task_completion(
            db, current_user.id, task_type, **kwargs
        )
        
        if not result.get("success"):
            return ApiResponse(
                code=400,
                message=result.get("error", "任务检测失败"),
                data=None
            )
        
        data = result.get("data", {})
        completed_count = data.get("completed_count", 0)
        
        if completed_count > 0:
            logger.info(f"用户 {current_user.id} 完成 {completed_count} 个成长任务, task_type={task_type}")
            return ApiResponse(
                message=f"完成 {completed_count} 个任务，奖励已发放",
                data=data
            )
        else:
            return ApiResponse(
                message="任务检测完成，没有新任务完成",
                data=data
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"触发任务完成异常: 用户ID={current_user.id}, task_type={task_type}, 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message="任务检测失败，请稍后重试",
            data=None
        )


@router.get("/task-types", response_model=ApiResponse)
def get_task_types(
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取任务类型列表
    """
    task_types = [
        {
            "type": GrowthTaskType.COMPLETE_CHART.value,
            "name": "完善星盘",
            "description": "创建个人星盘"
        },
        {
            "type": GrowthTaskType.COMPLETE_SYNASTRY.value,
            "name": "双人合盘",
            "description": "完成一次双人合盘分析"
        },
        {
            "type": GrowthTaskType.JOIN_GROUP.value,
            "name": "加入群组",
            "description": "创建或加入一个星盘群组"
        },
        {
            "type": GrowthTaskType.DAILY_CHECKIN.value,
            "name": "每日签到",
            "description": "完成第一次每日签到"
        },
        {
            "type": GrowthTaskType.FIRST_SHARE.value,
            "name": "首次分享",
            "description": "分享星盘或合盘结果"
        }
    ]
    
    return ApiResponse(
        message="success",
        data={"task_types": task_types}
    )


@router.post("/init-data", response_model=ApiResponse)
def initialize_growth_tasks_data(
    db: Session = Depends(get_db)
):
    """
    初始化成长任务数据（管理接口）
    """
    try:
        init_growth_tasks_data(db)
        
        from app.models import GrowthTask
        tasks_count = db.query(GrowthTask).count()
        
        return ApiResponse(
            message="成长任务数据初始化完成",
            data={
                "tasks_count": tasks_count
            }
        )
        
    except Exception as e:
        logger.error(f"初始化成长任务数据异常: 错误={str(e)}", exc_info=True)
        return ApiResponse(
            code=500,
            message=f"初始化失败: {str(e)}",
            data=None
        )
