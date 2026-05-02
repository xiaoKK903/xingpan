"""
数据库迁移脚本 - 竞猜系统
"""

import sqlite3
import json
from datetime import datetime, timedelta
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


def migrate_collective_predictions_table():
    """
    检查并扩展 collective_predictions 表
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if not check_table_exists(cursor, "collective_predictions"):
            print("创建 collective_predictions 表...")
            cursor.execute("""
                CREATE TABLE collective_predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prediction_date VARCHAR(20) NOT NULL,
                    target_date VARCHAR(20) NOT NULL,
                    title VARCHAR(200) NOT NULL,
                    description TEXT,
                    prediction_type VARCHAR(50) DEFAULT 'mood',
                    status VARCHAR(20) DEFAULT 'voting',
                    total_votes INTEGER DEFAULT 0,
                    is_resolved BOOLEAN DEFAULT 0,
                    resolved_at TIMESTAMP,
                    correct_option VARCHAR(100),
                    resolution_evidence TEXT,
                    accuracy_score FLOAT DEFAULT 0.0,
                    options TEXT,
                    vote_distribution TEXT,
                    actual_result TEXT,
                    total_stardust_pool INTEGER DEFAULT 0,
                    announced_at TIMESTAMP,
                    session_type VARCHAR(20) DEFAULT 'daily',
                    session_key VARCHAR(100),
                    theme_id INTEGER,
                    voting_starts_at TIMESTAMP,
                    voting_ends_at TIMESTAMP,
                    max_votes_per_user INTEGER DEFAULT 1,
                    base_vote_cost INTEGER DEFAULT 0,
                    extra_vote_cost INTEGER DEFAULT 20,
                    vip_multiplier FLOAT DEFAULT 1.5,
                    is_vip_enabled BOOLEAN DEFAULT 0,
                    ad_config TEXT,
                    event_brand_info TEXT,
                    reward_asset_type VARCHAR(20) DEFAULT 'fragment',
                    base_reward_amount INTEGER DEFAULT 10,
                    bonus_reward_amount INTEGER DEFAULT 0,
                    oracle_data_source VARCHAR(20) DEFAULT 'manual',
                    is_manual_resolution BOOLEAN DEFAULT 0,
                    resolved_by_admin_id INTEGER,
                    resolution_audit_log TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (theme_id) REFERENCES prediction_themes (id),
                    FOREIGN KEY (resolved_by_admin_id) REFERENCES users (id)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX idx_collective_predictions_prediction_date 
                ON collective_predictions (prediction_date)
            """)
            cursor.execute("""
                CREATE INDEX idx_collective_predictions_target_date 
                ON collective_predictions (target_date)
            """)
            cursor.execute("""
                CREATE INDEX idx_collective_predictions_status 
                ON collective_predictions (status)
            """)
            cursor.execute("""
                CREATE INDEX idx_collective_predictions_session_type 
                ON collective_predictions (session_type)
            """)
            cursor.execute("""
                CREATE INDEX idx_collective_predictions_voting_starts_at 
                ON collective_predictions (voting_starts_at)
            """)
            cursor.execute("""
                CREATE INDEX idx_collective_predictions_voting_ends_at 
                ON collective_predictions (voting_ends_at)
            """)
            
            conn.commit()
            print("✓ collective_predictions 表创建成功")
        else:
            print("✓ collective_predictions 表已存在")
            
            cursor.execute("""
                SELECT sql FROM sqlite_master 
                WHERE type='table' AND name='collective_predictions'
            """)
            result = cursor.fetchone()
            current_sql = result[0] if result else ""
            
            columns_needed = [
                ("session_type", "VARCHAR(20) DEFAULT 'daily'"),
                ("session_key", "VARCHAR(100)"),
                ("theme_id", "INTEGER"),
                ("voting_starts_at", "TIMESTAMP"),
                ("voting_ends_at", "TIMESTAMP"),
                ("max_votes_per_user", "INTEGER DEFAULT 1"),
                ("base_vote_cost", "INTEGER DEFAULT 0"),
                ("extra_vote_cost", "INTEGER DEFAULT 20"),
                ("vip_multiplier", "FLOAT DEFAULT 1.5"),
                ("is_vip_enabled", "BOOLEAN DEFAULT 0"),
                ("ad_config", "TEXT"),
                ("event_brand_info", "TEXT"),
                ("reward_asset_type", "VARCHAR(20) DEFAULT 'fragment'"),
                ("base_reward_amount", "INTEGER DEFAULT 10"),
                ("oracle_data_source", "VARCHAR(20) DEFAULT 'manual'"),
                ("is_manual_resolution", "BOOLEAN DEFAULT 0"),
                ("resolution_evidence", "TEXT"),
                ("announced_at", "TIMESTAMP"),
                ("actual_result", "TEXT"),
                ("total_stardust_pool", "INTEGER DEFAULT 0"),
                ("bonus_reward_amount", "INTEGER DEFAULT 0"),
                ("resolved_by_admin_id", "INTEGER"),
                ("resolution_audit_log", "TEXT"),
            ]
            
            for col_name, col_def in columns_needed:
                if col_name not in current_sql:
                    try:
                        cursor.execute(f"ALTER TABLE collective_predictions ADD COLUMN {col_name} {col_def}")
                        print(f"  ✓ 添加列: {col_name}")
                    except sqlite3.OperationalError as e:
                        print(f"  跳过列 {col_name}: {e}")
            
            conn.commit()
            
    except sqlite3.OperationalError as e:
        print(f"错误: {e}")
        conn.rollback()
    finally:
        conn.close()


def migrate_prediction_votes_table():
    """
    检查并扩展 prediction_votes 表
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if not check_table_exists(cursor, "prediction_votes"):
            print("创建 prediction_votes 表...")
            cursor.execute("""
                CREATE TABLE prediction_votes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prediction_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    vote_number INTEGER DEFAULT 1,
                    selected_option VARCHAR(100) NOT NULL,
                    confidence INTEGER DEFAULT 50,
                    vote_asset_type VARCHAR(20) DEFAULT 'fragment',
                    vote_cost INTEGER DEFAULT 0,
                    stardust_bet INTEGER DEFAULT 0,
                    is_vip_bonus BOOLEAN DEFAULT 0,
                    applied_multiplier FLOAT DEFAULT 1.0,
                    is_correct BOOLEAN,
                    reward_earned INTEGER DEFAULT 0,
                    reward_asset_type VARCHAR(20) DEFAULT 'fragment',
                    reward_claimed BOOLEAN DEFAULT 0,
                    reward_claimed_at TIMESTAMP,
                    is_validated BOOLEAN DEFAULT 1,
                    validated_at TIMESTAMP,
                    validation_notes VARCHAR(500),
                    vote_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (prediction_id) REFERENCES collective_predictions (id),
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX idx_prediction_votes_prediction_id 
                ON prediction_votes (prediction_id)
            """)
            cursor.execute("""
                CREATE INDEX idx_prediction_votes_user_id 
                ON prediction_votes (user_id)
            """)
            
            conn.commit()
            print("✓ prediction_votes 表创建成功")
        else:
            print("✓ prediction_votes 表已存在")
            
            cursor.execute("""
                SELECT sql FROM sqlite_master 
                WHERE type='table' AND name='prediction_votes'
            """)
            result = cursor.fetchone()
            current_sql = result[0] if result else ""
            
            columns_needed = [
                ("vote_number", "INTEGER DEFAULT 1"),
                ("vote_asset_type", "VARCHAR(20) DEFAULT 'fragment'"),
                ("vote_cost", "INTEGER DEFAULT 0"),
                ("stardust_bet", "INTEGER DEFAULT 0"),
                ("is_vip_bonus", "BOOLEAN DEFAULT 0"),
                ("applied_multiplier", "FLOAT DEFAULT 1.0"),
                ("reward_asset_type", "VARCHAR(20) DEFAULT 'fragment'"),
                ("reward_claimed_at", "TIMESTAMP"),
                ("is_validated", "BOOLEAN DEFAULT 1"),
                ("validated_at", "TIMESTAMP"),
                ("validation_notes", "VARCHAR(500)"),
                ("vote_data", "TEXT"),
            ]
            
            for col_name, col_def in columns_needed:
                if col_name not in current_sql:
                    try:
                        cursor.execute(f"ALTER TABLE prediction_votes ADD COLUMN {col_name} {col_def}")
                        print(f"  ✓ 添加列: {col_name}")
                    except sqlite3.OperationalError as e:
                        print(f"  跳过列 {col_name}: {e}")
            
            conn.commit()
            
    except sqlite3.OperationalError as e:
        print(f"错误: {e}")
        conn.rollback()
    finally:
        conn.close()


