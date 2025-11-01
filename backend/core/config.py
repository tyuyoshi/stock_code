"""Application Configuration"""

import os
from typing import Optional, List
from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )

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
    secret_key: str = "your-secret-key-here"  # TODO: Issue #30 - 本番環境では必ず変更（openssl rand -hex 32 で生成）
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    
    # CORS settings
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    cors_allow_headers: List[str] = ["*"]
    
    # Security settings
    api_rate_limit_per_minute: int = 60
    api_rate_limit_per_hour: int = 1000
    api_rate_limit_per_day: int = 10000
    
    # Security headers
    security_headers_enabled: bool = True

    def get_cors_origins(self) -> List[str]:
        """Get CORS allowed origins based on environment"""
        if self.environment == "production":
            # In production, only allow specific domains
            return self.cors_origins
        elif self.environment == "staging":
            # In staging, allow staging domains
            return self.cors_origins + ["https://staging.stockcode.com"]
        else:
            # In development, allow all origins (use with caution)
            return ["*"]
    
    def validate_secret_key(self) -> bool:
        """Validate that secret key is not default in production"""
        if self.environment == "production" and self.secret_key == "your-secret-key-here":
            raise ValueError(
                "SECRET_KEY must be changed in production! "
                "Generate with: openssl rand -hex 32"
            )
        return True

    @classmethod
    def parse_cors_origins(cls, v: any) -> List[str]:
        """Parse CORS origins from environment variable"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


settings = Settings()