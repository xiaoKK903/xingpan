"""
数据库迁移脚本 - 修复每日 CP 匹配系统的缺失列和表
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "ai_customer_service.db"


def get_connection():
    """获取数据库连接"""
    return sqlite3.connect(str(DB_PATH))


def check_table_exists(cursor, table_name: str) -> bool:
    """检查表是否存在"""
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name=?
    """, (table_name,))
    return cursor.fetchone() is not None


def check_column_exists(cursor, table_name: str, column_name: str) -> bool:
    """检查列是否存在"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


def migrate_daily_cp_matches_table():
    """
    为 daily_cp_matches 表添加缺失的列
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if not check_table_exists(cursor, "daily_cp_matches"):
            print("创建 daily_cp_matches 表...")
            cursor.execute("""
                CREATE TABLE daily_cp_matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    match_date VARCHAR(20) NOT NULL,
                    match_batch_id VARCHAR(50),
                    user_a_id INTEGER NOT NULL,
                    user_b_id INTEGER NOT NULL,
                    user_a_chart_id INTEGER,
                    user_b_chart_id INTEGER,
                    compatibility_score INTEGER DEFAULT 50,
                    match_type VARCHAR(50) DEFAULT 'random',
                    target_zodiac_sign VARCHAR(50),
                    synastry_aspects TEXT,
                    highlights_summary TEXT,
                    interpretation_text TEXT,
                    user_a_status VARCHAR(20) DEFAULT 'pending',
                    user_b_status VARCHAR(20) DEFAULT 'pending',
                    user_a_accepted_at TIMESTAMP,
                    user_b_accepted_at TIMESTAMP,
                    is_mutual_accepted BOOLEAN DEFAULT 0,
                    mutual_accepted_at TIMESTAMP,
                    session_id INTEGER,
                    user_a_profile_unlocked BOOLEAN DEFAULT 0,
                    user_a_profile_unlocked_at TIMESTAMP,
                    user_a_profile_unlock_order_id INTEGER,
                    user_b_profile_unlocked BOOLEAN DEFAULT 0,
                    user_b_profile_unlocked_at TIMESTAMP,
                    user_b_profile_unlock_order_id INTEGER,
                    match_source VARCHAR(50) DEFAULT 'daily_scheduled',
                    is_vip_targeted_match BOOLEAN DEFAULT 0,
                    status VARCHAR(20) DEFAULT 'active',
                    expired_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_a_id) REFERENCES users (id),
                    FOREIGN KEY (user_b_id) REFERENCES users (id),
                    FOREIGN KEY (user_a_chart_id) REFERENCES charts (id),
                    FOREIGN KEY (user_b_chart_id) REFERENCES charts (id),
                    FOREIGN KEY (session_id) REFERENCES time_limited_sessions (id),
                    UNIQUE (match_date, user_a_id, user_b_id)
                )
            """)
            
            cursor.execute("CREATE INDEX idx_daily_cp_matches_date ON daily_cp_matches (match_date)")
            cursor.execute("CREATE INDEX idx_daily_cp_matches_user_a ON daily_cp_matches (user_a_id)")
            cursor.execute("CREATE INDEX idx_daily_cp_matches_user_b ON daily_cp_matches (user_b_id)")
            cursor.execute("CREATE INDEX idx_daily_cp_matches_date_status ON daily_cp_matches (match_date, status)")
            cursor.execute("CREATE INDEX idx_daily_cp_matches_mutual ON daily_cp_matches (is_mutual_accepted, status)")
            
            conn.commit()
            print("✓ daily_cp_matches 表创建成功")
        else:
            print("检查 daily_cp_matches 表...")
            
            cursor.execute("PRAGMA table_info(daily_cp_matches)")
            existing_columns = [row[1] for row in cursor.fetchall()]
            print(f"  现有列: {existing_columns}")
            
            columns_to_add = [
                ("match_batch_id", "VARCHAR(50)"),
                ("user_a_chart_id", "INTEGER"),
                ("user_b_chart_id", "INTEGER"),
                ("compatibility_score", "INTEGER DEFAULT 50"),
                ("match_type", "VARCHAR(50) DEFAULT 'random'"),
                ("target_zodiac_sign", "VARCHAR(50)"),
                ("synastry_aspects", "TEXT"),
                ("highlights_summary", "TEXT"),
                ("interpretation_text", "TEXT"),
                ("user_a_status", "VARCHAR(20) DEFAULT 'pending'"),
                ("user_b_status", "VARCHAR(20) DEFAULT 'pending'"),
                ("user_a_accepted_at", "TIMESTAMP"),
                ("user_b_accepted_at", "TIMESTAMP"),
                ("is_mutual_accepted", "BOOLEAN DEFAULT 0"),
                ("mutual_accepted_at", "TIMESTAMP"),
                ("session_id", "INTEGER"),
                ("user_a_profile_unlocked", "BOOLEAN DEFAULT 0"),
                ("user_a_profile_unlocked_at", "TIMESTAMP"),
                ("user_a_profile_unlock_order_id", "INTEGER"),
                ("user_b_profile_unlocked", "BOOLEAN DEFAULT 0"),
                ("user_b_profile_unlocked_at", "TIMESTAMP"),
                ("user_b_profile_unlock_order_id", "INTEGER"),
                ("match_source", "VARCHAR(50) DEFAULT 'daily_scheduled'"),
                ("is_vip_targeted_match", "BOOLEAN DEFAULT 0"),
                ("status", "VARCHAR(20) DEFAULT 'active'"),
                ("expired_at", "TIMESTAMP"),
            ]
            
            added_count = 0
            for col_name, col_def in columns_to_add:
                if col_name not in existing_columns:
                    try:
                        cursor.execute(f"ALTER TABLE daily_cp_matches ADD COLUMN {col_name} {col_def}")
                        print(f"  ✓ 添加列: {col_name}")
                        added_count += 1
                    except sqlite3.OperationalError as e:
                        print(f"  跳过列 {col_name}: {e}")
            
            if added_count > 0:
                conn.commit()
                print(f"✓ daily_cp_matches 表迁移完成，添加了 {added_count} 个新列")
            else:
                print("✓ daily_cp_matches 表已经是最新的")
            
    except sqlite3.OperationalError as e:
        print(f"错误: {e}")
        conn.rollback()
    finally:
        conn.close()


