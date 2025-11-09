# Stock Code Codebase Understanding - Complete Analysis

## Executive Summary

Stock Code is a Japanese financial analysis SaaS platform with:
- **Backend**: FastAPI (Python 3.11+) with PostgreSQL
- **Frontend**: Next.js 14 with TypeScript and Tailwind CSS
- **Infrastructure**: GCP (Cloud Run, Cloud SQL, Cloud Storage) with Docker
- **Key Data Sources**: EDINET API, Yahoo Finance, Google OAuth 2.0

**Current Development Status** (As of 2025/11/09):
- 86 open issues (down from 97 after recent cleanup)
- 45 closed issues (comprehensive cleanup completed)
- Next priority: Issue #126 (Yahoo Finance API Rate Limiting)

## Project Structure

```
stock_code/
├── backend/               # FastAPI application
│   ├── api/              # API endpoints and routers
│   │   ├── routers/      # API route handlers
│   │   │   ├── auth.py                    # Google OAuth 2.0
│   │   │   ├── websocket.py               # WebSocket real-time prices
│   │   │   ├── stock_prices.py            # Stock price REST APIs
│   │   │   ├── companies.py               # Company CRUD
│   │   │   ├── screening.py               # Screening/filtering
│   │   │   ├── compare.py                 # Company comparison
│   │   │   ├── watchlist.py               # Portfolio tracking
│   │   │   └── export.py                  # CSV/Excel export
│   │   └── main.py                        # App initialization
│   ├── core/             # Core configuration
│   │   ├── config.py                      # Settings (environment-based)
│   │   ├── database.py                    # DB connection
│   │   ├── dependencies.py                # DI container
│   │   ├── rate_limiter.py                # API rate limiting (slowapi)
│   │   ├── auth.py                        # Auth utilities
│   │   ├── sessions.py                    # Redis session management
│   │   ├── security.py                    # Security headers, CORS
│   │   ├── middleware.py                  # HTTP middleware
│   │   └── constants.py                   # App constants
│   ├── models/           # SQLAlchemy ORM models
│   │   ├── company.py                     # Company master data
│   │   ├── financial.py                   # Financial data (statements, prices, indicators)
│   │   ├── user.py                        # User accounts with investment profile
│   │   └── watchlist.py                   # Watchlist and portfolio items
│   ├── services/         # Business logic services
│   │   ├── yahoo_finance_client.py        # Yahoo Finance data collection ⭐
│   │   ├── data_processor.py              # XBRL parsing, data aggregation
│   │   ├── financial_indicators.py        # 60+ financial metrics
│   │   ├── edinet_client.py               # EDINET API integration
│   │   ├── company_service.py             # Company business logic
│   │   ├── screening_service.py           # Screening/filtering logic
│   │   ├── compare_service.py             # Comparison logic
│   │   ├── export_service.py              # Export formatting
│   │   ├── google_oauth.py                # Google OAuth provider
│   │   ├── notification.py                # Slack/Email notifications
│   │   ├── trading_calendar.py            # Japanese trading holidays
│   │   └── xbrl_parser.py                 # XBRL financial document parsing
│   ├── batch/            # Batch job scripts
│   │   ├── daily_update.py                # Daily stock price update job ⭐
│   │   └── quarterly_update.py            # Quarterly financial data update
│   ├── tests/            # Comprehensive test suite (78% coverage)
│   │   ├── test_*.py                      # Unit and integration tests
│   │   └── conftest.py                    # Pytest fixtures and DI
│   ├── alembic/          # Database migration tool
│   ├── scripts/          # Utility scripts
│   └── requirements.txt   # Python dependencies
├── frontend/             # Next.js 14 application
│   └── src/
│       ├── app/          # App Router pages
│       ├── components/   # React components
│       └── lib/          # Utilities and API clients
├── infrastructure/       # GCP Terraform, Docker config
└── docs/                # Documentation
```

## Key Technical Implementations

### 1. Yahoo Finance Integration ⭐ (Issue #8 - COMPLETED)

**File**: `backend/services/yahoo_finance_client.py` (412 lines)

**Key Features**:
- Japanese stock ticker formatting (.T suffix)
- Redis caching with 5-minute TTL
- Basic rate limiting (0.5s delay between requests)
- Async bulk price fetching
- Error handling with graceful degradation

