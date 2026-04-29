import json
import io
import os
import re
import asyncio
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks

from app.astro import calculate_chart, parse_birth_datetime, HouseSystem
from app.report_generator import create_pdf_report, ReportTemplate
from app.interpretations import generate_full_interpretation
from app.models import Chart


def encode_safe_filename(filename: str) -> str:
    """
    安全编码文件名，确保跨浏览器兼容性
    
    遵循 RFC 5987 规范，同时支持多种浏览器的兼容性处理
    允许中文字符和其他 Unicode 字符，只替换真正危险的字符
    """
    import urllib.parse
    
    try:
        if not filename:
            return f'星盘报告_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        
        filename = str(filename).strip()
        
        filename = ''.join(c for c in filename if c.isprintable())
        
        dangerous_chars = r'<>:"/\|?*'
        dangerous_chars_set = set(dangerous_chars)
        
        result = []
        for c in filename:
            if c in dangerous_chars_set or ord(c) < 32:
                result.append('_')
            else:
                result.append(c)
        
        filename = ''.join(result)
        
        filename = filename.replace('  ', ' ').strip()
        
        if not filename or len(filename) == 0:
            filename = f'星盘报告_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        
        if filename.startswith('.'):
            filename = '报告' + filename
        
        return filename
    except Exception:
        return f'星盘报告_{datetime.now().strftime("%Y%m%d_%H%M%S")}'


def build_content_disposition_header(filename: str) -> str:
    """
    构建 Content-Disposition 响应头，确保跨浏览器兼容性
    
    关键点：
    1. filename 参数只能包含 ASCII 字符（因为 HTTP 头使用 latin-1 编码）
    2. filename*=UTF-8'' 参数使用 RFC 5987 编码，可以包含 Unicode 字符
    3. 现代浏览器会优先使用 filename* 参数（Chrome/Firefox/Safari/Edge 都支持）
    """
    import urllib.parse
    
    safe_filename = encode_safe_filename(filename)
    
    def to_ascii_filename(name):
        base = os.path.splitext(name)[0]
        ext = os.path.splitext(name)[1]
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ascii_base = re.sub(r'[^\x00-\x7f]', '', base).strip()
        if not ascii_base or len(ascii_base) < 2:
            ascii_base = f"chart_report_{timestamp}"
        
        return f"{ascii_base}{ext}"
    
    ascii_filename = to_ascii_filename(safe_filename)
    
    encoded_filename = urllib.parse.quote(safe_filename, safe='')
    
    header_parts = [
        f'attachment; filename="{ascii_filename}"',
        f"filename*=UTF-8''{encoded_filename}"
    ]
    
    return '; '.join(header_parts)


def calculate_chart_from_input(
    birth_date: str,
    birth_time: str,
    latitude: float,
    longitude: float,
    house_system: str = 'placidus'
) -> Dict[str, Any]:
    """
    从输入参数计算星盘数据
    
    Args:
        birth_date: 出生日期 (YYYY-MM-DD)
        birth_time: 出生时间 (HH:MM)
        latitude: 纬度
        longitude: 经度
        house_system: 宫位系统 (placidus 或 whole_sign)
    
    Returns:
        星盘计算结果字典
    """
    dt = parse_birth_datetime(birth_date, birth_time)
    
    chart_data = calculate_chart(
        year=dt["year"],
        month=dt["month"],
        day=dt["day"],
        hour=dt["hour"],
        minute=dt["minute"],
        latitude=latitude,
        longitude=longitude,
        house_system=house_system
    )
    
    return chart_data


