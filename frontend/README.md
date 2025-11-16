# Stock Code Frontend

Enterprise financial analysis SaaS platform frontend built with Next.js 14 App Router.

## Technology Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript 5.3
- **Styling**: Tailwind CSS 3.4
- **UI**: Radix UI, Lucide React
- **State**: React Query (TanStack Query)
- **Authentication**: Google OAuth 2.0
- **Real-time**: WebSocket
- **Charts**: Recharts

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
│   │   ├── companies/[id]/    # Company details page (intraday charts)
│   │   ├── watchlist/         # Watchlist pages (real-time)
│   │   ├── auth/              # Authentication pages
│   │   ├── layout.tsx         # Root layout
│   │   └── page.tsx           # Landing page
│   ├── components/            # React components
│   │   ├── ui/               # Reusable UI components
│   │   ├── companies/        # Company-specific components
│   │   ├── watchlist/        # Watchlist components
│   │   └── layout/           # Layout components (Header)
│   └── lib/                   # Utilities and libraries
│       ├── api/              # API client configuration
│       ├── auth/             # Authentication context
│       ├── hooks/            # Custom React hooks (useHash, useRealtimePrices)
│       ├── providers/        # React context providers
│       └── websocket.ts      # WebSocket client
└── public/                    # Static assets
```

## Key Features

### Authentication (Google OAuth 2.0)

Session-based authentication with HTTPOnly cookies.

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

Live stock price updates with automatic reconnection.

#### Components

**WatchlistTable** - Real-time watchlist display
```tsx
import { WatchlistTable } from "@/components/watchlist";

function WatchlistPage() {
  return <WatchlistTable watchlistId={123} autoConnect={true} />;
}
```

**useRealtimePrices Hook** - WebSocket connection management
```tsx
import { useRealtimePrices } from "@/lib/hooks/useRealtimePrices";

function MyComponent() {
  const { stocks, connectionState, error, isConnected, connect, disconnect } = useRealtimePrices(123);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, []);

  return <div>{stocks.map(stock => ...)}</div>;
}
```

#### Features

- ✅ Automatic reconnection (exponential backoff)
- ✅ Connection state management (visual feedback)
- ✅ Price change animations (green ↑ / red ↓)
- ✅ Real-time P&L calculation
- ✅ Memory leak prevention
- ✅ Performance optimization (React.memo, useMemo)

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

### Company Details Page

Comprehensive company information with intraday stock charts.

- Tab-based navigation (Overview, Financials, Indicators, Chart)
- Intraday charts with 5m/15m/1h/1d intervals
- Intelligent period selection (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y)
- Line/Area chart toggle
- Real-time statistics (max, min, avg, change rate)

### API Client

Axios-based API client with cookie-based authentication.

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
```

### Code Quality

- **TypeScript**: Strict mode enabled
- **ESLint**: Next.js recommended + custom rules
- **Prettier**: Code formatting

### Environment Variables

```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Testing

### Quick Test Checklist

**Authentication**:
- [ ] Google OAuth login works
- [ ] Session persists across page reloads
- [ ] Logout clears session

**WebSocket (Real-time Prices)**:
- [ ] Connection establishes successfully
- [ ] Prices update every 5 seconds
- [ ] Auto-reconnection works after connection loss
- [ ] Clean disconnection when leaving page
- [ ] No memory leaks after extended use

**Company Details**:
- [ ] All tabs load correctly
- [ ] Intraday charts display for 1d/5d periods
- [ ] Period/interval selection works
- [ ] Stats calculate correctly

### Detailed Testing

For comprehensive WebSocket testing procedures, see:
- **Backend WebSocket Testing Guide**: `/backend/docs/WEBSOCKET_TESTING.md`

## Deployment

### Build for Production

```bash
npm run build
npm start
```

### Docker

```bash
docker build -t stock-code-frontend .
docker run -p 3000:3000 stock-code-frontend
```

### Environment Variables (Production)

- `NEXT_PUBLIC_API_URL` - Backend API URL (e.g., https://api.example.com)

## Troubleshooting

### WebSocket Issues

**"Session token not found"**
- Ensure you're logged in via Google OAuth
- Check `stockcode_session` cookie exists

**Connection keeps reconnecting**
- Check backend WebSocket endpoint is running
- Verify: `ws://localhost:8000/api/v1/ws/watchlist/{id}/prices`

**Price updates not showing**
- Check browser console for errors
- Verify backend is sending messages (check backend logs)
- Ensure watchlist has stocks

### Authentication Issues

**Login redirect loop**
- Clear cookies and try again
- Check `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`

### Build Issues

**TypeScript errors**
- Run `npm run type-check` for detailed errors
- Update type definitions or add type assertions

## License

Proprietary - All Rights Reserved

## Support

For issues and questions, create a GitHub issue in the main repository:
- **Issues**: [GitHub Issues](https://github.com/tyuyoshi/stock_code/issues)
