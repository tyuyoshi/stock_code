# Suggested Commands for Stock Code Development

## Setup Commands
```bash
./setup.sh              # Run initial setup
cp .env.example .env    # Configure environment variables
```

## Development Commands

### With Docker
```bash
docker-compose up       # Start all services
docker-compose logs -f  # View logs
docker-compose down -v  # Stop and remove volumes
```

### Backend Development (without Docker)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Alembic初期化（初回のみ）
alembic init alembic
# ※ この後 alembic/env.py の設定が必要

# データベースマイグレーション
alembic upgrade head
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development (without Docker)
```bash
cd frontend
npm install
npm run dev             # Start development server
npm run build           # Production build
npm start              # Start production server
```

## Quality Assurance Commands

### Backend Testing & Quality
```bash
cd backend
pytest                  # Run tests
pytest --cov           # Run tests with coverage
black .                 # Format code
flake8                  # Lint code
mypy .                  # Type checking
```

### Frontend Testing & Quality
```bash
cd frontend
npm run lint            # ESLint
npm run type-check      # TypeScript type checking
npm run format          # Prettier formatting
npm run build           # Verify production build
```

## Database Commands
```bash
cd backend
# Alembic初期化（初回のみ）
alembic init alembic

# 新しいマイグレーション作成
alembic revision --autogenerate -m "descriptive message"

# マイグレーション実行
alembic upgrade head

# マイグレーション履歴確認
alembic history

# 現在のリビジョン確認
alembic current
```

## Utility Commands (Darwin/macOS)
```bash
lsof -i :PORT          # Find process using port
ps aux | grep process  # Find running processes
find . -name "pattern" # Find files by pattern
grep -r "pattern" .    # Search for text in files
```

## Git Commands
```bash
git status             # Check working tree status
git add .              # Stage all changes
git commit -m "message" # Commit changes
git push origin main   # Push to remote
```

## Troubleshooting Commands
```bash
# Docker関連
docker-compose down -v && docker-compose up --build
docker system prune    # Clean up Docker resources

# Port関連
lsof -i :8000         # Check what's using port 8000
lsof -i :3000         # Check what's using port 3000

# Process関連
ps aux | grep uvicorn  # Find uvicorn processes
ps aux | grep node    # Find Node.js processes
```