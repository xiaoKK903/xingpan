import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
import json

from app.models import (
    User, PlazaPost, PlazaLike, PlazaFlowerGift,
    TopicChallenge, TopicParticipation, TopicRewardClaim,
    TopicChallengeStatus, RewardType,
    PlazaPostStatus, UserVIP, StarDustTransaction
)
from app.services.social_plaza_service import get_user_map, get_user_vip_map, check_user_liked

logger = logging.getLogger(__name__)


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


def create_topic_challenge(
    db: Session,
    title: str,
    topic_tag: str,
    start_time: datetime,
    end_time: datetime,
    description: Optional[str] = None,
    banner_image_url: Optional[str] = None,
    cover_image_url: Optional[str] = None,
    reward_config: Optional[Dict] = None,
    max_participants: Optional[int] = None,
    is_featured: bool = False,
    sort_order: int = 0,
    created_by: Optional[int] = None,
) -> Tuple[Optional[TopicChallenge], Optional[str]]:
    try:
        if start_time >= end_time:
            return None, "开始时间必须早于结束时间"

        existing = db.query(TopicChallenge).filter(
            TopicChallenge.topic_tag == topic_tag,
            TopicChallenge.status != TopicChallengeStatus.ARCHIVED.value
        ).first()
        if existing:
            return None, f"话题标签 '{topic_tag}' 已存在"

        now = get_utc_now()
        status = TopicChallengeStatus.DRAFT.value
        if start_time <= now <= end_time:
            status = TopicChallengeStatus.ACTIVE.value
        elif now > end_time:
            status = TopicChallengeStatus.ENDED.value

        topic = TopicChallenge(
            title=title,
            description=description,
            topic_tag=topic_tag,
            banner_image_url=banner_image_url,
            cover_image_url=cover_image_url,
            start_time=start_time,
            end_time=end_time,
            status=status,
            sort_order=sort_order,
            max_participants=max_participants,
            participant_count=0,
            reward_config=json.dumps(reward_config, ensure_ascii=False) if reward_config else None,
            is_featured=is_featured,
            created_by=created_by,
        )

        db.add(topic)
        db.commit()
        db.refresh(topic)

        return topic, None

    except Exception as e:
        logger.error(f"创建话题挑战失败: {e}")
        db.rollback()
        return None, str(e)


def update_topic_challenge(
    db: Session,
    topic_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    topic_tag: Optional[str] = None,
    banner_image_url: Optional[str] = None,
    cover_image_url: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    status: Optional[str] = None,
    reward_config: Optional[Dict] = None,
    max_participants: Optional[int] = None,
    is_featured: Optional[bool] = None,
    sort_order: Optional[int] = None,
) -> Tuple[Optional[TopicChallenge], Optional[str]]:
    try:
        topic = db.query(TopicChallenge).filter(TopicChallenge.id == topic_id).first()
        if not topic:
            return None, "话题不存在"

        if title is not None:
            topic.title = title
        if description is not None:
            topic.description = description
        if banner_image_url is not None:
            topic.banner_image_url = banner_image_url
        if cover_image_url is not None:
            topic.cover_image_url = cover_image_url
        if max_participants is not None:
            topic.max_participants = max_participants
        if is_featured is not None:
            topic.is_featured = is_featured
        if sort_order is not None:
            topic.sort_order = sort_order
        if reward_config is not None:
            topic.reward_config = json.dumps(reward_config, ensure_ascii=False)

        if topic_tag is not None and topic_tag != topic.topic_tag:
            existing = db.query(TopicChallenge).filter(
                TopicChallenge.topic_tag == topic_tag,
                TopicChallenge.id != topic_id,
                TopicChallenge.status != TopicChallengeStatus.ARCHIVED.value
            ).first()
            if existing:
                return None, f"话题标签 '{topic_tag}' 已存在"
            topic.topic_tag = topic_tag

        if start_time is not None or end_time is not None:
            new_start = start_time if start_time is not None else topic.start_time
            new_end = end_time if end_time is not None else topic.end_time
            if new_start >= new_end:
                return None, "开始时间必须早于结束时间"
            if start_time is not None:
                topic.start_time = start_time
            if end_time is not None:
                topic.end_time = end_time

        if status is not None:
            if status not in [s.value for s in TopicChallengeStatus]:
                return None, f"无效的状态值: {status}"
            topic.status = status
        else:
            now = get_utc_now()
            if topic.start_time <= now <= topic.end_time:
                topic.status = TopicChallengeStatus.ACTIVE.value
            elif now > topic.end_time:
                topic.status = TopicChallengeStatus.ENDED.value

        topic.updated_at = get_utc_now()
        db.commit()
        db.refresh(topic)

        return topic, None

    except Exception as e:
        logger.error(f"更新话题挑战失败: {e}")
        db.rollback()
        return None, str(e)


