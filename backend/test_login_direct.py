"""直接测试登录函数"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models import User
from app.routers.users import verify_password, create_access_token
from app.schemas import UserResponse, Token, ApiResponse
from datetime import datetime

print("=" * 60)
print("直接测试登录流程")
print("=" * 60)

engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

db = SessionLocal()

try:
    print(f"\n1. 查找用户 'test'...")
    user = db.query(User).filter(User.username == 'test').first()
    
    if user:
        print(f"   ✓ 找到用户: {user.username}")
        print(f"   - ID: {user.id}")
        print(f"   - 邮箱: {user.email}")
        print(f"   - is_active: {user.is_active}")
        print(f"   - is_superuser: {user.is_superuser}")
        
        print(f"\n2. 验证密码 'test123'...")
        password_ok = verify_password('test123', user.hashed_password)
        print(f"   密码验证结果: {password_ok}")
        
        if password_ok:
            print(f"\n3. 生成 Token...")
            try:
                access_token = create_access_token(data={"sub": user.id})
                print(f"   ✓ Token 生成成功: {access_token[:50]}...")
                
                print(f"\n4. 构建响应...")
                token_data = Token(
                    access_token=access_token,
                    token_type="bearer",
                    user=UserResponse.model_validate(user)
                )
                
                response = ApiResponse(
                    code=200,
                    message="登录成功",
                    data=token_data.model_dump()
                )
                
                print(f"   ✓ 响应构建成功")
                print(f"   - code: {response.code}")
                print(f"   - message: {response.message}")
                print(f"   - user: {response.data.get('user', {}).get('username')}")
                
            except Exception as e:
                print(f"   ✗ Token 生成失败: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"   ✗ 密码验证失败")
            
            print(f"\n尝试使用其他常见密码...")
            common_passwords = ['123456', 'password', 'admin', 'admin123', 'test']
            for pwd in common_passwords:
                if verify_password(pwd, user.hashed_password):
                    print(f"   ✓ 找到正确密码: {pwd}")
                    break
            else:
                print(f"   ✗ 常见密码都不匹配")
    else:
        print(f"   ✗ 未找到用户 'test'")
        
        print(f"\n查找所有用户...")
        users = db.query(User).all()
        print(f"   共找到 {len(users)} 个用户:")
        for u in users:
            print(f"   - {u.username} (ID: {u.id}, active: {u.is_active})")
            
except Exception as e:
    print(f"\n✗ 错误: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
