import logging
import asyncio
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)


class TaskScheduler:
    """
    任务调度器
    
    职责：
    - 管理定时任务
    - 提供任务注册、启动、停止接口
    - 支持 IntervalTrigger 和 CronTrigger
    """
    
    _instance: Optional['TaskScheduler'] = None
    _scheduler: Optional[AsyncIOScheduler] = None
    _tasks: Dict[str, Dict[str, Any]] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def initialize(self):
        """初始化调度器"""
        if self._scheduler is None:
            self._scheduler = AsyncIOScheduler()
            logger.info("任务调度器已初始化")
    
    def start(self):
        """启动调度器"""
        if self._scheduler and not self._scheduler.running:
            self._scheduler.start()
            logger.info("任务调度器已启动")
    
    def stop(self):
        """停止调度器"""
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown()
            logger.info("任务调度器已停止")
    
    def add_interval_task(
        self,
        task_id: str,
        func: Callable,
        minutes: int = 5,
        seconds: int = 0,
        **kwargs
    ):
        """
        添加间隔执行任务
        
        Args:
            task_id: 任务ID
            func: 执行函数
            minutes: 间隔分钟数
            seconds: 间隔秒数
            **kwargs: 传递给函数的参数
        """
        if not self._scheduler:
            logger.warning("调度器未初始化，无法添加任务")
            return
        
        trigger = IntervalTrigger(minutes=minutes, seconds=seconds)
        
        job = self._scheduler.add_job(
            func,
            trigger=trigger,
            id=task_id,
            kwargs=kwargs,
            replace_existing=True
        )
        
        self._tasks[task_id] = {
            "id": task_id,
            "func": func,
            "trigger_type": "interval",
            "interval_minutes": minutes,
            "interval_seconds": seconds,
            "created_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"已添加间隔任务: {task_id}, 间隔: {minutes}分{seconds}秒")
    
    def add_cron_task(
        self,
        task_id: str,
        func: Callable,
        hour: Optional[int] = None,
        minute: int = 0,
        **kwargs
    ):
        """
        添加 Cron 定时任务
        
        Args:
            task_id: 任务ID
            func: 执行函数
            hour: 执行小时（None 表示每小时）
            minute: 执行分钟
            **kwargs: 传递给函数的参数
        """
        if not self._scheduler:
            logger.warning("调度器未初始化，无法添加任务")
            return
        
        trigger = CronTrigger(hour=hour, minute=minute)
        
        job = self._scheduler.add_job(
            func,
            trigger=trigger,
            id=task_id,
            kwargs=kwargs,
            replace_existing=True
        )
        
        self._tasks[task_id] = {
            "id": task_id,
            "func": func,
            "trigger_type": "cron",
            "hour": hour,
            "minute": minute,
            "created_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"已添加Cron任务: {task_id}, 时间: {hour or '*'}:{minute:02d}")
    
    def remove_task(self, task_id: str):
        """移除任务"""
        if self._scheduler:
            self._scheduler.remove_job(task_id)
        
        if task_id in self._tasks:
            del self._tasks[task_id]
        
        logger.info(f"已移除任务: {task_id}")
    
    def get_tasks(self) -> List[Dict[str, Any]]:
        """获取所有任务列表"""
        return list(self._tasks.values())
    
    def pause_task(self, task_id: str):
        """暂停任务"""
        if self._scheduler:
            self._scheduler.pause_job(task_id)
            logger.info(f"已暂停任务: {task_id}")
    
    def resume_task(self, task_id: str):
        """恢复任务"""
        if self._scheduler:
            self._scheduler.resume_job(task_id)
            logger.info(f"已恢复任务: {task_id}")


task_scheduler = TaskScheduler()


def get_task_scheduler() -> TaskScheduler:
    """获取任务调度器单例"""
    return task_scheduler
