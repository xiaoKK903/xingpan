from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
import bcrypt
import logging
from app.database import get_db
from app.models import User
from app.schemas import (
    UserCreate, 
    UserResponse, 
    UserLogin, 
    Token, 
    ApiResponse
)
from app.config import settings
from app.services.invite_service import (
    get_invite_code_by_code,
    create_invite_relation,
    process_share_reward,
    get_or_create_invite_code
)

logger = logging.getLogger(__name__)

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def get_password_hash(password: str) -> str:
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_raw = payload.get("sub")
        if user_id_raw is None:
            raise credentials_exception
        try:
            user_id = int(user_id_raw)
        except (ValueError, TypeError):
            raise credentials_exception
    except JWTError as e:
        print(f"JWT Error: {e}")
        raise credentials_exception
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="用户已被禁用")
    return current_user


def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    可选的用户获取函数，用于不需要强制登录的接口
    如果用户已登录则返回用户对象，否则返回 None
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None
    
    if not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header[7:]
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_raw = payload.get("sub")
        if user_id_raw is None:
            return None
        try:
            user_id = int(user_id_raw)
        except (ValueError, TypeError):
            return None
    except JWTError:
        return None
    
    user = db.query(User).filter(User.id == user_id).first()
    return user


@router.post("/register", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def register(
    request: Request,
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    if user_data.email:
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )
    
    inviter_code = None
    inviter = None
    if user_data.invite_code:
        inviter_code = get_invite_code_by_code(db, user_data.invite_code)
        if not inviter_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邀请码无效或已过期"
            )
        inviter = db.query(User).filter(User.id == inviter_code.user_id).first()
    
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password
    )
    db.add(new_user)
    db.flush()
    
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")
    
    invite_relation = None
    if inviter_code and inviter:
        invite_relation, error = create_invite_relation(
            db=db,
            inviter_id=inviter.id,
            invitee_id=new_user.id,
            invite_code=inviter_code.invite_code,
            ip=client_ip,
            device=user_agent
        )
        
        if invite_relation and invite_relation.is_valid:
            process_share_reward(db, invite_relation)
            logger.info(f"邀请关系创建成功并发放分享奖励: inviter_id={inviter.id}, invitee_id={new_user.id}")
        elif error:
            logger.warning(f"邀请关系创建失败: {error}")
    
    get_or_create_invite_code(db, new_user.id)
    
    db.commit()
    db.refresh(new_user)
    
    response_data = {
        "user": UserResponse.model_validate(new_user).model_dump()
    }
    
    if invite_relation:
        response_data["invite_info"] = {
            "inviter_username": inviter.username if inviter else None,
            "invite_code_used": invite_relation.invite_code_used,
            "is_valid": invite_relation.is_valid,
            "invalid_reason": invite_relation.invalid_reason
        }
    
    return ApiResponse(
        code=201,
        message="注册成功",
        data=response_data
    )


@router.post("/login", response_model=ApiResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户已被禁用"
        )
    
    access_token = create_access_token(data={"sub": user.id})
    token_data = Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )
    return ApiResponse(
        code=200,
        message="登录成功",
        data=token_data.model_dump()
    )


@router.get("/me", response_model=ApiResponse)
def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    return ApiResponse(
        code=200,
        message="success",
        data=UserResponse.model_validate(current_user).model_dump()
    )


@router.put("/me", response_model=ApiResponse)
def update_current_user(
    user_data: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    allowed_fields = ["email"]
    for field, value in user_data.items():
        if field in allowed_fields:
            setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    return ApiResponse(
        code=200,
        message="更新成功",
        data={"user": UserResponse.model_validate(current_user).model_dump()}
    )
