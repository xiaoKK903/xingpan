"""
数据库迁移脚本 - 星盘能量PK竞技系统
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


def create_user_daily_pk_table():
    """
    检查并创建 user_daily_pk 表（用户每日PK记录表）
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if not check_table_exists(cursor, "user_daily_pk"):
            print("创建 user_daily_pk 表...")
            cursor.execute("""
                CREATE TABLE user_daily_pk (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    battle_date VARCHAR(20) NOT NULL,
                    free_challenges_used INTEGER DEFAULT 0,
                    free_challenges_total INTEGER DEFAULT 3,
                    paid_challenges_used INTEGER DEFAULT 0,
                    paid_challenges_purchased INTEGER DEFAULT 0,
                    daily_wins INTEGER DEFAULT 0,
                    daily_losses INTEGER DEFAULT 0,
                    daily_draws INTEGER DEFAULT 0,
                    fragments_earned INTEGER DEFAULT 0,
                    fragments_lost INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE (user_id, battle_date)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX idx_user_daily_pk_user_id ON user_daily_pk (user_id)
            """)
            cursor.execute("""
                CREATE INDEX idx_user_daily_pk_battle_date ON user_daily_pk (battle_date)
            """)
            cursor.execute("""
                CREATE INDEX idx_user_daily_pk_date ON user_daily_pk (user_id, battle_date)
            """)
            
            conn.commit()
            print("✓ user_daily_pk 表创建成功")
        else:
            print("✓ user_daily_pk 表已存在")
            
            cursor.execute("""
                SELECT sql FROM sqlite_master 
                WHERE type='table' AND name='user_daily_pk'
            """)
            result = cursor.fetchone()
            current_sql = result[0] if result else ""
            
            columns_needed = [
                ("free_challenges_used", "INTEGER DEFAULT 0"),
                ("free_challenges_total", "INTEGER DEFAULT 3"),
                ("paid_challenges_used", "INTEGER DEFAULT 0"),
                ("paid_challenges_purchased", "INTEGER DEFAULT 0"),
                ("daily_wins", "INTEGER DEFAULT 0"),
                ("daily_losses", "INTEGER DEFAULT 0"),
                ("daily_draws", "INTEGER DEFAULT 0"),
                ("fragments_earned", "INTEGER DEFAULT 0"),
                ("fragments_lost", "INTEGER DEFAULT 0"),
            ]
            
            for col_name, col_def in columns_needed:
                if col_name not in current_sql:
                    try:
                        cursor.execute(f"ALTER TABLE user_daily_pk ADD COLUMN {col_name} {col_def}")
                        print(f"  ✓ 添加列: {col_name}")
                    except sqlite3.OperationalError as e:
                        print(f"  跳过列 {col_name}: {e}")
            
            conn.commit()
            
    except sqlite3.OperationalError as e:
        print(f"错误: {e}")
        conn.rollback()
    finally:
        conn.close()