def get_or_create_chart_data(
    db: Session,
    chart_id: int,
    user_id: int
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    获取或创建星盘数据
    
    从数据库中查找星盘，如果 chart_data 为空则重新计算
    
    Args:
        db: 数据库会话
        chart_id: 星盘ID
        user_id: 用户ID
    
    Returns:
        (chart_data, chart_record) 元组
    """
    chart = db.query(Chart).filter(
        Chart.id == chart_id,
        Chart.user_id == user_id,
        Chart.is_deleted == False
    ).first()
    
    if not chart:
        return None, None
    
    chart_data = None
    try:
        if chart.chart_data:
            chart_data = json.loads(chart.chart_data)
    except Exception:
        pass
    
    if not chart_data:
        chart_data = calculate_chart_from_input(
            birth_date=chart.birth_date,
            birth_time=chart.birth_time,
            latitude=chart.latitude,
            longitude=chart.longitude,
            house_system=chart.house_system
        )
    
    return chart_data, chart


def generate_chart_report(
    chart_data: Dict[str, Any],
    name: str = '星盘',
    birth_date: str = '',
    birth_time: str = '',
    birth_place: str = '',
    latitude: float = 0.0,
    longitude: float = 0.0,
    template: str = ReportTemplate.DETAILED
) -> Tuple[io.BytesIO, str]:
    """
    生成星盘 PDF 报告
    
    Args:
        chart_data: 星盘计算数据
        name: 姓名/星盘名称
        birth_date: 出生日期
        birth_time: 出生时间
        birth_place: 出生地点
        latitude: 纬度
        longitude: 经度
        template: 报告模板 (simple 或 detailed)
    
    Returns:
        (PDF 缓冲区, 文件名) 元组
    """
    if 'basic_info' not in chart_data:
        chart_data['basic_info'] = {
            'input': {
                'name': name,
                'date': birth_date,
                'time': birth_time,
                'place': birth_place,
                'latitude': latitude,
                'longitude': longitude
            }
        }
    
    pdf_buffer = create_pdf_report(chart_data, template=template)
    
    template_name = "详细版" if template == ReportTemplate.DETAILED else "简洁版"
    
    date_suffix = birth_date.replace('-', '') if birth_date else datetime.now().strftime('%Y%m%d')
    time_suffix = birth_time.replace(':', '') if birth_time else ''
    
    if time_suffix:
        filename = f"星盘解读报告_{name}_{date_suffix}_{time_suffix}_{template_name}.pdf"
    else:
        filename = f"星盘解读报告_{name}_{date_suffix}_{template_name}.pdf"
    
    return pdf_buffer, filename


class ChartService:
    """
    星盘服务类
    
    提供星盘计算、报告生成、数据管理等功能的集中管理
    """
    
    @staticmethod
    def calculate(
        birth_date: str,
        birth_time: str,
        latitude: float,
        longitude: float,
        house_system: str = 'placidus'
    ) -> Dict[str, Any]:
        """计算星盘"""
        return calculate_chart_from_input(
            birth_date, birth_time, latitude, longitude, house_system
        )
    
    @staticmethod
    def generate_interpretation(chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成星盘解读"""
        return generate_full_interpretation(chart_data)
    
    @staticmethod
    def generate_report(
        chart_data: Dict[str, Any],
        name: str = '星盘',
        birth_date: str = '',
        birth_time: str = '',
        birth_place: str = '',
        latitude: float = 0.0,
        longitude: float = 0.0,
        template: str = ReportTemplate.DETAILED
    ) -> Tuple[io.BytesIO, str]:
        """生成 PDF 报告"""
        return generate_chart_report(
            chart_data, name, birth_date, birth_time, 
            birth_place, latitude, longitude, template
        )
    
    @staticmethod
    def get_chart_data_from_db(
        db: Session,
        chart_id: int,
        user_id: int
    ) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """从数据库获取星盘数据"""
        return get_or_create_chart_data(db, chart_id, user_id)


async def generate_report_async(
    chart_data: Dict[str, Any],
    name: str = '星盘',
    birth_date: str = '',
    birth_time: str = '',
    birth_place: str = '',
    latitude: float = 0.0,
    longitude: float = 0.0,
    template: str = ReportTemplate.DETAILED
) -> Tuple[io.BytesIO, str]:
    """
    异步生成 PDF 报告
    
    使用 asyncio.to_thread 在独立线程中执行同步的 PDF 生成，
    避免阻塞事件循环
    """
    def _sync_generate():
        return generate_chart_report(
            chart_data, name, birth_date, birth_time,
            birth_place, latitude, longitude, template
        )
    
    result = await asyncio.to_thread(_sync_generate)
    return result
