import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func, select
from sqlalchemy.exc import IntegrityError
import json

from app.models import (
    User, PlazaPost, PlazaLike, PlazaFlowerGift, PlazaMention,
    PlazaPostReport, PlazaPostTag, PlazaUserShareRecord,
    PlazaPostType, PlazaPostStatus, UserVIP, Gift,
    TopicChallenge, TopicParticipation, TopicChallengeStatus
)

logger = logging.getLogger(__name__)


def get_utc_now() -> datetime:
    return datetime.utcnow()


def check_user_vip_status(db: Session, user_id: int) -> Tuple[bool, Optional[UserVIP]]:
    user_vip = db.query(UserVIP).filter(UserVIP.user_id == user_id).first()
    if not user_vip or not user_vip.is_vip:
        return False, None
    if user_vip.expires_at and user_vip.expires_at <= get_utc_now():
        return False, None
    return True, user_vip


def create_plaza_post(
    db: Session,
    user_id: int,
    post_type: str,
    title: Optional[str] = None,
    content: Optional[str] = None,
    image_urls: Optional[List[str]] = None,
    related_data: Optional[Dict] = None,
    synastry_record_id: Optional[int] = None,
    past_life_record_id: Optional[int] = None,
    photocard_record_id: Optional[int] = None,
    tags: Optional[List[str]] = None,
    topic_challenge_id: Optional[int] = None,
) -> Tuple[Optional[PlazaPost], Optional[str]]:
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None, "用户不存在"

        is_vip, user_vip = check_user_vip_status(db, user_id)

        topic = None
        if topic_challenge_id:
            topic = db.query(TopicChallenge).filter(
                TopicChallenge.id == topic_challenge_id
            ).first()
            if not topic:
                return None, "话题挑战不存在"

            now = get_utc_now()
            if topic.status != TopicChallengeStatus.ACTIVE.value:
                return None, "话题挑战未激活"
            if now < topic.start_time or now > topic.end_time:
                return None, "话题挑战不在活动时间内"

            existing_participation = db.query(TopicParticipation).filter(
                TopicParticipation.topic_id == topic_challenge_id,
                TopicParticipation.user_id == user_id
            ).first()
            if existing_participation:
                return None, "您已参与过此话题挑战"

            if topic.max_participants and topic.participant_count >= topic.max_participants:
                return None, "话题挑战参与人数已达上限"

        post = PlazaPost(
            user_id=user_id,
            post_type=post_type,
            title=title,
            content=content,
            image_urls=json.dumps(image_urls, ensure_ascii=False) if image_urls else None,
            related_data=json.dumps(related_data, ensure_ascii=False) if related_data else None,
            synastry_record_id=synastry_record_id,
            past_life_record_id=past_life_record_id,
            photocard_record_id=photocard_record_id,
            like_count=0,
            flower_count=0,
            mention_count=0,
            status=PlazaPostStatus.PUBLISHED.value,
            is_vip=is_vip,
            vip_border_style="gold_gradient" if is_vip else None,
        )

        db.add(post)
        db.flush()

        if tags and len(tags) > 0:
            for tag in tags:
                post_tag = PlazaPostTag(
                    post_id=post.id,
                    tag_key="custom",
                    tag_value=tag,
                    tag_category="user",
                    is_auto_generated=False,
                )
                db.add(post_tag)

        if topic and topic_challenge_id:
            participation = TopicParticipation(
                topic_id=topic_challenge_id,
                post_id=post.id,
                user_id=user_id,
                hot_score=0,
                participated_at=get_utc_now(),
            )
            db.add(participation)
            db.query(TopicChallenge).filter(TopicChallenge.id == topic_challenge_id).update(
                {TopicChallenge.participant_count: TopicChallenge.participant_count + 1},
                synchronize_session=False
            )

        db.commit()
        db.refresh(post)

        return post, None

    except Exception as e:
        logger.error(f"创建广场内容失败: {e}")
        db.rollback()
        return None, str(e)


