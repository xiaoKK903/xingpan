"""创建故事卡测试数据"""
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models import User, StoryCard, SynastryRecord
from app.services.past_life.story_card_service import generate_share_code

engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_test_data():
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("创建故事卡测试数据")
        print("=" * 60)
        
        test_user = db.query(User).filter(User.username == 'test').first()
        if not test_user:
            print("✗ 未找到 test 用户，请先创建用户")
            return
        
        print(f"✓ 找到测试用户: {test_user.username} (ID: {test_user.id})")
        
        test_cards = [
            {
                "card_template": "soulmate_knight",
                "template_name": "前世并肩骑士",
                "person_a_name": "test",
                "person_b_name": "Alice",
                "headline": "前世并肩作战的骑士",
                "subheadline": "曾在中世纪的战场上并肩作战",
                "story_content": "在遥远的中世纪，你们是并肩作战的骑士兄弟。在那片洒满热血的战场上，你们曾立下誓言，要守护彼此直到最后一刻。\n\n那场决定王国命运的战役中，你为了保护他而身受重伤，而他抱着奄奄一息的你，在夕阳下发誓：\"来世，我们还会相遇。\"",
                "story_short": "前世是并肩作战的骑士兄弟，在战场上结下深厚的友谊。",
                "compatibility_score": 85,
                "match_type": "前世羁绊",
                "dominant_element": "火",
                "key_aspect": "太阳三合火星",
                "rarity": "epic",
                "rarity_name": "史诗",
                "is_mounted": True,
                "is_public": True,
            },
            {
                "card_template": "confidant",
                "template_name": "知己挚友",
                "person_a_name": "test",
                "person_b_name": "Bob",
                "headline": "跨越时空的知己",
                "subheadline": "心灵相通，无需言语",
                "story_content": "你们是那种无需言语就能理解彼此的知己。在文艺复兴时期的佛罗伦萨，你们曾是艺术学院的同窗，一起探讨哲学、绘画、诗歌。\n\n当他因病离世时，你在日记中写道：\"真正的友谊不会因死亡而终结，它只是换了一种形式继续存在。\"",
                "story_short": "文艺复兴时期的艺术同窗，心灵相通的知己。",
                "compatibility_score": 92,
                "match_type": "心灵共鸣",
                "dominant_element": "风",
                "key_aspect": "水星拱月亮",
                "rarity": "rare",
                "rarity_name": "稀有",
                "is_mounted": True,
                "is_public": True,
            },
            {
                "card_template": "familiar_strangers",
                "template_name": "似曾相识",
                "person_a_name": "test",
                "person_b_name": "Carol",
                "headline": "似曾相识的陌生人",
                "subheadline": "初次见面却感觉早已认识",
                "story_content": "第一次见面时，你们都有一种奇妙的感觉——好像在哪里见过彼此。\n\n实际上，在1920年代的巴黎，你们曾是街头咖啡馆的常客。他是一位画家，而你是一位诗人。你们从未交谈过，但每天都会在同一时间出现在同一角落，用眼神交换无言的问候。",
                "story_short": "1920年代巴黎咖啡馆的神秘邂逅，眼神交换无言的问候。",
                "compatibility_score": 68,
                "match_type": "神秘缘分",
                "dominant_element": "水",
                "key_aspect": "金星六合海王星",
                "rarity": "common",
                "rarity_name": "普通",
                "is_mounted": False,
                "is_public": False,
            },
            {
                "card_template": "twin_flame",
                "template_name": "灵魂双生火焰",
                "person_a_name": "test",
                "person_b_name": "Diana",
                "headline": "灵魂双生火焰",
                "subheadline": "一个灵魂分裂成两半",
                "story_content": "传说中，有些灵魂在诞生时被分成两半，各自投入轮回。你们就是这样的双生火焰。\n\n无论转世多少次，你们总会在某个时刻相遇。古埃及时，你们是法老和王后；唐朝时，你们是诗人和歌妓；而这一世，你们终于在最合适的时机重逢。\n\n双生火焰的相遇不是偶然，而是灵魂永恒的约定。",
                "story_short": "传说中的灵魂双生火焰，历经多世轮回终于重逢。",
                "compatibility_score": 98,
                "match_type": "灵魂约定",
                "dominant_element": "水",
                "key_aspect": "月亮合相冥王星",
                "rarity": "legendary",
                "rarity_name": "传说",
                "is_mounted": True,
                "is_public": True,
            }
        ]
        
        existing_cards = db.query(StoryCard).filter(
            StoryCard.user_id == test_user.id,
            StoryCard.is_deleted == False
        ).count()
        
        if existing_cards > 0:
            print(f"⚠  用户已有 {existing_cards} 张卡片，跳过创建测试数据")
            db.close()
            return
        
        print("\n创建测试卡片...")
        for i, card_data in enumerate(test_cards):
            card = StoryCard(
                user_id=test_user.id,
                card_template=card_data["card_template"],
                template_name=card_data["template_name"],
                person_a_name=card_data["person_a_name"],
                person_b_name=card_data["person_b_name"],
                headline=card_data["headline"],
                subheadline=card_data["subheadline"],
                story_content=card_data["story_content"],
                story_short=card_data["story_short"],
                compatibility_score=card_data["compatibility_score"],
                match_type=card_data["match_type"],
                dominant_element=card_data["dominant_element"],
                key_aspect=card_data["key_aspect"],
                rarity=card_data["rarity"],
                rarity_name=card_data["rarity_name"],
                is_mounted=card_data["is_mounted"],
                mounted_at=datetime.utcnow() if card_data["is_mounted"] else None,
                is_public=card_data["is_public"],
                share_code=generate_share_code(),
                share_count=0,
                card_metadata=None,
                is_deleted=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(card)
            print(f"  ✓ 创建卡片 #{i+1}: {card_data['headline']} ({card_data['rarity_name']})")
        
        db.commit()
        print(f"\n✓ 成功创建 {len(test_cards)} 张测试卡片")
        
        mounted_count = db.query(StoryCard).filter(
            StoryCard.user_id == test_user.id,
            StoryCard.is_mounted == True,
            StoryCard.is_deleted == False
        ).count()
        
        total_count = db.query(StoryCard).filter(
            StoryCard.user_id == test_user.id,
            StoryCard.is_deleted == False
        ).count()
        
        print(f"  - 已挂载: {mounted_count} 张")
        print(f"  - 总计: {total_count} 张")
        
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()
    
    print("\n" + "=" * 60)
    print("测试数据创建完成！")
    print("=" * 60)


if __name__ == "__main__":
    create_test_data()
