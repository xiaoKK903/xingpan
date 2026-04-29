import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models import User
from app.routers.users import verify_password, get_password_hash

engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_database():
    db = SessionLocal()
    try:
        print("=== 数据库连接测试 ===")
        result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = [row[0] for row in result]
        print(f"数据库表: {tables}")
        
        users = db.query(User).all()
        print(f"\n=== 用户列表 ({len(users)} 个用户) ===")
        for user in users:
            print(f"  ID: {user.id}")
            print(f"  用户名: {user.username}")
            print(f"  邮箱: {user.email}")
            print(f"  活跃状态: {user.is_active}")
            print(f"  管理员: {user.is_superuser}")
            print(f"  密码哈希长度: {len(user.hashed_password)}")
            print("-" * 40)
        
        return users
    finally:
        db.close()

def test_password_verification():
    print("\n=== 密码验证测试 ===")
    
    test_password = "test123456"
    hashed = get_password_hash(test_password)
    print(f"原始密码: {test_password}")
    print(f"密码哈希: {hashed}")
    print(f"验证结果: {verify_password(test_password, hashed)}")
    
    wrong_password = "wrongpassword"
    print(f"\n错误密码验证结果: {verify_password(wrong_password, hashed)}")

if __name__ == "__main__":
    test_password_verification()
    users = test_database()
    
    print("\n=== 总结 ===")
    if len(users) == 0:
        print("数据库中没有用户，请先注册账号")
    else:
        print(f"数据库中有 {len(users)} 个用户")
        print("如果登录失败，请检查：")
        print("1. 用户名是否正确")
        print("2. 密码是否正确（注意大小写）")
        print("3. 后端服务是否正常运行")
