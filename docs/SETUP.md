# Stock Code Setup Guide

## Prerequisites

### Required Software

1. **Python 3.11+**
   ```bash
   python3 --version
   ```

2. **Node.js 18+**
   ```bash
   node --version
   npm --version
   ```

3. **Docker & Docker Compose**
   ```bash
   docker --version
   docker-compose --version
   ```

4. **PostgreSQL 15+** (if not using Docker)
   ```bash
   psql --version
   ```

5. **Git**
   ```bash
   git --version
   ```

## Quick Start with Docker

```bash
# Clone the repository
git clone https://github.com/tyuyoshi/stock_code.git
cd stock_code

# Copy environment variables
cp .env.example .env

# Run setup script
./setup.sh

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

## Manual Setup

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up database
createdb stockcode

# Run migrations
alembic upgrade head

# Start development server
uvicorn api.main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 3. Database Setup

#### Using Docker
```bash
docker run --name stockcode-postgres \
  -e POSTGRES_USER=stockcode \
  -e POSTGRES_PASSWORD=stockcode123 \
  -e POSTGRES_DB=stockcode \
  -p 5432:5432 \
  -d postgres:15-alpine
```

#### Manual PostgreSQL
```sql
-- Create database and user
CREATE USER stockcode WITH PASSWORD 'stockcode123';
CREATE DATABASE stockcode OWNER stockcode;
GRANT ALL PRIVILEGES ON DATABASE stockcode TO stockcode;
```

### 4. Redis Setup (Optional)

```bash
docker run --name stockcode-redis \
  -p 6379:6379 \
  -d redis:7-alpine
```

## Environment Variables

Key environment variables to configure:

```bash
# Database
DATABASE_URL=postgresql://stockcode:stockcode123@localhost:5432/stockcode

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-here  # Generate with: openssl rand -hex 32

# External APIs
EDINET_API_KEY=your-key
JPX_API_KEY=your-key
```

## GCP Deployment

### 1. Install gcloud CLI

```bash
# Download and install from: https://cloud.google.com/sdk/docs/install
gcloud init
```

### 2. Create GCP Project

```bash
gcloud projects create stock-code-prod
gcloud config set project stock-code-prod
```

### 3. Enable APIs

```bash
gcloud services enable \
  run.googleapis.com \
  sql-component.googleapis.com \
  sqladmin.googleapis.com \
  storage.googleapis.com \
  cloudscheduler.googleapis.com
```

### 4. Deploy with Terraform

```bash
cd infrastructure/terraform
terraform init
terraform plan
terraform apply
```

## Troubleshooting

### Port Already in Use

```bash
# Find process using port
lsof -i :8000  # or :3000 for frontend

# Kill process
kill -9 <PID>
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432

# Check connection
psql -U stockcode -h localhost -d stockcode
```

### Docker Issues

```bash
# Reset Docker environment
docker-compose down -v
docker system prune -a
docker-compose up --build
```

### Permission Issues

```bash
# Fix script permissions
chmod +x setup.sh
chmod +x backend/scripts/*.sh
```

## Development Tools

### Recommended VS Code Extensions

- Python
- Pylance
- ESLint
- Prettier
- Docker
- GitLens
- Thunder Client (API testing)

### Database GUI

- pgAdmin: http://localhost:5050 (when using docker-compose)
- TablePlus, DBeaver, or DataGrip

### API Testing

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
- Postman or Insomnia

## Useful Commands

```bash
# Backend
make test         # Run tests
make lint         # Run linter
make format       # Format code
make migrate      # Run migrations

# Frontend
npm run build     # Build production
npm run lint      # Run linter
npm run type-check # Type checking

# Docker
docker-compose logs -f backend   # View backend logs
docker-compose exec backend bash # Enter backend container
docker-compose restart frontend  # Restart frontend

# Database
pg_dump stockcode > backup.sql   # Backup database
psql stockcode < backup.sql      # Restore database
```