def get_plaza_post_list(
    db: Session,
    sort_by: str = "latest",
    limit: int = 20,
    offset: int = 0,
    post_type: Optional[str] = None,
    user_id: Optional[int] = None,
    topic_challenge_id: Optional[int] = None,
) -> Tuple[List[PlazaPost], int]:
    query = db.query(PlazaPost).filter(
        PlazaPost.status == PlazaPostStatus.PUBLISHED.value
    )

    if post_type:
        query = query.filter(PlazaPost.post_type == post_type)

    if user_id:
        query = query.filter(PlazaPost.user_id == user_id)

    if topic_challenge_id:
        query = query.join(
            TopicParticipation, TopicParticipation.post_id == PlazaPost.id
        ).filter(
            TopicParticipation.topic_id == topic_challenge_id
        )

    total_count = query.count()

    if sort_by == "hot":
        query = query.order_by(
            desc(PlazaPost.like_count + PlazaPost.flower_count),
            desc(PlazaPost.created_at),
        )
    else:
        query = query.order_by(desc(PlazaPost.created_at))

    posts = query.offset(offset).limit(limit).all()

    return posts, total_count


def get_plaza_post_by_id(db: Session, post_id: int) -> Optional[PlazaPost]:
    return db.query(PlazaPost).filter(
        PlazaPost.id == post_id,
        PlazaPost.status.in_([PlazaPostStatus.PUBLISHED.value, PlazaPostStatus.PENDING_REVIEW.value])
    ).first()


def toggle_like(
    db: Session,
    post_id: int,
    user_id: int,
) -> Tuple[bool, int, str]:
    try:
        post = get_plaza_post_by_id(db, post_id)
        if not post:
            return False, 0, "内容不存在或已被删除"

        existing_like = db.query(PlazaLike).filter(
            PlazaLike.post_id == post_id,
            PlazaLike.user_id == user_id,
        ).first()

        is_liked = False
        if existing_like:
            if existing_like.is_active:
                existing_like.is_active = False
                existing_like.updated_at = get_utc_now()
                db.query(PlazaPost).filter(PlazaPost.id == post_id).update(
                    {PlazaPost.like_count: PlazaPost.like_count - 1},
                    synchronize_session=False
                )
                is_liked = False
            else:
                existing_like.is_active = True
                existing_like.updated_at = get_utc_now()
                db.query(PlazaPost).filter(PlazaPost.id == post_id).update(
                    {PlazaPost.like_count: PlazaPost.like_count + 1},
                    synchronize_session=False
                )
                is_liked = True
        else:
            try:
                new_like = PlazaLike(
                    post_id=post_id,
                    user_id=user_id,
                    is_active=True,
                )
                db.add(new_like)
                db.flush()
                
                db.query(PlazaPost).filter(PlazaPost.id == post_id).update(
                    {PlazaPost.like_count: PlazaPost.like_count + 1},
                    synchronize_session=False
                )
                is_liked = True
            except IntegrityError:
                db.rollback()
                existing_like = db.query(PlazaLike).filter(
                    PlazaLike.post_id == post_id,
                    PlazaLike.user_id == user_id,
                ).first()
                if existing_like and not existing_like.is_active:
                    existing_like.is_active = True
                    existing_like.updated_at = get_utc_now()
                    db.query(PlazaPost).filter(PlazaPost.id == post_id).update(
                        {PlazaPost.like_count: PlazaPost.like_count + 1},
                        synchronize_session=False
                    )
                    is_liked = True
                else:
                    is_liked = False

        db.commit()
        
        updated_post = db.query(PlazaPost).filter(PlazaPost.id == post_id).first()
        return is_liked, updated_post.like_count if updated_post else 0, "success"

    except Exception as e:
        logger.error(f"点赞操作失败: {e}")
        db.rollback()
        return False, 0, str(e)


