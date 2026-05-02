from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import logging
import base64
import io
import uuid
import random

from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Chart, SynastryRecord
from app.routers.users import get_current_user
from app.schemas import ApiResponse
from app.synastry import calculate_synastry_chart
from app.synastry_analysis import generate_full_analysis
from app.services.ai_service import call_qwen_api, call_deepseek_api, DEFAULT_QWEN_FAST_MODEL, FAST_DEEPSEEK_MODEL
from app.services.synastry_highlights_service import (
    extract_synastry_highlights,
    generate_synastry_ai_prompt,
    generate_photocard_design,
    generate_emotional_value_analysis
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["合盘增强功能"])


class GenerateAiCopyRequest(BaseModel):
    synastry_record_id: Optional[int] = None
    person_a_name: Optional[str] = None
    person_a_birth_date: Optional[str] = None
    person_a_birth_time: Optional[str] = None
    person_a_latitude: Optional[float] = None
    person_a_longitude: Optional[float] = None
    person_b_name: Optional[str] = None
    person_b_birth_date: Optional[str] = None
    person_b_birth_time: Optional[str] = None
    person_b_latitude: Optional[float] = None
    person_b_longitude: Optional[float] = None
    use_deepseek: bool = True


class GeneratePhotocardRequest(BaseModel):
    synastry_record_id: Optional[int] = None
    card_type: str = "default"
    person_a_name: Optional[str] = None
    person_b_name: Optional[str] = None
    highlights: Optional[Dict[str, Any]] = None


class EnhancedSynastryRequest(BaseModel):
    person_a: Dict[str, Any]
    person_b: Dict[str, Any]
    generate_ai_copy: bool = True
    generate_photocard: bool = True


