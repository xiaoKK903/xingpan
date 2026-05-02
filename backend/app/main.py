from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import traceback
from datetime import datetime

from app.routers import users, conversations, messages, chat, astro, geo, charts, reports, synastry, ai_interpretation, daily_horoscope, synastry_analysis, transit, social_icebreaker, group_matrix, life_script, workbench, plaza, boss_battle, energy_weather, star_resonance, advanced_prediction, exclusive_items, element_quest, phase_connect, network_chain, synastry_enhanced, private_chat, photocard, checkin
from app.routers import vip, gifts, report_shop, payment
from app.schemas import ApiResponse

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    
    启动时初始化任务调度器
    关闭时停止任务调度器
    """
    from app.services.task_executor import task_executor
    from app.redis_client import redis_manager
    
    logger.info("正在初始化 Redis 连接...")
    await redis_manager.initialize()
    
    logger.info("正在初始化任务调度器...")
    task_executor.initialize()
    task_executor.start()
    
    logger.info("应用启动完成")
    
    yield
    
    logger.info("正在停止任务调度器...")
    task_executor.stop()
    
    logger.info("正在关闭 Redis 连接...")
    await redis_manager.close()
    
    logger.info("应用已关闭")


app = FastAPI(
    title="AI智能客服系统",
    description="基于FastAPI的AI智能客服系统后端API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/api/users", tags=["用户管理"])
app.include_router(conversations.router, prefix="/api/conversations", tags=["会话管理"])
app.include_router(messages.router, prefix="/api/messages", tags=["消息管理"])
app.include_router(chat.router, prefix="/api/chat", tags=["聊天接口"])
app.include_router(astro.router, prefix="/api/astro", tags=["星盘计算"])
app.include_router(geo.router, prefix="/api/geo", tags=["地理编码"])
app.include_router(charts.router, prefix="/api/charts", tags=["星盘存档"])
app.include_router(reports.router, prefix="/api/reports", tags=["报告生成"])
app.include_router(synastry.router, prefix="/api/synastry", tags=["双人合盘"])
app.include_router(ai_interpretation.router, prefix="/api/ai", tags=["AI解读"])
app.include_router(daily_horoscope.router, prefix="/api/horoscope", tags=["每日运势"])
app.include_router(synastry_analysis.router, prefix="/api/synastry-analysis", tags=["合盘深度分析"])
app.include_router(transit.router, prefix="/api/transit", tags=["行运气象站"])
app.include_router(social_icebreaker.router, prefix="/api/social-icebreaker", tags=["社交破冰助手"])
app.include_router(group_matrix.router, prefix="/api/group-matrix", tags=["多人星盘关系矩阵"])
app.include_router(life_script.router, prefix="/api/life-script", tags=["人生剧本时空穿梭机"])
app.include_router(workbench.router, prefix="/api/workbench", tags=["占星师工作台"])
app.include_router(plaza.router, prefix="/api/plaza", tags=["平行人生广场"])
app.include_router(boss_battle.router, prefix="/api/boss-battle", tags=["星象BOSS副本"])
app.include_router(energy_weather.router, prefix="/api/energy-weather", tags=["能量气象站"])
app.include_router(star_resonance.router, prefix="/api/star-resonance", tags=["星能共鸣池"])
app.include_router(advanced_prediction.router, prefix="/api/prediction", tags=["增强版竞猜系统"])
app.include_router(exclusive_items.router, prefix="/api/shop", tags=["专属物品商城"])
app.include_router(element_quest.router, prefix="/api/element-quest", tags=["元素缺角寻宝"])
app.include_router(phase_connect.router, prefix="/api/phase-connect", tags=["相位连连看"])
app.include_router(network_chain.router, prefix="/api/network-chain", tags=["星盘人脉链"])
app.include_router(synastry_enhanced.router, prefix="/api/synastry-enhanced", tags=["合盘增强功能"])
app.include_router(private_chat.router, prefix="/api/private-chat", tags=["用户私聊"])
app.include_router(photocard.router, prefix="/api/photocard", tags=["合影卡牌"])

app.include_router(vip.router, prefix="/api/vip", tags=["VIP会员"])
app.include_router(gifts.router, prefix="/api/gifts", tags=["虚拟礼物"])
app.include_router(report_shop.router, prefix="/api/report-shop", tags=["付费报告"])
app.include_router(payment.router, prefix="/api/payment", tags=["支付系统"])
app.include_router(checkin.router, prefix="/api/checkin", tags=["每日签到"])


@app.get("/")
def root():
    return {"message": "AI智能客服系统运行中", "version": "1.0.0"}


@app.get("/health")
def health_check():
    """健康检查接口"""
    from app.services.task_executor import task_executor
    task_status = task_executor.get_task_status()
    
    return {
        "status": "healthy",
        "timestamp": "now",
        "tasks": task_status
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    全局异常处理器 - 捕获所有未处理的异常
    确保服务不会崩溃，返回友好的错误响应
    """
    error_id = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    
    logger.error(
        f"[全局异常捕获] ErrorID: {error_id} | "
        f"Path: {request.url.path} | "
        f"Method: {request.method} | "
        f"Exception: {type(exc).__name__} | "
        f"Message: {str(exc)}"
    )
    logger.error(f"[全局异常捕获] ErrorID: {error_id} | Traceback: {traceback.format_exc()}")
    
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.status_code,
                "message": exc.detail,
                "data": None,
                "error_id": error_id
            }
        )
    
    return JSONResponse(
        status_code=200,
        content={
            "code": 500,
            "message": "系统繁忙，请稍后重试",
            "data": None,
            "error_id": error_id
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    HTTP异常处理器
    """
    error_id = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    
    logger.warning(
        f"[HTTP异常] ErrorID: {error_id} | "
        f"Path: {request.url.path} | "
        f"Status: {exc.status_code} | "
        f"Detail: {exc.detail}"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": exc.detail,
            "data": None,
            "error_id": error_id
        }
    )