def check_user_liked(db: Session, post_id: int, user_id: int) -> bool:
    like = db.query(PlazaLike).filter(
        PlazaLike.post_id == post_id,
        PlazaLike.user_id == user_id,
        PlazaLike.is_active == True,
    ).first()
    return like is not None


def send_flower_to_post(
    db: Session,
    post_id: int,
    sender_id: int,
    gift_id: int,
    quantity: int = 1,
    message: Optional[str] = None,
    is_anonymous: bool = False,
) -> Tuple[Optional[PlazaFlowerGift], Optional[str]]:
    try:
        if quantity < 1:
            return None, "送花数量必须大于0"

        post = get_plaza_post_by_id(db, post_id)
        if not post:
            return None, "内容不存在或已被删除"

        if sender_id == post.user_id:
            return None, "不能给自己送花"

        gift = db.query(Gift).filter(Gift.id == gift_id, Gift.is_active == True).first()
        if not gift:
            return None, "礼物不存在或已下架"

        total_cost = gift.price * quantity

        sender = db.query(User).filter(User.id == sender_id).with_for_update().first()
        if not sender:
            return None, "发送者不存在"

        if gift.currency_type == "stardust_point":
            if sender.stardust_point_balance < total_cost:
                return None, "星尘点数不足"
            sender.stardust_point_balance -= total_cost
        elif gift.currency_type == "stardust_fragment":
            if sender.stardust_fragment_balance < total_cost:
                return None, "星尘碎片不足"
            sender.stardust_fragment_balance -= total_cost
        else:
            return None, "不支持的支付方式"

        flower_gift = PlazaFlowerGift(
            post_id=post_id,
            sender_id=sender_id,
            receiver_id=post.user_id,
            gift_id=gift_id,
            gift_name=gift.name,
            gift_icon=gift.animation_effect,
            gift_rarity=gift.rarity,
            quantity=quantity,
            message=message,
            is_anonymous=is_anonymous,
            cost_points=total_cost if gift.currency_type == "stardust_point" else 0,
            cost_fragments=total_cost if gift.currency_type == "stardust_fragment" else 0,
        )

        db.add(flower_gift)
        
        db.query(PlazaPost).filter(PlazaPost.id == post_id).update(
            {PlazaPost.flower_count: PlazaPost.flower_count + quantity},
            synchronize_session=False
        )

        db.commit()
        db.refresh(flower_gift)

        return flower_gift, None

    except Exception as e:
        logger.error(f"送花操作失败: {e}")
        db.rollback()
        return None, str(e)


def create_mention(
    db: Session,
    post_id: int,
    inviter_id: int,
    invitee_id: int,
    invitation_type: str = "synastry",
    message: Optional[str] = None,
) -> Tuple[Optional[PlazaMention], Optional[str]]:
    try:
        post = get_plaza_post_by_id(db, post_id)
        if not post:
            return None, "内容不存在或已被删除"

        if inviter_id == invitee_id:
            return None, "不能邀请自己"

        inviter = db.query(User).filter(User.id == inviter_id).first()
        if not inviter:
            return None, "邀请者不存在"

        invitee = db.query(User).filter(User.id == invitee_id).first()
        if not invitee:
            return None, "被邀请者不存在"

        existing_mention = db.query(PlazaMention).filter(
            PlazaMention.post_id == post_id,
            PlazaMention.inviter_id == inviter_id,
            PlazaMention.invitee_id == invitee_id,
        ).first()

        if existing_mention:
            return None, "已发送过邀请"

        try:
            mention = PlazaMention(
                post_id=post_id,
                inviter_id=inviter_id,
                invitee_id=invitee_id,
                invitation_type=invitation_type,
                message=message,
            )

            db.add(mention)
            db.flush()
            
            db.query(PlazaPost).filter(PlazaPost.id == post_id).update(
                {PlazaPost.mention_count: PlazaPost.mention_count + 1},
                synchronize_session=False
            )

            db.commit()
            db.refresh(mention)

            return mention, None
            
        except IntegrityError:
            db.rollback()
            return None, "已发送过邀请"

    except Exception as e:
        logger.error(f"创建邀请失败: {e}")
        db.rollback()
        return None, str(e)