def create_energy_boosts_table():
    """
    检查并创建 energy_boosts 表（能量增益Buff表）
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if not check_table_exists(cursor, "energy_boosts"):
            print("创建 energy_boosts 表...")
            cursor.execute("""
                CREATE TABLE energy_boosts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    boost_type VARCHAR(50) NOT NULL,
                    boost_name VARCHAR(100) NOT NULL,
                    boost_description TEXT,
                    energy_multiplier FLOAT DEFAULT 1.0,
                    critical_hit_chance FLOAT DEFAULT 0.0,
                    protection_rate FLOAT DEFAULT 0.0,
                    is_active BOOLEAN DEFAULT 1,
                    valid_from TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    valid_until TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX idx_energy_boosts_user_id ON energy_boosts (user_id)
            """)
            cursor.execute("""
                CREATE INDEX idx_energy_boosts_type ON energy_boosts (boost_type)
            """)
            cursor.execute("""
                CREATE INDEX idx_energy_boosts_active ON energy_boosts (is_active)
            """)
            cursor.execute("""
                CREATE INDEX idx_energy_boosts_valid ON energy_boosts (valid_until)
            """)
            cursor.execute("""
                CREATE INDEX idx_active_boosts ON energy_boosts (user_id, is_active, valid_until)
            """)
            
            conn.commit()
            print("✓ energy_boosts 表创建成功")
        else:
            print("✓ energy_boosts 表已存在")
            
            cursor.execute("""
                SELECT sql FROM sqlite_master 
                WHERE type='table' AND name='energy_boosts'
            """)
            result = cursor.fetchone()
            current_sql = result[0] if result else ""
            
            columns_needed = [
                ("boost_type", "VARCHAR(50) NOT NULL DEFAULT 'double_energy'"),
                ("boost_name", "VARCHAR(100) NOT NULL DEFAULT '能量翻倍'"),
                ("boost_description", "TEXT"),
                ("energy_multiplier", "FLOAT DEFAULT 1.0"),
                ("critical_hit_chance", "FLOAT DEFAULT 0.0"),
                ("protection_rate", "FLOAT DEFAULT 0.0"),
                ("is_active", "BOOLEAN DEFAULT 1"),
                ("valid_from", "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP"),
                ("valid_until", "TIMESTAMP"),
            ]
            
            for col_name, col_def in columns_needed:
                if col_name not in current_sql:
                    try:
                        cursor.execute(f"ALTER TABLE energy_boosts ADD COLUMN {col_name} {col_def}")
                        print(f"  ✓ 添加列: {col_name}")
                    except sqlite3.OperationalError as e:
                        print(f"  跳过列 {col_name}: {e}")
            
            conn.commit()
            
    except sqlite3.OperationalError as e:
        print(f"错误: {e}")
        conn.rollback()
    finally:
        conn.close()


def create_pk_match_invites_table():
    """
    检查并创建 pk_match_invites 表（PK邀请记录表）
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if not check_table_exists(cursor, "pk_match_invites"):
            print("创建 pk_match_invites 表...")
            cursor.execute("""
                CREATE TABLE pk_match_invites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invite_code VARCHAR(20) NOT NULL,
                    inviter_id INTEGER NOT NULL,
                    invitee_id INTEGER,
                    match_id INTEGER,
                    wager_fragments INTEGER DEFAULT 10,
                    status VARCHAR(30) DEFAULT 'pending',
                    is_accepted BOOLEAN DEFAULT 0,
                    is_declined BOOLEAN DEFAULT 0,
                    is_expired BOOLEAN DEFAULT 0,
                    accepted_at TIMESTAMP,
                    declined_at TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (inviter_id) REFERENCES users (id),
                    FOREIGN KEY (invitee_id) REFERENCES users (id),
                    FOREIGN KEY (match_id) REFERENCES pk_matches (id),
                    UNIQUE (invite_code)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX idx_pk_match_invites_code ON pk_match_invites (invite_code)
            """)
            cursor.execute("""
                CREATE INDEX idx_pk_match_invites_inviter ON pk_match_invites (inviter_id)
            """)
            cursor.execute("""
                CREATE INDEX idx_pk_match_invites_invitee ON pk_match_invites (invitee_id)
            """)
            cursor.execute("""
                CREATE INDEX idx_pk_match_invites_expires ON pk_match_invites (expires_at)
            """)
            cursor.execute("""
                CREATE INDEX idx_pk_match_invites_created ON pk_match_invites (created_at)
            """)
            cursor.execute("""
                CREATE INDEX idx_pk_match_invites_status ON pk_match_invites (status)
            """)
            cursor.execute("""
                CREATE INDEX idx_pending_invites ON pk_match_invites (inviter_id, status, expires_at)
            """)
            cursor.execute("""
                CREATE INDEX idx_invitee_invites ON pk_match_invites (invitee_id, status)
            """)
            
            conn.commit()
            print("✓ pk_match_invites 表创建成功")
        else:
            print("✓ pk_match_invites 表已存在")
            
            cursor.execute("""
                SELECT sql FROM sqlite_master 
                WHERE type='table' AND name='pk_match_invites'
            """)
            result = cursor.fetchone()
            current_sql = result[0] if result else ""
            
            columns_needed = [
                ("status", "VARCHAR(30) DEFAULT 'pending'"),
                ("wager_fragments", "INTEGER DEFAULT 10"),
                ("is_accepted", "BOOLEAN DEFAULT 0"),
                ("is_declined", "BOOLEAN DEFAULT 0"),
                ("is_expired", "BOOLEAN DEFAULT 0"),
                ("accepted_at", "TIMESTAMP"),
                ("declined_at", "TIMESTAMP"),
                ("expires_at", "TIMESTAMP"),
            ]
            
            for col_name, col_def in columns_needed:
                if col_name not in current_sql:
                    try:
                        cursor.execute(f"ALTER TABLE pk_match_invites ADD COLUMN {col_name} {col_def}")
                        print(f"  ✓ 添加列: {col_name}")
                    except sqlite3.OperationalError as e:
                        print(f"  跳过列 {col_name}: {e}")
            
            if "status" in current_sql or "status" in str(result):
                try:
                    cursor.execute("""
                        UPDATE pk_match_invites 
                        SET status = 'accepted' 
                        WHERE is_accepted = 1
                    """)
                    print("  ✓ 迁移已接受的邀请状态")
                except sqlite3.OperationalError:
                    pass
                
                try:
                    cursor.execute("""
                        UPDATE pk_match_invites 
                        SET status = 'declined' 
                        WHERE is_declined = 1
                    """)
                    print("  ✓ 迁移已拒绝的邀请状态")
                except sqlite3.OperationalError:
                    pass
                
                try:
                    cursor.execute("""
                        UPDATE pk_match_invites 
                        SET status = 'expired' 
                        WHERE is_expired = 1
                    """)
                    print("  ✓ 迁移已过期的邀请状态")
                except sqlite3.OperationalError:
                    pass
                
                try:
                    cursor.execute("""
                        UPDATE pk_match_invites 
                        SET status = 'pending' 
                        WHERE status IS NULL OR status = ''
                    """)
                    print("  ✓ 设置默认状态为 pending")
                except sqlite3.OperationalError:
                    pass
            
            conn.commit()
            
    except sqlite3.OperationalError as e:
        print(f"错误: {e}")
        conn.rollback()
    finally:
        conn.close()