def get_topic_challenge_by_id(db: Session, topic_id: int) -> Optional[TopicChallenge]:
    return db.query(TopicChallenge).filter(TopicChallenge.id == topic_id).first()


def get_topic_challenge_by_tag(db: Session, topic_tag: str) -> Optional[TopicChallenge]:
    return db.query(TopicChallenge).filter(
        TopicChallenge.topic_tag == topic_tag,
        TopicChallenge.status != TopicChallengeStatus.ARCHIVED.value
    ).first()


def get_active_topic_challenge(db: Session) -> Optional[TopicChallenge]:
    now = get_utc_now()
    return db.query(TopicChallenge).filter(
        TopicChallenge.status == TopicChallengeStatus.ACTIVE.value,
        TopicChallenge.start_time <= now,
        TopicChallenge.end_time >= now
    ).order_by(
        desc(TopicChallenge.is_featured),
        asc(TopicChallenge.sort_order),
        desc(TopicChallenge.created_at)
    ).first()


def get_topic_challenge_list(
    db: Session,
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> Tuple[List[TopicChallenge], int]:
    query = db.query(TopicChallenge)

    if status:
        query = query.filter(TopicChallenge.status == status)

    total_count = query.count()

    topics = query.order_by(
        desc(TopicChallenge.is_featured),
        asc(TopicChallenge.sort_order),
        desc(TopicChallenge.created_at)
    ).offset(offset).limit(limit).all()

    return topics, total_count


def participate_in_topic(
    db: Session,
    topic_id: int,
    post_id: int,
    user_id: int,
) -> Tuple[Optional[TopicParticipation], Optional[str]]:
    try:
        topic = db.query(TopicChallenge).filter(TopicChallenge.id == topic_id).first()
        if not topic:
            return None, "话题不存在"

        now = get_utc_now()
        if topic.status != TopicChallengeStatus.ACTIVE.value:
            return None, "话题未激活"
        if now < topic.start_time or now > topic.end_time:
            return None, "话题不在活动时间内"

        if topic.max_participants and topic.participant_count >= topic.max_participants:
            return None, "话题参与人数已达上限"

        existing = db.query(TopicParticipation).filter(
            TopicParticipation.topic_id == topic_id,
            TopicParticipation.post_id == post_id
        ).first()
        if existing:
            return None, "该帖子已参与此话题"

        user_existing = db.query(TopicParticipation).filter(
            TopicParticipation.topic_id == topic_id,
            TopicParticipation.user_id == user_id
        ).first()
        if user_existing:
            return None, "您已参与过此话题"

        post = db.query(PlazaPost).filter(
            PlazaPost.id == post_id,
            PlazaPost.user_id == user_id,
            PlazaPost.status == PlazaPostStatus.PUBLISHED.value
        ).first()
        if not post:
            return None, "帖子不存在或无权操作"

        hot_score = post.like_count + post.flower_count

        participation = TopicParticipation(
            topic_id=topic_id,
            post_id=post_id,
            user_id=user_id,
            hot_score=hot_score,
            participated_at=get_utc_now(),
        )

        db.add(participation)
        db.query(TopicChallenge).filter(TopicChallenge.id == topic_id).update(
            {TopicChallenge.participant_count: TopicChallenge.participant_count + 1},
            synchronize_session=False
        )

        db.commit()
        db.refresh(participation)

        return participation, None

    except Exception as e:
        logger.error(f"参与话题失败: {e}")
        db.rollback()
        return None, str(e)


def update_participation_hot_score(
    db: Session,
    participation_id: int,
) -> Optional[TopicParticipation]:
    try:
        participation = db.query(TopicParticipation).filter(
            TopicParticipation.id == participation_id
        ).first()
        if not participation:
            return None

        post = db.query(PlazaPost).filter(PlazaPost.id == participation.post_id).first()
        if post:
            participation.hot_score = post.like_count + post.flower_count
            db.commit()
            db.refresh(participation)

        return participation

    except Exception as e:
        logger.error(f"更新参与热度失败: {e}")
        db.rollback()
        return None


def get_topic_leaderboard(
    db: Session,
    topic_id: int,
    limit: int = 100,
    offset: int = 0,
) -> Tuple[List[Dict], int]:
    participations = db.query(TopicParticipation).filter(
        TopicParticipation.topic_id == topic_id
    ).order_by(
        desc(TopicParticipation.hot_score),
        asc(TopicParticipation.participated_at)
    ).all()

    rank_map = {}
    for idx, p in enumerate(participations):
        rank_map[p.id] = idx + 1

    query = db.query(TopicParticipation).filter(
        TopicParticipation.topic_id == topic_id
    ).order_by(
        desc(TopicParticipation.hot_score),
        asc(TopicParticipation.participated_at)
    )

    total_count = query.count()
    paginated = query.offset(offset).limit(limit).all()

    post_ids = [p.post_id for p in paginated]
    user_ids = [p.user_id for p in paginated]

    posts = db.query(PlazaPost).filter(PlazaPost.id.in_(post_ids)).all()
    post_map = {p.id: p for p in posts}

    user_map = get_user_map(db, user_ids)
    vip_map = get_user_vip_map(db, user_ids)

    result = []
    for participation in paginated:
        post = post_map.get(participation.post_id)
        user = user_map.get(participation.user_id)
        is_vip, _ = vip_map.get(participation.user_id, (False, None))

        image_urls = None
        if post and post.image_urls:
            try:
                image_urls = json.loads(post.image_urls)
            except:
                image_urls = [post.image_urls]

        result.append({
            "rank": rank_map.get(participation.id, 0),
            "user_id": participation.user_id,
            "username": user.username if user else None,
            "is_vip": is_vip,
            "post_id": participation.post_id,
            "post_title": post.title if post else None,
            "post_content": post.content if post else None,
            "post_image_urls": image_urls,
            "hot_score": participation.hot_score,
            "reward_claimed": participation.reward_claimed,
            "final_rank": participation.final_rank,
            "participated_at": participation.participated_at.isoformat() if participation.participated_at else None,
        })

    return result, total_count


def get_topic_posts(
    db: Session,
    topic_id: int,
    sort_by: str = "latest",
    limit: int = 20,
    offset: int = 0,
    current_user_id: Optional[int] = None,
) -> Tuple[List[Dict], int]:
    query = db.query(TopicParticipation, PlazaPost).join(
        PlazaPost, TopicParticipation.post_id == PlazaPost.id
    ).filter(
        TopicParticipation.topic_id == topic_id,
        PlazaPost.status == PlazaPostStatus.PUBLISHED.value
    )

    total_count = query.count()

    if sort_by == "hot":
        query = query.order_by(
            desc(TopicParticipation.hot_score),
            desc(PlazaPost.created_at)
        )
    else:
        query = query.order_by(desc(TopicParticipation.participated_at))

    results = query.offset(offset).limit(limit).all()

    if not results:
        return [], total_count

    participations = [r[0] for r in results]
    posts = [r[1] for r in results]

    user_ids = list(set(p.user_id for p in posts))
    user_map = get_user_map(db, user_ids)
    vip_map = get_user_vip_map(db, user_ids)

    liked_map = {}
    if current_user_id:
        post_ids = [p.id for p in posts]
        likes = db.query(PlazaLike).filter(
            PlazaLike.post_id.in_(post_ids),
            PlazaLike.user_id == current_user_id,
            PlazaLike.is_active == True,
        ).all()
        liked_map = {like.post_id: True for like in likes}

    result = []
    for participation, post in zip(participations, posts):
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
            "topic_id": topic_id,
            "hot_score": participation.hot_score,
            "participated_at": participation.participated_at.isoformat() if participation.participated_at else None,
            "created_at": post.created_at.isoformat() if post.created_at else None,
            "updated_at": post.updated_at.isoformat() if post.updated_at else None,
        })

    return result, total_count