def create_prediction_option_stats_table():
    """
    创建 prediction_option_stats 表（独立统计表）
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if not check_table_exists(cursor, "prediction_option_stats"):
            print("创建 prediction_option_stats 表...")
            cursor.execute("""
                CREATE TABLE prediction_option_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prediction_id INTEGER NOT NULL,
                    option_value VARCHAR(100) NOT NULL,
                    vote_count INTEGER DEFAULT 0,
                    total_amount INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (prediction_id) REFERENCES collective_predictions (id)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX idx_prediction_option_stats_prediction_id 
                ON prediction_option_stats (prediction_id)
            """)
            cursor.execute("""
                CREATE INDEX idx_prediction_option_stats_option_value 
                ON prediction_option_stats (option_value)
            """)
            
            conn.commit()
            print("✓ prediction_option_stats 表创建成功")
        else:
            print("✓ prediction_option_stats 表已存在")
            
    except sqlite3.OperationalError as e:
        print(f"错误: {e}")
        conn.rollback()
    finally:
        conn.close()


def create_reward_claim_records_table():
    """
    创建 reward_claim_records 表（防重复领取）
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if not check_table_exists(cursor, "reward_claim_records"):
            print("创建 reward_claim_records 表...")
            cursor.execute("""
                CREATE TABLE reward_claim_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    prediction_id INTEGER NOT NULL,
                    vote_id INTEGER NOT NULL UNIQUE,
                    asset_type VARCHAR(20) NOT NULL,
                    amount INTEGER DEFAULT 0,
                    claimed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    claim_ip VARCHAR(50),
                    claim_session VARCHAR(100),
                    audit_note VARCHAR(500),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (prediction_id) REFERENCES collective_predictions (id),
                    FOREIGN KEY (vote_id) REFERENCES prediction_votes (id)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX idx_reward_claim_records_user_id 
                ON reward_claim_records (user_id)
            """)
            cursor.execute("""
                CREATE INDEX idx_reward_claim_records_prediction_id 
                ON reward_claim_records (prediction_id)
            """)
            cursor.execute("""
                CREATE UNIQUE INDEX idx_reward_claim_records_vote_id 
                ON reward_claim_records (vote_id)
            """)
            cursor.execute("""
                CREATE INDEX idx_reward_claim_records_claimed_at 
                ON reward_claim_records (claimed_at)
            """)
            
            conn.commit()
            print("✓ reward_claim_records 表创建成功")
        else:
            print("✓ reward_claim_records 表已存在")
            
    except sqlite3.OperationalError as e:
        print(f"错误: {e}")
        conn.rollback()
    finally:
        conn.close()


