import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple

from app.config import settings

logger = logging.getLogger(__name__)

TZ_AVAILABLE = False
tf = None
pytz = None

try:
    from timezonefinder import TimezoneFinder
    import pytz
    TZ_AVAILABLE = True
    tf = TimezoneFinder(in_memory=True)
    logger.info("时区库已加载: timezonefinder + pytz")
except ImportError as e:
    logger.warning(f"时区库未安装，将使用默认时区: {e}")


class TimezoneService:
    """时区服务 - 提供精确的时区转换和验证"""
    
    _instance = None
    _default_timezone = "Asia/Shanghai"
    _default_offset_hours = 8.0
    
    FALLBACK_TIMEZONES = {
        "CN": "Asia/Shanghai",
        "US": "America/New_York",
        "JP": "Asia/Tokyo",
        "KR": "Asia/Seoul",
        "GB": "Europe/London",
        "DE": "Europe/Berlin",
        "FR": "Europe/Paris",
        "AU": "Australia/Sydney",
        "CA": "America/Toronto",
        "BR": "America/Sao_Paulo",
        "IN": "Asia/Kolkata",
        "RU": "Europe/Moscow",
    }
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
    
    def is_available(self) -> bool:
        """检查时区库是否可用"""
        return TZ_AVAILABLE and tf is not None and pytz is not None
    
    def get_timezone_from_coords(self, latitude: float, longitude: float) -> Optional[str]:
        """
        根据经纬度获取时区字符串
        
        Args:
            latitude: 纬度 (-90 to 90)
            longitude: 经度 (-180 to 180)
            
        Returns:
            时区字符串，如 "Asia/Shanghai"，失败返回 None
        """
        if not self.is_available():
            return None
        
        try:
            latitude = max(min(float(latitude), 90.0), -90.0)
            longitude = max(min(float(longitude), 180.0), -180.0)
            
            timezone_str = tf.timezone_at(lat=latitude, lng=longitude)
            
            if timezone_str:
                logger.info(f"从坐标 ({latitude}, {longitude}) 获取时区: {timezone_str}")
                return timezone_str
            else:
                logger.warning(f"无法从坐标 ({latitude}, {longitude}) 获取时区，使用默认时区")
                return None
                
        except Exception as e:
            logger.error(f"获取时区失败: {e}")
            return None
    
    def get_timezone_offset(self, timezone_str: str, local_dt: datetime) -> Tuple[float, bool]:
        """
        获取指定时区在特定时间的UTC偏移量和是否夏令时
        
        Args:
            timezone_str: 时区字符串，如 "Asia/Shanghai"
            local_dt: 本地时间（不带时区信息的datetime）
            
        Returns:
            (offset_hours, is_dst): 偏移小时数，是否夏令时
        """
        if not self.is_available() or not pytz:
            return (self._default_offset_hours, False)
        
        try:
            tz = pytz.timezone(timezone_str)
            
            try:
                local_aware = tz.localize(local_dt, is_dst=None)
            except pytz.NonExistentTimeError:
                logger.info(f"时间 {local_dt} 在时区 {timezone_str} 不存在（夏令时切换），使用 is_dst=True")
                local_aware = tz.localize(local_dt, is_dst=True)
            except pytz.AmbiguousTimeError:
                logger.info(f"时间 {local_dt} 在时区 {timezone_str} 不明确（夏令时切换），使用 is_dst=False")
                local_aware = tz.localize(local_dt, is_dst=False)
            
            utc_offset = local_aware.utcoffset()
            if utc_offset:
                offset_hours = utc_offset.total_seconds() / 3600.0
            else:
                offset_hours = 0.0
            
            is_dst = local_aware.dst() != timedelta(0) if local_aware.dst() else False
            
            logger.debug(f"时区 {timezone_str} 在 {local_dt} 的偏移: {offset_hours}小时, 夏令时: {is_dst}")
            
            return (offset_hours, is_dst)
            
        except Exception as e:
            logger.error(f"获取时区偏移失败: {e}")
            return (self._default_offset_hours, False)
    
    def local_to_utc(
        self,
        year: int, month: int, day: int, hour: int, minute: int,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        timezone_str: Optional[str] = None
    ) -> Tuple[datetime, Dict[str, Any]]:
        """
        将本地时间转换为UTC时间
        
        Args:
            year, month, day, hour, minute: 本地时间
            latitude, longitude: 经纬度（用于自动检测时区）
            timezone_str: 可选的时区字符串，如 "Asia/Shanghai"
            
        Returns:
            (utc_datetime, debug_info): UTC时间和调试信息
        """
        local_dt = datetime(year, month, day, hour, minute)
        
        debug_info = {
            "input_local": local_dt.strftime("%Y-%m-%d %H:%M"),
            "latitude": latitude,
            "longitude": longitude,
            "timezone": None,
            "timezone_source": None,
            "offset_hours": None,
            "is_dst": None,
            "utc_time": None,
            "precision_note": None
        }
        
        utc_dt = None
        
        if timezone_str:
            debug_info["timezone_source"] = "explicit"
            debug_info["timezone"] = timezone_str
        elif latitude is not None and longitude is not None:
            timezone_str = self.get_timezone_from_coords(latitude, longitude)
            if timezone_str:
                debug_info["timezone_source"] = "coordinates"
                debug_info["timezone"] = timezone_str
        
        if timezone_str and self.is_available() and pytz:
            try:
                tz = pytz.timezone(timezone_str)
                
                try:
                    local_aware = tz.localize(local_dt, is_dst=None)
                except pytz.NonExistentTimeError:
                    debug_info["precision_note"] = "NonExistentTimeError: 时间不存在，使用夏令时"
                    local_aware = tz.localize(local_dt, is_dst=True)
                except pytz.AmbiguousTimeError:
                    debug_info["precision_note"] = "AmbiguousTimeError: 时间不明确，使用非夏令时"
                    local_aware = tz.localize(local_dt, is_dst=False)
                
                utc_dt = local_aware.astimezone(pytz.utc)
                debug_info["utc_time"] = utc_dt.strftime("%Y-%m-%d %H:%M:%S")
                
                dst = local_aware.dst()
                debug_info["is_dst"] = dst != timedelta(0) if dst else False
                
                utcoffset = local_aware.utcoffset()
                debug_info["offset_hours"] = utcoffset.total_seconds() / 3600.0 if utcoffset else 0
                
                logger.info(
                    f"时区转换成功: {local_dt} ({timezone_str}) -> "
                    f"UTC {utc_dt}, 偏移: {debug_info['offset_hours']}小时, "
                    f"DST: {debug_info['is_dst']}"
                )
                
            except Exception as e:
                logger.warning(f"时区转换失败，使用默认UTC+8: {e}")
                debug_info["precision_note"] = f"转换失败: {str(e)}"
        
        if utc_dt is None:
            offset_hours = self._default_offset_hours
            utc_dt = local_dt - timedelta(hours=offset_hours)
            debug_info["timezone"] = f"{self._default_timezone} (fallback)"
            debug_info["timezone_source"] = "fallback"
            debug_info["offset_hours"] = offset_hours
            debug_info["is_dst"] = False
            debug_info["utc_time"] = utc_dt.strftime("%Y-%m-%d %H:%M:%S")
            logger.warning(f"使用默认时区UTC+8: {local_dt} -> UTC {utc_dt}")
        
        return utc_dt, debug_info
    
    def utc_to_local(
        self,
        utc_dt: datetime,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        timezone_str: Optional[str] = None
    ) -> Tuple[datetime, Dict[str, Any]]:
        """
        将UTC时间转换为本地时间
        
        Args:
            utc_dt: UTC时间（建议带时区信息）
            latitude, longitude: 经纬度
            timezone_str: 时区字符串
            
        Returns:
            (local_datetime, debug_info): 本地时间和调试信息
        """
        debug_info = {
            "input_utc": utc_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "timezone": None,
            "offset_hours": None,
            "local_time": None
        }
        
        if not timezone_str and latitude is not None and longitude is not None:
            timezone_str = self.get_timezone_from_coords(latitude, longitude)
        
        if timezone_str and self.is_available() and pytz:
            try:
                tz = pytz.timezone(timezone_str)
                
                if utc_dt.tzinfo is None:
                    utc_aware = pytz.utc.localize(utc_dt)
                else:
                    utc_aware = utc_dt.astimezone(pytz.utc)
                
                local_aware = utc_aware.astimezone(tz)
                
                debug_info["timezone"] = timezone_str
                debug_info["local_time"] = local_aware.strftime("%Y-%m-%d %H:%M:%S")
                
                utcoffset = local_aware.utcoffset()
                debug_info["offset_hours"] = utcoffset.total_seconds() / 3600.0 if utcoffset else 0
                
                logger.info(
                    f"UTC转本地: UTC {utc_dt} -> "
                    f"{local_aware} ({timezone_str}), 偏移: {debug_info['offset_hours']}小时"
                )
                
                return local_aware.replace(tzinfo=None), debug_info
                
            except Exception as e:
                logger.warning(f"UTC转本地失败: {e}")
        
        offset_hours = self._default_offset_hours
        local_dt = utc_dt + timedelta(hours=offset_hours)
        debug_info["timezone"] = f"{self._default_timezone} (fallback)"
        debug_info["offset_hours"] = offset_hours
        debug_info["local_time"] = local_dt.strftime("%Y-%m-%d %H:%M:%S")
        
        return local_dt, debug_info
    
    def validate_timezone(self, timezone_str: str) -> bool:
        """验证时区字符串是否有效"""
        if not self.is_available() or not pytz:
            return False
        
        try:
            pytz.timezone(timezone_str)
            return True
        except pytz.exceptions.UnknownTimeZoneError:
            return False
    
    def get_current_offset_for_coords(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        获取指定坐标当前的时区偏移信息
        
        Returns:
            {
                "timezone": "Asia/Shanghai",
                "offset_hours": 8.0,
                "is_dst": False,
                "offset_display": "UTC+8"
            }
        """
        timezone_str = self.get_timezone_from_coords(latitude, longitude)
        
        if timezone_str:
            offset_hours, is_dst = self.get_timezone_offset(timezone_str, datetime.now())
            
            offset_sign = "+" if offset_hours >= 0 else ""
            offset_display = f"UTC{offset_sign}{offset_hours:g}"
            
            return {
                "timezone": timezone_str,
                "offset_hours": offset_hours,
                "is_dst": is_dst,
                "offset_display": offset_display
            }
        
        return {
            "timezone": self._default_timezone,
            "offset_hours": self._default_offset_hours,
            "is_dst": False,
            "offset_display": "UTC+8",
            "note": "使用默认时区"
        }


timezone_service = TimezoneService()


def get_timezone_service() -> TimezoneService:
    """获取时区服务单例"""
    return timezone_service