def create_pk_matches_table():
    """
    检查并创建 pk_matches 表（PK对战记录表）
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if not check_table_exists(cursor, "pk_matches"):
            print("创建 pk_matches 表...")
            cursor.execute("""
                CREATE TABLE pk_matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    match_no VARCHAR(50) NOT NULL,
                    match_type VARCHAR(20) DEFAULT 'random',
                    status VARCHAR(30) DEFAULT 'waiting',
                    challenger_id INTEGER NOT NULL,
                    defender_id INTEGER,
                    challenger_energy FLOAT DEFAULT 0.0,
                    defender_energy FLOAT DEFAULT 0.0,
                    challenger_boost_id INTEGER,
                    defender_boost_id INTEGER,
                    wager_fragments INTEGER DEFAULT 10,
                    winner_id INTEGER,
                    loser_id INTEGER,
                    result VARCHAR(20),
                    fragments_transferred INTEGER DEFAULT 0,
                    is_draw BOOLEAN DEFAULT 0,
                    is_challenger_critical BOOLEAN DEFAULT 0,
                    is_defender_critical BOOLEAN DEFAULT 0,
                    match_started_at TIMESTAMP,
                    match_completed_at TIMESTAMP,
                    expires_at TIMESTAMP,
                    match_data TEXT,
                    result_detail TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (challenger_id) REFERENCES users (id),
                    FOREIGN KEY (defender_id) REFERENCES users (id),
                    FOREIGN KEY (challenger_boost_id) REFERENCES energy_boosts (id),
                    FOREIGN KEY (defender_boost_id) REFERENCES energy_boosts (id),
                    FOREIGN KEY (winner_id) REFERENCES users (id),
                    FOREIGN KEY (loser_id) REFERENCES users (id),
                    UNIQUE (match_no)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX idx_pk_matches_no ON pk_matches (match_no)
            """)
            cursor.execute("""
                CREATE INDEX idx_pk_matches_type ON pk_matches (match_type)
            """)
            cursor.execute("""
                CREATE INDEX idx_pk_matches_status ON pk_matches (status, created_at)
            """)
            cursor.execute("""
                CREATE INDEX idx_pk_matches_challenger ON pk_matches (challenger_id, status, created_at)
            """)
            cursor.execute("""
                CREATE INDEX idx_pk_matches_defender ON pk_matches (defender_id, status, created_at)
            """)
            cursor.execute("""
                CREATE INDEX idx_pk_matches_expires ON pk_matches (status, expires_at)
            """)
            cursor.execute("""
                CREATE INDEX idx_pk_matches_created ON pk_matches (created_at)
            """)
            
            conn.commit()
            print("✓ pk_matches 表创建成功")
        else:
            print("✓ pk_matches 表已存在")
            
            cursor.execute("""
                SELECT sql FROM sqlite_master 
                WHERE type='table' AND name='pk_matches'
            """)
            result = cursor.fetchone()
            current_sql = result[0] if result else ""
            
            columns_needed = [
                ("match_type", "VARCHAR(20) DEFAULT 'random'"),
                ("status", "VARCHAR(30) DEFAULT 'waiting'"),
                ("challenger_energy", "FLOAT DEFAULT 0.0"),
                ("defender_energy", "FLOAT DEFAULT 0.0"),
                ("wager_fragments", "INTEGER DEFAULT 10"),
                ("winner_id", "INTEGER"),
                ("loser_id", "INTEGER"),
                ("result", "VARCHAR(20)"),
                ("fragments_transferred", "INTEGER DEFAULT 0"),
                ("is_draw", "BOOLEAN DEFAULT 0"),
                ("is_challenger_critical", "BOOLEAN DEFAULT 0"),
                ("is_defender_critical", "BOOLEAN DEFAULT 0"),
                ("match_started_at", "TIMESTAMP"),
                ("match_completed_at", "TIMESTAMP"),
                ("expires_at", "TIMESTAMP"),
                ("match_data", "TEXT"),
                ("result_detail", "TEXT"),
            ]
            
            for col_name, col_def in columns_needed:
                if col_name not in current_sql:
                    try:
                        cursor.execute(f"ALTER TABLE pk_matches ADD COLUMN {col_name} {col_def}")
                        print(f"  ✓ 添加列: {col_name}")
                    except sqlite3.OperationalError as e:
                        print(f"  跳过列 {col_name}: {e}")
            
            conn.commit()
            
    except sqlite3.OperationalError as e:
        print(f"错误: {e}")
        conn.rollback()
    finally:
        conn.close()


def create_user_energy_snapshots_table():
    """
    检查并创建 user_energy_snapshots 表（用户能量快照表）
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if not check_table_exists(cursor, "user_energy_snapshots"):
            print("创建 user_energy_snapshots 表...")
            cursor.execute("""
                CREATE TABLE user_energy_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    snapshot_date VARCHAR(20) NOT NULL,
                    daily_horoscope_score INTEGER DEFAULT 0,
                    daily_horoscope_detail TEXT,
                    task_completion_score INTEGER DEFAULT 0,
                    task_completion_detail TEXT,
                    total_energy_score FLOAT DEFAULT 0.0,
                    energy_boost_applied FLOAT DEFAULT 1.0,
                    pk_matches_count INTEGER DEFAULT 0,
                    pk_wins INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE (user_id, snapshot_date)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX idx_user_energy_snapshots_user ON user_energy_snapshots (user_id)
            """)
            cursor.execute("""
                CREATE INDEX idx_user_energy_snapshots_date ON user_energy_snapshots (snapshot_date)
            """)
            cursor.execute("""
                CREATE INDEX idx_energy_snapshot_date ON user_energy_snapshots (user_id, snapshot_date)
            """)
            
            conn.commit()
            print("✓ user_energy_snapshots 表创建成功")
        else:
            print("✓ user_energy_snapshots 表已存在")
            
            cursor.execute("""
                SELECT sql FROM sqlite_master 
                WHERE type='table' AND name='user_energy_snapshots'
            """)
            result = cursor.fetchone()
            current_sql = result[0] if result else ""
            
            columns_needed = [
                ("daily_horoscope_score", "INTEGER DEFAULT 0"),
                ("daily_horoscope_detail", "TEXT"),
                ("task_completion_score", "INTEGER DEFAULT 0"),
                ("task_completion_detail", "TEXT"),
                ("total_energy_score", "FLOAT DEFAULT 0.0"),
                ("energy_boost_applied", "FLOAT DEFAULT 1.0"),
                ("pk_matches_count", "INTEGER DEFAULT 0"),
                ("pk_wins", "INTEGER DEFAULT 0"),
            ]
            
            for col_name, col_def in columns_needed:
                if col_name not in current_sql:
                    try:
                        cursor.execute(f"ALTER TABLE user_energy_snapshots ADD COLUMN {col_name} {col_def}")
                        print(f"  ✓ 添加列: {col_name}")
                    except sqlite3.OperationalError as e:
                        print(f"  跳过列 {col_name}: {e}")
            
            conn.commit()
            
    except sqlite3.OperationalError as e:
        print(f"错误: {e}")
        conn.rollback()
    finally:
        conn.close()