def create_prediction_themes_table():
    """
    创建 prediction_themes 表
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if not check_table_exists(cursor, "prediction_themes"):
            print("创建 prediction_themes 表...")
            cursor.execute("""
                CREATE TABLE prediction_themes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    theme_key VARCHAR(100) UNIQUE NOT NULL,
                    theme_name VARCHAR(200) NOT NULL,
                    description TEXT,
                    theme_category VARCHAR(50) DEFAULT 'general',
                    default_options TEXT,
                    default_session_type VARCHAR(20) DEFAULT 'daily',
                    default_max_votes INTEGER DEFAULT 1,
                    default_base_cost INTEGER DEFAULT 0,
                    default_reward_type VARCHAR(20) DEFAULT 'fragment',
                    default_reward_amount INTEGER DEFAULT 10,
                    oracle_source VARCHAR(20) DEFAULT 'manual',
                    resolution_rule TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    is_permanent BOOLEAN DEFAULT 0,
                    start_date TIMESTAMP,
                    end_date TIMESTAMP,
                    ad_config TEXT,
                    brand_info TEXT,
                    sort_order INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE UNIQUE INDEX idx_prediction_themes_theme_key 
                ON prediction_themes (theme_key)
            """)
            cursor.execute("""
                CREATE INDEX idx_prediction_themes_is_active 
                ON prediction_themes (is_active)
            """)
            
            conn.commit()
            print("✓ prediction_themes 表创建成功")
        else:
            print("✓ prediction_themes 表已存在")
            
    except sqlite3.OperationalError as e:
        print(f"错误: {e}")
        conn.rollback()
    finally:
        conn.close()


def create_user_tags_table():
    """
    创建 user_tags 表
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if not check_table_exists(cursor, "user_tags"):
            print("创建 user_tags 表...")
            cursor.execute("""
                CREATE TABLE user_tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    tag_category VARCHAR(50) NOT NULL,
                    tag_key VARCHAR(100) NOT NULL,
                    tag_value VARCHAR(500),
                    tag_score FLOAT DEFAULT 1.0,
                    confidence FLOAT DEFAULT 0.5,
                    source_type VARCHAR(50) DEFAULT 'inference',
                    source_reference VARCHAR(200),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX idx_user_tags_user_id 
                ON user_tags (user_id)
            """)
            cursor.execute("""
                CREATE INDEX idx_user_tags_tag_category 
                ON user_tags (tag_category)
            """)
            cursor.execute("""
                CREATE INDEX idx_user_tags_tag_key 
                ON user_tags (tag_key)
            """)
            
            conn.commit()
            print("✓ user_tags 表创建成功")
        else:
            print("✓ user_tags 表已存在")
            
    except sqlite3.OperationalError as e:
        print(f"错误: {e}")
        conn.rollback()
    finally:
        conn.close()