**Methods**:
```python
YahooFinanceClient:
  __init__(redis_client: Optional[Redis])
  _format_ticker(ticker_symbol: str) -> str
  _get_cache_key(ticker: str, data_type: str) -> str
  async _get_cached_data(cache_key: str) -> Optional[Dict]
  async _set_cached_data(cache_key: str, data: Dict)
  async get_stock_price(ticker_symbol: str, use_cache: bool) -> Optional[Dict]
  async get_historical_data(ticker_symbol: str, period: str) -> Optional[Dict]
  async get_company_info(ticker_symbol: str) -> Optional[Dict]
  async get_dividends(ticker_symbol: str) -> Optional[Dict]
  async get_stock_splits(ticker_symbol: str) -> Optional[Dict]
  async bulk_fetch_prices(tickers: List[str]) -> Dict[str, Dict]
```

**Current Rate Limiting**:
- Simple fixed delay: 0.5 seconds between requests
- **INSUFFICIENT** for production - No token bucket, no Redis-based coordination
- **Risk**: N watchlists × M stocks per 5 seconds can exceed Yahoo's limits

### 2. WebSocket Real-time Price Updates (Issue #117 - COMPLETED, Issue #125 - COMPLETED)

**File**: `backend/api/routers/websocket.py` (464 lines)

