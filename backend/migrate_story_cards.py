"""
数据库迁移脚本 - story_cards 表
使用 SQLAlchemy 实现，支持多数据库兼容
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine, text, inspect, MetaData, Table, Column
from sqlalchemy import Integer, String, Text, Boolean, DateTime, ForeignKey, Index
from app.config import settings
from app.database import Base


def get_engine():
    return create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})


def enable_foreign_keys(engine):
    if 'sqlite' in settings.DATABASE_URL:
        with engine.connect() as conn:
            conn.execute(text("PRAGMA foreign_keys = ON"))
            conn.commit()
        print("✓ 已启用外键约束")


def check_table_exists(engine, table_name):
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def get_table_columns(engine, table_name):
    inspector = inspect(engine)
    columns = inspector.get_columns(table_name)
    return {col['name']: col for col in columns}


def get_table_indexes(engine, table_name):
    inspector = inspect(engine)
    indexes = inspector.get_indexes(table_name)
    return {idx['name']: idx for idx in indexes}


def create_story_cards_table(engine):
    if check_table_exists(engine, 'story_cards'):
        print("✓ story_cards 表已存在")
        return False
    
    print("创建 story_cards 表...")
    
    from app.models.chart import StoryCard
    
    metadata = MetaData()
    story_cards_table = Table(
        'story_cards', metadata,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('user_id', Integer, ForeignKey('users.id'), nullable=False, index=True),
        Column('synastry_record_id', Integer, ForeignKey('synastry_records.id'), nullable=True, index=True),
        Column('past_life_synastry_id', Integer, nullable=True, index=True),
        Column('card_template', String(50), nullable=False, default='soulmate_knight'),
        Column('template_name', String(100), nullable=True),
        Column('person_a_name', String(100), nullable=True),
        Column('person_b_name', String(100), nullable=True),
        Column('target_user_id', Integer, ForeignKey('users.id'), nullable=True, index=True),
        Column('headline', String(200), nullable=False),
        Column('subheadline', String(300), nullable=True),
        Column('story_content', Text, nullable=False),
        Column('story_short', String(500), nullable=True),
        Column('compatibility_score', Integer, nullable=True),
        Column('match_type', String(50), nullable=True),
        Column('dominant_element', String(20), nullable=True),
        Column('key_aspect', String(200), nullable=True),
        Column('rarity', String(20), default='common', index=True),
        Column('rarity_name', String(50), nullable=True),
        Column('is_mounted', Boolean, default=False, index=True),
        Column('mounted_at', DateTime, nullable=True),
        Column('is_public', Boolean, default=False, index=True),
        Column('share_code', String(20), unique=True, nullable=True, index=True),
        Column('share_count', Integer, default=0),
        Column('card_metadata', Text, nullable=True),
        Column('is_deleted', Boolean, default=False, index=True),
        Column('created_at', DateTime, index=True),
        Column('updated_at', DateTime),
        extend_existing=True
    )
    
    metadata.create_all(engine, tables=[story_cards_table])
    print("✓ story_cards 表创建成功")
    return True


def upgrade_story_cards_table(engine):
    if not check_table_exists(engine, 'story_cards'):
        print("story_cards 表不存在，跳过升级")
        return
    
    existing_columns = get_table_columns(engine, 'story_cards')
    existing_indexes = get_table_indexes(engine, 'story_cards')
    
    print(f"现有列数: {len(existing_columns)}")
    print(f"现有索引数: {len(existing_indexes)}")
    
    columns_to_add = [
        ('past_life_synastry_id', 'INTEGER'),
        ('template_name', 'VARCHAR(100)'),
        ('target_user_id', 'INTEGER'),
        ('subheadline', 'VARCHAR(300)'),
        ('story_short', 'VARCHAR(500)'),
        ('compatibility_score', 'INTEGER'),
        ('match_type', 'VARCHAR(50)'),
        ('dominant_element', 'VARCHAR(20)'),
        ('key_aspect', 'VARCHAR(200)'),
        ('rarity_name', 'VARCHAR(50)'),
        ('is_mounted', 'INTEGER DEFAULT 0'),
        ('mounted_at', 'DATETIME'),
        ('is_public', 'INTEGER DEFAULT 0'),
        ('share_code', 'VARCHAR(20)'),
        ('share_count', 'INTEGER DEFAULT 0'),
        ('card_metadata', 'TEXT'),
        ('is_deleted', 'INTEGER DEFAULT 0'),
    ]
    
    with engine.connect() as conn:
        for col_name, col_type in columns_to_add:
            if col_name not in existing_columns:
                try:
                    alter_sql = f"ALTER TABLE story_cards ADD COLUMN {col_name} {col_type}"
                    conn.execute(text(alter_sql))
                    conn.commit()
                    print(f"  ✓ 添加列: {col_name}")
                except Exception as e:
                    if 'duplicate' not in str(e).lower():
                        print(f"  ⚠ 无法添加列 {col_name}: {e}")
        
        indexes_to_ensure = [
            ('idx_story_cards_user_id', 'CREATE INDEX IF NOT EXISTS idx_story_cards_user_id ON story_cards (user_id)'),
            ('idx_story_cards_synastry_record_id', 'CREATE INDEX IF NOT EXISTS idx_story_cards_synastry_record_id ON story_cards (synastry_record_id)'),
            ('idx_story_cards_is_mounted', 'CREATE INDEX IF NOT EXISTS idx_story_cards_is_mounted ON story_cards (is_mounted)'),
            ('idx_story_cards_rarity', 'CREATE INDEX IF NOT EXISTS idx_story_cards_rarity ON story_cards (rarity)'),
            ('idx_story_cards_is_deleted', 'CREATE INDEX IF NOT EXISTS idx_story_cards_is_deleted ON story_cards (is_deleted)'),
        ]
        
        for idx_name, idx_sql in indexes_to_ensure:
            if idx_name not in existing_indexes:
                try:
                    conn.execute(text(idx_sql))
                    conn.commit()
                    print(f"  ✓ 添加索引: {idx_name}")
                except Exception as e:
                    print(f"  ⚠ 无法添加索引 {idx_name}: {e}")
        
        share_code_idx_name = 'idx_story_cards_share_code'
        if share_code_idx_name not in existing_indexes:
            try:
                if 'sqlite' in settings.DATABASE_URL:
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_story_cards_share_code ON story_cards (share_code)"))
                else:
                    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_story_cards_share_code ON story_cards (share_code) WHERE share_code IS NOT NULL"))
                conn.commit()
                print(f"  ✓ 添加索引: {share_code_idx_name}")
            except Exception as e:
                print(f"  ⚠ 无法添加索引 {share_code_idx_name}: {e}")


def check_related_tables(engine):
    required_tables = ['users', 'synastry_records']
    optional_tables = ['past_life_synastry_records']
    
    print("\n检查关联表...")
    all_ok = True
    
    for table in required_tables:
        if check_table_exists(engine, table):
            print(f"  ✓ {table} 表存在")
        else:
            print(f"  ✗ {table} 表不存在")
            all_ok = False
    
    for table in optional_tables:
        if check_table_exists(engine, table):
            print(f"  ✓ {table} 表存在")
        else:
            print(f"  ⚠ {table} 表不存在 (可选)")
    
    return all_ok


def main():
    print("=" * 60)
    print("数据库迁移脚本 - story_cards 表 (SQLAlchemy版)")
    print("=" * 60)
    print(f"数据库URL: {settings.DATABASE_URL}")
    print()
    
    engine = get_engine()
    
    print("1. 启用外键约束...")
    enable_foreign_keys(engine)
    
    print("\n2. 检查关联表...")
    check_related_tables(engine)
    
    print("\n3. 创建 story_cards 表...")
    table_created = create_story_cards_table(engine)
    
    if not table_created:
        print("\n4. 升级 story_cards 表结构...")
        upgrade_story_cards_table(engine)
    
    print("\n" + "=" * 60)
    print("迁移完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
