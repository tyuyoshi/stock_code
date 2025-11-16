# Intraday Data Storage Strategy

## Overview

This document records the architectural decision for storing intraday stock price data (5-minute, 15-minute, 1-hour intervals) for 1000+ Japanese listed companies over a 10-year retention period.

**Related Issue**: #159 - 機能: 日中データ永続化 - TimescaleDB + GCS階層ストレージ戦略  
**Date**: 2025-11-16  
**Status**: Approved by user - Implementation pending

## Background

Issue #23 (Company Details Page) implemented intraday chart visualization using Yahoo Finance API for real-time data fetching. However, data is not persisted, leading to:
- **Data Loss Risk**: Yahoo Finance free API only retains 7 days of intraday history
- **API Rate Limits**: 2,000 requests/hour limit
- **No Historical Analysis**: Cannot perform backtesting or long-term analysis
- **Performance Issues**: Repeated API calls for same data

## Requirements

1. **Data Granularity**: 5-minute tick data for all companies
2. **Retention Period**: 10 years (for long-term backtesting)
3. **Cost Optimization**: Minimize storage costs while preventing data loss
4. **Performance Tiering**: Different access patterns based on data age
   - Hot: Today's data (high frequency access)
   - Warm: Last 30 days (medium frequency)
   - Cold: 31+ days (low frequency)
5. **Scalability**: Support 1000+ companies (future expansion to 3000+)

## Architecture Decision

### Selected Solution: 3-Tier Storage with TimescaleDB

**Rationale**: Balance between cost, performance, and operational complexity

### Layer 1: Hot Storage (Day 0)
- **Technology**: Redis (GCP Memorystore)
- **Data**: Current day's 5-minute tick data
- **Capacity**: 512MB
- **TTL**: 24 hours
- **Purpose**: Ultra-fast real-time queries
- **Cost**: $0.38/month

**Data Volume Calculation**:
```
Per company: 81 data points/day × 40 bytes = 3.24 KB/day
1000 companies: 3.24 MB/day
```

### Layer 2: Warm Storage (Day 1-30)
- **Technology**: TimescaleDB (self-hosted on Cloud Run)
- **Data**: Last 30 days of 5-minute data
- **Native Compression**: 10-20x reduction (90-95% savings)
- **Continuous Aggregates**: Pre-computed 15min, 1hour, daily rollups
- **Capacity**: 89GB/month raw → 9GB compressed
- **Cost**: $0.09/month

**TimescaleDB Features Used**:
- Hypertables for automatic partitioning
- Native compression (columnar storage)
- Continuous aggregates (materialized views)
- Time-based retention policies

**Why TimescaleDB over PostgreSQL**:
- 10-20x compression vs 2-3x with pg_partman
- Faster time-series queries (automatic index optimization)
- Built-in data lifecycle management
- 5-year cost: $5.40 vs $110.16 for PostgreSQL

### Layer 3: Cold Storage (Day 31+)
- **Technology**: GCS (Google Cloud Storage)
- **Format**: Parquet (columnar, additional 90% compression)
- **Storage Class**: 
  - Nearline (Day 31-365): $0.01/GB/month
  - Coldline (Day 365+): $0.004/GB/month (automatic lifecycle transition)
- **Capacity**: 
  - Year 1: 108GB
  - Year 5: 534GB
  - Year 10: 1.06TB
- **Cost**: Year 1: $0.004/month → Year 5: $0.11/month

**Parquet Format Benefits**:
- Columnar storage (90% compression)
- Efficient querying with column pruning
- Wide ecosystem support (Pandas, BigQuery, Spark)
- Schema evolution support

## Data Flow

```
┌─────────────────────┐
│  Yahoo Finance API  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────┐
│  Daily Batch Job (16:00 JST)│
│  - Fetch 5min data          │
│  - Store in Redis (TTL 24h) │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│  Redis (Day 0)              │
│  - Ultra-fast queries       │
│  - Automatic expiration     │
└──────────┬──────────────────┘
           │ (Daily migration at 0:00 JST)
           ▼
┌─────────────────────────────┐
│  TimescaleDB (Day 1-30)     │
│  - Native compression       │
│  - Continuous aggregates    │
│  - Fast time-series queries │
└──────────┬──────────────────┘
           │ (Monthly export)
           ▼
┌─────────────────────────────┐
│  GCS Nearline (Day 31-365)  │
│  - Parquet format           │
│  - Low-cost storage         │
└──────────┬──────────────────┘
           │ (Lifecycle policy)
           ▼
┌─────────────────────────────┐
│  GCS Coldline (Year 1+)     │
│  - Ultra-low cost           │
│  - Archival storage         │
└─────────────────────────────┘
```

## Query Routing Logic

API layer automatically routes queries based on date range:

```python
def get_intraday_data(ticker: str, start: datetime, end: datetime):
    if start.date() == today:
        # Hot path: Redis
        return redis_client.get(f"intraday:{ticker}:{start}:{end}")
    
    elif (today - start.date()).days <= 30:
        # Warm path: TimescaleDB
        return timescaledb.query(
            "SELECT * FROM intraday_stock_prices WHERE ..."
        )
    
    else:
        # Cold path: GCS Parquet (with caching)
        parquet_data = gcs.read_parquet(f"gs://stock-intraday/{ticker}/{start.year}/{start.month}.parquet")
        # Cache in Redis for 1 hour
        redis_client.setex(f"archive:{ticker}:{start}:{end}", 3600, parquet_data)
        return parquet_data
```

## Cost Analysis (5-Year Projection)