def create_tiered_vote_costs_table():
    """
    创建 tiered_vote_costs 表（阶梯式费用）
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if not check_table_exists(cursor, "tiered_vote_costs"):
            print("创建 tiered_vote_costs 表...")
            cursor.execute("""
                CREATE TABLE tiered_vote_costs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prediction_id INTEGER NOT NULL,
                    vote_tier INTEGER DEFAULT 1,
                    allowed_asset_types VARCHAR(200) DEFAULT 'fragment',
                    cost_fragment INTEGER DEFAULT 0,
                    cost_point INTEGER DEFAULT 0,
                    cost_ticket INTEGER DEFAULT 0,
                    reward_multiplier FLOAT DEFAULT 1.0,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (prediction_id) REFERENCES collective_predictions (id)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX idx_tiered_vote_costs_prediction_id 
                ON tiered_vote_costs (prediction_id)
            """)
            cursor.execute("""
                CREATE INDEX idx_tiered_vote_costs_is_active 
                ON tiered_vote_costs (is_active)
            """)
            
            conn.commit()
            print("✓ tiered_vote_costs 表创建成功")
        else:
            print("✓ tiered_vote_costs 表已存在")
            
    except sqlite3.OperationalError as e:
        print(f"错误: {e}")
        conn.rollback()
    finally:
        conn.close()


def create_rate_limit_tables():
    """
    创建限流相关表
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if not check_table_exists(cursor, "rate_limit_records"):
            print("创建 rate_limit_records 表...")
            cursor.execute("""
                CREATE TABLE rate_limit_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    ip_address VARCHAR(50),
                    action_type VARCHAR(50) NOT NULL,
                    action_count INTEGER DEFAULT 0,
                    window_start TIMESTAMP NOT NULL,
                    window_end TIMESTAMP NOT NULL,
                    is_blocked BOOLEAN DEFAULT 0,
                    blocked_reason VARCHAR(500),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX idx_rate_limit_records_user_id 
                ON rate_limit_records (user_id)
            """)
            cursor.execute("""
                CREATE INDEX idx_rate_limit_records_action_type 
                ON rate_limit_records (action_type)
            """)
            cursor.execute("""
                CREATE INDEX idx_rate_limit_records_window_end 
                ON rate_limit_records (window_end)
            """)
            
            conn.commit()
            print("✓ rate_limit_records 表创建成功")
        else:
            print("✓ rate_limit_records 表已存在")
        
        if not check_table_exists(cursor, "abnormal_behavior_logs"):
            print("创建 abnormal_behavior_logs 表...")
            cursor.execute("""
                CREATE TABLE abnormal_behavior_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    ip_address VARCHAR(50),
                    session_id VARCHAR(100),
                    behavior_type VARCHAR(50) NOT NULL,
                    severity VARCHAR(20) DEFAULT 'low',
                    request_data TEXT,
                    request_path VARCHAR(200),
                    request_method VARCHAR(20),
                    detection_rule VARCHAR(100),
                    risk_score FLOAT DEFAULT 0.0,
                    is_manual_reviewed BOOLEAN DEFAULT 0,
                    review_result VARCHAR(20),
                    reviewed_at TIMESTAMP,
                    action_taken VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX idx_abnormal_behavior_logs_user_id 
                ON abnormal_behavior_logs (user_id)
            """)
            cursor.execute("""
                CREATE INDEX idx_abnormal_behavior_logs_behavior_type 
                ON abnormal_behavior_logs (behavior_type)
            """)
            cursor.execute("""
                CREATE INDEX idx_abnormal_behavior_logs_created_at 
                ON abnormal_behavior_logs (created_at)
            """)
            
            conn.commit()
            print("✓ abnormal_behavior_logs 表创建成功")
        else:
            print("✓ abnormal_behavior_logs 表已存在")
            
    except sqlite3.OperationalError as e:
        print(f"错误: {e}")
        conn.rollback()
    finally:
        conn.close()


