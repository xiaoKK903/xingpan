"""
查看数据库中的用户信息
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "ai_customer_service.db"


def show_users():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id, username, email, is_superuser, 
                   stardust_fragment_balance, stardust_point_balance,
                   created_at
            FROM users
        """)
        
        users = cursor.fetchall()
        
        print("="*60)
        print("  数据库中的用户列表")
        print("="*60)
        print()
        
        for user in users:
            print(f"ID: {user[0]}")
            print(f"  用户名: {user[1]}")
            print(f"  邮箱: {user[2] or '未设置'}")
            print(f"  管理员: {'是' if user[3] else '否'}")
            print(f"  星元碎片: {user[4] or 0}")
            print(f"  高阶星尘: {user[5] or 0}")
            print(f"  创建时间: {user[6]}")
            print()
        
        print("="*60)
        print(f"  总计 {len(users)} 个用户")
        print("="*60)
        
    except sqlite3.OperationalError as e:
        print(f"错误: {e}")
    finally:
        conn.close()


def check_password_hash():
    """查看密码哈希字段"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        
        print("\n" + "="*60)
        print("  users 表结构")
        print("="*60)
        
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
            
    except sqlite3.OperationalError as e:
        print(f"错误: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    show_users()
    check_password_hash()