def create_time_limited_sessions_table():
    """
    检查并创建 time_limited_sessions 表
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if not check_table_exists(cursor, "time_limited_sessions"):
            print("创建 time_limited_sessions 表...")
            cursor.execute("""
                CREATE TABLE time_limited_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_key VARCHAR(100) UNIQUE NOT NULL,
                    user_a_id INTEGER NOT NULL,
                    user_b_id INTEGER NOT NULL,
                    match_id INTEGER NOT NULL,
                    base_duration_hours INTEGER DEFAULT 24,
                    extended_duration_hours INTEGER DEFAULT 0,
                    total_duration_hours INTEGER DEFAULT 24,
                    started_at TIMESTAMP NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    is_extended BOOLEAN DEFAULT 0,
                    extension_count INTEGER DEFAULT 0,
                    private_chat_id INTEGER,
                    is_active BOOLEAN DEFAULT 1,
                    closed_at TIMESTAMP,
                    close_reason VARCHAR(50),
                    message_count INTEGER DEFAULT 0,
                    last_message_at TIMESTAMP,
                    extra_metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_a_id) REFERENCES users (id),
                    FOREIGN KEY (user_b_id) REFERENCES users (id),
                    FOREIGN KEY (match_id) REFERENCES daily_cp_matches (id),
                    FOREIGN KEY (private_chat_id) REFERENCES user_private_chats (id)
                )
            """)
            
            cursor.execute("CREATE INDEX idx_time_limited_sessions_key ON time_limited_sessions (session_key)")
            cursor.execute("CREATE INDEX idx_time_limited_sessions_expires ON time_limited_sessions (expires_at, is_active)")
            cursor.execute("CREATE INDEX idx_time_limited_sessions_users ON time_limited_sessions (user_a_id, user_b_id)")
            
            conn.commit()
            print("✓ time_limited_sessions 表创建成功")
        else:
            print("✓ time_limited_sessions 表已存在")
            
            cursor.execute("PRAGMA table_info(time_limited_sessions)")
            existing_columns = [row[1] for row in cursor.fetchall()]
            
            columns_to_add = [
                ("extra_metadata", "TEXT"),
            ]
            
            for col_name, col_def in columns_to_add:
                if col_name not in existing_columns:
                    try:
                        cursor.execute(f"ALTER TABLE time_limited_sessions ADD COLUMN {col_name} {col_def}")
                        print(f"  ✓ 添加列: {col_name}")
                    except sqlite3.OperationalError as e:
                        print(f"  跳过列 {col_name}: {e}")
            
            conn.commit()
            
    except sqlite3.OperationalError as e:
        print(f"错误: {e}")
        conn.rollback()
    finally:
        conn.close()


def create_session_extensions_table():
    """
    检查并创建 session_extensions 表
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if not check_table_exists(cursor, "session_extensions"):
            print("创建 session_extensions 表...")
            cursor.execute("""
                CREATE TABLE session_extensions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    extension_hours INTEGER NOT NULL,
                    price INTEGER DEFAULT 0,
                    currency_type VARCHAR(20) DEFAULT 'stardust_point',
                    payment_order_id INTEGER,
                    is_vip_free BOOLEAN DEFAULT 0,
                    extended_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES time_limited_sessions (id)
                )
            """)
            
            cursor.execute("CREATE INDEX idx_session_extensions_session ON session_extensions (session_id)")
            
            conn.commit()
            print("✓ session_extensions 表创建成功")
        else:
            print("✓ session_extensions 表已存在")
            
    except sqlite3.OperationalError as e:
        print(f"错误: {e}")
        conn.rollback()
    finally:
        conn.close()


