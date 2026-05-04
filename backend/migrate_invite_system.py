"""
数据库迁移脚本 - 邀请好友系统
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "ai_customer_service.db"


def check_and_create_invite_tables():
    """
    检查并创建邀请系统相关的表
    """
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='invite_codes'
        """)
        
        if not cursor.fetchone():
            print("创建 invite_codes 表...")
            cursor.execute("""
                CREATE TABLE invite_codes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE,
                    invite_code VARCHAR(20) NOT NULL UNIQUE,
                    total_invites INTEGER DEFAULT 0,
                    valid_invites INTEGER DEFAULT 0,
                    paid_invites INTEGER DEFAULT 0,
                    total_rewards_earned INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX idx_invite_codes_user_id ON invite_codes (user_id)
            """)
            cursor.execute("""
                CREATE INDEX idx_invite_codes_invite_code ON invite_codes (invite_code)
            """)
            cursor.execute("""
                CREATE INDEX idx_invite_codes_is_active ON invite_codes (is_active)
            """)
            
            conn.commit()
            print("✓ invite_codes 表创建成功")
        else:
            print("✓ invite_codes 表已存在")
        
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='invite_relations'
        """)
        
        if not cursor.fetchone():
            print("创建 invite_relations 表...")
            cursor.execute("""
                CREATE TABLE invite_relations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    inviter_id INTEGER NOT NULL,
                    invitee_id INTEGER NOT NULL UNIQUE,
                    invite_code_used VARCHAR(20) NOT NULL,
                    register_ip VARCHAR(50),
                    is_register_completed BOOLEAN DEFAULT 0,
                    register_completed_at TIMESTAMP,
                    has_first_payment BOOLEAN DEFAULT 0,
                    first_payment_at TIMESTAMP,
                    first_payment_amount INTEGER DEFAULT 0,
                    is_valid BOOLEAN DEFAULT 1,
                    invalid_reason VARCHAR(200),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (inviter_id) REFERENCES users (id),
                    FOREIGN KEY (invitee_id) REFERENCES users (id)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX idx_invite_relations_inviter_id ON invite_relations (inviter_id)
            """)
            cursor.execute("""
                CREATE INDEX idx_invite_relations_invitee_id ON invite_relations (invitee_id)
            """)
            cursor.execute("""
                CREATE INDEX idx_invite_relations_invite_code_used ON invite_relations (invite_code_used)
            """)
            cursor.execute("""
                CREATE INDEX idx_invite_relations_is_register_completed ON invite_relations (is_register_completed)
            """)
            cursor.execute("""
                CREATE INDEX idx_invite_relations_has_first_payment ON invite_relations (has_first_payment)
            """)
            cursor.execute("""
                CREATE INDEX idx_invite_relations_is_valid ON invite_relations (is_valid)
            """)
            
            conn.commit()
            print("✓ invite_relations 表创建成功")
        else:
            print("✓ invite_relations 表已存在")
        
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='invite_rewards'
        """)
        
        if not cursor.fetchone():
            print("创建 invite_rewards 表...")
            cursor.execute("""
                CREATE TABLE invite_rewards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invite_relation_id INTEGER NOT NULL,
                    inviter_id INTEGER NOT NULL,
                    invitee_id INTEGER NOT NULL,
                    reward_stage VARCHAR(20) NOT NULL,
                    reward_type VARCHAR(20) NOT NULL,
                    reward_amount INTEGER DEFAULT 0,
                    reward_currency VARCHAR(20),
                    related_transaction_id INTEGER,
                    description VARCHAR(500),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (invite_relation_id) REFERENCES invite_relations (id),
                    FOREIGN KEY (inviter_id) REFERENCES users (id),
                    FOREIGN KEY (invitee_id) REFERENCES users (id)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX idx_invite_rewards_inviter_id ON invite_rewards (inviter_id)
            """)
            cursor.execute("""
                CREATE INDEX idx_invite_rewards_invitee_id ON invite_rewards (invitee_id)
            """)
            cursor.execute("""
                CREATE INDEX idx_invite_rewards_relation_id ON invite_rewards (invite_relation_id)
            """)
            cursor.execute("""
                CREATE INDEX idx_invite_rewards_reward_stage ON invite_rewards (reward_stage)
            """)
            
            conn.commit()
            print("✓ invite_rewards 表创建成功")
        else:
            print("✓ invite_rewards 表已存在")
        
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='invite_share_logs'
        """)
        
        if not cursor.fetchone():
            print("创建 invite_share_logs 表...")
            cursor.execute("""
                CREATE TABLE invite_share_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    share_type VARCHAR(20) DEFAULT 'general',
                    share_platform VARCHAR(20),
                    invite_code VARCHAR(20),
                    synastry_record_id INTEGER,
                    share_ip VARCHAR(50),
                    share_device TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX idx_invite_share_logs_user_id ON invite_share_logs (user_id)
            """)
            cursor.execute("""
                CREATE INDEX idx_invite_share_logs_invite_code ON invite_share_logs (invite_code)
            """)
            cursor.execute("""
                CREATE INDEX idx_invite_share_logs_share_type ON invite_share_logs (share_type)
            """)
            cursor.execute("""
                CREATE INDEX idx_invite_share_logs_created_at ON invite_share_logs (created_at)
            """)
            
            conn.commit()
            print("✓ invite_share_logs 表创建成功")
        else:
            print("✓ invite_share_logs 表已存在")
        
        cursor.execute("""
            SELECT sql FROM sqlite_master 
            WHERE type='table' AND name='users'
        """)
        result = cursor.fetchone()
        current_sql = result[0] if result else ""
        
        if "blind_box_tickets" not in current_sql:
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN blind_box_tickets INTEGER DEFAULT 0")
                print("✓ 添加列: blind_box_tickets")
                conn.commit()
            except sqlite3.OperationalError as e:
                print(f"  警告: 无法添加列 blind_box_tickets: {e}")
        else:
            print("✓ blind_box_tickets 列已存在")
            
    except sqlite3.OperationalError as e:
        print(f"错误: {e}")
        conn.rollback()
    finally:
        conn.close()


def main():
    print("=" * 60)
    print("数据库迁移脚本 - 邀请好友系统")
    print("=" * 60)
    print(f"数据库路径: {DB_PATH}")
    print()
    
    check_and_create_invite_tables()
    print()
    
    print("=" * 60)
    print("邀请系统迁移完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
