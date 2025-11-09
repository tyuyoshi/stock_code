"""Main FastAPI Application"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from core.config import settings
from core.middleware import SecurityHeadersMiddleware, RequestSizeMiddleware
from core.rate_limiter import limiter, custom_rate_limit_exceeded_handler, RateLimits
from api.routers import stock_prices, companies, screening, compare, export, auth, watchlist, websocket

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

# Validate OAuth credentials on startup (skip in test environment)
if settings.environment not in ["test", "testing"]:
    if not settings.google_client_id or not settings.google_client_secret:
        raise ValueError(
            "Google OAuth credentials not configured. "
            "Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in environment."
        )

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Add request size limit middleware
app.add_middleware(RequestSizeMiddleware)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(stock_prices.router)
app.include_router(companies.router)
app.include_router(screening.router)
app.include_router(compare.router)
app.include_router(export.router)
app.include_router(watchlist.router)
app.include_router(websocket.router)


@app.get("/")
@limiter.limit(RateLimits.STANDARD)
async def root(request: Request):
    """Root endpoint"""
    return {"message": "Stock Code API", "version": "0.1.0"}


@app.head("/")
@limiter.limit(RateLimits.STANDARD)
async def root_head(request: Request):
    """Root endpoint for HEAD requests"""
    return {"message": "Stock Code API", "version": "0.1.0"}


@app.get("/health")
@limiter.exempt
async def health_check(request: Request):
    """Health check endpoint - exempt from rate limiting"""
    return JSONResponse(
        status_code=200,
        content={"status": "healthy", "service": "stock-code-api"},
    )


@app.head("/health")
@limiter.exempt
async def health_check_head(request: Request):
    """Health check endpoint for HEAD requests - exempt from rate limiting"""
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