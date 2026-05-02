"""
数据库迁移脚本 - 元素缺角寻宝系统
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "ai_customer_service.db"


def get_connection():
    return sqlite3.connect(str(DB_PATH))


def check_table_exists(cursor, table_name):
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name=?
    """, (table_name,))
    return cursor.fetchone() is not None


def get_table_columns(cursor, table_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cursor.fetchall()]


def create_user_element_profiles_table():
    """
    检查并创建 user_element_profiles 表（用户元素画像表）
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if not check_table_exists(cursor, "user_element_profiles"):
            print("创建 user_element_profiles 表...")
            cursor.execute("""
                CREATE TABLE user_element_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    chart_id INTEGER,
                    fire_score FLOAT DEFAULT 0.0,
                    earth_score FLOAT DEFAULT 0.0,
                    air_score FLOAT DEFAULT 0.0,
                    water_score FLOAT DEFAULT 0.0,
                    fire_level VARCHAR(20) DEFAULT 'balanced',
                    earth_level VARCHAR(20) DEFAULT 'balanced',
                    air_level VARCHAR(20) DEFAULT 'balanced',
                    water_level VARCHAR(20) DEFAULT 'balanced',
                    total_score FLOAT DEFAULT 0.0,
                    average_score FLOAT DEFAULT 25.0,
                    dominant_element VARCHAR(20),
                    secondary_dominant VARCHAR(20),
                    primary_deficiency VARCHAR(20),
                    has_deficiency BOOLEAN DEFAULT 0,
                    deficiency_count INTEGER DEFAULT 0,
                    element_data TEXT,
                    last_analyzed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (chart_id) REFERENCES charts (id),
                    UNIQUE (user_id)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX idx_user_element_profiles_user_id 
                ON user_element_profiles (user_id)
            """)
            cursor.execute("""
                CREATE INDEX idx_user_element_profiles_has_deficiency 
                ON user_element_profiles (has_deficiency)
            """)
            cursor.execute("""
                CREATE INDEX idx_user_element_profiles_dominant_element 
                ON user_element_profiles (dominant_element)
            """)
            cursor.execute("""
                CREATE INDEX idx_user_element_profiles_primary_deficiency 
                ON user_element_profiles (primary_deficiency)
            """)
            
            conn.commit()
            print("✓ user_element_profiles 表创建成功")
        else:
            print("✓ user_element_profiles 表已存在")
            
            cursor.execute("""
                SELECT sql FROM sqlite_master 
                WHERE type='table' AND name='user_element_profiles'
            """)
            result = cursor.fetchone()
            current_sql = result[0] if result else ""
            
            columns_needed = [
                ("fire_score", "FLOAT DEFAULT 0.0"),
                ("earth_score", "FLOAT DEFAULT 0.0"),
                ("air_score", "FLOAT DEFAULT 0.0"),
                ("water_score", "FLOAT DEFAULT 0.0"),
                ("fire_level", "VARCHAR(20) DEFAULT 'balanced'"),
                ("earth_level", "VARCHAR(20) DEFAULT 'balanced'"),
                ("air_level", "VARCHAR(20) DEFAULT 'balanced'"),
                ("water_level", "VARCHAR(20) DEFAULT 'balanced'"),
                ("total_score", "FLOAT DEFAULT 0.0"),
                ("average_score", "FLOAT DEFAULT 25.0"),
                ("dominant_element", "VARCHAR(20)"),
                ("secondary_dominant", "VARCHAR(20)"),
                ("primary_deficiency", "VARCHAR(20)"),
                ("has_deficiency", "BOOLEAN DEFAULT 0"),
                ("deficiency_count", "INTEGER DEFAULT 0"),
                ("element_data", "TEXT"),
                ("last_analyzed_at", "TIMESTAMP"),
            ]
            
            for col_name, col_def in columns_needed:
                if col_name not in current_sql:
                    try:
                        cursor.execute(f"ALTER TABLE user_element_profiles ADD COLUMN {col_name} {col_def}")
                        print(f"  ✓ 添加列: {col_name}")
                    except sqlite3.OperationalError as e:
                        print(f"  跳过列 {col_name}: {e}")
            
            conn.commit()
            
    except sqlite3.OperationalError as e:
        print(f"错误: {e}")
        conn.rollback()
    finally:
        conn.close()


def create_user_energy_tags_table():
    """
    检查并创建 user_energy_tags 表（用户能量标签表）
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if not check_table_exists(cursor, "user_energy_tags"):
            print("创建 user_energy_tags 表...")
            cursor.execute("""
                CREATE TABLE user_energy_tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    profile_id INTEGER,
                    tag_key VARCHAR(100) NOT NULL,
                    tag_name VARCHAR(100) NOT NULL,
                    tag_category VARCHAR(50) DEFAULT 'element',
                    tag_score FLOAT DEFAULT 1.0,
                    description VARCHAR(500),
                    source_type VARCHAR(50) DEFAULT 'analysis',
                    source_reference VARCHAR(200),
                    is_active BOOLEAN DEFAULT 1,
                    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    occurrence_count INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (profile_id) REFERENCES user_element_profiles (id)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX idx_user_energy_tags_user_id 
                ON user_energy_tags (user_id)
            """)
            cursor.execute("""
                CREATE INDEX idx_user_energy_tags_tag_key 
                ON user_energy_tags (tag_key)
            """)
            cursor.execute("""
                CREATE INDEX idx_user_energy_tags_tag_category 
                ON user_energy_tags (tag_category)
            """)
            cursor.execute("""
                CREATE INDEX idx_user_energy_tags_is_active 
                ON user_energy_tags (is_active)
            """)
            
            conn.commit()
            print("✓ user_energy_tags 表创建成功")
        else:
            print("✓ user_energy_tags 表已存在")
            
            cursor.execute("""
                SELECT sql FROM sqlite_master 
                WHERE type='table' AND name='user_energy_tags'
            """)
            result = cursor.fetchone()
            current_sql = result[0] if result else ""
            
            columns_needed = [
                ("tag_category", "VARCHAR(50) DEFAULT 'element'"),
                ("tag_score", "FLOAT DEFAULT 1.0"),
                ("description", "VARCHAR(500)"),
                ("source_type", "VARCHAR(50) DEFAULT 'analysis'"),
                ("source_reference", "VARCHAR(200)"),
                ("is_active", "BOOLEAN DEFAULT 1"),
                ("occurrence_count", "INTEGER DEFAULT 1"),
            ]
            
            for col_name, col_def in columns_needed:
                if col_name not in current_sql:
                    try:
                        cursor.execute(f"ALTER TABLE user_energy_tags ADD COLUMN {col_name} {col_def}")
                        print(f"  ✓ 添加列: {col_name}")
                    except sqlite3.OperationalError as e:
                        print(f"  跳过列 {col_name}: {e}")
            
            conn.commit()
            
    except sqlite3.OperationalError as e:
        print(f"错误: {e}")
        conn.rollback()
    finally:
        conn.close()