def create_pk_transactions_table():
    """
    检查并创建 pk_transactions 表（PK交易记录表）
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if not check_table_exists(cursor, "pk_transactions"):
            print("创建 pk_transactions 表...")
            cursor.execute("""
                CREATE TABLE pk_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_no VARCHAR(50) NOT NULL,
                    user_id INTEGER NOT NULL,
                    match_id INTEGER,
                    transaction_type VARCHAR(50) NOT NULL,
                    transaction_subtype VARCHAR(50),
                    currency_type VARCHAR(20) DEFAULT 'fragment',
                    amount INTEGER DEFAULT 0,
                    balance_before INTEGER DEFAULT 0,
                    balance_after INTEGER DEFAULT 0,
                    related_match_no VARCHAR(50),
                    related_opponent_id INTEGER,
                    is_wager BOOLEAN DEFAULT 0,
                    is_winnings BOOLEAN DEFAULT 0,
                    is_loss BOOLEAN DEFAULT 0,
                    description VARCHAR(500),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (match_id) REFERENCES pk_matches (id),
                    FOREIGN KEY (related_opponent_id) REFERENCES users (id),
                    UNIQUE (transaction_no)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX idx_pk_transactions_no ON pk_transactions (transaction_no)
            """)
            cursor.execute("""
                CREATE INDEX idx_pk_transactions_user ON pk_transactions (user_id, created_at)
            """)
            cursor.execute("""
                CREATE INDEX idx_pk_transactions_match ON pk_transactions (match_id)
            """)
            cursor.execute("""
                CREATE INDEX idx_pk_transactions_type ON pk_transactions (transaction_type)
            """)
            cursor.execute("""
                CREATE INDEX idx_pk_transactions_created ON pk_transactions (created_at)
            """)
            
            conn.commit()
            print("✓ pk_transactions 表创建成功")
        else:
            print("✓ pk_transactions 表已存在")
            
            cursor.execute("""
                SELECT sql FROM sqlite_master 
                WHERE type='table' AND name='pk_transactions'
            """)
            result = cursor.fetchone()
            current_sql = result[0] if result else ""
            
            columns_needed = [
                ("transaction_type", "VARCHAR(50) NOT NULL DEFAULT 'wager'"),
                ("transaction_subtype", "VARCHAR(50)"),
                ("currency_type", "VARCHAR(20) DEFAULT 'fragment'"),
                ("amount", "INTEGER DEFAULT 0"),
                ("balance_before", "INTEGER DEFAULT 0"),
                ("balance_after", "INTEGER DEFAULT 0"),
                ("related_match_no", "VARCHAR(50)"),
                ("related_opponent_id", "INTEGER"),
                ("is_wager", "BOOLEAN DEFAULT 0"),
                ("is_winnings", "BOOLEAN DEFAULT 0"),
                ("is_loss", "BOOLEAN DEFAULT 0"),
                ("description", "VARCHAR(500)"),
            ]
            
            for col_name, col_def in columns_needed:
                if col_name not in current_sql:
                    try:
                        cursor.execute(f"ALTER TABLE pk_transactions ADD COLUMN {col_name} {col_def}")
                        print(f"  ✓ 添加列: {col_name}")
                    except sqlite3.OperationalError as e:
                        print(f"  跳过列 {col_name}: {e}")
            
            conn.commit()
            
    except sqlite3.OperationalError as e:
        print(f"错误: {e}")
        conn.rollback()
    finally:
        conn.close()


def create_pk_challenge_purchases_table():
    """
    检查并创建 pk_challenge_purchases 表（PK挑战次数购买记录表）
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if not check_table_exists(cursor, "pk_challenge_purchases"):
            print("创建 pk_challenge_purchases 表...")
            cursor.execute("""
                CREATE TABLE pk_challenge_purchases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    purchase_no VARCHAR(50) NOT NULL,
                    user_id INTEGER NOT NULL,
                    challenges_purchased INTEGER DEFAULT 1,
                    price_per_challenge INTEGER DEFAULT 0,
                    total_price INTEGER DEFAULT 0,
                    currency_type VARCHAR(20) DEFAULT 'point',
                    payment_order_id INTEGER,
                    is_paid BOOLEAN DEFAULT 0,
                    paid_at TIMESTAMP,
                    purchase_date VARCHAR(20) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (payment_order_id) REFERENCES payment_orders (id),
                    UNIQUE (purchase_no)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX idx_pk_challenge_purchases_no ON pk_challenge_purchases (purchase_no)
            """)
            cursor.execute("""
                CREATE INDEX idx_pk_purchases_user ON pk_challenge_purchases (user_id, purchase_date)
            """)
            cursor.execute("""
                CREATE INDEX idx_pk_challenge_purchases_paid ON pk_challenge_purchases (is_paid)
            """)
            cursor.execute("""
                CREATE INDEX idx_pk_challenge_purchases_created ON pk_challenge_purchases (created_at)
            """)
            
            conn.commit()
            print("✓ pk_challenge_purchases 表创建成功")
        else:
            print("✓ pk_challenge_purchases 表已存在")
            
            cursor.execute("""
                SELECT sql FROM sqlite_master 
                WHERE type='table' AND name='pk_challenge_purchases'
            """)
            result = cursor.fetchone()
            current_sql = result[0] if result else ""
            
            columns_needed = [
                ("challenges_purchased", "INTEGER DEFAULT 1"),
                ("price_per_challenge", "INTEGER DEFAULT 0"),
                ("total_price", "INTEGER DEFAULT 0"),
                ("currency_type", "VARCHAR(20) DEFAULT 'point'"),
                ("payment_order_id", "INTEGER"),
                ("is_paid", "BOOLEAN DEFAULT 0"),
                ("paid_at", "TIMESTAMP"),
                ("purchase_date", "VARCHAR(20)"),
            ]
            
            for col_name, col_def in columns_needed:
                if col_name not in current_sql:
                    try:
                        cursor.execute(f"ALTER TABLE pk_challenge_purchases ADD COLUMN {col_name} {col_def}")
                        print(f"  ✓ 添加列: {col_name}")
                    except sqlite3.OperationalError as e:
                        print(f"  跳过列 {col_name}: {e}")
            
            conn.commit()
            
    except sqlite3.OperationalError as e:
        print(f"错误: {e}")
        conn.rollback()
    finally:
        conn.close()


