import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import User
from app.config import settings

engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

ADMIN_USERNAME = "admin"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin123"

def create_admin():
    db = SessionLocal()
    try:
        existing_admin = db.query(User).filter(User.username == ADMIN_USERNAME).first()
        
        if existing_admin:
            print(f"管理员账号 '{ADMIN_USERNAME}' 已存在")
            if not existing_admin.is_superuser:
                existing_admin.is_superuser = True
                db.commit()
                print(f"已将 '{ADMIN_USERNAME}' 升级为管理员")
            return
        
        password_bytes = ADMIN_PASSWORD.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        hashed_password = hashed.decode('utf-8')
        
        admin = User(
            username=ADMIN_USERNAME,
            email=ADMIN_EMAIL,
            hashed_password=hashed_password,
            is_active=True,
            is_superuser=True
        )
        
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        print("=" * 50)
        print("管理员账号创建成功！")
        print("=" * 50)
        print(f"用户名: {ADMIN_USERNAME}")
        print(f"密码: {ADMIN_PASSWORD}")
        print(f"邮箱: {ADMIN_EMAIL}")
        print("=" * 50)
        print("请登录后及时修改密码！")
        print("=" * 50)
        
    except Exception as e:
        print(f"创建失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()