def check_and_create_prophecy_tickets_table():
    """
    检查并创建 prophecy_tickets 表
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if not check_table_exists(cursor, "prophecy_tickets"):
            print("创建 prophecy_tickets 表...")
            cursor.execute("""
                CREATE TABLE prophecy_tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    ticket_type VARCHAR(50) DEFAULT 'general',
                    source_snapshot_id INTEGER,
                    is_used BOOLEAN DEFAULT 0,
                    used_at TIMESTAMP,
                    used_for VARCHAR(200),
                    valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    valid_until TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX idx_prophecy_tickets_user_id 
                ON prophecy_tickets (user_id)
            """)
            cursor.execute("""
                CREATE INDEX idx_prophecy_tickets_is_used 
                ON prophecy_tickets (is_used)
            """)
            cursor.execute("""
                CREATE INDEX idx_prophecy_tickets_valid_until 
                ON prophecy_tickets (valid_until)
            """)
            
            conn.commit()
            print("✓ prophecy_tickets 表创建成功")
        else:
            print("✓ prophecy_tickets 表已存在")
            
            cursor.execute("""
                SELECT sql FROM sqlite_master 
                WHERE type='table' AND name='prophecy_tickets'
            """)
            result = cursor.fetchone()
            current_sql = result[0] if result else ""
            
            columns_needed = [
                ("ticket_type", "VARCHAR(50) DEFAULT 'general'"),
                ("source_snapshot_id", "INTEGER"),
                ("is_used", "BOOLEAN DEFAULT 0"),
                ("used_at", "TIMESTAMP"),
                ("used_for", "VARCHAR(200)"),
                ("valid_from", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
                ("valid_until", "TIMESTAMP"),
            ]
            
            for col_name, col_def in columns_needed:
                if col_name not in current_sql:
                    try:
                        cursor.execute(f"ALTER TABLE prophecy_tickets ADD COLUMN {col_name} {col_def}")
                        print(f"  ✓ 添加列: {col_name}")
                    except sqlite3.OperationalError as e:
                        print(f"  跳过列 {col_name}: {e}")
            
            conn.commit()
            
    except sqlite3.OperationalError as e:
        print(f"错误: {e}")
        conn.rollback()
    finally:
        conn.close()


def initialize_default_themes():
    """
    初始化默认竞猜主题
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT COUNT(*) FROM prediction_themes")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("初始化默认竞猜主题...")
            
            now = datetime.now()
            
            themes = [
                {
                    "theme_key": "daily_element_dominance",
                    "theme_name": "今日主导元素",
                    "description": "预测今日星能共鸣池的主导元素",
                    "theme_category": "daily",
                    "default_options": json.dumps({
                        "labels": ["火象元素", "土象元素", "风象元素", "水象元素"],
                        "values": ["fire", "earth", "air", "water"],
                        "icons": ["🔥", "🌍", "💨", "💧"]
                    }),
                    "default_session_type": "daily",
                    "default_max_votes": 3,
                    "default_base_cost": 0,
                    "default_reward_type": "point",
                    "default_reward_amount": 50,
                    "oracle_source": "resonance_pool",
                    "is_active": 1,
                    "is_permanent": 1,
                    "sort_order": 1,
                },
                {
                    "theme_key": "daily_weather_forecast",
                    "theme_name": "能量天气预报",
                    "description": "预测今日能量气象站的主要天气",
                    "theme_category": "daily",
                    "default_options": json.dumps({
                        "labels": ["晴天", "多云", "阵雨", "星芒风暴", "极光"],
                        "values": ["sunny", "cloudy", "rainy", "storm", "aurora"],
                        "icons": ["☀️", "☁️", "🌧️", "⚡", "🌌"]
                    }),
                    "default_session_type": "daily",
                    "default_max_votes": 2,
                    "default_base_cost": 0,
                    "default_reward_type": "point",
                    "default_reward_amount": 30,
                    "oracle_source": "weather",
                    "is_active": 1,
                    "is_permanent": 1,
                    "sort_order": 2,
                },
                {
                    "theme_key": "weekly_lucky_sign",
                    "theme_name": "本周幸运星座",
                    "description": "预测本周最幸运的星座",
                    "theme_category": "weekly",
                    "default_options": json.dumps({
                        "labels": ["白羊座", "金牛座", "双子座", "巨蟹座", "狮子座", "处女座", 
                                   "天秤座", "天蝎座", "射手座", "摩羯座", "水瓶座", "双鱼座"],
                        "values": ["aries", "taurus", "gemini", "cancer", "leo", "virgo",
                                   "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"],
                        "icons": ["♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"]
                    }),
                    "default_session_type": "weekly",
                    "default_max_votes": 5,
                    "default_base_cost": 0,
                    "default_reward_type": "point",
                    "default_reward_amount": 100,
                    "oracle_source": "resonance_pool",
                    "is_active": 1,
                    "is_permanent": 1,
                    "sort_order": 3,
                },
                {
                    "theme_key": "monthly_dominant_planet",
                    "theme_name": "本月主导行星",
                    "description": "预测本月影响力最大的行星",
                    "theme_category": "monthly",
                    "default_options": json.dumps({
                        "labels": ["太阳", "月亮", "水星", "金星", "火星", "木星", "土星", "天王星", "海王星", "冥王星"],
                        "values": ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"],
                        "icons": ["☉", "☽", "☿", "♀", "♂", "♃", "♄", "♅", "♆", "♇"]
                    }),
                    "default_session_type": "special",
                    "default_max_votes": 10,
                    "default_base_cost": 0,
                    "default_reward_type": "point",
                    "default_reward_amount": 200,
                    "oracle_source": "resonance_pool",
                    "is_active": 1,
                    "is_permanent": 1,
                    "sort_order": 4,
                }
            ]
            
            for theme in themes:
                cursor.execute("""
                    INSERT INTO prediction_themes (
                        theme_key, theme_name, description, theme_category,
                        default_options, default_session_type, default_max_votes,
                        default_base_cost, default_reward_type, default_reward_amount,
                        oracle_source, is_active, is_permanent, sort_order,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    theme["theme_key"],
                    theme["theme_name"],
                    theme["description"],
                    theme["theme_category"],
                    theme["default_options"],
                    theme["default_session_type"],
                    theme["default_max_votes"],
                    theme["default_base_cost"],
                    theme["default_reward_type"],
                    theme["default_reward_amount"],
                    theme["oracle_source"],
                    theme["is_active"],
                    theme["is_permanent"],
                    theme["sort_order"],
                    now,
                    now
                ))
            
            conn.commit()
            print(f"✓ 初始化了 {len(themes)} 个默认主题")
        else:
            print("✓ 主题已存在，跳过初始化")
            
    except sqlite3.OperationalError as e:
        print(f"错误: {e}")
        conn.rollback()
    finally:
        conn.close()


def create_test_predictions():
    """
    创建测试用的竞猜场次
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT COUNT(*) FROM collective_predictions WHERE session_type='daily'")
        count = cursor.fetchone()[0]
        
        if count < 2:
            print("创建测试竞猜场次...")
            
            now = datetime.now()
            
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            voting_ends_today = today + timedelta(hours=23, minutes=59)
            voting_starts_tomorrow = today + timedelta(days=1)
            voting_ends_tomorrow = voting_starts_tomorrow + timedelta(hours=23, minutes=59)
            
            options_1 = json.dumps({
                "labels": ["火象元素", "土象元素", "风象元素", "水象元素"],
                "values": ["fire", "earth", "air", "water"],
                "icons": ["🔥", "🌍", "💨", "💧"]
            })
            
            options_2 = json.dumps({
                "labels": ["晴天", "多云", "阵雨", "星芒风暴"],
                "values": ["sunny", "cloudy", "rainy", "storm"],
                "icons": ["☀️", "☁️", "🌧️", "⚡"]
            })
            
            cursor.execute("""
                INSERT INTO collective_predictions (
                    title, description, prediction_type, target_date,
                    prediction_date, status, total_votes, is_resolved,
                    options, vote_distribution, created_at, updated_at,
                    session_type, session_key, theme_id,
                    voting_starts_at, voting_ends_at,
                    max_votes_per_user, base_vote_cost, extra_vote_cost,
                    vip_multiplier, is_vip_enabled,
                    reward_asset_type, base_reward_amount,
                    oracle_data_source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "今日主导元素预测",
                "预测今日星能共鸣池的主导元素。火象元素在今天的能量流动中会占据主导吗？",
                "element_prediction",
                today.strftime("%Y-%m-%d"),
                today.strftime("%Y-%m-%d"),
                "voting",
                0,
                0,
                options_1,
                "{}",
                now,
                now,
                "daily",
                f"daily_element_{today.strftime('%Y%m%d')}",
                1,
                today,
                voting_ends_today,
                3,
                0,
                20,
                1.5,
                1,
                "point",
                50,
                "resonance_pool"
            ))
            
            cursor.execute("""
                INSERT INTO collective_predictions (
                    title, description, prediction_type, target_date,
                    prediction_date, status, total_votes, is_resolved,
                    options, vote_distribution, created_at, updated_at,
                    session_type, session_key, theme_id,
                    voting_starts_at, voting_ends_at,
                    max_votes_per_user, base_vote_cost, extra_vote_cost,
                    vip_multiplier, is_vip_enabled,
                    reward_asset_type, base_reward_amount,
                    oracle_data_source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "能量天气预报",
                "预测今日的主要能量天气类型。今天的星象能量会是晴朗还是多变？",
                "weather_prediction",
                today.strftime("%Y-%m-%d"),
                today.strftime("%Y-%m-%d"),
                "voting",
                0,
                0,
                options_2,
                "{}",
                now,
                now,
                "daily",
                f"daily_weather_{today.strftime('%Y%m%d')}",
                2,
                today,
                voting_ends_today,
                2,
                0,
                30,
                1.5,
                1,
                "point",
                30,
                "weather"
            ))
            
            cursor.execute("""
                INSERT INTO collective_predictions (
                    title, description, prediction_type, target_date,
                    prediction_date, status, total_votes, is_resolved,
                    options, vote_distribution, created_at, updated_at,
                    session_type, session_key, theme_id,
                    voting_starts_at, voting_ends_at,
                    max_votes_per_user, base_vote_cost, extra_vote_cost,
                    vip_multiplier, is_vip_enabled,
                    reward_asset_type, base_reward_amount,
                    oracle_data_source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "明日主导元素预测",
                "预测明日星能共鸣池的主导元素。提前参与明日的竞猜场！",
                "element_prediction",
                voting_starts_tomorrow.strftime("%Y-%m-%d"),
                voting_starts_tomorrow.strftime("%Y-%m-%d"),
                "upcoming",
                0,
                0,
                options_1,
                "{}",
                now,
                now,
                "daily",
                f"daily_element_{voting_starts_tomorrow.strftime('%Y%m%d')}",
                1,
                voting_starts_tomorrow,
                voting_ends_tomorrow,
                3,
                0,
                20,
                1.5,
                1,
                "point",
                50,
                "resonance_pool"
            ))
            
            conn.commit()
            print("✓ 创建了 3 个测试场次（2个开放，1个即将开始）")
        else:
            print(f"✓ 已存在 {count} 个每日场次，跳过创建")
            
    except sqlite3.OperationalError as e:
        print(f"错误: {e}")
        conn.rollback()
    finally:
        conn.close()


def initialize_user_assets():
    """
    为用户初始化演示资产数据
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id, username, stardust_fragment_balance, stardust_point_balance FROM users LIMIT 10")
        users = cursor.fetchall()
        
        if not users:
            print("没有用户，跳过资产初始化")
            return
        
        print(f"初始化 {len(users)} 个用户的演示资产...")
        
        now = datetime.now()
        
        for user in users:
            user_id = user[0]
            username = user[1]
            fragment_balance = user[2] or 0
            point_balance = user[3] or 0
            
            if fragment_balance < 100:
                cursor.execute("""
                    UPDATE users SET stardust_fragment_balance = 100 
                    WHERE id = ?
                """, (user_id,))
                print(f"  ✓ 用户 {username}: 设置星元碎片为 100")
            else:
                print(f"  ✓ 用户 {username}: 星元碎片余额为 {fragment_balance}")
            
            if point_balance < 50:
                cursor.execute("""
                    UPDATE users SET stardust_point_balance = 50 
                    WHERE id = ?
                """, (user_id,))
                print(f"  ✓ 用户 {username}: 设置高阶星尘为 50")
            else:
                print(f"  ✓ 用户 {username}: 高阶星尘余额为 {point_balance}")
            
            cursor.execute("SELECT COUNT(*) FROM prophecy_tickets WHERE user_id = ?", (user_id,))
            ticket_count = cursor.fetchone()[0]
            
            if ticket_count < 3:
                for i in range(3 - ticket_count):
                    cursor.execute("""
                        INSERT INTO prophecy_tickets (
                            user_id, ticket_type, is_used,
                            valid_from, valid_until, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        user_id,
                        "general",
                        0,
                        now,
                        now + timedelta(days=30),
                        now
                    ))
                print(f"  ✓ 用户 {username}: 创建了 {3 - ticket_count} 张预言券")
        
        conn.commit()
        print("✓ 用户资产初始化完成")
            
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
        print("数据库状态汇总")
        print("=" * 60)
        
        tables = [
            "collective_predictions",
            "prediction_votes",
            "prediction_option_stats",
            "prediction_themes",
            "prophecy_tickets",
            "reward_claim_records",
            "tiered_vote_costs",
            "user_tags",
            "rate_limit_records",
            "abnormal_behavior_logs",
            "users",
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
    print("数据库迁移脚本 - 竞猜系统")
    print("=" * 60)
    print(f"数据库路径: {DB_PATH}")
    print()
    
    migrate_collective_predictions_table()
    print()
    
    migrate_prediction_votes_table()
    print()
    
    create_prediction_option_stats_table()
    print()
    
    create_reward_claim_records_table()
    print()
    
    create_prediction_themes_table()
    print()
    
    create_user_tags_table()
    print()
    
    create_tiered_vote_costs_table()
    print()
    
    create_rate_limit_tables()
    print()
    
    check_and_create_prophecy_tickets_table()
    print()
    
    initialize_default_themes()
    print()
    
    create_test_predictions()
    print()
    
    initialize_user_assets()
    print()
    
    show_database_status()
    print()
    
    print("=" * 60)
    print("迁移完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