def respond_to_mention(
    db: Session,
    mention_id: int,
    user_id: int,
    is_accepted: bool,
    decline_reason: Optional[str] = None,
) -> Tuple[Optional[PlazaMention], Optional[str]]:
    try:
        mention = db.query(PlazaMention).filter(
            PlazaMention.id == mention_id,
            PlazaMention.invitee_id == user_id,
        ).first()

        if not mention:
            return None, "邀请不存在或无权操作"

        if mention.is_accepted is not None:
            return None, "已处理过此邀请"

        mention.is_accepted = is_accepted
        if is_accepted:
            mention.accepted_at = get_utc_now()
        else:
            mention.declined_at = get_utc_now()
            mention.decline_reason = decline_reason

        db.commit()
        db.refresh(mention)

        return mention, None

    except Exception as e:
        logger.error(f"处理邀请失败: {e}")
        db.rollback()
        return None, str(e)


def report_post(
    db: Session,
    post_id: int,
    reporter_id: Optional[int],
    report_category: str,
    report_reason: Optional[str] = None,
    reporter_ip: Optional[str] = None,
) -> Tuple[Optional[PlazaPostReport], Optional[str]]:
    try:
        post = get_plaza_post_by_id(db, post_id)
        if not post:
            return None, "内容不存在或已被删除"

        if reporter_id:
            existing_report = db.query(PlazaPostReport).filter(
                PlazaPostReport.post_id == post_id,
                PlazaPostReport.reporter_id == reporter_id,
            ).first()
            if existing_report:
                return None, "您已举报过此内容"

        report = PlazaPostReport(
            post_id=post_id,
            reporter_id=reporter_id,
            report_category=report_category,
            report_reason=report_reason,
            reporter_ip=reporter_ip,
        )

        db.add(report)
        db.commit()
        db.refresh(report)

        return report, None

    except Exception as e:
        logger.error(f"举报内容失败: {e}")
        db.rollback()
        return None, str(e)


def hide_post(
    db: Session,
    post_id: int,
    admin_id: int,
    hide_reason: Optional[str] = None,
) -> Tuple[Optional[PlazaPost], Optional[str]]:
    try:
        post = db.query(PlazaPost).filter(PlazaPost.id == post_id).first()
        if not post:
            return None, "内容不存在"

        post.status = PlazaPostStatus.HIDDEN.value
        post.hide_reason = hide_reason
        post.hidden_by = admin_id
        post.updated_at = get_utc_now()

        db.commit()
        db.refresh(post)

        return post, None

    except Exception as e:
        logger.error(f"隐藏内容失败: {e}")
        db.rollback()
        return None, str(e)


def remove_post(
    db: Session,
    post_id: int,
    admin_id: int,
    hide_reason: Optional[str] = None,
) -> Tuple[Optional[PlazaPost], Optional[str]]:
    try:
        post = db.query(PlazaPost).filter(PlazaPost.id == post_id).first()
        if not post:
            return None, "内容不存在"

        post.status = PlazaPostStatus.REMOVED.value
        post.hide_reason = hide_reason
        post.hidden_by = admin_id
        post.updated_at = get_utc_now()

        db.commit()
        db.refresh(post)

        return post, None

    except Exception as e:
        logger.error(f"下架内容失败: {e}")
        db.rollback()
        return None, str(e)


