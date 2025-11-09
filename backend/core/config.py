"""Application Configuration"""

import os
from typing import Optional, List, Union
from pydantic import ConfigDict, field_validator
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
    cors_origins: Union[str, List[str]] = "http://localhost:3000,http://localhost:8000"
    cors_allow_credentials: bool = True
    cors_allow_methods: Union[str, List[str]] = "GET,POST,PUT,DELETE,OPTIONS"
    cors_allow_headers: Union[str, List[str]] = "*"
    
    # Security settings
    api_rate_limit_per_minute: int = 60
    api_rate_limit_per_hour: int = 1000
    api_rate_limit_per_day: int = 10000
    
    # Security headers
    security_headers_enabled: bool = True
    
    # Google OAuth 2.0
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    google_redirect_uri: str = "http://localhost:8000/api/v1/auth/google/callback"
    
    # Session settings
    session_expire_days: int = 7
    session_cookie_name: str = "stockcode_session"
    session_cookie_httponly: bool = True
    session_cookie_secure: bool = False
    session_cookie_samesite: str = "lax"
    session_cookie_domain: Optional[str] = "localhost"  # localhost for dev, None for production
    session_cookie_path: str = "/"
    
    # Frontend URL
    frontend_url: str = "http://localhost:3000"

    # Yahoo Finance Rate Limiting
    yahoo_finance_max_tokens: int = 100
    yahoo_finance_refill_rate: float = 0.5  # tokens/second (30/min, 1800/hour)
    yahoo_finance_rate_limit_key: str = "rate_limit:yahoo_api"

    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v
    
    @field_validator('cors_allow_methods', mode='before')
    @classmethod
    def parse_cors_methods(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse CORS methods from string or list"""
        if isinstance(v, str):
            return [method.strip() for method in v.split(',') if method.strip()]
        return v
    
    @field_validator('cors_allow_headers', mode='before')
    @classmethod
    def parse_cors_headers(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse CORS headers from string or list"""
        if isinstance(v, str):
            if v == "*":
                return ["*"]
            return [header.strip() for header in v.split(',') if header.strip()]
        return v
    
    def get_cors_origins(self) -> List[str]:
        """Get CORS allowed origins based on environment"""
        # Ensure cors_origins is a list
        origins = self.cors_origins if isinstance(self.cors_origins, list) else [self.cors_origins]
        
        if self.environment == "production":
            # In production, only allow specific domains
            return origins
        elif self.environment == "staging":
            # In staging, allow staging domains
            return origins + ["https://staging.stockcode.com"]
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



settings = Settings()