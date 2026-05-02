from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.schemas import ApiResponse
from app.database import get_db
from app.models import (
    User,
    SessionType,
    RewardAssetType,
    OracleDataSource
)
from app.routers.users import get_current_user, get_current_user_optional
from app.services.advanced_prediction_service import (
    get_advanced_prediction_service,
    AdvancedPredictionService
)
from app.services.exclusive_item_service import (
    get_exclusive_item_service,
    ExclusiveItemService
)
from app.services.secure_prediction_service import (
    get_secure_prediction_service,
    SecurePredictionService,
    VoteErrorCode
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["增强版竞猜系统"])


class CastVoteRequest(BaseModel):
    prediction_id: int = Field(..., description="预测场次ID")
    selected_option: str = Field(..., description="选择的选项值")
    confidence: int = Field(50, ge=0, le=100, description="信心值 0-100")
    use_asset: str = Field("fragment", description="使用的资产类型: fragment, point, ticket")


class ManualResolutionRequest(BaseModel):
    prediction_id: int = Field(..., description="预测场次ID")
    correct_option: str = Field(..., description="正确选项值")
    reason: str = Field("", description="结算原因")


class PurchaseItemRequest(BaseModel):
    item_id: int = Field(..., description="物品ID")
    use_currency: str = Field("point", description="使用的货币: point, fragment")