def create_user_pk_stats_table():
    """
    检查并创建 user_pk_stats 表（用户PK统计表）
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if not check_table_exists(cursor, "user_pk_stats"):
            print("创建 user_pk_stats 表...")
            cursor.execute("""
                CREATE TABLE user_pk_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    total_matches INTEGER DEFAULT 0,
                    total_wins INTEGER DEFAULT 0,
                    total_losses INTEGER DEFAULT 0,
                    total_draws INTEGER DEFAULT 0,
                    total_fragments_won INTEGER DEFAULT 0,
                    total_fragments_lost INTEGER DEFAULT 0,
                    net_fragments INTEGER DEFAULT 0,
                    current_win_streak INTEGER DEFAULT 0,
                    best_win_streak INTEGER DEFAULT 0,
                    highest_energy_used FLOAT DEFAULT 0.0,
                    highest_wager_won INTEGER DEFAULT 0,
                    random_match_count INTEGER DEFAULT 0,
                    friend_match_count INTEGER DEFAULT 0,
                    last_match_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE (user_id)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX idx_user_pk_stats_user ON user_pk_stats (user_id)
            """)
            
            conn.commit()
            print("✓ user_pk_stats 表创建成功")
        else:
            print("✓ user_pk_stats 表已存在")
            
            cursor.execute("""
                SELECT sql FROM sqlite_master 
                WHERE type='table' AND name='user_pk_stats'
            """)
            result = cursor.fetchone()
            current_sql = result[0] if result else ""
            
            columns_needed = [
                ("total_matches", "INTEGER DEFAULT 0"),
                ("total_wins", "INTEGER DEFAULT 0"),
                ("total_losses", "INTEGER DEFAULT 0"),
                ("total_draws", "INTEGER DEFAULT 0"),
                ("total_fragments_won", "INTEGER DEFAULT 0"),
                ("total_fragments_lost", "INTEGER DEFAULT 0"),
                ("net_fragments", "INTEGER DEFAULT 0"),
                ("current_win_streak", "INTEGER DEFAULT 0"),
                ("best_win_streak", "INTEGER DEFAULT 0"),
                ("highest_energy_used", "FLOAT DEFAULT 0.0"),
                ("highest_wager_won", "INTEGER DEFAULT 0"),
                ("random_match_count", "INTEGER DEFAULT 0"),
                ("friend_match_count", "INTEGER DEFAULT 0"),
                ("last_match_at", "TIMESTAMP"),
            ]
            
            for col_name, col_def in columns_needed:
                if col_name not in current_sql:
                    try:
                        cursor.execute(f"ALTER TABLE user_pk_stats ADD COLUMN {col_name} {col_def}")
                        print(f"  ✓ 添加列: {col_name}")
                    except sqlite3.OperationalError as e:
                        print(f"  跳过列 {col_name}: {e}")
            
            conn.commit()
            
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
        print("星盘能量PK竞技系统 - 数据库状态汇总")
        print("=" * 60)
        
        tables = [
            "user_daily_pk",
            "energy_boosts",
            "pk_match_invites",
            "pk_matches",
            "user_energy_snapshots",
            "pk_transactions",
            "pk_challenge_purchases",
            "user_pk_stats",
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
    print("数据库迁移脚本 - 星盘能量PK竞技系统")
    print("=" * 60)
    print(f"数据库路径: {DB_PATH}")
    print()
    
    create_user_daily_pk_table()
    print()
    
    create_energy_boosts_table()
    print()
    
    create_pk_match_invites_table()
    print()
    
    create_pk_matches_table()
    print()
    
    create_user_energy_snapshots_table()
    print()
    
    create_pk_transactions_table()
    print()
    
    create_pk_challenge_purchases_table()
    print()
    
    create_user_pk_stats_table()
    print()
    
    show_database_status()
    print()
    
    print("=" * 60)
    print("迁移完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
