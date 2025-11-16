# Stock Code Frontend

Enterprise financial analysis SaaS platform frontend built with Next.js 14 App Router.

## Technology Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript 5.3
- **Styling**: Tailwind CSS 3.4
- **UI Components**: Radix UI, Lucide React
- **State Management**: Zustand, React Query
- **Authentication**: Google OAuth 2.0
- **Real-time Updates**: WebSocket

## Getting Started

### Prerequisites

- Node.js 20.x or later
- npm 10.x or later
- Backend API running on `http://localhost:8000`

### Installation

```bash
# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local

# Start development server
npm run dev
```

Visit `http://localhost:3000` to see the application.

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── auth/              # Authentication pages
│   │   ├── watchlist/         # Watchlist pages (real-time)
│   │   ├── layout.tsx         # Root layout
│   │   └── page.tsx           # Landing page
│   ├── components/            # React components
│   │   ├── ui/               # Reusable UI components
│   │   └── watchlist/        # Watchlist-specific components
│   └── lib/                   # Utilities and libraries
│       ├── api/              # API client configuration
│       ├── auth/             # Authentication context
│       ├── hooks/            # Custom React hooks
│       ├── providers/        # React context providers
│       └── websocket.ts      # WebSocket client
├── public/                    # Static assets
└── tailwind.config.ts        # Tailwind configuration
```

## Features

### Authentication (Google OAuth 2.0)

- Session-based authentication with HTTPOnly cookies
- Protected routes with AuthContext
- Automatic session refresh

**Usage**:
```tsx
import { useAuth } from "@/lib/auth/AuthContext";

function MyComponent() {
  const { user, isLoading, login, logout } = useAuth();

  if (isLoading) return <div>Loading...</div>;
  if (!user) return <button onClick={login}>Login</button>;

  return <div>Welcome, {user.name}!</div>;
}
```

### Real-time Stock Prices (WebSocket)

Complete WebSocket integration for live stock price updates with automatic reconnection.

#### Components

**WatchlistTable** - Main component for displaying real-time watchlist
```tsx
import { WatchlistTable } from "@/components/watchlist";

function WatchlistPage() {
  return <WatchlistTable watchlistId={123} autoConnect={true} />;
}
```

**useRealtimePrices Hook** - React Hook for WebSocket connection
```tsx
import { useRealtimePrices } from "@/lib/hooks/useRealtimePrices";

function MyComponent() {
  const { stocks, connectionState, error, isConnected } = useRealtimePrices(123);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, []);

  return <div>{stocks.map(stock => ...)}</div>;
}
```

**WebSocketClient** - Low-level WebSocket client
```tsx
import { WebSocketClient, ConnectionState } from "@/lib/websocket";

const client = new WebSocketClient({
  watchlistId: 123,
  onMessage: (message) => console.log(message),
  onStateChange: (state) => console.log(state),
  onError: (error) => console.error(error),
});

client.connect();
// ... later
client.disconnect();
```

#### WebSocket Features

1. **Automatic Reconnection** - Exponential backoff (3s, 6s, 12s, 24s, 48s)
2. **Connection State Management** - Visual feedback for connection status
3. **Error Handling** - Toast notifications for connection errors
4. **Memory Leak Prevention** - Proper cleanup on unmount
5. **Performance Optimization** - React.memo, useMemo, useCallback
6. **Price Change Animations** - Visual feedback for price updates (green ↑ / red ↓)
7. **Real-time P&L Calculation** - Unrealized profit/loss updates every 5 seconds

#### Message Format

```typescript
{
  type: "price_update",
  watchlist_id: 123,
  stocks: [
    {
      company_id: 1,
      ticker_symbol: "7203",
      company_name: "Toyota Motor Corp",
      current_price: 2850.5,
      change: 12.5,
      change_percent: 0.44,
      quantity: 100,
      purchase_price: 2800.0,
      unrealized_pl: 5050.0
    }
  ],
  timestamp: "2025-11-09T17:30:00"
}
```

#### Connection States

- `CONNECTING` - Initial connection in progress
- `CONNECTED` - Successfully connected, receiving updates
- `RECONNECTING` - Connection lost, attempting to reconnect
- `DISCONNECTED` - Manually disconnected
- `ERROR` - Connection error (max retries exceeded)

### API Client

Axios-based API client with interceptors and cookie-based authentication.

```tsx
import { apiClient } from "@/lib/api/client";