def settle_topic_rewards(
    db: Session,
    topic_id: int,
) -> Tuple[int, Optional[str]]:
    try:
        topic = db.query(TopicChallenge).filter(TopicChallenge.id == topic_id).first()
        if not topic:
            return 0, "话题不存在"

        now = get_utc_now()
        if now < topic.end_time:
            return 0, "话题未结束，无法结算"

        sample_participation = db.query(TopicParticipation).filter(
            TopicParticipation.topic_id == topic_id,
            TopicParticipation.final_rank.isnot(None)
        ).first()
        if sample_participation:
            total_participations = db.query(TopicParticipation).filter(
                TopicParticipation.topic_id == topic_id
            ).count()
            logger.info(f"话题 {topic_id} 已结算，返回已结算数量 {total_participations}")
            return total_participations, None

        participations = db.query(TopicParticipation).filter(
            TopicParticipation.topic_id == topic_id
        ).order_by(
            desc(TopicParticipation.hot_score),
            asc(TopicParticipation.participated_at)
        ).all()

        if not participations:
            return 0, "没有参与记录"

        reward_config = None
        if topic.reward_config:
            try:
                reward_config = json.loads(topic.reward_config)
            except:
                reward_config = None

        if not reward_config:
            reward_config = {
                "rewards": [
                    {"rank_from": 1, "rank_to": 3, "type": "blind_box_ticket", "amount": 3, "description": "盲盒券 x3"},
                    {"rank_from": 4, "rank_to": 10, "type": "blind_box_ticket", "amount": 1, "description": "盲盒券 x1"},
                ]
            }

        rewards = reward_config.get("rewards", [])

        settled_count = 0
        for idx, participation in enumerate(participations):
            if participation.final_rank is not None:
                settled_count += 1
                continue

            rank = idx + 1
            participation.final_rank = rank

            for reward_rule in rewards:
                rank_from = reward_rule.get("rank_from", 0)
                rank_to = reward_rule.get("rank_to", 0)
                if rank_from <= rank <= rank_to:
                    participation.reward_type = reward_rule.get("type")
                    participation.reward_amount = reward_rule.get("amount", 0)
                    break

            settled_count += 1

        topic.status = TopicChallengeStatus.ENDED.value
        db.commit()

        return settled_count, None

    except Exception as e:
        logger.error(f"结算话题奖励失败: {e}")
        db.rollback()
        return 0, str(e)


