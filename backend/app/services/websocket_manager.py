import logging
import json
import asyncio
from typing import Dict, Any, Optional, Set
from datetime import datetime
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    WebSocket 连接管理器
    
    职责：
    - 管理 WebSocket 连接
    - 实现实时消息推送
    - 支持按频道订阅/发布
    - 与 Redis Pub/Sub 集成（可选）
    """
    
    _instance: Optional['WebSocketManager'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._active_connections: Dict[str, Set[WebSocket]] = {}
            cls._instance._user_connections: Dict[int, WebSocket] = {}
        return cls._instance
    
    async def connect(
        self,
        websocket: WebSocket,
        channel: str = "global",
        user_id: Optional[int] = None
    ):
        """
        接受 WebSocket 连接
        
        Args:
            websocket: WebSocket 连接
            channel: 订阅频道
            user_id: 用户ID（可选）
        """
        await websocket.accept()
        
        if channel not in self._active_connections:
            self._active_connections[channel] = set()
        self._active_connections[channel].add(websocket)
        
        if user_id:
            self._user_connections[user_id] = websocket
        
        logger.info(f"WebSocket 连接建立: channel={channel}, user_id={user_id}")
        
        await self._send_message(
            websocket,
            "system",
            {
                "message": "连接成功",
                "channel": channel,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    async def disconnect(
        self,
        websocket: WebSocket,
        channel: str = "global",
        user_id: Optional[int] = None
    ):
        """
        断开 WebSocket 连接
        
        Args:
            websocket: WebSocket 连接
            channel: 订阅频道
            user_id: 用户ID（可选）
        """
        if channel in self._active_connections:
            if websocket in self._active_connections[channel]:
                self._active_connections[channel].remove(websocket)
        
        if user_id and user_id in self._user_connections:
            del self._user_connections[user_id]
        
        logger.info(f"WebSocket 连接断开: channel={channel}, user_id={user_id}")
    
    async def _send_message(
        self,
        websocket: WebSocket,
        message_type: str,
        data: Dict[str, Any]
    ):
        """
        发送消息到单个连接
        
        Args:
            websocket: WebSocket 连接
            message_type: 消息类型
            data: 消息数据
        """
        try:
            message = {
                "type": message_type,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            }
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"发送 WebSocket 消息失败: {e}")
    
    async def broadcast(
        self,
        message_type: str,
        data: Dict[str, Any],
        channel: str = "global"
    ):
        """
        广播消息到频道
        
        Args:
            message_type: 消息类型
            data: 消息数据
            channel: 广播频道
        """
        if channel not in self._active_connections:
            return
        
        message = {
            "type": message_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        disconnected = []
        
        for websocket in self._active_connections[channel]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"广播消息失败: {e}")
                disconnected.append(websocket)
        
        for ws in disconnected:
            self._active_connections[channel].remove(ws)
        
        logger.info(f"已广播消息: channel={channel}, type={message_type}, connections={len(self._active_connections[channel])}")
    
    async def send_to_user(
        self,
        user_id: int,
        message_type: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        发送消息给指定用户
        
        Args:
            user_id: 用户ID
            message_type: 消息类型
            data: 消息数据
            
        Returns:
            是否发送成功
        """
        if user_id not in self._user_connections:
            return False
        
        websocket = self._user_connections[user_id]
        
        try:
            await self._send_message(websocket, message_type, data)
            return True
        except Exception as e:
            logger.error(f"发送消息给用户 {user_id} 失败: {e}")
            del self._user_connections[user_id]
            return False
    
    def get_connection_count(self, channel: str = "global") -> int:
        """
        获取频道连接数
        
        Args:
            channel: 频道名称
            
        Returns:
            连接数
        """
        if channel not in self._active_connections:
            return 0
        return len(self._active_connections[channel])
    
    def get_channels(self) -> Dict[str, int]:
        """
        获取所有频道及其连接数
        
        Returns:
            频道连接数字典
        """
        return {
            channel: len(connections)
            for channel, connections in self._active_connections.items()
        }


websocket_manager = WebSocketManager()


def get_websocket_manager() -> WebSocketManager:
    """获取 WebSocket 管理器单例"""
    return websocket_manager
