"""
重置用户密码脚本 - 使用 bcrypt
"""

import sqlite3
from pathlib import Path
from datetime import datetime
import bcrypt

DB_PATH = Path(__file__).parent / "ai_customer_service.db"


def get_password_hash(password: str) -> str:
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def reset_user_password(username, new_password):
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        hashed = get_password_hash(new_password)
        
        cursor.execute("""
            UPDATE users 
            SET hashed_password = ?, updated_at = ?
            WHERE username = ?
        """, (hashed, datetime.now(), username))
        
        if cursor.rowcount > 0:
            conn.commit()
            print(f"✓ 用户 '{username}' 密码已重置为: {new_password}")
            return True
        else:
            print(f"✗ 未找到用户 '{username}'")
            return False
            
    except sqlite3.OperationalError as e:
        print(f"错误: {e}")
        return False
    finally:
        conn.close()


def create_test_user(username, password, email=None, is_superuser=False):
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        hashed = get_password_hash(password)
        now = datetime.now()
        
        cursor.execute("""
            SELECT id FROM users WHERE username = ?
        """, (username,))
        
        if cursor.fetchone():
            print(f"用户 '{username}' 已存在，尝试重置密码...")
            return reset_user_password(username, password)
        
        cursor.execute("""
            INSERT INTO users (
                username, email, hashed_password, is_active, is_superuser,
                stardust_fragment_balance, stardust_point_balance,
                created_at, updated_at
            ) VALUES (?, ?, ?, 1, ?, 100, 50, ?, ?)
        """, (username, email or f"{username}@test.com", hashed, is_superuser, now, now))
        
        conn.commit()
        print(f"✓ 创建测试用户成功:")
        print(f"  用户名: {username}")
        print(f"  密码: {password}")
        print(f"  管理员: {'是' if is_superuser else '否'}")
        print(f"  星元碎片: 100")
        print(f"  高阶星尘: 50")
        return True
            
    except sqlite3.OperationalError as e:
        print(f"错误: {e}")
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    print("="*60)
    print("  密码重置脚本")
    print("="*60)
    print()
    
    print("重置现有用户密码:")
    print("-"*40)
    
    users_to_reset = [
        ("testuser", "test123"),
        ("aaawhz123", "aaawhz123"),
        ("admin", "admin123"),
        ("test", "test123"),
    ]
    
    for username, password in users_to_reset:
        reset_user_password(username, password)
    
    print()
    print("创建新测试用户:")
    print("-"*40)
    
    create_test_user("demo", "demo123", "demo@test.com", False)
    create_test_user("admin2", "admin123", "admin2@test.com", True)
    
    print()
    print("="*60)
    print("  完成！可用的测试账号:")
    print("="*60)
    print()
    print("  普通用户:")
    print("    - 用户名: testuser / 密码: test123")
    print("    - 用户名: aaawhz123 / 密码: aaawhz123")
    print("    - 用户名: test / 密码: test123")
    print("    - 用户名: demo / 密码: demo123 (新建)")
    print()
    print("  管理员:")
    print("    - 用户名: admin / 密码: admin123")
    print("    - 用户名: admin2 / 密码: admin123 (新建)")
    print()