def claim_topic_reward(
    db: Session,
    topic_id: int,
    user_id: int,
) -> Tuple[Optional[Dict], Optional[str]]:
    try:
        participation = db.query(TopicParticipation).filter(
            TopicParticipation.topic_id == topic_id,
            TopicParticipation.user_id == user_id
        ).with_for_update(skip_locked=False).first()

        if not participation:
            return None, "您未参与此话题"

        if participation.reward_claimed:
            return None, "您已领取过奖励"

        if not participation.final_rank:
            return None, "奖励尚未结算"

        if not participation.reward_type:
            return None, "您没有获得奖励"

        user = db.query(User).filter(
            User.id == user_id
        ).with_for_update(skip_locked=False).first()
        if not user:
            return None, "用户不存在"

        reward_type = participation.reward_type
        reward_amount = participation.reward_amount or 0

        transaction_id = None
        vip_subscription_id = None

        if reward_type == RewardType.BLIND_BOX_TICKET.value:
            current_tickets = user.blind_box_tickets or 0
            user.blind_box_tickets = current_tickets + reward_amount
            reward_description = f"盲盒券 x{reward_amount}"

        elif reward_type == RewardType.STARDUST_FRAGMENT.value:
            current_balance = user.stardust_fragment_balance or 0
            new_balance = current_balance + reward_amount
            user.stardust_fragment_balance = new_balance
            transaction = StarDustTransaction(
                user_id=user_id,
                transaction_type="topic_reward",
                currency_type="fragment",
                amount=reward_amount,
                balance_before=current_balance,
                balance_after=new_balance,
                description=f"话题挑战奖励：星尘碎片 x{reward_amount}",
            )
            db.add(transaction)
            db.flush()
            transaction_id = transaction.id
            reward_description = f"星尘碎片 x{reward_amount}"

        elif reward_type == RewardType.STARDUST_POINT.value:
            current_balance = user.stardust_point_balance or 0
            new_balance = current_balance + reward_amount
            user.stardust_point_balance = new_balance
            transaction = StarDustTransaction(
                user_id=user_id,
                transaction_type="topic_reward",
                currency_type="point",
                amount=reward_amount,
                balance_before=current_balance,
                balance_after=new_balance,
                description=f"话题挑战奖励：星尘点数 x{reward_amount}",
            )
            db.add(transaction)
            db.flush()
            transaction_id = transaction.id
            reward_description = f"星尘点数 x{reward_amount}"

        else:
            return None, f"不支持的奖励类型: {reward_type}"

        participation.reward_claimed = True
        participation.reward_claimed_at = get_utc_now()

        claim = TopicRewardClaim(
            topic_id=topic_id,
            participation_id=participation.id,
            user_id=user_id,
            rank=participation.final_rank,
            reward_type=reward_type,
            reward_amount=reward_amount,
            reward_description=reward_description,
            transaction_id=transaction_id,
            vip_subscription_id=vip_subscription_id,
            claimed_at=get_utc_now(),
        )
        db.add(claim)

        db.commit()

        result = {
            "rank": participation.final_rank,
            "reward_type": reward_type,
            "reward_amount": reward_amount,
            "reward_description": reward_description,
            "claimed_at": claim.claimed_at.isoformat() if claim.claimed_at else None,
        }

        return result, None

    except Exception as e:
        logger.error(f"领取话题奖励失败: {e}")
        db.rollback()
        return None, str(e)