def create_blind_box_matches_table():
    """
    检查并创建 blind_box_matches 表（盲盒匹配记录表）
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if not check_table_exists(cursor, "blind_box_matches"):
            print("创建 blind_box_matches 表...")
            cursor.execute("""
                CREATE TABLE blind_box_matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    matched_user_id INTEGER NOT NULL,
                    blind_box_id VARCHAR(50) NOT NULL,
                    complement_score FLOAT DEFAULT 0.0,
                    match_type VARCHAR(20) DEFAULT 'partial',
                    clues_data TEXT,
                    complement_details TEXT,
                    completeness_data TEXT,
                    is_revealed BOOLEAN DEFAULT 0,
                    revealed_at TIMESTAMP,
                    is_claimed BOOLEAN DEFAULT 0,
                    claimed_at TIMESTAMP,
                    reward_earned INTEGER DEFAULT 0,
                    status VARCHAR(20) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (matched_user_id) REFERENCES users (id),
                    UNIQUE (blind_box_id)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX idx_blind_box_matches_user_id 
                ON blind_box_matches (user_id)
            """)
            cursor.execute("""
                CREATE INDEX idx_blind_box_matches_matched_user_id 
                ON blind_box_matches (matched_user_id)
            """)
            cursor.execute("""
                CREATE INDEX idx_blind_box_matches_blind_box_id 
                ON blind_box_matches (blind_box_id)
            """)
            cursor.execute("""
                CREATE INDEX idx_blind_box_matches_status 
                ON blind_box_matches (status)
            """)
            cursor.execute("""
                CREATE INDEX idx_blind_box_matches_is_revealed 
                ON blind_box_matches (is_revealed)
            """)
            cursor.execute("""
                CREATE INDEX idx_blind_box_matches_is_claimed 
                ON blind_box_matches (is_claimed)
            """)
            cursor.execute("""
                CREATE INDEX idx_blind_box_matches_created_at 
                ON blind_box_matches (created_at)
            """)
            
            conn.commit()
            print("✓ blind_box_matches 表创建成功")
        else:
            print("✓ blind_box_matches 表已存在")
            
            cursor.execute("""
                SELECT sql FROM sqlite_master 
                WHERE type='table' AND name='blind_box_matches'
            """)
            result = cursor.fetchone()
            current_sql = result[0] if result else ""
            
            columns_needed = [
                ("complement_score", "FLOAT DEFAULT 0.0"),
                ("match_type", "VARCHAR(20) DEFAULT 'partial'"),
                ("clues_data", "TEXT"),
                ("complement_details", "TEXT"),
                ("completeness_data", "TEXT"),
                ("is_revealed", "BOOLEAN DEFAULT 0"),
                ("revealed_at", "TIMESTAMP"),
                ("is_claimed", "BOOLEAN DEFAULT 0"),
                ("claimed_at", "TIMESTAMP"),
                ("reward_earned", "INTEGER DEFAULT 0"),
                ("status", "VARCHAR(20) DEFAULT 'active'"),
            ]
            
            for col_name, col_def in columns_needed:
                if col_name not in current_sql:
                    try:
                        cursor.execute(f"ALTER TABLE blind_box_matches ADD COLUMN {col_name} {col_def}")
                        print(f"  ✓ 添加列: {col_name}")
                    except sqlite3.OperationalError as e:
                        print(f"  跳过列 {col_name}: {e}")
            
            conn.commit()
            
    except sqlite3.OperationalError as e:
        print(f"错误: {e}")
        conn.rollback()
    finally:
        conn.close()


def create_quest_logs_table():
    """
    检查并创建 quest_logs 表（寻宝日志表）
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if not check_table_exists(cursor, "quest_logs"):
            print("创建 quest_logs 表...")
            cursor.execute("""
                CREATE TABLE quest_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    quest_date VARCHAR(20) NOT NULL,
                    quest_type VARCHAR(50) DEFAULT 'blind_box_match',
                    blind_box_match_id INTEGER,
                    quest_status VARCHAR(20) DEFAULT 'completed',
                    reward_earned INTEGER DEFAULT 0,
                    reward_type VARCHAR(20) DEFAULT 'fragment',
                    meta_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (blind_box_match_id) REFERENCES blind_box_matches (id)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX idx_quest_logs_user_id 
                ON quest_logs (user_id)
            """)
            cursor.execute("""
                CREATE INDEX idx_quest_logs_quest_date 
                ON quest_logs (quest_date)
            """)
            cursor.execute("""
                CREATE INDEX idx_quest_logs_quest_type 
                ON quest_logs (quest_type)
            """)
            cursor.execute("""
                CREATE INDEX idx_quest_logs_created_at 
                ON quest_logs (created_at)
            """)
            
            conn.commit()
            print("✓ quest_logs 表创建成功")
        else:
            print("✓ quest_logs 表已存在")
            
            cursor.execute("""
                SELECT sql FROM sqlite_master 
                WHERE type='table' AND name='quest_logs'
            """)
            result = cursor.fetchone()
            current_sql = result[0] if result else ""
            
            columns_needed = [
                ("quest_type", "VARCHAR(50) DEFAULT 'blind_box_match'"),
                ("blind_box_match_id", "INTEGER"),
                ("quest_status", "VARCHAR(20) DEFAULT 'completed'"),
                ("reward_earned", "INTEGER DEFAULT 0"),
                ("reward_type", "VARCHAR(20) DEFAULT 'fragment'"),
                ("meta_data", "TEXT"),
            ]
            
            for col_name, col_def in columns_needed:
                if col_name not in current_sql:
                    try:
                        cursor.execute(f"ALTER TABLE quest_logs ADD COLUMN {col_name} {col_def}")
                        print(f"  ✓ 添加列: {col_name}")
                    except sqlite3.OperationalError as e:
                        print(f"  跳过列 {col_name}: {e}")
            
            conn.commit()
            
    except sqlite3.OperationalError as e:
        print(f"错误: {e}")
        conn.rollback()
    finally:
        conn.close()


