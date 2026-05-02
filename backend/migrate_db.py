"""
数据库迁移脚本 - 添加能量气象站所需的新列和表
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "ai_customer_service.db"


def migrate_users_table():
    """
    为 users 表添加新列：
    - stardust_fragment_balance (星元碎片余额)
    - stardust_point_balance (星尘积分余额)
    """
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT sql FROM sqlite_master 
            WHERE type='table' AND name='users'
        """)
        result = cursor.fetchone()
        current_sql = result[0] if result else ""
        
        columns_to_add = []
        if "stardust_fragment_balance" not in current_sql:
            columns_to_add.append(
                "ALTER TABLE users ADD COLUMN stardust_fragment_balance INTEGER DEFAULT 0"
            )
        if "stardust_point_balance" not in current_sql:
            columns_to_add.append(
                "ALTER TABLE users ADD COLUMN stardust_point_balance INTEGER DEFAULT 0"
            )
        
        for sql in columns_to_add:
            print(f"执行: {sql}")
            cursor.execute(sql)
        
        conn.commit()
        
        if columns_to_add:
            print(f"✓ users 表迁移完成，添加了 {len(columns_to_add)} 个新列")
        else:
            print("✓ users 表已经是最新的")
            
    except sqlite3.OperationalError as e:
        print(f"警告: {e}")
        conn.rollback()
    finally:
        conn.close()


def check_and_create_mission_completions_table():
    """
    检查并创建 mission_completions 表（如果不存在）
    """
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='mission_completions'
        """)
        
        if not cursor.fetchone():
            print("创建 mission_completions 表...")
            cursor.execute("""
                CREATE TABLE mission_completions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    mission_id VARCHAR(100) NOT NULL,
                    mission_type VARCHAR(50),
                    mission_title VARCHAR(200),
                    completion_key VARCHAR(200) UNIQUE NOT NULL,
                    reward_amount INTEGER DEFAULT 0,
                    currency_type VARCHAR(20) DEFAULT 'fragment',
                    transaction_id INTEGER,
                    proof_text TEXT,
                    completion_data TEXT,
                    is_bonus BOOLEAN DEFAULT 0,
                    bonus_reason VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (transaction_id) REFERENCES stardust_transactions (id)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX idx_mission_completions_user_id 
                ON mission_completions (user_id)
            """)
            cursor.execute("""
                CREATE UNIQUE INDEX idx_mission_completions_completion_key 
                ON mission_completions (completion_key)
            """)
            cursor.execute("""
                CREATE INDEX idx_mission_completions_created_at 
                ON mission_completions (created_at)
            """)
            
            conn.commit()
            print("✓ mission_completions 表创建成功")
        else:
            print("✓ mission_completions 表已存在")
            
            cursor.execute("""
                SELECT sql FROM sqlite_master 
                WHERE type='table' AND name='mission_completions'
            """)
            result = cursor.fetchone()
            current_sql = result[0] if result else ""
            
            columns_needed = [
                ("is_bonus", "BOOLEAN DEFAULT 0"),
                ("bonus_reason", "VARCHAR(100)"),
                ("completion_key", "VARCHAR(200) UNIQUE NOT NULL"),
                ("currency_type", "VARCHAR(20) DEFAULT 'fragment'"),
                ("transaction_id", "INTEGER"),
            ]
            
            for col_name, col_def in columns_needed:
                if col_name not in current_sql:
                    try:
                        cursor.execute(f"ALTER TABLE mission_completions ADD COLUMN {col_name} {col_def}")
                        print(f"  ✓ 添加列: {col_name}")
                    except sqlite3.OperationalError as e:
                        print(f"  警告: 无法添加列 {col_name}: {e}")
            
            conn.commit()
            
    except sqlite3.OperationalError as e:
        print(f"错误: {e}")
        conn.rollback()
    finally:
        conn.close()


def check_and_create_stardust_transactions_table():
    """
    检查并创建 stardust_transactions 表（如果不存在）
    """
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='stardust_transactions'
        """)
        
        if not cursor.fetchone():
            print("创建 stardust_transactions 表...")
            cursor.execute("""
                CREATE TABLE stardust_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    transaction_type VARCHAR(50) NOT NULL,
                    currency_type VARCHAR(20) DEFAULT 'fragment',
                    amount INTEGER DEFAULT 0,
                    balance_before INTEGER DEFAULT 0,
                    balance_after INTEGER DEFAULT 0,
                    related_type VARCHAR(50),
                    related_id VARCHAR(100),
                    related_ref VARCHAR(200),
                    description VARCHAR(500),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX idx_stardust_transactions_user_id 
                ON stardust_transactions (user_id)
            """)
            cursor.execute("""
                CREATE INDEX idx_stardust_transactions_created_at 
                ON stardust_transactions (created_at)
            """)
            cursor.execute("""
                CREATE INDEX idx_stardust_transactions_currency_type 
                ON stardust_transactions (currency_type)
            """)
            
            conn.commit()
            print("✓ stardust_transactions 表创建成功")
        else:
            print("✓ stardust_transactions 表已存在")
            
            cursor.execute("""
                SELECT sql FROM sqlite_master 
                WHERE type='table' AND name='stardust_transactions'
            """)
            result = cursor.fetchone()
            current_sql = result[0] if result else ""
            
            columns_needed = [
                ("currency_type", "VARCHAR(20) DEFAULT 'fragment'"),
                ("related_ref", "VARCHAR(200)"),
            ]
            
            for col_name, col_def in columns_needed:
                if col_name not in current_sql:
                    try:
                        cursor.execute(f"ALTER TABLE stardust_transactions ADD COLUMN {col_name} {col_def}")
                        print(f"  ✓ 添加列: {col_name}")
                    except sqlite3.OperationalError as e:
                        print(f"  警告: 无法添加列 {col_name}: {e}")
            
            conn.commit()
            
    except sqlite3.OperationalError as e:
        print(f"错误: {e}")
        conn.rollback()
    finally:
        conn.close()


