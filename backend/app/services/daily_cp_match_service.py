import logging
import json
import random
import secrets
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, update, select, func

from app.models import (
    User, Chart, DailyCPMatch, DailyCPMatchStatus, 
    DailyMatchLimit, TimeLimitedSession, MatchPreference,
    ProfileUnlock, UserVIP, UserPrivateChat, SynastryRecord,
    StarDustTransaction
)
from app.synastry import calculate_synastry_chart
from app.synastry_analysis import generate_full_analysis
from app.services.synastry_highlights_service import (
    extract_synastry_highlights, generate_emotional_value_analysis
)

logger = logging.getLogger(__name__)


ZODIAC_SIGN_NAMES = {
    0: "白羊座", 1: "金牛座", 2: "双子座", 3: "巨蟹座",
    4: "狮子座", 5: "处女座", 6: "天秤座", 7: "天蝎座",
    8: "射手座", 9: "摩羯座", 10: "水瓶座", 11: "双鱼座"
}


ZODIAC_ELEMENTS = {
    "白羊座": "fire", "狮子座": "fire", "射手座": "fire",
    "金牛座": "earth", "处女座": "earth", "摩羯座": "earth",
    "双子座": "air", "天秤座": "air", "水瓶座": "air",
    "巨蟹座": "water", "天蝎座": "water", "双鱼座": "water"
}

MAX_QUERY_LIMIT = 1000
MATCH_CANDIDATE_LIMIT = 50

UNLOCK_PROFILE_CONFIG = {
    "cost": 50,
    "currency_type": "point",
    "description": "解锁匹配用户资料"
}


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


def get_today_date_str() -> str:
    return get_utc_now().strftime("%Y-%m-%d")


def generate_batch_id() -> str:
    timestamp = get_utc_now().strftime("%Y%m%d%H%M%S")
    random_part = secrets.token_hex(4).upper()
    return f"BATCH_{timestamp}_{random_part}"


def generate_secure_session_key() -> str:
    return secrets.token_urlsafe(32)


def generate_secure_chat_identifier() -> str:
    return secrets.token_hex(16)


def get_user_zodiac_sign_from_chart(chart: Chart) -> Optional[str]:
    if not chart or not chart.chart_data:
        return None
    
    try:
        chart_data = json.loads(chart.chart_data)
        sun_sign = chart_data.get("sun_sign", {}).get("sign")
        if sun_sign:
            return sun_sign
    except Exception as e:
        logger.error(f"解析星盘数据失败: {e}")
    
    return None


def get_user_latest_chart(db: Session, user_id: int) -> Optional[Chart]:
    return db.query(Chart).filter(
        Chart.user_id == user_id,
        Chart.is_deleted == False
    ).order_by(Chart.created_at.desc()).first()


def calculate_compatibility_score(
    synastry_data: Dict[str, Any],
    highlights: Dict[str, Any]
) -> int:
    aspect_stats = highlights.get("aspect_stats", {})
    total = aspect_stats.get("total", 0)
    harmonious = aspect_stats.get("harmonious", 0)
    
    highlights_list = highlights.get("highlights", [])
    highlight_score = sum(h.get("score", 0) for h in highlights_list)
    
    base_score = 50
    
    if total > 0:
        harmony_ratio = harmonious / total
        base_score += int(harmony_ratio * 30)
    
    base_score += min(20, int(highlight_score / 5))
    
    final_score = min(99, max(30, base_score))
    
    return final_score


def generate_simplified_interpretation(
    highlights: Dict[str, Any],
    compatibility_score: int
) -> str:
    overall_theme = highlights.get("overall_theme", {})
    theme_name = overall_theme.get("name", "缘分连接")
    theme_description = overall_theme.get("description", "")
    
    highlights_list = highlights.get("highlights", [])
    
    key_points = []
    for h in highlights_list[:3]:
        icon = h.get("icon", "✨")
        name = h.get("name", "")
        desc = h.get("description", "")
        if name:
            key_points.append(f"{icon} {name}：{desc}")
    
    element_analysis = highlights.get("element_analysis", {})
    elem_a = element_analysis.get("person_a", {}).get("element_info", {}).get("name", "")
    elem_b = element_analysis.get("person_b", {}).get("element_info", {}).get("name", "")
    elem_desc = element_analysis.get("description", "")
    
    score_comment = ""
    if compatibility_score >= 85:
        score_comment = "你们是天生一对，有着极高的契合度！"
    elif compatibility_score >= 70:
        score_comment = "你们的关系充满和谐与默契，值得珍惜。"
    elif compatibility_score >= 55:
        score_comment = "你们需要更多的沟通和理解，但也有独特的化学反应。"
    else:
        score_comment = "你们的关系可能会遇到一些挑战，但正是这些差异带来成长的机会。"
    
    parts = []
    parts.append(f"【{theme_name}】")
    if theme_description:
        parts.append(theme_description)
    
    if key_points:
        parts.append("\n【关系亮点】")
        parts.extend(key_points)
    
    if elem_a and elem_b and elem_desc:
        parts.append(f"\n【元素分析】{elem_a}与{elem_b}")
        parts.append(elem_desc)
    
    parts.append(f"\n【运势寄语】{score_comment}")
    
    return "\n".join(parts)