@router.post("/generate-ai-copy", response_model=ApiResponse)
async def generate_synastry_ai_copy(
    request: GenerateAiCopyRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """生成合盘AI文案"""
    try:
        synastry_data = None
        highlights = None
        person_a_name = "人物A"
        person_b_name = "人物B"
        
        if request.synastry_record_id:
            record = db.query(SynastryRecord).filter(
                SynastryRecord.id == request.synastry_record_id,
                SynastryRecord.user_id == current_user.id,
                SynastryRecord.is_deleted == False
            ).first()
            
            if not record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="合盘记录不存在"
                )
            
            if record.synastry_data:
                try:
                    synastry_data = json.loads(record.synastry_data)
                except:
                    pass
            
            person_a_name = record.person_a_name or "人物A"
            person_b_name = record.person_b_name or "人物B"
        
        elif (request.person_a_birth_date and request.person_a_birth_time and
              request.person_b_birth_date and request.person_b_birth_time):
            
            person_a = {
                "name": request.person_a_name or "人物A",
                "birth_date": request.person_a_birth_date,
                "birth_time": request.person_a_birth_time,
                "birth_place": "",
                "latitude": request.person_a_latitude or 39.9042,
                "longitude": request.person_a_longitude or 116.4074,
                "house_system": "placidus"
            }
            
            person_b = {
                "name": request.person_b_name or "人物B",
                "birth_date": request.person_b_birth_date,
                "birth_time": request.person_b_birth_time,
                "birth_place": "",
                "latitude": request.person_b_latitude or 39.9042,
                "longitude": request.person_b_longitude or 116.4074,
                "house_system": "placidus"
            }
            
            person_a_name = person_a["name"]
            person_b_name = person_b["name"]
            
            synastry_data = calculate_synastry_chart(person_a, person_b)
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请提供合盘记录ID或出生时间信息"
            )
        
        if not synastry_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无法获取合盘数据"
            )
        
        highlights = extract_synastry_highlights(synastry_data)
        
        ai_prompt = generate_synastry_ai_prompt(
            highlights,
            person_a_name,
            person_b_name
        )
        
        try:
            if request.use_deepseek:
                ai_content = await call_deepseek_api(
                    prompt=ai_prompt,
                    system_prompt="你是一位专业的占星师和情感分析师，擅长用温暖、优美的中文语言来解读星盘合盘。请根据提供的合盘分析数据，撰写一段优美、富有洞察力的文案。",
                    model=FAST_DEEPSEEK_MODEL,
                    temperature=0.8,
                    max_tokens=1500,
                    fast_mode=True
                )
            else:
                ai_content = await call_qwen_api(
                    prompt=ai_prompt,
                    model=DEFAULT_QWEN_FAST_MODEL,
                    temperature=0.8,
                    max_tokens=1500
                )
        except Exception as e:
            logger.error(f"AI调用失败: {e}")
            ai_content = generate_default_ai_copy(highlights, person_a_name, person_b_name)
        
        return ApiResponse(
            message="AI文案生成成功",
            data={
                "person_a_name": person_a_name,
                "person_b_name": person_b_name,
                "highlights": highlights,
                "ai_content": ai_content,
                "generated_at": datetime.utcnow().isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成AI文案失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成AI文案失败: {str(e)}"
        )


@router.post("/generate-photocard", response_model=ApiResponse)
async def generate_synastry_photocard(
    request: GeneratePhotocardRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """生成限定合影卡牌"""
    try:
        synastry_data = None
        highlights = None
        person_a_name = request.person_a_name or "人物A"
        person_b_name = request.person_b_name or "人物B"
        
        if request.highlights:
            highlights = request.highlights
        elif request.synastry_record_id:
            record = db.query(SynastryRecord).filter(
                SynastryRecord.id == request.synastry_record_id,
                SynastryRecord.user_id == current_user.id,
                SynastryRecord.is_deleted == False
            ).first()
            
            if not record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="合盘记录不存在"
                )
            
            person_a_name = record.person_a_name or person_a_name
            person_b_name = record.person_b_name or person_b_name
            
            if record.synastry_data:
                try:
                    synastry_data = json.loads(record.synastry_data)
                    highlights = extract_synastry_highlights(synastry_data)
                except:
                    pass
        
        if not highlights:
            highlights = generate_default_highlights()
        
        card_design = generate_photocard_design(
            highlights,
            person_a_name,
            person_b_name,
            request.card_type
        )
        
        card_svg = generate_card_svg(card_design)
        
        card_base64 = base64.b64encode(card_svg.encode('utf-8')).decode('utf-8')
        
        return ApiResponse(
            message="合影卡牌生成成功",
            data={
                "card_id": card_design["card_id"],
                "card_type": request.card_type,
                "card_name": card_design["theme_name"],
                "rarity": card_design["rarity"],
                "is_limited_edition": card_design["limited_edition"],
                "design": card_design["design"],
                "content": card_design["content"],
                "card_svg": card_svg,
                "card_base64": f"data:image/svg+xml;base64,{card_base64}",
                "generated_at": datetime.utcnow().isoformat()
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成合影卡牌失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成合影卡牌失败: {str(e)}"
        )


@router.post("/enhanced-analysis", response_model=ApiResponse)
async def get_enhanced_synastry_analysis(
    request: EnhancedSynastryRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(lambda: None)
):
    """获取增强版合盘分析（包含亮点、AI文案、卡牌设计）"""
    try:
        person_a = request.person_a
        person_b = request.person_b
        
        required_fields = ["birth_date", "birth_time", "latitude", "longitude"]
        for field in required_fields:
            if field not in person_a or field not in person_b:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"缺少必要字段: {field}"
                )
        
        person_a_full = {
            "name": person_a.get("name", "人物A"),
            "birth_date": person_a["birth_date"],
            "birth_time": person_a["birth_time"],
            "birth_place": person_a.get("birth_place", ""),
            "latitude": person_a["latitude"],
            "longitude": person_a["longitude"],
            "house_system": person_a.get("house_system", "placidus")
        }
        
        person_b_full = {
            "name": person_b.get("name", "人物B"),
            "birth_date": person_b["birth_date"],
            "birth_time": person_b["birth_time"],
            "birth_place": person_b.get("birth_place", ""),
            "latitude": person_b["latitude"],
            "longitude": person_b["longitude"],
            "house_system": person_b.get("house_system", "placidus")
        }
        
        synastry_data = calculate_synastry_chart(person_a_full, person_b_full)
        analysis_data = generate_full_analysis(synastry_data)
        highlights = extract_synastry_highlights(synastry_data)
        emotional_analysis = generate_emotional_value_analysis(synastry_data, highlights)
        
        result = {
            "synastry": synastry_data,
            "analysis": analysis_data,
            "highlights": highlights,
            "emotional_analysis": emotional_analysis
        }
        
        if request.generate_ai_copy:
            try:
                ai_prompt = generate_synastry_ai_prompt(
                    highlights,
                    person_a_full["name"],
                    person_b_full["name"]
                )
                
                ai_content = await call_deepseek_api(
                    prompt=ai_prompt,
                    system_prompt="你是一位专业的占星师和情感分析师，擅长用温暖、优美的中文语言来解读星盘合盘。",
                    model=FAST_DEEPSEEK_MODEL,
                    temperature=0.8,
                    max_tokens=1500,
                    fast_mode=True
                )
                
                result["ai_copy"] = ai_content
            except Exception as e:
                logger.error(f"AI文案生成失败: {e}")
                result["ai_copy"] = generate_default_ai_copy(
                    highlights,
                    person_a_full["name"],
                    person_b_full["name"]
                )
        
        if request.generate_photocard:
            card_design = generate_photocard_design(
                highlights,
                person_a_full["name"],
                person_b_full["name"],
                "default"
            )
            result["photocard_design"] = card_design
        
        return ApiResponse(
            message="增强版合盘分析完成",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"增强版合盘分析失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"增强版合盘分析失败: {str(e)}"
        )


def generate_default_ai_copy(
    highlights: Dict[str, Any],
    person_a_name: str,
    person_b_name: str
) -> str:
    """生成默认AI文案（当API调用失败时使用）"""
    overall_theme = highlights.get("overall_theme", {})
    highlights_list = highlights.get("highlights", [])
    element_analysis = highlights.get("element_analysis", {})
    
    parts = []
    
    parts.append(f"## {person_a_name} 与 {person_b_name} 的星盘合盘分析")
    parts.append("")
    
    theme_name = overall_theme.get("name", "特殊缘分")
    theme_desc = overall_theme.get("description", "你们的相遇有着特殊的意义。")
    parts.append(f"### 整体评价：{theme_name}")
    parts.append(theme_desc)
    parts.append("")
    
    if highlights_list:
        parts.append("### 关系亮点")
        for h in highlights_list[:3]:
            icon = h.get("icon", "✨")
            name = h.get("name", "")
            desc = h.get("description", "")
            parts.append(f"{icon} **{name}**")
            parts.append(desc)
            parts.append("")
    
    parts.append("### 相处建议")
    parts.append("这段关系的发展需要双方的共同努力。建议你们：")
    parts.append("1. 多倾听对方的想法和感受，理解彼此的差异")
    parts.append("2. 在沟通中保持耐心，避免情绪化的表达")
    parts.append("3. 共同创造美好的回忆，让关系更加稳固")
    parts.append("4. 珍惜这段缘分，用真诚和付出去经营")
    
    return "\n".join(parts)


def generate_default_highlights() -> Dict[str, Any]:
    """生成默认亮点数据"""
    return {
        "highlights": [
            {
                "category": "emotional_harmony",
                "name": "情感和谐",
                "icon": "💕",
                "description": "月亮与金星的互动带来情感上的理解与支持",
                "score": 75,
                "strength": "moderate",
                "matched_aspects": []
            },
            {
                "category": "communication_synergy",
                "name": "思维契合",
                "icon": "🧠",
                "description": "水星相位显示沟通上的默契",
                "score": 65,
                "strength": "moderate",
                "matched_aspects": []
            }
        ],
        "special_indicators": [],
        "overall_theme": {
            "type": "harmonious",
            "name": "和谐型关系",
            "description": "你们的关系以和谐为主，大多数时候能够顺畅沟通、相互理解。"
        },
        "aspect_stats": {
            "total": 12,
            "harmonious": 7,
            "challenging": 3,
            "harmony_ratio": 58
        },
        "generated_at": datetime.utcnow().isoformat()
    }


def generate_card_svg(card_design: Dict[str, Any]) -> str:
    """生成卡牌SVG图像"""
    content = card_design.get("content", {})
    design = card_design.get("design", {})
    persons = content.get("persons", {})
    primary_highlight = content.get("primary_highlight", {})
    
    bg_gradient = design.get("background", "linear-gradient(135deg, #1a1a3e 0%, #2d1b69 100%)")
    accent_color = design.get("accent_color", "#8b5cf6")
    decorations = design.get("decorations", ["✨", "⭐", "💫", "🌟"])
    decorations_str = " ".join(decorations[:4])
    
    person_a = persons.get("person_a", {})
    person_b = persons.get("person_b", {})
    
    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 600" width="400" height="600">
  <defs>
    <linearGradient id="bgGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#1a1a3e;stop-opacity:1" />
      <stop offset="50%" style="stop-color:#2d1b69;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#4c1d95;stop-opacity:1" />
    </linearGradient>
    <linearGradient id="goldBorder" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#fbbf24;stop-opacity:1" />
      <stop offset="50%" style="stop-color:#f59e0b;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#d97706;stop-opacity:1" />
    </linearGradient>
    <radialGradient id="centerGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" style="stop-color:{accent_color};stop-opacity:0.3" />
      <stop offset="100%" style="stop-color:{accent_color};stop-opacity:0" />
    </radialGradient>
    <filter id="glow">
      <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
      <feMerge>
        <feMergeNode in="coloredBlur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>
  
  <rect x="0" y="0" width="400" height="600" fill="url(#bgGradient)" rx="20" ry="20"/>
  
  <rect x="10" y="10" width="380" height="580" fill="none" stroke="url(#goldBorder)" stroke-width="2" rx="15" ry="15"/>
  
  <circle cx="200" cy="300" r="180" fill="url(#centerGlow)"/>
  
  <text x="200" y="50" text-anchor="middle" fill="#fbbf24" font-size="14" font-weight="bold">
    {decorations_str} 限定合影卡牌 {decorations_str}
  </text>
  
  <text x="200" y="80" text-anchor="middle" fill="#a78bfa" font-size="12" opacity="0.8">
    {card_design.get('theme_name', '星空相遇')}
  </text>
  
  <g transform="translate(200, 200)">
    <circle cx="-90" cy="0" r="55" fill="url(#goldBorder)" opacity="0.3"/>
    <circle cx="-90" cy="0" r="50" fill="#2d1b69" stroke="{accent_color}" stroke-width="2"/>
    <text x="-90" y="-5" text-anchor="middle" fill="#fff" font-size="20">👤</text>
    <text x="-90" y="30" text-anchor="middle" fill="#a78bfa" font-size="11">
      {person_a.get('name', '人物A')}
    </text>
    <text x="-90" y="48" text-anchor="middle" fill="#64748b" font-size="9">
      {person_a.get('sun_sign', '')}
    </text>
    
    <text x="0" y="5" text-anchor="middle" fill="#fbbf24" font-size="28" filter="url(#glow)">💕</text>
    <text x="0" y="30" text-anchor="middle" fill="#8b5cf6" font-size="10">VS</text>
    
    <circle cx="90" cy="0" r="55" fill="url(#goldBorder)" opacity="0.3"/>
    <circle cx="90" cy="0" r="50" fill="#2d1b69" stroke="{accent_color}" stroke-width="2"/>
    <text x="90" y="-5" text-anchor="middle" fill="#fff" font-size="20">👤</text>
    <text x="90" y="30" text-anchor="middle" fill="#a78bfa" font-size="11">
      {person_b.get('name', '人物B')}
    </text>
    <text x="90" y="48" text-anchor="middle" fill="#64748b" font-size="9">
      {person_b.get('sun_sign', '')}
    </text>
  </g>
  
  <rect x="30" y="360" width="340" height="120" rx="10" fill="rgba(45, 27, 105, 0.6)" stroke="{accent_color}" stroke-width="1" opacity="0.8"/>
  
  <text x="200" y="385" text-anchor="middle" fill="#fbbf24" font-size="13" font-weight="bold">
    {primary_highlight.get('icon', '✨')} {primary_highlight.get('name', '缘分天定')}
  </text>
  
  <text x="200" y="410" text-anchor="middle" fill="#e2e8f0" font-size="11" width="300">
    {primary_highlight.get('description', '这是一段值得珍惜的缘分')[:60]}
  </text>
  
  <text x="200" y="445" text-anchor="middle" fill="#a78bfa" font-size="12">
    匹配度: <tspan fill="#22c55e" font-weight="bold">{content.get('compatibility_score', 70)}%</tspan>
  </text>
  
  <rect x="30" y="500" width="340" height="70" rx="8" fill="rgba(20, 20, 50, 0.8)" stroke="#4c1d95" stroke-width="1"/>
  
  <text x="200" y="525" text-anchor="middle" fill="#64748b" font-size="10">
    卡牌编号: {card_design.get('card_id', 'SC_XXXXXXX')}
  </text>
  
  <text x="200" y="545" text-anchor="middle" fill="#64748b" font-size="9">
    稀有度: <tspan fill="{get_rarity_color(card_design.get('rarity', 'common'))}">{get_rarity_label(card_design.get('rarity', 'common'))}</tspan>
  </text>
  
  <text x="200" y="565" text-anchor="middle" fill="#4c1d95" font-size="8" opacity="0.6">
    星盘查询系统 · {datetime.now().strftime('%Y.%m.%d')}
  </text>
  
  <text x="20" y="30" fill="#64748b" font-size="24" opacity="0.3">✦</text>
  <text x="360" y="30" fill="#64748b" font-size="24" opacity="0.3">✦</text>
  <text x="20" y="580" fill="#64748b" font-size="24" opacity="0.3">✦</text>
  <text x="360" y="580" fill="#64748b" font-size="24" opacity="0.3">✦</text>
</svg>'''
    
    return svg


def get_rarity_color(rarity: str) -> str:
    colors = {
        "legendary": "#fbbf24",
        "epic": "#a78bfa",
        "rare": "#60a5fa",
        "common": "#94a3b8"
    }
    return colors.get(rarity, "#94a3b8")


def get_rarity_label(rarity: str) -> str:
    labels = {
        "legendary": "传说",
        "epic": "史诗",
        "rare": "稀有",
        "common": "普通"
    }
    return labels.get(rarity, "普通")
