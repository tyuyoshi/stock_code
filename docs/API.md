# Stock Code API Documentation

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

Most endpoints require JWT authentication. Include the token in the Authorization header:

```
Authorization: Bearer <token>
```

## Endpoints

### Authentication

#### POST /auth/register
Register a new user.

#### POST /auth/login
Authenticate user and receive JWT token.

#### POST /auth/refresh
Refresh JWT token.

### Companies

#### GET /companies/search
Search for companies.

Query Parameters:
- `q`: Search query (company name or ticker)
- `market`: Market division filter
- `industry`: Industry code filter
- `page`: Page number (default: 1)
- `limit`: Results per page (default: 20)

#### GET /companies/{company_id}
Get detailed company information.

#### GET /companies/{company_id}/financials
Get financial statements for a company.

Query Parameters:
- `period`: annual | quarterly
- `years`: Number of years of data (default: 5)

### Screening

#### POST /screening
Screen companies based on multiple criteria.

Request Body:
```json
{
  "criteria": {
    "per": {"min": 0, "max": 20},
    "pbr": {"min": 0, "max": 2},
    "roe": {"min": 10, "max": null},
    "market_cap": {"min": 1000000000, "max": null}
  },
  "sort": "market_cap",
  "order": "desc",
  "limit": 50
}
```

### Comparison

#### POST /comparison/companies
Compare multiple companies.

Request Body:
```json
{
  "company_ids": [1, 2, 3],
  "metrics": ["per", "pbr", "roe", "revenue_growth"],
  "period": "latest"
}
```

### Export

#### GET /export/csv
Export data in CSV format.

#### GET /export/excel
Export data in Excel format.

## Error Responses

All errors follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}
  }
}
```

Common HTTP status codes:
- 200: Success
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 429: Too Many Requests
- 500: Internal Server Error