def get_user_posts(
    db: Session,
    user_id: int,
    limit: int = 20,
    offset: int = 0,
) -> Tuple[List[PlazaPost], int]:
    query = db.query(PlazaPost).filter(
        PlazaPost.user_id == user_id,
        PlazaPost.status == PlazaPostStatus.PUBLISHED.value,
    )

    total_count = query.count()
    posts = query.order_by(desc(PlazaPost.created_at)).offset(offset).limit(limit).all()

    return posts, total_count


def delete_user_post(
    db: Session,
    post_id: int,
    user_id: int,
) -> Tuple[bool, str]:
    try:
        post = db.query(PlazaPost).filter(
            PlazaPost.id == post_id,
            PlazaPost.user_id == user_id,
        ).first()

        if not post:
            return False, "内容不存在或无权删除"

        post.status = PlazaPostStatus.USER_DELETED.value
        post.updated_at = get_utc_now()

        db.commit()
        return True, "删除成功"

    except Exception as e:
        logger.error(f"删除内容失败: {e}")
        db.rollback()
        return False, str(e)


def get_user_map(db: Session, user_ids: List[int]) -> Dict[int, User]:
    if not user_ids:
        return {}
    
    users = db.query(User).filter(User.id.in_(user_ids)).all()
    return {user.id: user for user in users}


def get_post_likes(
    db: Session,
    post_id: int,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict]:
    likes = db.query(PlazaLike, User).join(
        User, PlazaLike.user_id == User.id
    ).filter(
        PlazaLike.post_id == post_id,
        PlazaLike.is_active == True,
    ).order_by(desc(PlazaLike.created_at)).offset(offset).limit(limit).all()

    result = []
    for like, user in likes:
        result.append({
            "user_id": user.id,
            "username": user.username,
            "liked_at": like.created_at.isoformat() if like.created_at else None,
        })

    return result


def get_post_flowers(
    db: Session,
    post_id: int,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict]:
    flowers = db.query(PlazaFlowerGift, User).join(
        User, PlazaFlowerGift.sender_id == User.id
    ).filter(
        PlazaFlowerGift.post_id == post_id,
    ).order_by(desc(PlazaFlowerGift.created_at)).offset(offset).limit(limit).all()

    result = []
    for flower, user in flowers:
        result.append({
            "id": flower.id,
            "sender_id": flower.sender_id,
            "sender_name": None if flower.is_anonymous else user.username,
            "is_anonymous": flower.is_anonymous,
            "gift_name": flower.gift_name,
            "gift_icon": flower.gift_icon,
            "gift_rarity": flower.gift_rarity,
            "quantity": flower.quantity,
            "message": flower.message,
            "sent_at": flower.created_at.isoformat() if flower.created_at else None,
        })

    return result


def get_post_mentions(
    db: Session,
    post_id: int,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict]:
    mentions = db.query(PlazaMention).filter(
        PlazaMention.post_id == post_id,
    ).order_by(desc(PlazaMention.created_at)).offset(offset).limit(limit).all()
    
    if not mentions:
        return []
    
    inviter_ids = list(set(m.inviter_id for m in mentions))
    invitee_ids = list(set(m.invitee_id for m in mentions))
    all_user_ids = list(set(inviter_ids + invitee_ids))
    
    user_map = get_user_map(db, all_user_ids)

    result = []
    for mention in mentions:
        inviter = user_map.get(mention.inviter_id)
        invitee = user_map.get(mention.invitee_id)
        result.append({
            "id": mention.id,
            "inviter_id": mention.inviter_id,
            "inviter_name": inviter.username if inviter else None,
            "invitee_id": mention.invitee_id,
            "invitee_name": invitee.username if invitee else None,
            "invitation_type": mention.invitation_type,
            "message": mention.message,
            "is_accepted": mention.is_accepted,
            "accepted_at": mention.accepted_at.isoformat() if mention.accepted_at else None,
            "declined_at": mention.declined_at.isoformat() if mention.declined_at else None,
            "decline_reason": mention.decline_reason,
            "created_at": mention.created_at.isoformat() if mention.created_at else None,
        })

    return result