// All requests automatically include credentials (cookies)
const response = await apiClient.get("/api/v1/companies");
const companies = response.data;
```

## Development

### Available Scripts

```bash
npm run dev          # Start development server
npm run build        # Build for production
npm start            # Start production server
npm run lint         # Run ESLint
npm run type-check   # Run TypeScript type checking
npm run format       # Format code with Prettier
```

### Code Quality

- **TypeScript**: Strict mode enabled
- **ESLint**: Next.js recommended + custom rules
- **Prettier**: Code formatting
- **Husky**: Pre-commit hooks (optional)

### Environment Variables

```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Testing

### WebSocket Testing Guide

Complete testing procedures for real-time price updates (Issue #123).

#### Test Environment Setup

**Prerequisites**:

1. **Backend Running**:
```bash
cd backend
source venv/bin/activate
uvicorn api.main:app --reload
```

2. **Redis Running** (for sessions):
```bash
docker compose up redis
```

3. **PostgreSQL Running** (for data):
```bash
docker compose up postgres
```

4. **Frontend Running**:
```bash
cd frontend
npm run dev
```

5. **Test Data Setup**:
   - At least one user account (via Google OAuth)
   - At least one watchlist with stocks (use backend API to create)

#### Quick Test Data Creation

```bash
# Create a test watchlist via backend API
curl -X POST http://localhost:8000/api/v1/watchlists \
  -H "Content-Type: application/json" \
  -H "Cookie: stockcode_session=YOUR_SESSION_TOKEN" \
  -d '{
    "name": "Test Watchlist",
    "description": "For WebSocket testing",
    "is_public": false
  }'

# Add stocks to watchlist
curl -X POST http://localhost:8000/api/v1/watchlists/1/stocks \
  -H "Content-Type: application/json" \
  -H "Cookie: stockcode_session=YOUR_SESSION_TOKEN" \
  -d '{
    "company_id": 1,
    "quantity": 100,
    "purchase_price": 2800.0,
    "memo": "Toyota test"
  }'
```

#### Test Cases

##### TC-01: Initial Connection

**Purpose**: Verify WebSocket connection establishes successfully

**Steps**:
1. Login to the application
2. Navigate to `/watchlist` page
3. Observe connection status indicator

**Expected Result**:
- ✅ Connection status shows "接続中..." briefly
- ✅ Connection status changes to "リアルタイム接続中" (green)
- ✅ Stock prices appear in the table within 5 seconds

**Browser DevTools Check**:
- Network tab → WS filter shows active connection
- Messages tab shows "price_update" messages every 5 seconds

##### TC-02: Real-time Price Updates

**Purpose**: Verify prices update in real-time

**Steps**:
1. Complete TC-01 (establish connection)
2. Wait for 5 seconds
3. Observe stock price updates

**Expected Result**:
- ✅ Prices update every 5 seconds
- ✅ Price change indicator shows correct direction (green ↑ or red ↓)
- ✅ Flash animation appears on price change (green or red background)
- ✅ Change percentage updates correctly
- ✅ P&L (評価損益) updates in real-time

##### TC-03: Connection Interruption & Reconnection

**Purpose**: Verify automatic reconnection on connection loss

**Steps**:
1. Complete TC-01 (establish connection)
2. Stop backend server: `Ctrl+C`
3. Observe connection status
4. Wait 3 seconds
5. Restart backend: `uvicorn api.main:app --reload`
6. Observe reconnection

**Expected Result**:
- ✅ Status changes to "再接続中..." (yellow, spinning icon)
- ✅ Toast notification shows "接続エラー"
- ✅ After backend restart, status returns to "リアルタイム接続中"
- ✅ Price updates resume after reconnection
- ✅ Maximum 5 reconnection attempts (3s, 6s, 12s, 24s, 48s intervals)

##### TC-04: Manual Disconnection

**Purpose**: Verify clean disconnection when leaving page

**Steps**:
1. Complete TC-01 (establish connection)
2. Navigate away from `/watchlist` page (e.g., go to `/`)
3. Check browser DevTools Network tab

**Expected Result**:
- ✅ WebSocket connection closes cleanly (status: 1000)
- ✅ No reconnection attempts after leaving page
- ✅ No JavaScript errors in console

##### TC-05: Authentication Failure

**Purpose**: Verify error handling for invalid session

**Steps**:
1. Logout from the application
2. Manually delete `stockcode_session` cookie from browser
3. Navigate to `/watchlist` page

**Expected Result**:
- ✅ Redirected to login page OR
- ✅ Error message: "ログインが必要です"
- ✅ No WebSocket connection attempt

##### TC-06: Multiple Concurrent Connections

**Purpose**: Verify multiple browser tabs work correctly

**Steps**:
1. Complete TC-01 in Tab 1
2. Open new tab (Tab 2)
3. Navigate to `/watchlist` in Tab 2
4. Observe both tabs

**Expected Result**:
- ✅ Both tabs show "リアルタイム接続中"
- ✅ Both tabs receive price updates independently
- ✅ Close Tab 1 → Tab 2 continues receiving updates
- ✅ Backend shows 2 separate WebSocket connections (check backend logs)

##### TC-07: Performance & Memory Leaks

**Purpose**: Verify no memory leaks after extended use

**Steps**:
1. Open browser DevTools → Performance → Memory
2. Take heap snapshot (Snapshot 1)
3. Complete TC-01 (connect to WebSocket)
4. Wait for 10 price updates (50 seconds)
5. Navigate away from page
6. Force garbage collection (if available)
7. Take heap snapshot (Snapshot 2)
8. Repeat steps 3-7 five times
9. Compare heap snapshots

**Expected Result**:
- ✅ Memory usage remains stable across multiple connect/disconnect cycles
- ✅ No significant memory growth in Snapshot 2-6 compared to Snapshot 1
- ✅ WebSocket objects are properly garbage collected
- ✅ No detached DOM nodes accumulating

##### TC-08: Component Rendering Performance

**Purpose**: Verify React components don't re-render unnecessarily

**Steps**:
1. Install React Developer Tools extension
2. Complete TC-01
3. Open React DevTools → Profiler
4. Click "Record" button
5. Wait for 3 price updates (15 seconds)
6. Stop recording
7. Analyze render timeline

**Expected Result**:
- ✅ Only components with changed data re-render (PriceCell, PLCell)
- ✅ WatchlistTable component uses React.memo effectively
- ✅ ConnectionStatus component only re-renders on state change
- ✅ No full page re-renders on price updates

##### TC-09: Error Notification (Toast)

**Purpose**: Verify toast notifications for errors

**Steps**:
1. Complete TC-01
2. Stop backend server
3. Wait for connection error
4. Observe toast notification

**Expected Result**:
- ✅ Toast appears in top-right corner
- ✅ Title: "接続エラー"
- ✅ Description shows error message
- ✅ Toast has red/destructive styling
- ✅ Toast auto-dismisses after a few seconds

##### TC-10: Different Connection States

**Purpose**: Verify all connection state UI feedback

**Test Matrix**:

| State | Icon | Color | Text | Trigger |
|-------|------|-------|------|---------|
| CONNECTING | Loader (spin) | Blue | 接続中... | Initial connection |
| CONNECTED | Wifi | Green | リアルタイム接続中 | Successful connection |
| RECONNECTING | Loader (spin) | Yellow | 再接続中... | Connection lost |
| ERROR | AlertCircle | Red | 接続エラー | Max retries exceeded |
| DISCONNECTED | WifiOff | Gray | 未接続 | Manual disconnect |

**Expected Result**:
- ✅ All states display correct icon, color, and text
- ✅ Spinning animation only for CONNECTING and RECONNECTING
- ✅ State transitions are smooth and immediate

#### Performance Benchmarks

**Target Metrics**:
- **Initial Connection Time**: < 500ms
- **Price Update Latency**: < 100ms (from backend send to UI update)
- **Memory Usage**: < 10MB increase per connection
- **CPU Usage**: < 5% during idle connection
- **Re-render Count**: < 10 components per price update

**Measurement Tools**:

1. **Chrome DevTools**:
   - Performance → Record → Analyze
   - Network → WS → Messages tab (timing)
   - Memory → Heap snapshots

2. **React DevTools**:
   - Profiler → Flamegraph
   - Components → Highlight updates

3. **Browser Console**:
```javascript
// Measure WebSocket message latency
const ws = /* get WebSocket from Network tab */;
ws.addEventListener('message', (event) => {
  const data = JSON.parse(event.data);
  const serverTime = new Date(data.timestamp);
  const clientTime = new Date();
  const latency = clientTime - serverTime;
  console.log(`Latency: ${latency}ms`);
});
```

#### Known Issues & Limitations

**Current Limitations**:

1. **Session Cookie Dependency**:
   - WebSocket authentication requires `stockcode_session` cookie
   - Cannot connect from different domain (CORS)

2. **Browser Support**:
   - Requires modern browsers with WebSocket support (Chrome 90+, Firefox 88+, Safari 14+)
   - No polyfill for older browsers

3. **Reconnection Strategy**:
   - Maximum 5 reconnection attempts
   - After 5 failures, manual page refresh required

**Future Improvements**:
- [ ] Add heartbeat/ping-pong for connection health check
- [ ] Implement message queuing for missed updates during reconnection
- [ ] Add user preference for update frequency (5s, 10s, 30s)
- [ ] Support multiple watchlists on same page

#### Test Checklist

Before marking Issue #123 as complete:

- [ ] TC-01: Initial connection works
- [ ] TC-02: Real-time updates work
- [ ] TC-03: Reconnection works
- [ ] TC-04: Clean disconnection works
- [ ] TC-05: Authentication failure handled
- [ ] TC-06: Multiple tabs work
- [ ] TC-07: No memory leaks detected
- [ ] TC-08: Render performance optimized
- [ ] TC-09: Error toasts appear
- [ ] TC-10: All connection states display correctly
- [ ] All ESLint warnings fixed
- [ ] TypeScript type checking passes
- [ ] Code formatted with Prettier
- [ ] Documentation complete

## Deployment

### Build for Production

```bash
npm run build
npm start
```

### Docker

```bash
# Build image
docker build -t stock-code-frontend .

# Run container
docker run -p 3000:3000 stock-code-frontend
```

### Environment Variables (Production)

- `NEXT_PUBLIC_API_URL` - Backend API URL (e.g., https://api.example.com)

## Troubleshooting

### WebSocket Connection Issues

**Problem**: "Session token not found"
- **Solution**: Ensure you're logged in via Google OAuth
- **Check**: Cookie `stockcode_session` exists in browser

**Problem**: Connection keeps reconnecting
- **Solution**: Check backend WebSocket endpoint is running
- **Verify**: `ws://localhost:8000/api/v1/ws/watchlist/{id}/prices`

**Problem**: Price updates not showing
- **Solution**: Check browser console for errors
- **Verify**: Backend WebSocket is sending messages (check backend logs)
- **Check**: Verify watchlist has stocks (use `/api/v1/watchlists/{id}/stocks` endpoint)

### Authentication Issues

**Problem**: Login redirect loop
- **Solution**: Clear cookies and try again
- **Check**: `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are correct

### Build Issues

**Problem**: TypeScript errors
- **Solution**: Run `npm run type-check` to see detailed errors
- **Fix**: Update type definitions or add type assertions

## Contributing

1. Create feature branch: `git checkout -b feature/issue-XXX`
2. Make changes and test thoroughly
3. Run quality checks: `npm run lint && npm run type-check`
4. Commit with descriptive message (in Japanese for this project)
5. Create pull request

## License

Proprietary - All Rights Reserved

## Support

For issues and questions, please create a GitHub issue in the main repository.
