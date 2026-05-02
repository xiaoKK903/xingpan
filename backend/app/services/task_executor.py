import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from app.database import SessionLocal
from app.services.task_scheduler import task_scheduler
from app.services.online_user_cache_service import online_user_cache_service
from app.services.data_archive_service import data_archive_service
from app.services.prediction_settlement_service import prediction_settlement_service
from app.services.community_energy_service import community_energy_service
from app.services.energy_weather_service import energy_weather_service
from app.services.websocket_manager import websocket_manager

logger = logging.getLogger(__name__)


class TaskExecutor:
    """
    任务执行器
    
    职责：
    - 定义并执行具体的异步任务
    - 与调度器集成
    - 处理任务执行结果
    """
    
    def __init__(self):
        self._initialized = False
    
    def initialize(self):
        """初始化任务执行器，注册所有定时任务"""
        if self._initialized:
            return
        
        task_scheduler.initialize()
        
        task_scheduler.add_interval_task(
            task_id="cleanup_online_users",
            func=self._cleanup_online_users_task,
            minutes=5
        )
        
        task_scheduler.add_interval_task(
            task_id="update_energy_snapshot",
            func=self._update_energy_snapshot_task,
            minutes=5
        )
        
        task_scheduler.add_interval_task(
            task_id="check_energy_mission_triggers",
            func=self._check_mission_triggers_task,
            minutes=15
        )
        
        task_scheduler.add_cron_task(
            task_id="archive_old_data",
            func=self._archive_data_task,
            hour=3,
            minute=0
        )
        
        task_scheduler.add_cron_task(
            task_id="create_daily_predictions",
            func=self._create_predictions_task,
            hour=0,
            minute=5
        )
        
        task_scheduler.add_cron_task(
            task_id="resolve_predictions",
            func=self._resolve_predictions_task,
            hour=23,
            minute=55
        )
        
        task_scheduler.add_cron_task(
            task_id="hourly_energy_weather",
            func=self._hourly_energy_weather_task,
            hour=None,
            minute=0
        )
        
        self._initialized = True
        logger.info("任务执行器已初始化，所有任务已注册")
    
    def start(self):
        """启动调度器"""
        task_scheduler.start()
        logger.info("任务调度器已启动")
    
    def stop(self):
        """停止调度器"""
        task_scheduler.stop()
        logger.info("任务调度器已停止")
    
    async def _cleanup_online_users_task(self):
        """
        清理过期在线用户任务
        
        每5分钟执行一次
        """
        try:
            await online_user_cache_service.cleanup_expired_users()
            logger.info("在线用户清理任务执行完成")
        except Exception as e:
            logger.error(f"在线用户清理任务失败: {e}")
    
    async def _update_energy_snapshot_task(self):
        """
        更新能量快照任务
        
        每5分钟执行一次，生成并推送新的能量快照
        """
        try:
            db = SessionLocal()
            try:
                snapshot = community_energy_service.create_snapshot(db, scope="global")
                
                snapshot_dict = {
                    "id": snapshot.id,
                    "snapshot_type": snapshot.snapshot_type,
                    "scope": snapshot.scope,
                    "online_users": snapshot.online_users,
                    "overall_energy_score": snapshot.overall_energy_score,
                    "overall_mood": snapshot.overall_mood,
                    "snapshot_at": snapshot.snapshot_at.isoformat() if snapshot.snapshot_at else None
                }
                
                await websocket_manager.broadcast(
                    message_type="energy_update",
                    data=snapshot_dict,
                    channel="global"
                )
                
                logger.info(f"能量快照更新任务执行完成，在线用户: {snapshot.online_users}")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"能量快照更新任务失败: {e}")
    
    async def _check_mission_triggers_task(self):
        """
        检查能量任务触发条件
        
        每15分钟执行一次
        """
        try:
            db = SessionLocal()
            try:
                weather = energy_weather_service.get_current_weather(db)
                
                if weather:
                    logger.info(f"检查任务触发条件 - 当前天气: {weather.get('weather_label', '未知')}")
                
                logger.info("任务触发检查完成")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"任务触发检查失败: {e}")
    
    async def _archive_data_task(self):
        """
        数据归档任务
        
        每天凌晨3点执行
        """
        try:
            db = SessionLocal()
            try:
                result = data_archive_service.run_full_archive(db)
                
                logger.info(f"数据归档任务执行完成: {result}")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"数据归档任务失败: {e}")
    
    async def _create_predictions_task(self):
        """
        创建每日预测任务
        
        每天凌晨0:05执行
        """
        try:
            db = SessionLocal()
            try:
                predictions = prediction_settlement_service.create_daily_predictions(db)
                
                logger.info(f"创建每日预测任务执行完成，创建了 {len(predictions)} 个预测")
                
                if predictions:
                    await websocket_manager.broadcast(
                        message_type="new_prediction",
                        data={
                            "predictions": predictions,
                            "message": "新的每日预测已上线"
                        },
                        channel="global"
                    )
            finally:
                db.close()
        except Exception as e:
            logger.error(f"创建每日预测任务失败: {e}")
    
    async def _resolve_predictions_task(self):
        """
        结算预测任务
        
        每天23:55执行，结算当日的预测
        """
        try:
            db = SessionLocal()
            try:
                result = prediction_settlement_service.resolve_daily_predictions(db)
                
                logger.info(f"预测结算任务执行完成: {result}")
                
                if result.get("resolved_count", 0) > 0:
                    await websocket_manager.broadcast(
                        message_type="prediction_settled",
                        data=result,
                        channel="global"
                    )
            finally:
                db.close()
        except Exception as e:
            logger.error(f"预测结算任务失败: {e}")
    
    async def _hourly_energy_weather_task(self):
        """
        每小时能量气象站任务
        
        每小时执行一次：
        1. 统计所有在线用户星盘
        2. 计算天象夹角
        3. 算出全场当日能量值
        4. 检测凶星天象并预警
        5. 根据集体情绪推送暖心小任务
        """
        try:
            db = SessionLocal()
            try:
                weather = energy_weather_service.calculate_hourly_energy(db)
                weather_dict = energy_weather_service._snapshot_to_dict(weather)
                
                has_warning = weather_dict.get("has_warning", False)
                is_critical = weather_dict.get("is_critical", False)
                
                if has_warning:
                    warning_type = "红色预警" if is_critical else "天气预警"
                    logger.warning(f"[{warning_type}] 检测到凶星天象！在线用户: {weather_dict.get('online_user_count')}, 能量分数: {weather_dict.get('overall_energy_score')}")
                    
                    ominous_events = weather_dict.get("ominous_events", [])
                    for event in ominous_events:
                        if event.get("is_warning"):
                            logger.warning(f"  - {event.get('name')}: {event.get('description')}")
                
                await websocket_manager.broadcast(
                    message_type="energy_weather_update",
                    data=weather_dict,
                    channel="global"
                )
                
                triggered_missions = weather_dict.get("triggered_missions", [])
                if triggered_missions:
                    logger.info(f"推送暖心小任务: {len(triggered_missions)} 个任务已生成")
                    
                    await websocket_manager.broadcast(
                        message_type="new_warm_missions",
                        data={
                            "missions": triggered_missions,
                            "collective_mood": weather_dict.get("collective_mood"),
                            "weather_label": weather_dict.get("weather_label"),
                            "has_warning": has_warning
                        },
                        channel="global"
                    )
                
                logger.info(
                    f"能量气象站每小时统计完成: "
                    f"在线用户={weather_dict.get('online_user_count')}, "
                    f"能量分数={weather_dict.get('overall_energy_score')}, "
                    f"天气={weather_dict.get('weather_label')}, "
                    f"预警={has_warning}"
                )
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"每小时能量气象站任务失败: {e}")
    
    def get_task_status(self) -> dict:
        """获取所有任务状态"""
        return {
            "initialized": self._initialized,
            "scheduler_running": task_scheduler._scheduler.running if task_scheduler._scheduler else False,
            "registered_tasks": task_scheduler.get_tasks()
        }


task_executor = TaskExecutor()


def get_task_executor() -> TaskExecutor:
    """获取任务执行器单例"""
    return task_executor
