# WebSocket Real-time Price Updates - Testing Guide

## Overview

This document provides comprehensive testing procedures for the WebSocket real-time stock price update feature (Issue #123).

## Test Environment Setup

### Prerequisites

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

### Quick Test Data Creation

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
curl -X POST http://localhost:8000/api/v1/watchlists/1/items \
  -H "Content-Type: application/json" \
  -H "Cookie: stockcode_session=YOUR_SESSION_TOKEN" \
  -d '{
    "company_id": 1,
    "quantity": 100,
    "purchase_price": 2800.0,
    "memo": "Toyota test"
  }'
```

## Test Cases

### TC-01: Initial Connection

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

---

### TC-02: Real-time Price Updates

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

**Timing Check**:
- Use browser console timestamp: `new Date().toISOString()`
- Verify updates occur at ~5 second intervals

---

### TC-03: Connection Interruption & Reconnection

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

**Error Handling Check**:
- Reconnection attempts visible in browser console
- No JavaScript errors in console

---

### TC-04: Manual Disconnection

**Purpose**: Verify clean disconnection when leaving page

**Steps**:
1. Complete TC-01 (establish connection)
2. Navigate away from `/watchlist` page (e.g., go to `/`)
3. Check browser DevTools Network tab

**Expected Result**:
- ✅ WebSocket connection closes cleanly (status: 1000)
- ✅ No reconnection attempts after leaving page
- ✅ No JavaScript errors in console

---

### TC-05: Authentication Failure

**Purpose**: Verify error handling for invalid session

**Steps**:
1. Logout from the application
2. Manually delete `stockcode_session` cookie from browser
3. Navigate to `/watchlist` page

**Expected Result**:
- ✅ Redirected to login page OR
- ✅ Error message: "ログインが必要です"
- ✅ No WebSocket connection attempt

---

### TC-06: Multiple Concurrent Connections

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

---

### TC-07: Performance & Memory Leaks

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

**Chrome DevTools**:
- Performance → Memory → Allocation timeline
- Look for sawtooth pattern (memory allocated then freed)
- Avoid continuous upward trend (memory leak indicator)

---

### TC-08: Component Rendering Performance

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

**React DevTools Check**:
- "Highlight updates when components render" should only highlight price cells
- Profiler flame graph should show minimal render work

---

### TC-09: Error Notification (Toast)

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

---

### TC-10: Different Connection States

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

---

## Performance Benchmarks

### Target Metrics

- **Initial Connection Time**: < 500ms
- **Price Update Latency**: < 100ms (from backend send to UI update)
- **Memory Usage**: < 10MB increase per connection
- **CPU Usage**: < 5% during idle connection
- **Re-render Count**: < 10 components per price update

### Measurement Tools

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

---

## Known Issues & Limitations

### Current Limitations

1. **Session Cookie Dependency**:
   - WebSocket authentication requires `stockcode_session` cookie
   - Cannot connect from different domain (CORS)

2. **Browser Support**:
   - Requires modern browsers with WebSocket support (Chrome 90+, Firefox 88+, Safari 14+)
   - No polyfill for older browsers

3. **Reconnection Strategy**:
   - Maximum 5 reconnection attempts
   - After 5 failures, manual page refresh required

### Future Improvements

- [ ] Add heartbeat/ping-pong for connection health check
- [ ] Implement message queuing for missed updates during reconnection
- [ ] Add user preference for update frequency (5s, 10s, 30s)
- [ ] Support multiple watchlists on same page

---

## Troubleshooting

### Issue: "Session token not found"

**Symptoms**: WebSocket fails to connect, error in console

**Solutions**:
1. Verify you're logged in (check for `stockcode_session` cookie)
2. Refresh page to get new session token
3. Re-login if session expired

### Issue: Prices not updating

**Symptoms**: Connection shows "リアルタイム接続中" but no price changes

**Solutions**:
1. Check backend logs for errors
2. Verify backend WebSocket is sending messages
3. Check if stock prices are available from Yahoo Finance API
4. Verify watchlist has items (check backend API)

### Issue: High CPU usage

**Symptoms**: Browser tab consumes > 20% CPU while idle

**Solutions**:
1. Check for infinite re-render loops (React DevTools)
2. Verify animations use GPU acceleration (transform, opacity)
3. Limit number of stocks in watchlist (< 50 recommended)

### Issue: Memory leak suspected

**Symptoms**: Memory usage increases over time, browser slows down

**Solutions**:
1. Take heap snapshots to identify leaking objects
2. Verify WebSocket cleanup on page navigation
3. Check for event listeners not being removed
4. Report issue with reproduction steps

---

## Test Checklist

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

---

## Success Criteria

✅ **Feature Complete When**:

1. All 10 test cases pass
2. No TypeScript errors
3. No ESLint warnings
4. Performance benchmarks met
5. Documentation complete
6. Code review approved
7. Merged to main branch

---

## Related Documentation

- Backend WebSocket API: `/backend/api/routers/websocket.py`
- Frontend README: `/frontend/README.md`
- Issue #123: https://github.com/tyuyoshi/stock_code/issues/123
- Backend Testing Guide: `/backend/WATCHLIST_TESTING.md` (if exists)

---

**Last Updated**: 2025-11-09
**Author**: Claude Code
**Issue**: #123 - Frontend WebSocket Client
