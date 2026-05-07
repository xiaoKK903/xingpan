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
    帮我看下两个大模型的key是什么
    
    先查找项目中与“大模型 key”相关的配置或环境变量。
    
    在这个仓库里，两个大模型的 key 在 .env 里：
    
    DASHSCOPE_API_KEY=sk-556b657fe9d745539045879218f51920
    
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    
    DASHSCOPE_API_KEY: Optional[str] = None
    QWEN_MODEL: str = "qwen-max"
    
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_MODEL: str = "deepseek-v4-pro"
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    
    REDIS_URL: Optional[str] = None
    REDIS_DEFAULT_TTL: int = 1800


@lru_cache()
def get_settings():
    settings = Settings()
    return settings


settings = get_settings()