def match_users_by_compatibility(
    db: Session,
    user: User,
    user_chart: Chart,
    available_users: List[Tuple[User, Chart]],
    target_zodiac_sign: Optional[str] = None,
    match_count: int = 1
) -> List[Tuple[User, Chart, Dict[str, Any]]]:
    if not available_users:
        return []
    
    user_chart_data = {}
    if user_chart.chart_data:
        try:
            user_chart_data = json.loads(user_chart.chart_data)
        except:
            pass
    
    user_sun_sign = get_user_zodiac_sign_from_chart(user_chart)
    
    scored_matches = []
    
    for candidate_user, candidate_chart in available_users:
        if candidate_user.id == user.id:
            continue
        
        candidate_sun_sign = get_user_zodiac_sign_from_chart(candidate_chart)
        
        if target_zodiac_sign and candidate_sun_sign != target_zodiac_sign:
            continue
        
        try:
            person_a = {
                "name": user.username,
                "birth_date": user_chart.birth_date,
                "birth_time": user_chart.birth_time,
                "birth_place": user_chart.birth_place or "",
                "latitude": user_chart.latitude,
                "longitude": user_chart.longitude,
                "house_system": user_chart.house_system or "placidus"
            }
            
            person_b = {
                "name": candidate_user.username,
                "birth_date": candidate_chart.birth_date,
                "birth_time": candidate_chart.birth_time,
                "birth_place": candidate_chart.birth_place or "",
                "latitude": candidate_chart.latitude,
                "longitude": candidate_chart.longitude,
                "house_system": candidate_chart.house_system or "placidus"
            }
            
            synastry_data = calculate_synastry_chart(person_a, person_b)
            analysis_data = generate_full_analysis(synastry_data)
            highlights = extract_synastry_highlights(synastry_data)
            emotional_analysis = generate_emotional_value_analysis(synastry_data, highlights)
            
            compatibility_score = calculate_compatibility_score(synastry_data, highlights)
            interpretation = generate_simplified_interpretation(highlights, compatibility_score)
            
            match_data = {
                "compatibility_score": compatibility_score,
                "synastry_data": synastry_data,
                "analysis_data": analysis_data,
                "highlights": highlights,
                "emotional_analysis": emotional_analysis,
                "interpretation": interpretation,
                "user_sun_sign": user_sun_sign,
                "candidate_sun_sign": candidate_sun_sign
            }
            
            scored_matches.append((candidate_user, candidate_chart, match_data, compatibility_score))
            
        except Exception as e:
            logger.error(f"计算合盘失败: user_id={candidate_user.id}, error={str(e)}")
            continue
    
    scored_matches.sort(key=lambda x: x[3], reverse=True)
    
    results = []
    for match in scored_matches[:match_count]:
        results.append((match[0], match[1], match[2]))
    
    return results


def check_user_vip_status(db: Session, user_id: int) -> Tuple[bool, int]:
    user_vip = db.query(UserVIP).filter(
        UserVIP.user_id == user_id
    ).first()
    
    is_vip = bool(
        user_vip and 
        user_vip.is_vip and 
        (user_vip.expires_at is None or user_vip.expires_at > get_utc_now())
    )
    
    vip_extra_count = 3 if is_vip else 0
    
    return is_vip, vip_extra_count