**Architecture** (After Issue #125 fix):
- **Centralized Background Tasks**: One background task per watchlist (not per connection)
- **ConnectionManager**: Manages active WebSocket connections and background tasks
- **Memory Leak Prevention**: Proper asyncio.Task lifecycle management
- **90% API Call Reduction**: Single task broadcasts to N connections

**Key Classes/Functions**:
```python
ConnectionManager:
  active_connections: Dict[int, Set[WebSocket]]  # watchlist_id -> connections
  background_tasks: Dict[int, asyncio.Task]      # watchlist_id -> update task
  _lock: asyncio.Lock                             # Concurrent access protection
  
  async def connect(websocket, watchlist_id, watchlist, yahoo_client)
    → Creates background task on first connection to watchlist
  
  async def disconnect(websocket, watchlist_id)
    → Cancels background task when last connection closes
  
  async def _price_update_worker(watchlist_id, watchlist, yahoo_client)
    → Runs every 5 seconds, fetches prices once, broadcasts to all connections
    → Creates fresh DB session per iteration to prevent pool exhaustion
    → Proper cleanup with db.close() in finally block
  
  async def send_personal_message(message, websocket)
  async def broadcast_to_watchlist(message, watchlist_id)

Endpoint:
  @router.websocket("/api/v1/ws/watchlist/{watchlist_id}/prices")
  async def watchlist_price_stream(websocket, watchlist_id, db, redis_client)
    → Authenticates via session token
    → Verifies watchlist access
    → Sends initial price data
    → Connects to manager (starts background task if first connection)
    → Keeps alive until disconnection
```

**Performance Characteristics**:
- **Before Fix (Per-Connection Model)**: 10 connections = 10 loops × 1 API call/5s = 2 API calls/sec
- **After Fix (Centralized Model)**: 10 connections = 1 task × 1 API call/5s = 0.2 API calls/sec
- **Reduction**: 90% fewer API calls, 90% less memory

**Database Session Management** (Critical from PR #132 review):
```python
# In _price_update_worker
db = next(get_db())  # Fresh session per iteration
try:
    price_data = await fetch_watchlist_prices(watchlist, yahoo_client, db)
    await self.broadcast_to_watchlist(price_data, watchlist_id)
finally:
    db.close()  # Always cleanup to prevent connection pool exhaustion
await asyncio.sleep(5)
```

### 3. Stock Price REST APIs (Issue #8 - COMPLETED)

**File**: `backend/api/routers/stock_prices.py`

**Endpoints**:
- `GET /api/v1/stock-prices/{ticker}/latest` - Latest price (cached or live from Yahoo)
- `GET /api/v1/stock-prices/{ticker}/history` - Historical data (5+ years)
- `GET /api/v1/stock-prices/chart/{period}` - Chart data (1d/5d/1m/3m/1y/5y)
- `GET /api/v1/stock-prices/multiple/prices` - Bulk price fetch
- Query parameter `live=true` to bypass cache and fetch from Yahoo Finance

**Response Models**:
```python
LatestPriceResponse:
  ticker_symbol, current_price, open_price, high_price, low_price
  volume, previous_close, change, change_percent, market_cap, currency, last_updated

StockPriceResponse:
  id, company_id, ticker_symbol, date, open_price, high_price, low_price
  close_price, adjusted_close, volume, data_source, created_at

ChartDataResponse:
  ticker_symbol, period, data: List[ChartDataPoint]
```

### 4. Batch Jobs - Daily Stock Price Updates (Issue #85 - COMPLETED)

**File**: `backend/batch/daily_update.py` (247 lines)

**Schedule**: 16:00 JST (4 PM) on weekdays via Cloud Scheduler

**Key Class**: `DailyUpdateJob`

**Methods**:
```python
async def run()
  → Main orchestration: check trading calendar, fetch prices, notify

async def update_stock_prices(companies: List[Company])
  → Bulk fetch prices from Yahoo Finance
  → Batch insert into database (100 records at a time)
  → 3x retry with exponential backoff on failure

async def update_financial_indicators(companies: List[Company])
  → Recalculate 60+ financial metrics

async def cleanup_old_data()
  → Remove stock prices older than 5 years

def get_active_companies() -> List[Company]
  → Query companies with is_active=true
```

**Features**:
- Japanese trading calendar integration (holiday detection)
- Error handling with retry mechanism
- Slack/Email notifications on completion
- Redis caching for price data
- Batch processing for efficiency

**Flow**:
1. Check if today is a trading day (Japanese calendar)
2. Query all active companies
3. Fetch latest stock prices in bulk
4. Store in database
5. Recalculate financial indicators
6. Clean up old data
7. Send notification to Slack

### 5. Rate Limiting Infrastructure

**File**: `backend/core/rate_limiter.py` (125 lines)

**Current Implementation** (slowapi library):
```python
limiter = Limiter(
    key_func=rate_limit_key_func,  # IP address based
    default_limits=[
        f"{settings.api_rate_limit_per_day}/day",      # 10,000/day
        f"{settings.api_rate_limit_per_hour}/hour",    # 1,000/hour
        f"{settings.api_rate_limit_per_minute}/minute" # 60/minute
    ],
    storage_uri=settings.redis_url  # Redis-backed storage
)

# Preset rate limits for different endpoint types
class RateLimits:
    AUTH = "5/minute"
    REGISTRATION = "10/hour"
    STANDARD = "60/minute"
    READ_HEAVY = "100/minute"
    EXPENSIVE = "10/minute"
    DATA_EXPORT = "5/hour"
```

**Configuration** (backend/core/config.py):
```python
api_rate_limit_per_minute: int = 60
api_rate_limit_per_hour: int = 1000
api_rate_limit_per_day: int = 10000
```

**Status**:
- ✅ API endpoint rate limiting IMPLEMENTED
- ❌ Yahoo Finance API rate limiting NOT IMPLEMENTED (Issue #126 - NEXT PRIORITY)

### 6. Redis Integration

**Purpose**: Caching, session management, rate limiting

**Usage**:
1. **Price Caching** (5-minute TTL):
   - Key: `yahoo_finance:{ticker}:{data_type}`
   - Used by: YahooFinanceClient, WebSocket price updates

2. **Session Management** (7-day TTL):
   - Key: `session:{token}`
   - Stores: user_id, roles, investment profile
   - Used by: Auth, WebSocket authentication

3. **OAuth State** (5-minute TTL, one-time use):
   - Key: `oauth_state:{state}`
   - Prevents CSRF attacks

4. **Rate Limiting**:
   - slowapi uses Redis to track request counts per IP
   - Persists across server restarts

**Client Code**:
```python
# In services
from core.dependencies import get_redis_client
redis_client = get_redis_client()

# In batch jobs
if settings.redis_url:
    redis_client = Redis.from_url(settings.redis_url)
```

## Critical Development Issues

### Issue #126: Yahoo Finance API Rate Limiting ⚠️ URGENT

**Status**: Not implemented - NEXT PRIORITY

**Problem**:
- Current: Simple 0.5s fixed delay between requests
- Scenario: 10 watchlists × 20 stocks = 40 API calls per 5 seconds = 8 req/sec
- Yahoo Finance limits: ~2000 requests per hour (0.56 req/sec per IP)
- **Risk**: HTTP 429 Too Many Requests, IP blocking

**Solution Required** (Token Bucket Algorithm):
```python
class TokenBucketRateLimiter:
    def __init__(self, redis_client, max_tokens=100, refill_rate=1.0):
        self.max_tokens = 100          # Bucket capacity
        self.refill_rate = 1.0         # Tokens per second
        self.redis_client = redis_client
    
    async def acquire(self, tokens=1):
        # Wait until tokens available, respecting bucket capacity
        # Track in Redis for distributed coordination
```

**Implementation Locations**:
1. YahooFinanceClient methods that make HTTP requests
2. WebSocket price update worker (coordination across all watchlists)
3. Batch daily update job
4. Stock price REST API endpoints

## Security & Authentication

**Google OAuth 2.0** (Issue #34 - COMPLETED):
- File: `backend/services/google_oauth.py`
- Client ID: `backend/.env` (NOT in git)
- Redirect URI: `http://localhost:8000/api/v1/auth/google/callback`
- State parameter: CSRF protection with 5-min TTL

**Session Management** (backend/core/sessions.py):
- Redis-backed sessions with 7-day TTL
- HTTPOnly cookies with SameSite=lax flag
- Session token validation on every authenticated request

**Route Protection**:
```python
# In auth.py - Session validation
@router.get("/api/v1/auth/me")
async def get_current_user(
    redis_client: Redis = Depends(get_redis_client)
) -> UserResponse:
    session_data = get_session(session_token, redis_client)
    if not session_data:
        raise HTTPException(401, "Unauthorized")
```

## Database Models

**Key Tables**:
1. **users**: User accounts, roles (free/premium/enterprise), investment profile
2. **companies**: Company master data, ticker symbols
3. **stock_prices**: Daily OHLCV data, source tracking
4. **financial_statements**: Quarterly financial reports
5. **financial_indicators**: Calculated metrics (60+ types)
6. **watchlists**: User portfolios
7. **watchlist_items**: Stocks in watchlists with quantity, purchase price

**Indexes** (Issue #88 - COMPLETED):
- 7 strategic indexes for screening performance
- 50% query time reduction (40ms → 20ms target)

## Testing Infrastructure

**Coverage**: 78% (56/91 tests passing in backend)

**Test Files**:
- `test_auth.py` - Authentication flows (12 tests)
- `test_companies.py` - Company APIs
- `test_websocket.py` - WebSocket price updates (19 tests)
- `test_watchlist.py` - Portfolio management
- `test_yahoo_finance_client.py` - Price data fetching
- `test_screening.py` - Filtering/screening
- `test_export.py` - CSV/Excel export

**Test Database**:
- Separate PostgreSQL instance for tests
- Fixtures for common data: users, companies, watchlists
- Redis fixture for session/cache testing

## Next Priority Tasks

### Immediate (Week 1) - CRITICAL
1. **Issue #126**: Yahoo Finance API rate limiting
   - Token bucket implementation with Redis
   - Affect: YahooFinanceClient, WebSocket, batch jobs, REST APIs
   - Effort: 2-3 hours
   - Blocks: Production stability

### High Priority (Week 2-3)
2. **Issue #123**: Frontend WebSocket Client (React/Next.js)
   - Real-time UI updates using WebSocket
   - useRealtimePrices hook implementation
   - WatchlistTable integration

3. **Issue #118**: Portfolio analysis API
   - P&L calculations, sector allocation, risk metrics
   - REST endpoints for dashboard

4. **Issue #23**: Company Details Page
   - Financial data visualization
   - Backend APIs available (Issue #35)

5. **Issue #24**: Screening Interface
   - Advanced filtering UI
   - Backend APIs available (Issue #35)

### Medium Priority (Week 4+)
6. **Issue #128**: Market hours optimization
   - Adaptive polling (reduce updates during non-trading hours)
   - 80% bandwidth reduction potential

7. **Issue #129**: Database query optimization
   - Caching for watchlist queries
   - 99% DB query reduction

8. **Issue #130**: Message compression
   - Gzip compression for WebSocket messages
   - 70-90% bandwidth reduction

## Key Development Patterns

**Async Pattern**:
- All external API calls use `async/await`
- Database sessions managed with `next(get_db())`
- Background tasks with `asyncio.create_task()`

**DI Pattern** (FastAPI depends):
```python
async def endpoint(
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis_client),
    yahoo: YahooFinanceClient = Depends(get_yahoo_finance_client)
):
    # Use injected dependencies
```

**Error Handling**:
- HTTPException for API errors (with proper status codes)
- Logging with context (user_id, watchlist_id, etc.)
- Graceful degradation (e.g., APIs work without Redis)

**Caching Strategy**:
- Redis for short-term data (5 min for prices)
- Database for historical data
- Minimal in-memory state

## Environment Setup

**Required .env Variables**:
```
DATABASE_URL=postgresql://user:pass@localhost/stockcode
REDIS_URL=redis://localhost:6379/0
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
ENVIRONMENT=development
```

**Docker Services**:
- `postgres` - Database
- `redis` - Cache/sessions
- `backend` - FastAPI application
- `frontend` - Next.js development server
- `scheduler` (optional) - Cloud Scheduler emulator

## Conclusions & Insights

1. **Architecture is Sound**: Centralized background tasks prevent memory leaks
2. **Rate Limiting Gap**: Critical missing implementation for Yahoo Finance (Issue #126)
3. **Performance Ready**: 78% test coverage, 50% DB query optimization, WebSocket memory leak fixed
4. **Security Strong**: OAuth 2.0, session management, CSRF protection implemented
5. **Scalability Path**: Token bucket algorithm needed before production scale

**Recommended Next Step**: Implement Issue #126 (Yahoo Finance rate limiting) before scaling WebSocket connections beyond 10-20 concurrent users per watchlist.
