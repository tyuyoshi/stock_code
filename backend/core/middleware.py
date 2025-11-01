"""Security middleware for FastAPI application"""

from fastapi import Request
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        if settings.security_headers_enabled:
            # Prevent MIME type sniffing
            response.headers["X-Content-Type-Options"] = "nosniff"
            
            # Prevent clickjacking
            response.headers["X-Frame-Options"] = "DENY"
            
            # Enable browser XSS protection
            response.headers["X-XSS-Protection"] = "1; mode=block"
            
            # Content Security Policy
            if settings.environment == "production":
                response.headers["Content-Security-Policy"] = (
                    "default-src 'self'; "
                    "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
                    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                    "img-src 'self' data: https:; "
                    "font-src 'self' data: https://fonts.gstatic.com; "
                    "connect-src 'self' https://api.stockcode.com"
                )
            
            # Force HTTPS in production
            if settings.environment in ["production", "staging"]:
                response.headers["Strict-Transport-Security"] = (
                    "max-age=31536000; includeSubDomains; preload"
                )
            
            # Referrer policy
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            
            # Permissions policy (formerly Feature Policy)
            response.headers["Permissions-Policy"] = (
                "geolocation=(), microphone=(), camera=()"
            )
        
        return response


class RequestSizeMiddleware(BaseHTTPMiddleware):
    """Limit request body size to prevent DoS attacks"""
    
    MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB
    
    async def dispatch(self, request: Request, call_next):
        if request.headers.get("content-length"):
            content_length = int(request.headers["content-length"])
            if content_length > self.MAX_REQUEST_SIZE:
                return Response(
                    content="Request body too large",
                    status_code=413
                )
        
        response = await call_next(request)
        return response