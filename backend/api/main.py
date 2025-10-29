"""Main FastAPI Application"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI(
    title="Stock Code API",
    description="企業分析SaaSサービス API",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS設定
# TODO: Issue #30 - 本番環境では環境変数から特定のオリジンのみ許可
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 開発環境のみ。本番では ["https://yourdomain.com"] のように特定
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Stock Code API", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse(
        status_code=200,
        content={"status": "healthy", "service": "stock-code-api"},
    )