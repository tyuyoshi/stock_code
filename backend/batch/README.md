# Stock Code Batch Jobs

This directory contains batch job implementations for automated data updates and maintenance tasks.

## Overview

The batch job system provides:
- **Daily stock price updates** from Yahoo Finance
- **Trading day calendar** with Japanese holidays
- **Error notification system** (Slack/Email)
- **Automated scheduling** via cron and Cloud Scheduler
- **Retry mechanisms** for robust execution

## Components

### Core Modules

1. **daily_update.py** - Main daily batch job
2. **trading_calendar.py** - Japanese market trading day calculator
3. **notification.py** - Error notification and reporting service

### Scheduling

1. **Docker/Local Environment**: cron-based scheduling
2. **Production (GCP)**: Cloud Scheduler + Cloud Run Jobs

## Usage

### Manual Execution

```bash
# Run daily update manually
cd backend
python -m batch.daily_update

# Test trading calendar
python services/trading_calendar.py

# Test notifications
python services/notification.py

# Run comprehensive tests
python scripts/test_batch_job.py
```

### Docker Scheduler Service

```bash
# Start scheduler service
docker compose --profile scheduler up -d

# View logs
docker compose logs -f scheduler

# Stop scheduler
docker compose --profile scheduler down
```

### Configuration

Environment variables for notifications:

```bash
# Slack notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# Email notifications
EMAIL_NOTIFICATIONS_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
NOTIFICATION_EMAILS=admin@company.com,dev@company.com
```

## Features

### Trading Calendar

- **Japanese holidays**: New Year, Golden Week, etc.
- **Weekend detection**: Automatic Saturday/Sunday skip
- **Substitute holidays**: Handles weekend holiday substitutions
- **Custom holiday rules**: Olympics and special cases

### Error Handling

- **Retry logic**: Exponential backoff (max 3 attempts)
- **Partial success handling**: Reports success rate
- **Error aggregation**: Collects and reports all errors
- **Graceful degradation**: Continues on individual failures

### Notifications

- **Slack integration**: Rich message formatting with status colors
- **Email notifications**: HTML and plain text formats
- **Severity levels**: INFO, WARNING, ERROR, CRITICAL
- **Execution metrics**: Runtime, success rate, error details

## Scheduling

### Development (Docker Cron)

- **Schedule**: 16:00 JST daily (weekdays only)
- **Implementation**: Custom cron container
- **Logs**: Persistent volume for log retention

```cron
# Daily update at 16:00 JST (07:00 UTC)
0 7 * * 1-5 /app/scripts/run_daily_update.sh >> /var/log/cron.log 2>&1
```

### Production (Cloud Scheduler)

- **Schedule**: 16:00 JST daily (weekdays)
- **Implementation**: Cloud Scheduler → Cloud Run Jobs
- **Retry**: 3 attempts with exponential backoff
- **Timeout**: 30 minutes per execution

```hcl
resource "google_cloud_scheduler_job" "daily_stock_update" {
  name         = "stock-code-daily-update"
  schedule     = "0 16 * * 1-5"  # 16:00 JST on weekdays
  time_zone    = "Asia/Tokyo"
  # ... (see infrastructure/terraform/scheduler.tf)
}
```

## Data Flow

```
1. Check Trading Day → Skip if holiday/weekend
2. Get Company List → Query all active companies
3. Batch Processing → 10 companies per API batch
4. Data Validation → Check received data quality
5. Database Update → Upsert stock prices
6. Error Collection → Aggregate any failures
7. Send Notification → Report execution results
8. Cleanup → Close connections and temporary data
```

## Monitoring

### Log Locations

- **Docker**: `/var/log/cron.log` (mounted volume)
- **Cloud Run**: Cloud Logging (auto-collected)
- **Application**: Structured JSON logs

### Metrics Tracked

- **Execution time**: Total job duration
- **Success rate**: Percentage of successful company updates
- **Error count**: Number of failed company updates
- **API call metrics**: Rate limiting and response times

### Health Checks

```bash
# Cron health check (every 6 hours)
0 */6 * * * echo "$(date): Stock Code Scheduler is running" >> /var/log/cron.log 2>&1

# Manual health check
docker exec stock_code_scheduler ps aux | grep cron
```

## Troubleshooting

### Common Issues

1. **Trading day false positives**
   ```bash
   # Check trading calendar
   python -c "from services.trading_calendar import is_trading_day; print(is_trading_day())"
   ```

2. **API rate limiting**
   ```bash
   # Check Yahoo Finance API status
   python -c "
   import yfinance as yf
   ticker = yf.Ticker('7203.T')
   print(ticker.info)
   "
   ```

3. **Database connectivity**
   ```bash
   # Test database connection
   python -c "
   from core.database import SessionLocal
   db = SessionLocal()
   print('DB connection OK')
   db.close()
   "
   ```

4. **Notification failures**
   ```bash
   # Test notification service
   python services/notification.py
   ```

### Log Analysis

```bash
# Check recent cron execution
docker exec stock_code_scheduler tail -f /var/log/cron.log

# Check application logs
docker compose logs --tail=100 scheduler

# Check for errors
docker compose logs scheduler | grep -i error
```

## Development

### Adding New Batch Jobs

1. Create job class in `batch/` directory
2. Implement async `run()` method
3. Add error handling and notifications
4. Update cron schedule if needed
5. Add tests to `test_batch_job.py`

### Testing

```bash
# Run test suite
python scripts/test_batch_job.py

# Test specific components
python -m pytest tests/test_batch/ -v

# Integration test
docker compose --profile scheduler up -d
# Wait for execution...
docker compose logs scheduler
```

## Security

- **Service accounts**: Minimal required permissions
- **Secret management**: Environment variables and Secret Manager
- **Network isolation**: VPC and firewall rules
- **Audit logging**: All executions logged and monitored

## Performance

- **Batch processing**: 10 companies per API call
- **Connection pooling**: Reuse database connections
- **Rate limiting**: Respect Yahoo Finance API limits
- **Caching**: Redis for repeated data access
- **Cleanup**: Automatic log rotation and old data removal