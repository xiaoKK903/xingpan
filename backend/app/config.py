from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from functools import lru_cache
import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = os.path.join(BASE_DIR, ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    PROJECT_NAME: str = "AI智能客服系统"
    VERSION: str = "1.0.0"
    
    DATABASE_URL: str = "sqlite:///./ai_customer_service.db"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    
    DASHSCOPE_API_KEY: Optional[str] = None
    QWEN_MODEL: str = "qwen-max"
    
    REDIS_URL: Optional[str] = None
    REDIS_DEFAULT_TTL: int = 1800


@lru_cache()
def get_settings():
    settings = Settings()
    return settings


settings = get_settings()