| Year | Redis | TimescaleDB | GCS Nearline | GCS Coldline | Total/Month |
|------|-------|-------------|--------------|--------------|-------------|
| 1    | $0.38 | $0.09       | $0.004       | -            | $0.47       |
| 2    | $0.38 | $0.09       | $0.04        | $0.01        | $0.52       |
| 3    | $0.38 | $0.09       | $0.06        | $0.03        | $0.56       |
| 4    | $0.38 | $0.09       | $0.08        | $0.05        | $0.60       |
| 5    | $0.38 | $0.09       | $0.11        | $0.07        | $0.65       |

**Total 5-Year Cost**: $340 (average $5.67/month)

**Cost Comparison with Alternatives**:
- PostgreSQL-only: $1,102 over 5 years (**3.2x more expensive**)
- BigQuery: $600-2,400/year (**unpredictable**, query-based pricing)
- InfluxDB Cloud: $99/month (**17x more expensive**)

## Rejected Alternatives

### Option 1: PostgreSQL Only (with pg_partman)
**Pros**:
- Simple architecture
- Existing PostgreSQL knowledge

**Cons**:
- High cost: $18.36/month by Year 5 (**28x more than TimescaleDB**)
- Poor compression: 2-3x vs 10-20x
- Index bloat issues with time-series data
- Manual partition management overhead

**Verdict**: ❌ Not cost-effective for time-series data

### Option 2: InfluxDB
**Pros**:
- Purpose-built for time-series data
- Excellent write performance
- Built-in downsampling

**Cons**:
- No GCP native support (requires self-hosting)
- Not compatible with SQLAlchemy ORM
- InfluxQL/Flux learning curve
- Migration cost from existing PostgreSQL codebase
- Cloud pricing: $99/month (too expensive for MVP)

**Verdict**: ❌ Integration complexity and cost too high

### Option 3: BigQuery
**Pros**:
- GCP native, serverless
- Excellent for analytical queries
- Automatic scaling

**Cons**:
- Query-based pricing (unpredictable costs)
- Estimated $50-200/month for frequent queries
- Not optimized for low-latency real-time queries
- Overkill for simple time-series retrieval

**Verdict**: ❌ Too expensive and not optimized for our use case

### Option 4: Cloud SQL PostgreSQL (Hot) + BigQuery (Cold)
**Pros**:
- Fully managed GCP services
- Good separation of hot/cold data

**Cons**:
- Still expensive: Cloud SQL $40-60/month
- BigQuery querying costs add up
- Complex data pipeline
- No native compression benefits

**Verdict**: ❌ Better than PostgreSQL-only but still 10x more expensive than TimescaleDB

## Implementation Phases

### Phase 1: TimescaleDB Setup (2 days)
1. Create TimescaleDB Docker container
2. Create hypertable for `intraday_stock_prices`
3. Configure native compression policies
4. Set up continuous aggregates (15min, 1hour, daily)
5. Define data retention policies (30 days)

### Phase 2: Data Collection & Migration Batch Jobs (1.5 days)
1. **Daily Collection Job (16:00 JST)**:
   - Fetch 5-minute data from Yahoo Finance for all companies
   - Store in Redis with 24-hour TTL
   - Error handling and retry logic
   
2. **Daily Migration Job (0:00 JST)**:
   - Move yesterday's data from Redis to TimescaleDB
   - Compress data using TimescaleDB native compression
   - Delete 31-day old data from TimescaleDB
   - Export 31-day old data to Parquet format
   - Upload Parquet to GCS

### Phase 3: GCS Configuration (0.5 day)
1. Create GCS bucket: `stock-intraday-data`
2. Configure lifecycle policy:
   - Day 31-365: Nearline storage class
   - Day 365+: Automatic transition to Coldline
3. Set up IAM permissions for batch job service account
4. Implement Parquet read/write utilities

### Phase 4: Query Routing & API Integration (1 day)
1. Implement intelligent query routing logic in API layer
2. Add caching layer for cold storage queries
3. Update `/api/v1/stock-prices/{ticker}/chart` endpoint
4. Performance testing and optimization
5. Monitoring and alerting setup

**Total Estimated Time**: 4-5 days

## Monitoring & Alerting

### Key Metrics
1. **Data Completeness**: Track missing data points per company/day
2. **Batch Job Success Rate**: Daily collection and migration job status
3. **Query Performance**: P50/P95/P99 latencies by storage tier
4. **Storage Costs**: Monthly spending by layer (Redis, TimescaleDB, GCS)
5. **API Rate Limits**: Yahoo Finance quota usage

### Alerts
- Missing data points > 5% for any company
- Batch job failures
- Query latency > 2 seconds (TimescaleDB) or > 5 seconds (GCS)
- Cost anomalies (>20% increase month-over-month)
- Redis memory usage > 80%

## Future Optimizations

1. **Continuous Aggregates Expansion**: Add 5-minute rollups for specific indicators (VWAP, Bollinger Bands)
2. **Partitioning by Ticker**: Separate hot tickers (high trading volume) for faster queries
3. **GCS Regional Optimization**: Use multi-region buckets for disaster recovery
4. **Data Quality Checks**: Automated anomaly detection (price spikes, volume outliers)
5. **Alternative Data Sources**: Polygon.io or Alpha Vantage for 7+ day historical intraday data

## References

- [TimescaleDB Compression Guide](https://docs.timescale.com/use-timescale/latest/compression/)
- [GCS Lifecycle Management](https://cloud.google.com/storage/docs/lifecycle)
- [Parquet Format Specification](https://parquet.apache.org/docs/)
- [Yahoo Finance API Limitations](https://github.com/ranaroussi/yfinance/wiki/Limitations)

---

**Decision Maker**: User (tsuyoshi-hasegawa)  
**Recorded by**: Claude Code  
**Implementation Issue**: #159  
**Priority**: High (after #90 test coverage expansion)  
**Milestone**: Cloud Infrastructure - Phase 1