def build_topic_response(
    topic: TopicChallenge,
    include_participation: bool = False,
    current_user_id: Optional[int] = None,
    db: Optional[Session] = None,
) -> Dict:
    reward_config = None
    if topic.reward_config:
        try:
            reward_config = json.loads(topic.reward_config)
        except:
            reward_config = None

    user_participation = None
    if include_participation and current_user_id and db:
        participation = db.query(TopicParticipation).filter(
            TopicParticipation.topic_id == topic.id,
            TopicParticipation.user_id == current_user_id
        ).first()
        if participation:
            user_participation = {
                "post_id": participation.post_id,
                "hot_score": participation.hot_score,
                "final_rank": participation.final_rank,
                "reward_claimed": participation.reward_claimed,
                "reward_type": participation.reward_type,
                "reward_amount": participation.reward_amount,
                "participated_at": participation.participated_at.isoformat() if participation.participated_at else None,
            }

    now = get_utc_now()
    time_status = "upcoming"
    if topic.start_time <= now <= topic.end_time:
        time_status = "active"
    elif now > topic.end_time:
        time_status = "ended"

    return {
        "id": topic.id,
        "title": topic.title,
        "description": topic.description,
        "topic_tag": topic.topic_tag,
        "banner_image_url": topic.banner_image_url,
        "cover_image_url": topic.cover_image_url,
        "start_time": topic.start_time.isoformat() if topic.start_time else None,
        "end_time": topic.end_time.isoformat() if topic.end_time else None,
        "status": topic.status,
        "time_status": time_status,
        "sort_order": topic.sort_order,
        "max_participants": topic.max_participants,
        "participant_count": topic.participant_count,
        "reward_config": reward_config,
        "is_featured": topic.is_featured,
        "created_by": topic.created_by,
        "user_participation": user_participation,
        "created_at": topic.created_at.isoformat() if topic.created_at else None,
        "updated_at": topic.updated_at.isoformat() if topic.updated_at else None,
    }
