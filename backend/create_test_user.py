import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, User
from app.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    existing_user = db.query(User).filter(User.username == "test").first()
    
    if existing_user:
        print("用户 'test' 已存在")
    else:
        password = "test123"
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        new_user = User(
            username="test",
            email="test@example.com",
            hashed_password=hashed.decode('utf-8'),
            is_active=True,
            is_superuser=False
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        print(f"用户 'test' 创建成功！")
        print(f"用户名: test")
        print(f"密码: test123")
        
except Exception as e:
    print(f"错误: {e}")
    db.rollback()
finally:
    db.close()
