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

### Manual Testing - WebSocket

1. **Start Backend & Frontend**:
```bash
# Terminal 1: Backend
cd backend && source venv/bin/activate
uvicorn api.main:app --reload

# Terminal 2: Frontend
cd frontend && npm run dev
```

2. **Login with Google OAuth**:
   - Visit `http://localhost:3000`
   - Click "Login" button
   - Authorize with Google account

3. **Test Watchlist Page**:
   - Visit `http://localhost:3000/watchlist`
   - Check connection status indicator (top-right)
   - Verify real-time price updates (every 5 seconds)
   - Check price change animations (green ↑ / red ↓)
   - Verify P&L calculations update in real-time

4. **Test Reconnection**:
   - Stop backend server
   - Observe "Reconnecting..." status
   - Restart backend
   - Verify automatic reconnection

5. **Test Memory Leaks**:
   - Open browser DevTools → Performance
   - Record memory snapshot
   - Navigate to/from watchlist page multiple times
   - Check for memory growth (should remain stable)

### Browser DevTools

**WebSocket Connection**:
1. Open DevTools → Network tab
2. Filter: WS (WebSocket)
3. Click on WebSocket connection
4. View Messages tab for real-time messages

**React DevTools**:
- Install React Developer Tools extension
- Verify component memoization (should not re-render unnecessarily)

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