def prepare_match_candidates(
    db: Session,
    user_id: int,
    match_type: str,
    target_zodiac_sign: Optional[str] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False, "用户不存在", None
    
    user_chart = get_user_latest_chart(db, user.id)
    if not user_chart:
        return False, "请先保存您的星盘数据", None
    
    is_vip, vip_extra_count = check_user_vip_status(db, user.id)
    
    limit = db.query(DailyMatchLimit).filter(
        DailyMatchLimit.user_id == user.id,
        DailyMatchLimit.limit_date == get_today_date_str()
    ).first()
    
    free_matches_remaining = 1
    vip_extra_matches_remaining = vip_extra_count
    targeted_matches_remaining = 3 if is_vip else 0
    
    if limit:
        free_matches_remaining = max(0, limit.free_match_max - limit.free_match_count)
        vip_extra_matches_remaining = max(0, limit.vip_extra_match_max - limit.vip_extra_match_count)
        targeted_matches_remaining = max(0, limit.targeted_match_max - limit.targeted_match_count)
    
    can_match = False
    reason = "今日匹配次数已用完"
    
    if match_type == "free":
        if free_matches_remaining > 0:
            can_match = True
            reason = "可以进行免费匹配"
        elif is_vip and vip_extra_matches_remaining > 0:
            can_match = True
            reason = "可以使用VIP额外匹配次数"
        else:
            reason = "今日免费匹配次数已用完"
    
    elif match_type == "vip_extra":
        if is_vip and vip_extra_matches_remaining > 0:
            can_match = True
            reason = "可以进行VIP额外匹配"
        elif not is_vip:
            reason = "您不是VIP会员"
        else:
            reason = "VIP额外匹配次数已用完"
    
    elif match_type == "targeted":
        if not is_vip:
            reason = "定向匹配需要VIP会员"
        elif not target_zodiac_sign:
            reason = "定向匹配需要指定目标星座"
        elif targeted_matches_remaining <= 0:
            reason = "今日定向匹配次数已用完"
        else:
            can_match = True
            reason = "可以进行定向匹配"
    
    if not can_match:
        return False, reason, None
    
    potential_users = db.query(User, Chart).join(
        Chart, User.id == Chart.user_id
    ).filter(
        User.id != user.id,
        User.is_active == True,
        Chart.is_deleted == False
    ).limit(MATCH_CANDIDATE_LIMIT).all()
    
    if not potential_users:
        return False, "暂时没有可匹配的用户", None
    
    today = get_today_date_str()
    
    user_ids_matched_today = db.query(DailyCPMatch.user_a_id, DailyCPMatch.user_b_id).filter(
        DailyCPMatch.match_date == today,
        or_(
            DailyCPMatch.user_a_id == user.id,
            DailyCPMatch.user_b_id == user.id
        )
    ).limit(MAX_QUERY_LIMIT).all()
    
    matched_user_ids = set()
    for ua, ub in user_ids_matched_today:
        matched_user_ids.add(ua)
        matched_user_ids.add(ub)
    
    available_candidates = []
    for candidate_user, candidate_chart in potential_users:
        if candidate_user.id not in matched_user_ids:
            available_candidates.append((candidate_user, candidate_chart))
    
    if not available_candidates:
        return False, "今日可匹配用户已全部匹配完毕，请明天再来", None
    
    random.shuffle(available_candidates)
    
    matches = match_users_by_compatibility(
        db, user, user_chart, 
        available_candidates[:min(10, len(available_candidates))],
        target_zodiac_sign=target_zodiac_sign,
        match_count=1
    )
    
    if not matches:
        return False, "未找到合适的匹配", None
    
    matched_user, matched_chart, match_data = matches[0]
    
    return True, "准备就绪", {
        "user": user,
        "user_chart": user_chart,
        "matched_user": matched_user,
        "matched_chart": matched_chart,
        "match_data": match_data,
        "is_targeted": match_type == "targeted",
        "match_type": match_type,
        "target_zodiac_sign": target_zodiac_sign
    }


def execute_match_commit(
    db: Session,
    match_context: Dict[str, Any]
) -> Tuple[bool, str, Optional[DailyCPMatch]]:
    if not match_context:
        return False, "无效的匹配上下文", None
    
    try:
        user = match_context["user"]
        user_chart = match_context["user_chart"]
        matched_user = match_context["matched_user"]
        matched_chart = match_context["matched_chart"]
        match_data = match_context["match_data"]
        match_type = match_context["match_type"]
        is_targeted = match_context["is_targeted"]
        target_zodiac_sign = match_context["target_zodiac_sign"]
        
        today = get_today_date_str()
        now = get_utc_now()
        
        existing_match = db.query(DailyCPMatch).filter(
            or_(
                and_(
                    DailyCPMatch.user_a_id == user.id,
                    DailyCPMatch.user_b_id == matched_user.id
                ),
                and_(
                    DailyCPMatch.user_a_id == matched_user.id,
                    DailyCPMatch.user_b_id == user.id
                )
            ),
            DailyCPMatch.match_date == today,
            DailyCPMatch.status == "active"
        ).with_for_update().first()
        
        if existing_match:
            return False, "已存在有效匹配", None
        
        is_vip, vip_extra_count = check_user_vip_status(db, user.id)
        
        limit = db.query(DailyMatchLimit).filter(
            DailyMatchLimit.user_id == user.id,
            DailyMatchLimit.limit_date == today
        ).with_for_update().first()
        
        if not limit:
            limit = DailyMatchLimit(
                user_id=user.id,
                limit_date=today,
                free_match_count=0,
                free_match_max=1,
                vip_extra_match_count=0,
                vip_extra_match_max=vip_extra_count if is_vip else 0,
                paid_match_count=0,
                paid_match_max=10,
                targeted_match_count=0,
                targeted_match_max=3 if is_vip else 0,
                is_vip=is_vip
            )
            db.add(limit)
            db.flush()
        
        consumed = False
        
        if match_type == "free":
            if limit.free_match_count < limit.free_match_max:
                limit.free_match_count += 1
                consumed = True
            elif limit.vip_extra_match_count < limit.vip_extra_match_max:
                limit.vip_extra_match_count += 1
                consumed = True
        
        elif match_type == "vip_extra":
            if limit.vip_extra_match_count < limit.vip_extra_match_max:
                limit.vip_extra_match_count += 1
                consumed = True
        
        elif match_type == "targeted":
            if limit.targeted_match_count < limit.targeted_match_max:
                limit.targeted_match_count += 1
                consumed = True
        
        if not consumed:
            db.rollback()
            return False, "匹配次数不足", None
        
        batch_id = generate_batch_id()
        
        highlights = match_data.get("highlights", {})
        synastry_aspects = json.dumps(highlights.get("highlights", []), ensure_ascii=False)
        highlights_summary = json.dumps({
            "overall_theme": highlights.get("overall_theme", {}),
            "aspect_stats": highlights.get("aspect_stats", {}),
            "special_indicators": highlights.get("special_indicators", [])
        }, ensure_ascii=False)
        
        match_record = DailyCPMatch(
            match_date=today,
            match_batch_id=batch_id,
            user_a_id=user.id,
            user_b_id=matched_user.id,
            user_a_chart_id=user_chart.id,
            user_b_chart_id=matched_chart.id,
            compatibility_score=match_data.get("compatibility_score", 50),
            match_type="targeted" if is_targeted else "random",
            target_zodiac_sign=target_zodiac_sign,
            synastry_aspects=synastry_aspects,
            highlights_summary=highlights_summary,
            interpretation_text=match_data.get("interpretation", ""),
            user_a_status=DailyCPMatchStatus.PENDING,
            user_b_status=DailyCPMatchStatus.PENDING,
            match_source="manual_request",
            is_vip_targeted_match=is_targeted,
            status="active"
        )
        
        db.add(match_record)
        db.flush()
        
        db.commit()
        db.refresh(match_record)
        
        logger.info(f"创建每日匹配记录成功: match_id={match_record.id}, user_a={user.id}, user_b={matched_user.id}")
        
        return True, "匹配成功", match_record
        
    except Exception as e:
        db.rollback()
        logger.error(f"执行匹配提交失败: {str(e)}", exc_info=True)
        return False, str(e) or "匹配失败", None


def check_match_availability(
    db: Session,
    user_id: int,
    match_type: str = "free"
) -> Tuple[bool, str, Dict[str, Any]]:
    try:
        is_vip, vip_extra_count = check_user_vip_status(db, user_id)
        today = get_today_date_str()
        
        limit = db.query(DailyMatchLimit).filter(
            DailyMatchLimit.user_id == user_id,
            DailyMatchLimit.limit_date == today
        ).first()
        
        free_matches_remaining = 1
        vip_extra_matches_remaining = vip_extra_count
        
        if limit:
            free_matches_remaining = max(0, limit.free_match_max - limit.free_match_count)
            vip_extra_matches_remaining = max(0, limit.vip_extra_match_max - limit.vip_extra_match_count)
        
        can_match = False
        reason = "今日匹配次数已用完"
        
        if match_type == "free":
            if free_matches_remaining > 0:
                can_match = True
                reason = "可以进行免费匹配"
            elif is_vip and vip_extra_matches_remaining > 0:
                can_match = True
                reason = "可以使用VIP额外匹配次数"
            else:
                reason = "今日免费匹配次数已用完"
        
        elif match_type == "vip_extra":
            if is_vip and vip_extra_matches_remaining > 0:
                can_match = True
                reason = "可以进行VIP额外匹配"
            elif not is_vip:
                reason = "您不是VIP会员"
            else:
                reason = "VIP额外匹配次数已用完"
        
        return (
            can_match,
            reason,
            {
                "free_matches_remaining": free_matches_remaining,
                "vip_extra_matches_remaining": vip_extra_matches_remaining,
                "is_vip": is_vip
            }
        )
        
    except Exception as e:
        logger.error(f"检查匹配可用性失败: {str(e)}", exc_info=True)
        return False, "检查失败", {
            "free_matches_remaining": 0,
            "vip_extra_matches_remaining": 0,
            "is_vip": False
        }


def get_match_for_user(
    db: Session,
    match: DailyCPMatch,
    user_id: int
) -> Optional[Dict[str, Any]]:
    if match.user_a_id != user_id and match.user_b_id != user_id:
        return None
    
    is_user_a = match.user_a_id == user_id
    
    other_user_id = match.user_b_id if is_user_a else match.user_a_id
    other_user = db.query(User).filter(User.id == other_user_id).first()
    
    if not other_user:
        return None
    
    my_status = match.user_a_status if is_user_a else match.user_b_status
    other_status = match.user_b_status if is_user_a else match.user_a_status
    
    my_profile_unlocked = match.user_a_profile_unlocked if is_user_a else match.user_b_profile_unlocked
    other_profile_unlocked = match.user_b_profile_unlocked if is_user_a else match.user_a_profile_unlocked
    
    highlights_summary = {}
    if match.highlights_summary:
        try:
            highlights_summary = json.loads(match.highlights_summary)
        except:
            pass
    
    synastry_aspects = []
    if match.synastry_aspects:
        try:
            synastry_aspects = json.loads(match.synastry_aspects)
        except:
            pass
    
    other_user_chart = None
    if is_user_a and match.user_b_chart_id:
        other_user_chart = db.query(Chart).filter(Chart.id == match.user_b_chart_id).first()
    elif not is_user_a and match.user_a_chart_id:
        other_user_chart = db.query(Chart).filter(Chart.id == match.user_a_chart_id).first()
    
    other_sun_sign = None
    if other_user_chart:
        other_sun_sign = get_user_zodiac_sign_from_chart(other_user_chart)
    
    my_chart = None
    if is_user_a and match.user_a_chart_id:
        my_chart = db.query(Chart).filter(Chart.id == match.user_a_chart_id).first()
    elif not is_user_a and match.user_b_chart_id:
        my_chart = db.query(Chart).filter(Chart.id == match.user_b_chart_id).first()
    
    my_sun_sign = None
    if my_chart:
        my_sun_sign = get_user_zodiac_sign_from_chart(my_chart)
    
    session_info = None
    if match.session_id:
        session = db.query(TimeLimitedSession).filter(
            TimeLimitedSession.id == match.session_id
        ).first()
        if session:
            now = get_utc_now()
            time_remaining = session.expires_at - now if session.expires_at > now else timedelta(0)
            
            session_info = {
                "session_id": session.id,
                "session_key": session.session_key,
                "started_at": session.started_at.isoformat() if session.started_at else None,
                "expires_at": session.expires_at.isoformat() if session.expires_at else None,
                "time_remaining_seconds": int(time_remaining.total_seconds()),
                "is_active": session.is_active,
                "is_extended": session.is_extended,
                "extension_count": session.extension_count,
                "total_duration_hours": session.total_duration_hours,
                "private_chat_id": session.private_chat_id,
                "message_count": session.message_count
            }
    
    return {
        "match_id": match.id,
        "match_date": match.match_date,
        "compatibility_score": match.compatibility_score,
        "match_type": match.match_type,
        "target_zodiac_sign": match.target_zodiac_sign,
        
        "my_info": {
            "user_id": user_id,
            "sun_sign": my_sun_sign,
            "status": my_status,
            "profile_unlocked": my_profile_unlocked
        },
        
        "other_user_info": {
            "user_id": other_user.id,
            "username": other_user.username,
            "sun_sign": other_sun_sign,
            "status": other_status,
            "profile_unlocked": other_profile_unlocked,
            "basic_info_visible": True,
            "full_info_visible": other_profile_unlocked or my_profile_unlocked
        },
        
        "match_details": {
            "highlights_summary": highlights_summary,
            "synastry_aspects": synastry_aspects[:5],
            "interpretation": match.interpretation_text
        },
        
        "mutual_accepted": match.is_mutual_accepted,
        "mutual_accepted_at": match.mutual_accepted_at.isoformat() if match.mutual_accepted_at else None,
        
        "session": session_info,
        
        "match_source": match.match_source,
        "is_vip_targeted_match": match.is_vip_targeted_match,
        
        "created_at": match.created_at.isoformat() if match.created_at else None
    }


def accept_match(
    db: Session,
    match_id: int,
    user_id: int
) -> Tuple[bool, str, Optional[DailyCPMatch]]:
    try:
        match = db.query(DailyCPMatch).filter(
            DailyCPMatch.id == match_id,
            DailyCPMatch.status == "active"
        ).with_for_update().first()
        
        if not match:
            return False, "匹配不存在", None
        
        if match.user_a_id != user_id and match.user_b_id != user_id:
            return False, "无权操作此匹配", None
        
        is_user_a = match.user_a_id == user_id
        
        if is_user_a:
            if match.user_a_status == DailyCPMatchStatus.ACCEPTED:
                return False, "您已经接受了匹配", match
            if match.user_a_status == DailyCPMatchStatus.REJECTED:
                return False, "您已经拒绝了匹配", match
            
            match.user_a_status = DailyCPMatchStatus.ACCEPTED
            match.user_a_accepted_at = get_utc_now()
        else:
            if match.user_b_status == DailyCPMatchStatus.ACCEPTED:
                return False, "您已经接受了匹配", match
            if match.user_b_status == DailyCPMatchStatus.REJECTED:
                return False, "您已经拒绝了匹配", match
            
            match.user_b_status = DailyCPMatchStatus.ACCEPTED
            match.user_b_accepted_at = get_utc_now()
        
        db.flush()
        
        if match.user_a_status == DailyCPMatchStatus.ACCEPTED and match.user_b_status == DailyCPMatchStatus.ACCEPTED:
            match.is_mutual_accepted = True
            match.mutual_accepted_at = get_utc_now()
            
            try:
                now = get_utc_now()
                expires_at = now + timedelta(hours=24)
                
                session_key = generate_secure_session_key()
                
                min_id = min(match.user_a_id, match.user_b_id)
                max_id = max(match.user_a_id, match.user_b_id)
                chat_identifier = generate_secure_chat_identifier()
                
                existing_chat = db.query(UserPrivateChat).filter(
                    UserPrivateChat.user_a_id == min_id,
                    UserPrivateChat.user_b_id == max_id,
                    UserPrivateChat.is_active == True
                ).first()
                
                private_chat_id = None
                if existing_chat:
                    private_chat_id = existing_chat.id
                else:
                    new_chat = UserPrivateChat(
                        user_a_id=min_id,
                        user_b_id=max_id,
                        chat_identifier=chat_identifier,
                        match_source="daily_cp_match",
                        match_source_id=match.id,
                        match_compatibility_score=match.compatibility_score,
                        match_type="time_limited",
                        is_active=True
                    )
                    db.add(new_chat)
                    db.flush()
                    private_chat_id = new_chat.id
                
                session = TimeLimitedSession(
                    session_key=session_key,
                    user_a_id=match.user_a_id,
                    user_b_id=match.user_b_id,
                    match_id=match.id,
                    base_duration_hours=24,
                    extended_duration_hours=0,
                    total_duration_hours=24,
                    started_at=now,
                    expires_at=expires_at,
                    is_extended=False,
                    extension_count=0,
                    private_chat_id=private_chat_id,
                    is_active=True
                )
                
                db.add(session)
                db.flush()
                
                match.session_id = session.id
                
                logger.info(f"创建限时会话成功: session_id={session.id}, match_id={match.id}")
                
            except Exception as e:
                logger.error(f"创建会话失败，回滚操作: {str(e)}", exc_info=True)
                raise
        
        db.commit()
        db.refresh(match)
        
        if match.is_mutual_accepted:
            return True, "双方已确认匹配，限时聊天已开启", match
        
        return True, "已接受匹配，等待对方确认", match
        
    except Exception as e:
        db.rollback()
        logger.error(f"接受匹配失败: {str(e)}", exc_info=True)
        return False, str(e) or "操作失败", None


def reject_match(
    db: Session,
    match_id: int,
    user_id: int
) -> Tuple[bool, str, Optional[DailyCPMatch]]:
    try:
        match = db.query(DailyCPMatch).filter(
            DailyCPMatch.id == match_id,
            DailyCPMatch.status == "active"
        ).with_for_update().first()
        
        if not match:
            return False, "匹配不存在", None
        
        if match.user_a_id != user_id and match.user_b_id != user_id:
            return False, "无权操作此匹配", None
        
        is_user_a = match.user_a_id == user_id
        
        if is_user_a:
            if match.user_a_status in [DailyCPMatchStatus.ACCEPTED, DailyCPMatchStatus.REJECTED]:
                return False, "您已经操作过此匹配", match
            match.user_a_status = DailyCPMatchStatus.REJECTED
        else:
            if match.user_b_status in [DailyCPMatchStatus.ACCEPTED, DailyCPMatchStatus.REJECTED]:
                return False, "您已经操作过此匹配", match
            match.user_b_status = DailyCPMatchStatus.REJECTED
        
        match.status = "rejected"
        match.expired_at = get_utc_now()
        
        db.commit()
        db.refresh(match)
        
        return True, "已拒绝匹配", match
        
    except Exception as e:
        db.rollback()
        logger.error(f"拒绝匹配失败: {str(e)}", exc_info=True)
        return False, str(e) or "操作失败", None


def check_and_close_expired_sessions(db: Session) -> int:
    now = get_utc_now()
    
    try:
        expired_sessions = db.query(TimeLimitedSession).filter(
            TimeLimitedSession.is_active == True,
            TimeLimitedSession.expires_at <= now
        ).limit(MAX_QUERY_LIMIT).all()
        
        if not expired_sessions:
            return 0
        
        session_ids = [s.id for s in expired_sessions]
        
        stmt1 = update(TimeLimitedSession).where(
            TimeLimitedSession.id.in_(session_ids)
        ).values(
            is_active=False,
            closed_at=now,
            close_reason="expired"
        )
        db.execute(stmt1)
        
        db.commit()
        
        closed_count = len(session_ids)
        logger.info(f"批量关闭过期会话: count={closed_count}")
        
        return closed_count
        
    except Exception as e:
        db.rollback()
        logger.error(f"关闭过期会话失败: {str(e)}", exc_info=True)
        return 0


def extend_session(
    db: Session,
    session_id: int,
    user_id: int,
    extension_hours: int = 168,
    is_vip_free: bool = False
) -> Tuple[bool, str, Optional[TimeLimitedSession]]:
    try:
        session = db.query(TimeLimitedSession).filter(
            TimeLimitedSession.id == session_id,
            TimeLimitedSession.is_active == True
        ).with_for_update().first()
        
        if not session:
            return False, "会话不存在或已过期", None
        
        if session.user_a_id != user_id and session.user_b_id != user_id:
            return False, "无权操作此会话", None
        
        now = get_utc_now()
        new_expires_at = session.expires_at + timedelta(hours=extension_hours)
        
        session.extended_duration_hours += extension_hours
        session.total_duration_hours += extension_hours
        session.is_extended = True
        session.extension_count += 1
        session.expires_at = new_expires_at
        
        db.commit()
        db.refresh(session)
        
        logger.info(f"延长会话成功: session_id={session.id}, 延长{extension_hours}小时")
        
        return True, f"会话已延长{extension_hours}小时", session
        
    except Exception as e:
        db.rollback()
        logger.error(f"延长会话失败: {str(e)}", exc_info=True)
        return False, str(e) or "操作失败", None


def perform_manual_match(
    db: Session,
    user: User,
    match_type: str = "free",
    target_zodiac_sign: Optional[str] = None
) -> Tuple[bool, str, Optional[DailyCPMatch]]:
    success, message, match_context = prepare_match_candidates(
        db, user.id, match_type, target_zodiac_sign
    )
    
    if not success or not match_context:
        return False, message, None
    
    return execute_match_commit(db, match_context)


def get_match_detail(
    db: Session,
    match_id: int,
    user_id: int
) -> Optional[Dict[str, Any]]:
    match = db.query(DailyCPMatch).filter(
        DailyCPMatch.id == match_id,
        DailyCPMatch.status == "active"
    ).first()
    if not match:
        return None

    if user_id != match.user_a_id and user_id != match.user_b_id:
        return None

    detail = get_match_for_user(db, match, user_id)
    detail["can_unlock_profile"] = False
    detail["can_extend_session"] = False

    if user_id == match.user_a_id:
        detail["can_unlock_profile"] = not match.user_a_profile_unlocked
    else:
        detail["can_unlock_profile"] = not match.user_b_profile_unlocked

    if match.session_id:
        session = db.query(TimeLimitedSession).filter(
            TimeLimitedSession.id == match.session_id,
            (TimeLimitedSession.user_a_id == user_id) | (TimeLimitedSession.user_b_id == user_id)
        ).first()
        if session and session.is_active:
            detail["can_extend_session"] = True

    return detail


def get_session_detail(
    db: Session,
    session_id: int,
    user_id: int
) -> Optional[Dict[str, Any]]:
    session = db.query(TimeLimitedSession).filter(
        TimeLimitedSession.id == session_id,
        (TimeLimitedSession.user_a_id == user_id) | (TimeLimitedSession.user_b_id == user_id)
    ).first()
    if not session:
        return None

    other_user_id = session.user_b_id if session.user_a_id == user_id else session.user_a_id
    other_user = db.query(User).filter(User.id == other_user_id).first()

    return {
        "session_id": session.id,
        "session_key": session.session_key,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "expires_at": session.expires_at.isoformat() if session.expires_at else None,
        "is_active": session.is_active,
        "is_extended": session.is_extended,
        "extension_count": session.extension_count,
        "total_duration_hours": session.total_duration_hours,
        "message_count": session.message_count,
        "private_chat_id": session.private_chat_id,
        "other_user": {
            "user_id": other_user.id if other_user else None,
            "username": other_user.username if other_user else None
        }
    }


def deduct_user_balance(
    db: Session,
    user_id: int,
    amount: int,
    currency_type: str,
    transaction_type: str,
    description: str,
    related_type: str = None,
    related_id: str = None
) -> Tuple[bool, str, Optional[StarDustTransaction]]:
    try:
        user = db.query(User).filter(
            User.id == user_id
        ).with_for_update().first()
        
        if not user:
            return False, "用户不存在", None
        
        now = get_utc_now()
        
        if currency_type == "point":
            balance = user.stardust_point_balance or 0
        elif currency_type == "fragment":
            balance = user.stardust_fragment_balance or 0
        else:
            return False, "不支持的货币类型", None
        
        if balance < amount:
            currency_name = "高阶星尘" if currency_type == "point" else "星元碎片"
            return False, f"{currency_name}不足，需要 {amount}，当前 {balance}", None
        
        balance_after = balance - amount
        
        if currency_type == "point":
            user.stardust_point_balance = balance_after
        else:
            user.stardust_fragment_balance = balance_after
        
        transaction = StarDustTransaction(
            user_id=user_id,
            transaction_type=transaction_type,
            currency_type=currency_type,
            amount=-amount,
            balance_before=balance,
            balance_after=balance_after,
            related_type=related_type,
            related_id=related_id,
            description=description,
            created_at=now
        )
        
        db.add(transaction)
        db.flush()
        
        return True, "扣费成功", transaction
        
    except Exception as e:
        logger.error(f"扣费失败: {str(e)}", exc_info=True)
        return False, str(e) or "扣费失败", None


def unlock_profile(
    db: Session,
    match_id: int,
    user_id: int,
    target_user_id: int
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    now = get_utc_now()
    
    config = UNLOCK_PROFILE_CONFIG
    cost = config["cost"]
    currency_type = config["currency_type"]
    description = config["description"]
    
    if cost <= 0:
        logger.error(f"解锁配置错误: cost={cost}，必须大于0")
        return False, "系统配置错误，请联系管理员", None
    
    try:
        match = db.query(DailyCPMatch).filter(
            DailyCPMatch.id == match_id,
            DailyCPMatch.status == "active"
        ).with_for_update().first()

        if not match:
            db.rollback()
            return False, "匹配不存在", None

        if user_id != match.user_a_id and user_id != match.user_b_id:
            db.rollback()
            return False, "无权解锁此资料", None

        if target_user_id != match.user_a_id and target_user_id != match.user_b_id:
            db.rollback()
            return False, "目标用户不在当前匹配中", None

        if user_id == target_user_id:
            db.rollback()
            return False, "不能解锁自己的资料", None

        is_user_a = user_id == match.user_a_id
        is_target_user_b = target_user_id == match.user_b_id
        
        if is_user_a and is_target_user_b:
            if match.user_a_profile_unlocked:
                db.rollback()
                return False, "对方资料已解锁", None
            unlock_field = "user_a_profile_unlocked"
        elif not is_user_a and not is_target_user_b:
            if match.user_b_profile_unlocked:
                db.rollback()
                return False, "对方资料已解锁", None
            unlock_field = "user_b_profile_unlocked"
        else:
            db.rollback()
            return False, "参数错误", None
        
        success, msg, transaction = deduct_user_balance(
            db=db,
            user_id=user_id,
            amount=cost,
            currency_type=currency_type,
            transaction_type="profile_unlock",
            description=f"{description}: 匹配ID {match_id}",
            related_type="daily_cp_match",
            related_id=str(match_id)
        )
        
        if not success:
            db.rollback()
            return False, msg, None
        
        if unlock_field == "user_a_profile_unlocked":
            match.user_a_profile_unlocked = True
            match.user_a_profile_unlocked_at = now
        else:
            match.user_b_profile_unlocked = True
            match.user_b_profile_unlocked_at = now
        
        unlock_record = ProfileUnlock(
            unlock_no=f"UNL_{secrets.token_hex(6).upper()}",
            match_id=match.id,
            buyer_user_id=user_id,
            target_user_id=target_user_id,
            price=cost,
            currency_type=currency_type,
            unlocked_at=now,
            expires_at=None,
            is_permanent=True,
            status="completed"
        )
        db.add(unlock_record)

        db.commit()
        db.refresh(match)

        return True, "资料解锁成功", {
            "match_id": match.id,
            "target_user_id": target_user_id,
            "profile_unlocked": True,
            "unlocked_at": now.isoformat(),
            "cost": cost,
            "currency_type": currency_type
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"解锁资料失败: {str(e)}", exc_info=True)
        return False, "操作失败，请稍后重试", None


def create_daily_match_record_internal(
    db: Session,
    user_a: User,
    user_a_chart: Chart,
    user_b: User,
    user_b_chart: Chart,
    match_data: Dict[str, Any],
    match_source: str = "daily_scheduled",
    is_targeted: bool = False,
    target_zodiac_sign: Optional[str] = None
) -> DailyCPMatch:
    today = get_today_date_str()
    batch_id = generate_batch_id()
    
    highlights = match_data.get("highlights", {})
    synastry_aspects = json.dumps(highlights.get("highlights", []), ensure_ascii=False)
    highlights_summary = json.dumps({
        "overall_theme": highlights.get("overall_theme", {}),
        "aspect_stats": highlights.get("aspect_stats", {}),
        "special_indicators": highlights.get("special_indicators", [])
    }, ensure_ascii=False)
    
    match = DailyCPMatch(
        match_date=today,
        match_batch_id=batch_id,
        user_a_id=user_a.id,
        user_b_id=user_b.id,
        user_a_chart_id=user_a_chart.id,
        user_b_chart_id=user_b_chart.id,
        compatibility_score=match_data.get("compatibility_score", 50),
        match_type="targeted" if is_targeted else "random",
        target_zodiac_sign=target_zodiac_sign,
        synastry_aspects=synastry_aspects,
        highlights_summary=highlights_summary,
        interpretation_text=match_data.get("interpretation", ""),
        user_a_status=DailyCPMatchStatus.PENDING,
        user_b_status=DailyCPMatchStatus.PENDING,
        match_source=match_source,
        is_vip_targeted_match=is_targeted,
        status="active"
    )
    
    db.add(match)
    db.flush()
    
    logger.info(f"创建每日匹配记录成功: match_id={match.id}, user_a={user_a.id}, user_b={user_b.id}")
    
    return match


def create_daily_match_record(
    db: Session,
    user_a: User,
    user_a_chart: Chart,
    user_b: User,
    user_b_chart: Chart,
    match_data: Dict[str, Any],
    match_source: str = "daily_scheduled",
    is_targeted: bool = False,
    target_zodiac_sign: Optional[str] = None
) -> DailyCPMatch:
    return create_daily_match_record_internal(
        db, user_a, user_a_chart, user_b, user_b_chart,
        match_data, match_source, is_targeted, target_zodiac_sign
    )


def get_user_today_match(
    db: Session,
    user_id: int
) -> Optional[DailyCPMatch]:
    today = get_today_date_str()
    
    match = db.query(DailyCPMatch).filter(
        or_(
            DailyCPMatch.user_a_id == user_id,
            DailyCPMatch.user_b_id == user_id
        ),
        DailyCPMatch.match_date == today,
        DailyCPMatch.status == "active"
    ).first()
    
    return match
