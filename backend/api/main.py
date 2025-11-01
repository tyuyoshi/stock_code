"""Main FastAPI Application"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from core.config import settings
from core.middleware import SecurityHeadersMiddleware, RequestSizeMiddleware
from core.rate_limiter import limiter, custom_rate_limit_exceeded_handler

app = FastAPI(
    title="Stock Code API",
    description="企業分析SaaSサービス API",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Add rate limiter to the app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, custom_rate_limit_exceeded_handler)

# CORS設定 - 環境に応じた設定を適用
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Validate secret key on startup
settings.validate_secret_key()

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Add request size limit middleware
app.add_middleware(RequestSizeMiddleware)


@app.get("/")
@limiter.limit("100/minute")
async def root(request: Request):
    """Root endpoint"""
    return {"message": "Stock Code API", "version": "0.1.0"}


@app.get("/health")
@limiter.exempt
async def health_check():
    """Health check endpoint - exempt from rate limiting"""
    return JSONResponse(
        status_code=200,
        content={"status": "healthy", "service": "stock-code-api"},
    )


@app.options("/{path:path}")
@limiter.exempt
async def options_handler(path: str):
    """Handle OPTIONS requests for CORS preflight"""
    return JSONResponse(
        status_code=200,
        content={"message": "OK"},
    )