@router.get("/themes", response_model=ApiResponse)
async def get_prediction_themes(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    获取所有活跃的固定主题
    """
    try:
        service = get_advanced_prediction_service()
        themes = service.get_active_themes(db)
        
        return ApiResponse(
            message="获取固定主题成功",
            data={
                "themes": themes,
                "count": len(themes)
            }
        )
        
    except Exception as e:
        logger.error(f"获取固定主题失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取固定主题失败: {str(e)}"
        )


@router.post("/themes/init", response_model=ApiResponse)
async def initialize_default_themes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    初始化默认固定主题（管理员操作）
    """
    try:
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="仅管理员可执行此操作"
            )
        
        service = get_advanced_prediction_service()
        themes = service.initialize_fixed_themes(db)
        
        return ApiResponse(
            message=f"初始化固定主题成功，共 {len(themes)} 个",
            data={
                "themes": themes,
                "count": len(themes)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"初始化固定主题失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"初始化失败: {str(e)}"
        )


@router.get("/upcoming", response_model=ApiResponse)
async def get_upcoming_predictions(
    include_announced: bool = Query(True, description="是否包含已预告但未开始的场次"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    获取即将开始的场次（提前预告）
    """
    try:
        service = get_advanced_prediction_service()
        predictions = service.get_upcoming_predictions(db, include_announced)
        
        return ApiResponse(
            message="获取预告场次成功",
            data={
                "predictions": predictions,
                "count": len(predictions),
                "include_announced": include_announced
            }
        )
        
    except Exception as e:
        logger.error(f"获取预告场次失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取预告场次失败: {str(e)}"
        )


@router.get("/open", response_model=ApiResponse)
async def get_open_predictions(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    获取当前开放投票的场次
    """
    try:
        service = get_advanced_prediction_service()
        predictions = service.get_open_predictions(db)
        
        return ApiResponse(
            message="获取开放场次成功",
            data={
                "predictions": predictions,
                "count": len(predictions)
            }
        )
        
    except Exception as e:
        logger.error(f"获取开放场次失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取开放场次失败: {str(e)}"
        )


@router.get("/detail/{prediction_id}", response_model=ApiResponse)
async def get_prediction_detail(
    prediction_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    获取预测场次详情
    """
    try:
        from app.models import CollectivePrediction
        from sqlalchemy.orm import joinedload
        
        prediction = db.query(CollectivePrediction).filter(
            CollectivePrediction.id == prediction_id
        ).first()
        
        if not prediction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="预测场次不存在"
            )
        
        service = get_advanced_prediction_service()
        result = service._prediction_to_dict(prediction)
        
        if current_user:
            from app.models import PredictionVote
            user_votes = db.query(PredictionVote).filter(
                PredictionVote.prediction_id == prediction_id,
                PredictionVote.user_id == current_user.id
            ).all()
            
            result["user_votes"] = [service._vote_to_dict(v) for v in user_votes]
            result["user_vote_count"] = len(user_votes)
            
            validation = service.validate_vote(db, current_user.id, prediction_id)
            result["vote_validation"] = {
                "valid": validation.valid,
                "error_code": validation.error_code,
                "error_message": validation.error_message,
                "user_vote_count": validation.user_vote_count,
                "max_allowed": validation.max_allowed,
                "cost_required": validation.cost_required
            }
        
        return ApiResponse(
            message="获取场次详情成功",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取场次详情失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取场次详情失败: {str(e)}"
        )


@router.post("/validate-vote", response_model=ApiResponse)
async def validate_vote(
    prediction_id: int = Query(..., description="预测场次ID"),
    use_asset: str = Query("fragment", description="使用的资产类型: fragment, point, ticket"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    验证投票是否合法
    """
    try:
        service = get_advanced_prediction_service()
        validation = service.validate_vote(db, current_user.id, prediction_id, use_asset)
        
        return ApiResponse(
            message="验证完成",
            data={
                "valid": validation.valid,
                "error_code": validation.error_code,
                "error_message": validation.error_message,
                "user_vote_count": validation.user_vote_count,
                "max_allowed": validation.max_allowed,
                "cost_required": validation.cost_required,
                "user_balance": validation.user_balance
            }
        )
        
    except Exception as e:
        logger.error(f"验证投票失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"验证失败: {str(e)}"
        )


@router.post("/vote", response_model=ApiResponse)
async def cast_vote(
    request: CastVoteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    用户投票
    
    支持使用不同资产类型投票：
    - fragment: 星元碎片
    - point: 高阶星尘
    - ticket: 预言券
    
    如果用户是VIP，会自动应用会员加成
    """
    try:
        service = get_advanced_prediction_service()
        
        is_vip = current_user.is_superuser or False
        
        result = service.cast_vote(
            db=db,
            user_id=current_user.id,
            prediction_id=request.prediction_id,
            selected_option=request.selected_option,
            confidence=request.confidence,
            use_asset=request.use_asset,
            is_vip=is_vip
        )
        
        if not result.get("success"):
            return ApiResponse(
                message=result.get("error", "投票失败"),
                code=400,
                data={
                    "success": False,
                    "error_code": result.get("error_code"),
                    "error": result.get("error")
                }
            )
        
        return ApiResponse(
            message=result.get("message", "投票成功！"),
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"投票失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"投票失败: {str(e)}"
        )


@router.get("/my-history", response_model=ApiResponse)
async def get_my_prediction_history(
    limit: int = Query(20, ge=1, le=100, description="限制数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取我的预测历史
    """
    try:
        service = get_advanced_prediction_service()
        history = service.get_user_prediction_history(db, current_user.id, limit)
        
        correct_count = sum(
            1 for h in history 
            if h.get("vote", {}).get("is_correct") == True
        )
        total_count = len(history)
        accuracy_rate = round(correct_count / total_count * 100, 1) if total_count > 0 else 0
        
        return ApiResponse(
            message="获取预测历史成功",
            data={
                "history": history,
                "count": total_count,
                "correct_count": correct_count,
                "accuracy_rate": accuracy_rate
            }
        )
        
    except Exception as e:
        logger.error(f"获取预测历史失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取预测历史失败: {str(e)}"
        )


@router.get("/my-tags", response_model=ApiResponse)
async def get_my_tags(
    categories: Optional[str] = Query(None, description="标签类别，多个用逗号分隔"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取我的用户标签
    
    标签类别包括：
    - emotion: 情绪标签
    - constellation_behavior: 星座行为
    - voting_preference: 投票偏好
    - element_preference: 元素偏好
    - planet_preference: 行星偏好
    - activity_pattern: 活动模式
    - spending_habit: 消费习惯
    """
    try:
        service = get_advanced_prediction_service()
        
        category_list = None
        if categories:
            category_list = [c.strip() for c in categories.split(",")]
        
        tags = service.get_user_tags(db, current_user.id, category_list)
        
        return ApiResponse(
            message="获取用户标签成功",
            data={
                "tags": tags,
                "count": len(tags),
                "categories_filtered": category_list
            }
        )
        
    except Exception as e:
        logger.error(f"获取用户标签失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户标签失败: {str(e)}"
        )


@router.post("/admin/create-daily", response_model=ApiResponse)
async def create_daily_sessions(
    target_date: Optional[str] = Query(None, description="目标日期 YYYY-MM-DD，默认明天"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建每日场次（管理员操作）
    """
    try:
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="仅管理员可执行此操作"
            )
        
        service = get_advanced_prediction_service()
        predictions = service.create_daily_sessions(db, target_date)
        
        return ApiResponse(
            message=f"创建每日场次成功，共 {len(predictions)} 场",
            data={
                "predictions": predictions,
                "count": len(predictions),
                "target_date": target_date
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建每日场次失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建场次失败: {str(e)}"
        )


@router.post("/admin/create-weekly", response_model=ApiResponse)
async def create_weekly_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建每周场次（管理员操作）
    """
    try:
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="仅管理员可执行此操作"
            )
        
        service = get_advanced_prediction_service()
        predictions = service.create_weekly_sessions(db)
        
        return ApiResponse(
            message=f"创建每周场次成功，共 {len(predictions)} 场",
            data={
                "predictions": predictions,
                "count": len(predictions)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建每周场次失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建场次失败: {str(e)}"
        )


@router.post("/admin/resolve-oracle", response_model=ApiResponse)
async def resolve_prediction_oracle(
    prediction_id: int = Query(..., description="预测场次ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    使用预言机自动结算（管理员操作）
    
    根据场次配置的预言机数据源自动计算正确选项
    """
    try:
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="仅管理员可执行此操作"
            )
        
        service = get_advanced_prediction_service()
        result = service.resolve_prediction_oracle(db, prediction_id)
        
        if not result.success:
            return ApiResponse(
                message=result.error_message or "结算失败",
                code=400,
                data={
                    "success": False,
                    "prediction_id": result.prediction_id,
                    "error": result.error_message
                }
            )
        
        return ApiResponse(
            message=f"预言机结算成功！正确选项: {result.correct_option}",
            data={
                "success": True,
                "prediction_id": result.prediction_id,
                "correct_option": result.correct_option,
                "correct_count": result.correct_count,
                "incorrect_count": result.incorrect_count,
                "total_reward_distributed": result.total_reward_distributed,
                "evidence_summary": result.evidence_summary
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"预言机结算失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"结算失败: {str(e)}"
        )


@router.post("/admin/resolve-manual", response_model=ApiResponse)
async def resolve_prediction_manual(
    request: ManualResolutionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    人工控场结算（管理员操作）
    
    支持运营人员手动指定正确选项进行结算
    """
    try:
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="仅管理员可执行此操作"
            )
        
        service = get_advanced_prediction_service()
        result = service.resolve_prediction_manual(
            db=db,
            prediction_id=request.prediction_id,
            correct_option=request.correct_option,
            admin_id=current_user.id,
            reason=request.reason
        )
        
        if not result.success:
            return ApiResponse(
                message=result.error_message or "结算失败",
                code=400,
                data={
                    "success": False,
                    "prediction_id": result.prediction_id,
                    "error": result.error_message
                }
            )
        
        return ApiResponse(
            message=f"人工结算成功！正确选项: {result.correct_option}",
            data={
                "success": True,
                "prediction_id": result.prediction_id,
                "correct_option": result.correct_option,
                "correct_count": result.correct_count,
                "incorrect_count": result.incorrect_count,
                "total_reward_distributed": result.total_reward_distributed,
                "evidence_summary": result.evidence_summary
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"人工结算失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"结算失败: {str(e)}"
        )


@router.post("/vote-secure", response_model=ApiResponse)
async def cast_vote_secure(
    request: CastVoteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    fastapi_request: Request = None
):
    """
    安全投票（并发安全，带限流和异常检测）
    
    特性：
    - 行级锁保护，防止并发重复投票
    - 独立统计表，原子累加
    - 接口限流（分钟/小时/日限制）
    - 异常行为检测（防止脚本刷票）
    - 阶梯式付费规则
    """
    try:
        secure_service = get_secure_prediction_service()
        
        ip_address = None
        session_id = None
        
        if fastapi_request:
            try:
                ip_address = fastapi_request.client.host if fastapi_request.client else None
                session_id = fastapi_request.headers.get("X-Session-ID")
            except:
                pass
        
        is_vip = current_user.is_superuser or False
        
        result = secure_service.cast_vote_secure(
            db=db,
            user_id=current_user.id,
            prediction_id=request.prediction_id,
            selected_option=request.selected_option,
            use_asset_type=request.use_asset,
            confidence=request.confidence,
            is_vip=is_vip,
            ip_address=ip_address,
            session_id=session_id
        )
        
        if not result.success:
            return ApiResponse(
                message=result.error_message or "投票失败",
                code=400,
                data={
                    "success": False,
                    "error_code": result.error_code,
                    "error": result.error_message
                }
            )
        
        return ApiResponse(
            message="投票成功！",
            data={
                "success": True,
                "vote_id": result.vote_id,
                "vote_number": result.vote_number,
                "prediction_id": result.prediction_id,
                "selected_option": result.selected_option,
                "cost_amount": result.cost_amount,
                "cost_asset_type": result.cost_asset_type,
                "reward_multiplier": result.reward_multiplier
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"安全投票失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"投票失败: {str(e)}"
        )


@router.post("/claim-reward", response_model=ApiResponse)
async def claim_reward_secure(
    vote_id: int = Query(..., description="投票记录ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    fastapi_request: Request = None
):
    """
    安全领取奖励（防重复领取）
    
    特性：
    - 唯一索引防止重复领取
    - 审计日志记录
    - 事务保护
    """
    try:
        secure_service = get_secure_prediction_service()
        
        ip_address = None
        session_id = None
        
        if fastapi_request:
            try:
                ip_address = fastapi_request.client.host if fastapi_request.client else None
                session_id = fastapi_request.headers.get("X-Session-ID")
            except:
                pass
        
        result = secure_service.claim_reward_secure(
            db=db,
            user_id=current_user.id,
            vote_id=vote_id,
            ip_address=ip_address,
            session_id=session_id
        )
        
        if not result.get("success"):
            return ApiResponse(
                message=result.get("error", "领取失败"),
                code=400,
                data=result
            )
        
        return ApiResponse(
            message="奖励领取成功！",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"奖励领取失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"领取失败: {str(e)}"
        )


@router.get("/detail-optimized/{prediction_id}", response_model=ApiResponse)
async def get_prediction_detail_optimized(
    prediction_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    优化的场次详情查询（消除N+1问题）
    
    使用 JOIN 和预加载减少数据库查询次数
    """
    try:
        secure_service = get_secure_prediction_service()
        
        result = secure_service.get_prediction_detail_optimized(
            db=db,
            prediction_id=prediction_id,
            user_id=current_user.id if current_user else None
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"]
            )
        
        return ApiResponse(
            message="获取场次详情成功",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取场次详情失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取失败: {str(e)}"
        )


@router.get("/check-rate-limit", response_model=ApiResponse)
async def check_rate_limit(
    action_type: str = Query("vote", description="操作类型: vote, claim, etc."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    检查接口限流状态
    
    返回当前用户的剩余请求次数和风险评分
    """
    try:
        secure_service = get_secure_prediction_service()
        
        result = secure_service.check_rate_limit(
            db=db,
            user_id=current_user.id,
            action_type=action_type
        )
        
        return ApiResponse(
            message="限流检查完成",
            data={
                "allowed": result.allowed,
                "remaining": result.remaining,
                "reset_time": result.reset_time.isoformat() if result.reset_time else None,
                "block_reason": result.block_reason,
                "risk_score": result.risk_score
            }
        )
        
    except Exception as e:
        logger.error(f"限流检查失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"检查失败: {str(e)}"
        )


@router.get("/tiered-costs/{prediction_id}", response_model=ApiResponse)
async def get_tiered_costs(
    prediction_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    获取阶梯式付费规则
    
    返回场次各投票层级的费用配置
    """
    try:
        secure_service = get_secure_prediction_service()
        
        from app.models import TieredVoteCost, CollectivePrediction
        
        prediction = db.query(CollectivePrediction).filter(
            CollectivePrediction.id == prediction_id
        ).first()
        
        if not prediction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="预测场次不存在"
            )
        
        tiered_costs = db.query(TieredVoteCost).filter(
            TieredVoteCost.prediction_id == prediction_id,
            TieredVoteCost.is_active == True
        ).order_by(TieredVoteCost.vote_tier.asc()).all()
        
        if not tiered_costs:
            secure_service.get_tiered_cost(db, prediction_id, 1)
            tiered_costs = db.query(TieredVoteCost).filter(
                TieredVoteCost.prediction_id == prediction_id,
                TieredVoteCost.is_active == True
            ).order_by(TieredVoteCost.vote_tier.asc()).all()
        
        user_vote_count = 0
        if current_user:
            from app.models import PredictionVote
            user_vote_count = db.query(func.count(PredictionVote.id)).filter(
                PredictionVote.prediction_id == prediction_id,
                PredictionVote.user_id == current_user.id
            ).scalar() or 0
        
        return ApiResponse(
            message="获取阶梯式付费规则成功",
            data={
                "prediction_id": prediction_id,
                "max_votes_per_user": prediction.max_votes_per_user or 1,
                "user_vote_count": user_vote_count,
                "tiered_costs": [
                    {
                        "vote_tier": tc.vote_tier,
                        "allowed_asset_types": tc.allowed_asset_types.split(","),
                        "cost_fragment": tc.cost_fragment,
                        "cost_point": tc.cost_point,
                        "cost_ticket": tc.cost_ticket,
                        "reward_multiplier": tc.reward_multiplier,
                        "is_current_tier": user_vote_count + 1 == tc.vote_tier
                    }
                    for tc in tiered_costs
                ]
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取阶梯式付费规则失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取失败: {str(e)}"
        )
