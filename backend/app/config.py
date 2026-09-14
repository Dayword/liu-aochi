"""全局配置：环境变量优先，未设置则使用默认值。"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DB_URL: str = "mysql+pymysql://root:root@127.0.0.1:3306/code_adventurer?charset=utf8mb4"
    REDIS_URL: str = "redis://127.0.0.1:6379/0"
    SECRET_KEY: str = "code-adventurer-dev-secret-change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    # AI（留空 = 离线演示模式）
    AI_BASE_URL: str = ""
    AI_API_KEY: str = ""
    AI_MODEL: str = ""
    AI_TIMEOUT: int = 30

    # 代码沙箱
    CODE_RUN_TIMEOUT: int = 5
    CODE_MAX_SIZE: int = 64 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