def record_share(
    db: Session,
    user_id: int,
    post_id: Optional[int],
    share_platform: Optional[str],
    share_type: str = "external",
    share_url: Optional[str] = None,
    share_text: Optional[str] = None,
) -> Optional[PlazaUserShareRecord]:
    try:
        share = PlazaUserShareRecord(
            user_id=user_id,
            post_id=post_id,
            share_platform=share_platform,
            share_type=share_type,
            share_url=share_url,
            share_text=share_text,
        )
        db.add(share)
        db.commit()
        db.refresh(share)
        return share
    except Exception as e:
        logger.error(f"记录分享失败: {e}")
        db.rollback()
        return None


def get_user_vip_map(db: Session, user_ids: List[int]) -> Dict[int, Tuple[bool, Optional[UserVIP]]]:
    if not user_ids:
        return {}
    
    result = {}
    user_vips = db.query(UserVIP).filter(UserVIP.user_id.in_(user_ids)).all()
    
    vip_map = {uv.user_id: uv for uv in user_vips}
    now = get_utc_now()
    
    for user_id in user_ids:
        user_vip = vip_map.get(user_id)
        if user_vip and user_vip.is_vip:
            if user_vip.expires_at and user_vip.expires_at <= now:
                result[user_id] = (False, None)
            else:
                result[user_id] = (True, user_vip)
        else:
            result[user_id] = (False, None)
    
    return result


def build_post_responses(
    db: Session,
    posts: List[PlazaPost],
    current_user_id: Optional[int] = None,
) -> List[Dict]:
    if not posts:
        return []
    
    user_ids = list(set(post.user_id for post in posts))
    
    user_map = get_user_map(db, user_ids)
    vip_map = get_user_vip_map(db, user_ids)
    
    liked_map = {}
    if current_user_id:
        post_ids = [post.id for post in posts]
        likes = db.query(PlazaLike).filter(
            PlazaLike.post_id.in_(post_ids),
            PlazaLike.user_id == current_user_id,
            PlazaLike.is_active == True,
        ).all()
        liked_map = {like.post_id: True for like in likes}

    post_type_labels = {
        PlazaPostType.SYNASTRY_CARD.value: "合盘卡牌",
        PlazaPostType.DAILY_HOROSCOPE.value: "今日运势",
        PlazaPostType.PAST_LIFE_STORY.value: "前世今生",
        PlazaPostType.CARD_DRAW.value: "星盘抽卡",
    }

    result = []
    for post in posts:
        user = user_map.get(post.user_id)
        is_vip, _ = vip_map.get(post.user_id, (False, None))
        
        image_urls = None
        if post.image_urls:
            try:
                image_urls = json.loads(post.image_urls)
            except:
                image_urls = [post.image_urls]

        related_data = None
        if post.related_data:
            try:
                related_data = json.loads(post.related_data)
            except:
                related_data = {}

        result.append({
            "id": post.id,
            "user_id": post.user_id,
            "username": user.username if user else None,
            "post_type": post.post_type,
            "post_type_label": post_type_labels.get(post.post_type, post.post_type),
            "title": post.title,
            "content": post.content,
            "image_urls": image_urls,
            "related_data": related_data,
            "like_count": post.like_count,
            "flower_count": post.flower_count,
            "mention_count": post.mention_count,
            "is_liked": liked_map.get(post.id, False),
            "is_vip": is_vip or post.is_vip,
            "vip_border_style": post.vip_border_style,
            "status": post.status,
            "created_at": post.created_at.isoformat() if post.created_at else None,
            "updated_at": post.updated_at.isoformat() if post.updated_at else None,
        })

    return result


def build_post_response(
    db: Session,
    post: PlazaPost,
    current_user_id: Optional[int] = None,
) -> Dict:
    results = build_post_responses(db, [post], current_user_id)
    return results[0] if results else {}