def check_and_create_energy_contributions_table():
    """
    检查并创建 energy_contributions 表（如果不存在）
    """
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='energy_contributions'
        """)
        
        if not cursor.fetchone():
            print("创建 energy_contributions 表...")
            cursor.execute("""
                CREATE TABLE energy_contributions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    contribution_type VARCHAR(50) NOT NULL,
                    planet_type VARCHAR(50),
                    planet_name VARCHAR(50),
                    energy_amount FLOAT DEFAULT 0.0,
                    energy_multiplier FLOAT DEFAULT 1.0,
                    target_scope VARCHAR(20) DEFAULT 'global',
                    target_dimension VARCHAR(50),
                    duration_minutes INTEGER DEFAULT 30,
                    expires_at TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    cost_stardust INTEGER DEFAULT 0,
                    contribution_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX idx_energy_contributions_user_id 
                ON energy_contributions (user_id)
            """)
            cursor.execute("""
                CREATE INDEX idx_energy_contributions_is_active 
                ON energy_contributions (is_active)
            """)
            cursor.execute("""
                CREATE INDEX idx_energy_contributions_expires_at 
                ON energy_contributions (expires_at)
            """)
            
            conn.commit()
            print("✓ energy_contributions 表创建成功")
        else:
            print("✓ energy_contributions 表已存在")
            
    except sqlite3.OperationalError as e:
        print(f"错误: {e}")
        conn.rollback()
    finally:
        conn.close()


def check_and_create_energy_mission_tables():
    """
    检查并创建能量任务相关的表
    """
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='energy_missions'
        """)
        
        if not cursor.fetchone():
            print("创建 energy_missions 表...")
            cursor.execute("""
                CREATE TABLE energy_missions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mission_type VARCHAR(50) NOT NULL,
                    title VARCHAR(200) NOT NULL,
                    description TEXT,
                    trigger_condition VARCHAR(100),
                    trigger_aspect VARCHAR(50),
                    trigger_planet VARCHAR(50),
                    target_dimension VARCHAR(50),
                    difficulty VARCHAR(20) DEFAULT 'medium',
                    base_reward INTEGER DEFAULT 10,
                    max_participants INTEGER DEFAULT 100,
                    participant_count INTEGER DEFAULT 0,
                    energy_contributed FLOAT DEFAULT 0.0,
                    status VARCHAR(20) DEFAULT 'active',
                    start_at TIMESTAMP,
                    end_at TIMESTAMP,
                    duration_minutes INTEGER DEFAULT 30,
                    mission_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            print("✓ energy_missions 表创建成功")
        else:
            print("✓ energy_missions 表已存在")
        
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='mission_participations'
        """)
        
        if not cursor.fetchone():
            print("创建 mission_participations 表...")
            cursor.execute("""
                CREATE TABLE mission_participations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    mission_id INTEGER NOT NULL,
                    status VARCHAR(20) DEFAULT 'joined',
                    energy_contributed FLOAT DEFAULT 0.0,
                    contribution_type VARCHAR(50),
                    reward_earned INTEGER DEFAULT 0,
                    reward_claimed BOOLEAN DEFAULT 0,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    participation_data TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (mission_id) REFERENCES energy_missions (id)
                )
            """)
            conn.commit()
            print("✓ mission_participations 表创建成功")
        else:
            print("✓ mission_participations 表已存在")
            
    except sqlite3.OperationalError as e:
        print(f"错误: {e}")
        conn.rollback()
    finally:
        conn.close()


def main():
    print("=" * 60)
    print("数据库迁移脚本 - 能量气象站系统")
    print("=" * 60)
    print(f"数据库路径: {DB_PATH}")
    print()
    
    migrate_users_table()
    print()
    
    check_and_create_stardust_transactions_table()
    print()
    
    check_and_create_mission_completions_table()
    print()
    
    check_and_create_energy_contributions_table()
    print()
    
    check_and_create_energy_mission_tables()
    print()
    
    print("=" * 60)
    print("迁移完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
