"""Application configuration using Pydantic BaseSettings."""
from typing import Optional, List, Union
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = Field(default="ROS GUI Backend API", env="APP_NAME")
    APP_VERSION: str = Field(default="2.0.0", env="APP_VERSION")
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # Server
    HOST: str = Field(default="127.0.0.1", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/ros_gui",
        env="DATABASE_URL"
    )
    DATABASE_ECHO: bool = Field(default=False, env="DATABASE_ECHO")
    
    # Redis
    REDIS_HOST: str = Field(default="127.0.0.1", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    REDIS_URL: Optional[str] = Field(default=None, env="REDIS_URL")
    
    # JWT
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production-use-env-var",
        env="SECRET_KEY"
    )
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["*"],
        env="CORS_ORIGINS"
    )
    
    # LLM Agent (for AI control)
    LLM_API_KEY: Optional[str] = Field(default=None, env="LLM_API_KEY")
    LLM_API_BASE: Optional[str] = Field(default=None, env="LLM_API_BASE")
    LLM_MODEL: str = Field(default="gpt-4", env="LLM_MODEL")
    LLM_ENABLED: bool = Field(default=False, env="LLM_ENABLED")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()

