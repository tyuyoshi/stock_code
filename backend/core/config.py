"""Application Configuration"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # App settings
    app_name: str = "Stock Code API"
    debug: bool = False
    environment: str = "development"

    # Database
    database_url: Optional[str] = None
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # GCP settings
    gcp_project_id: Optional[str] = None
    gcp_region: str = "asia-northeast1"
    
    # API Keys
    edinet_api_key: Optional[str] = None
    jpx_api_key: Optional[str] = None
    
    # Redis
    redis_url: Optional[str] = None
    
    # JWT
    secret_key: str = "your-secret-key-here"  # Change in production
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()