def create_profile_unlocks_table():
    """
    检查并创建 profile_unlocks 表
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if not check_table_exists(cursor, "profile_unlocks"):
            print("创建 profile_unlocks 表...")
            cursor.execute("""
                CREATE TABLE profile_unlocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    unlock_no VARCHAR(50) UNIQUE NOT NULL,
                    match_id INTEGER NOT NULL,
                    buyer_user_id INTEGER NOT NULL,
                    target_user_id INTEGER NOT NULL,
                    price INTEGER DEFAULT 0,
                    currency_type VARCHAR(20) DEFAULT 'stardust_point',
                    payment_order_id INTEGER,
                    is_vip_free BOOLEAN DEFAULT 0,
                    unlocked_at TIMESTAMP,
                    expires_at TIMESTAMP,
                    is_permanent BOOLEAN DEFAULT 0,
                    status VARCHAR(20) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (match_id) REFERENCES daily_cp_matches (id),
                    FOREIGN KEY (buyer_user_id) REFERENCES users (id),
                    FOREIGN KEY (target_user_id) REFERENCES users (id)
                )
            """)
            
            cursor.execute("CREATE INDEX idx_profile_unlocks_match ON profile_unlocks (match_id)")
            cursor.execute("CREATE INDEX idx_profile_unlocks_buyer ON profile_unlocks (buyer_user_id)")
            cursor.execute("CREATE INDEX idx_profile_unlocks_target ON profile_unlocks (target_user_id)")
            cursor.execute("CREATE INDEX idx_profile_unlocks_unlock_no ON profile_unlocks (unlock_no)")
            
            conn.commit()
            print("✓ profile_unlocks 表创建成功")
        else:
            print("✓ profile_unlocks 表已存在")
            
    except sqlite3.OperationalError as e:
        print(f"错误: {e}")
        conn.rollback()
    finally:
        conn.close()


def create_match_preferences_table():
    """
    检查并创建 match_preferences 表
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if not check_table_exists(cursor, "match_preferences"):
            print("创建 match_preferences 表...")
            cursor.execute("""
                CREATE TABLE match_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE NOT NULL,
                    target_zodiac_sign VARCHAR(50),
                    excluded_zodiac_signs TEXT,
                    prefer_harmonious_aspects BOOLEAN DEFAULT 1,
                    custom_filters TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            cursor.execute("CREATE INDEX idx_match_preferences_user ON match_preferences (user_id)")
            
            conn.commit()
            print("✓ match_preferences 表创建成功")
        else:
            print("✓ match_preferences 表已存在")
            
    except sqlite3.OperationalError as e:
        print(f"错误: {e}")
        conn.rollback()
    finally:
        conn.close()


def create_daily_match_limits_table():
    """
    检查并创建 daily_match_limits 表
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if not check_table_exists(cursor, "daily_match_limits"):
            print("创建 daily_match_limits 表...")
            cursor.execute("""
                CREATE TABLE daily_match_limits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    limit_date VARCHAR(20) NOT NULL,
                    free_match_count INTEGER DEFAULT 0,
                    free_match_max INTEGER DEFAULT 1,
                    vip_extra_match_count INTEGER DEFAULT 0,
                    vip_extra_match_max INTEGER DEFAULT 0,
                    paid_match_count INTEGER DEFAULT 0,
                    paid_match_max INTEGER DEFAULT 10,
                    targeted_match_count INTEGER DEFAULT 0,
                    targeted_match_max INTEGER DEFAULT 0,
                    is_vip BOOLEAN DEFAULT 0,
                    vip_plan_type VARCHAR(20),
                    extra_metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE (user_id, limit_date)
                )
            """)
            
            cursor.execute("CREATE INDEX idx_daily_match_limits_user ON daily_match_limits (user_id)")
            cursor.execute("CREATE INDEX idx_daily_match_limits_date ON daily_match_limits (limit_date)")
            cursor.execute("CREATE UNIQUE INDEX idx_daily_match_limits_user_date ON daily_match_limits (user_id, limit_date)")
            
            conn.commit()
            print("✓ daily_match_limits 表创建成功")
        else:
            print("✓ daily_match_limits 表已存在")
            
            cursor.execute("PRAGMA table_info(daily_match_limits)")
            existing_columns = [row[1] for row in cursor.fetchall()]
            
            columns_to_add = [
                ("vip_extra_match_max", "INTEGER DEFAULT 0"),
                ("paid_match_max", "INTEGER DEFAULT 10"),
                ("targeted_match_max", "INTEGER DEFAULT 0"),
                ("is_vip", "BOOLEAN DEFAULT 0"),
                ("vip_plan_type", "VARCHAR(20)"),
                ("extra_metadata", "TEXT"),
            ]
            
            for col_name, col_def in columns_to_add:
                if col_name not in existing_columns:
                    try:
                        cursor.execute(f"ALTER TABLE daily_match_limits ADD COLUMN {col_name} {col_def}")
                        print(f"  ✓ 添加列: {col_name}")
                    except sqlite3.OperationalError as e:
                        print(f"  跳过列 {col_name}: {e}")
            
            conn.commit()
            
    except sqlite3.OperationalError as e:
        print(f"错误: {e}")
        conn.rollback()
    finally:
        conn.close()


def main():
    print("=" * 60)
    print("开始迁移每日 CP 匹配系统数据库...")
    print("=" * 60)
    
    migrate_daily_cp_matches_table()
    create_time_limited_sessions_table()
    create_session_extensions_table()
    create_profile_unlocks_table()
    create_match_preferences_table()
    create_daily_match_limits_table()
    
    print("\n" + "=" * 60)
    print("迁移完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