def create_daily_quest_limits_table():
    """
    检查并创建 daily_quest_limits 表（每日寻宝次数限制表）
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if not check_table_exists(cursor, "daily_quest_limits"):
            print("创建 daily_quest_limits 表...")
            cursor.execute("""
                CREATE TABLE daily_quest_limits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    limit_date VARCHAR(20) NOT NULL,
                    quest_type VARCHAR(50) DEFAULT 'blind_box_match',
                    used_count INTEGER DEFAULT 0,
                    max_count INTEGER DEFAULT 3,
                    is_vip BOOLEAN DEFAULT 0,
                    vip_extra_count INTEGER DEFAULT 0,
                    refresh_count INTEGER DEFAULT 0,
                    max_refresh INTEGER DEFAULT 1,
                    meta_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX idx_daily_quest_limits_user_id 
                ON daily_quest_limits (user_id)
            """)
            cursor.execute("""
                CREATE INDEX idx_daily_quest_limits_limit_date 
                ON daily_quest_limits (limit_date)
            """)
            cursor.execute("""
                CREATE INDEX idx_daily_quest_limits_quest_type 
                ON daily_quest_limits (quest_type)
            """)
            
            conn.commit()
            print("✓ daily_quest_limits 表创建成功")
        else:
            print("✓ daily_quest_limits 表已存在")
            
            cursor.execute("""
                SELECT sql FROM sqlite_master 
                WHERE type='table' AND name='daily_quest_limits'
            """)
            result = cursor.fetchone()
            current_sql = result[0] if result else ""
            
            columns_needed = [
                ("quest_type", "VARCHAR(50) DEFAULT 'blind_box_match'"),
                ("used_count", "INTEGER DEFAULT 0"),
                ("max_count", "INTEGER DEFAULT 3"),
                ("is_vip", "BOOLEAN DEFAULT 0"),
                ("vip_extra_count", "INTEGER DEFAULT 0"),
                ("refresh_count", "INTEGER DEFAULT 0"),
                ("max_refresh", "INTEGER DEFAULT 1"),
                ("meta_data", "TEXT"),
            ]
            
            for col_name, col_def in columns_needed:
                if col_name not in current_sql:
                    try:
                        cursor.execute(f"ALTER TABLE daily_quest_limits ADD COLUMN {col_name} {col_def}")
                        print(f"  ✓ 添加列: {col_name}")
                    except sqlite3.OperationalError as e:
                        print(f"  跳过列 {col_name}: {e}")
            
            conn.commit()
            
    except sqlite3.OperationalError as e:
        print(f"错误: {e}")
        conn.rollback()
    finally:
        conn.close()


def create_clue_reveal_history_table():
    """
    检查并创建 clue_reveal_history 表（线索揭示历史表）
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if not check_table_exists(cursor, "clue_reveal_history"):
            print("创建 clue_reveal_history 表...")
            cursor.execute("""
                CREATE TABLE clue_reveal_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    blind_box_match_id INTEGER NOT NULL,
                    clue_index INTEGER NOT NULL,
                    clue_type VARCHAR(50),
                    clue_content TEXT,
                    hint_level VARCHAR(20) DEFAULT 'subtle',
                    revealed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (blind_box_match_id) REFERENCES blind_box_matches (id)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX idx_clue_reveal_history_user_id 
                ON clue_reveal_history (user_id)
            """)
            cursor.execute("""
                CREATE INDEX idx_clue_reveal_history_blind_box_match_id 
                ON clue_reveal_history (blind_box_match_id)
            """)
            cursor.execute("""
                CREATE INDEX idx_clue_reveal_history_revealed_at 
                ON clue_reveal_history (revealed_at)
            """)
            
            conn.commit()
            print("✓ clue_reveal_history 表创建成功")
        else:
            print("✓ clue_reveal_history 表已存在")
            
    except sqlite3.OperationalError as e:
        print(f"错误: {e}")
        conn.rollback()
    finally:
        conn.close()


def show_database_status():
    """
    显示数据库状态
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        print()
        print("=" * 60)
        print("元素缺角寻宝系统 - 数据库状态汇总")
        print("=" * 60)
        
        tables = [
            "user_element_profiles",
            "user_energy_tags",
            "blind_box_matches",
            "quest_logs",
            "daily_quest_limits",
            "clue_reveal_history",
        ]
        
        for table in tables:
            if check_table_exists(cursor, table):
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  ✓ {table}: {count} 条记录")
            else:
                print(f"  ✗ {table}: 不存在")
        
        print()
        print("=" * 60)
        
    except sqlite3.OperationalError as e:
        print(f"错误: {e}")
    finally:
        conn.close()


def main():
    print("=" * 60)
    print("数据库迁移脚本 - 元素缺角寻宝系统")
    print("=" * 60)
    print(f"数据库路径: {DB_PATH}")
    print()
    
    create_user_element_profiles_table()
    print()
    
    create_user_energy_tags_table()
    print()
    
    create_blind_box_matches_table()
    print()
    
    create_quest_logs_table()
    print()
    
    create_daily_quest_limits_table()
    print()
    
    create_clue_reveal_history_table()
    print()
    
    show_database_status()
    print()
    
    print("=" * 60)
    print("迁移完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
