# Task Completion Checklist

## Before Committing Code

### Backend Changes
1. **Code Quality**
   ```bash
   cd backend
   black .                 # Format code
   flake8                  # Check linting
   mypy .                  # Type checking
   ```

2. **Testing**
   ```bash
   pytest                  # Run all tests
   pytest --cov           # Check test coverage
   ```

3. **Database**
   ```bash
   # If models changed:
   alembic revision --autogenerate -m "descriptive message"
   alembic upgrade head   # Test migration
   ```

4. **Alembic Configuration Check**
   - [ ] `alembic.ini` exists in backend directory
   - [ ] `alembic/env.py` properly configured with:
     - Database URL from environment variables
     - Correct model metadata import
   - [ ] Migrations run without errors

### Frontend Changes
1. **Code Quality**
   ```bash
   cd frontend
   npm run lint            # ESLint checking
   npm run type-check      # TypeScript validation
   npm run format          # Prettier formatting
   ```

2. **Build Verification**
   ```bash
   npm run build           # Ensure production build works
   ```

### Both Backend and Frontend
1. **Integration Testing**
   ```bash
   docker-compose up       # Test full stack integration
   docker-compose down -v  # Clean up
   ```

## Security Checks
- [ ] No hardcoded secrets or API keys
- [ ] Environment variables properly configured
- [ ] CORS settings appropriate for environment
- [ ] Authentication/authorization implemented where needed

## Documentation Updates
- [ ] Update API documentation if endpoints changed
- [ ] Update README if setup instructions changed
- [ ] Update CLAUDE.md if development processes changed

## Git Best Practices
- [ ] Meaningful commit messages
- [ ] Atomic commits (one logical change per commit)
- [ ] Branch naming follows conventions
- [ ] Pull request includes description of changes

## Known Issues to Address
Based on CLAUDE.md, these critical items should be prioritized:
- [ ] Fix CORS configuration for production (Issue #30)
- [ ] Generate secure secret keys for production (Issue #30)
- [ ] Implement authentication system (Issue #34)
- [ ] Complete XBRL parser for EDINET data (Issue #33)
- [ ] Complete Alembic env.py configuration (Issue #31)
- [ ] Implement comprehensive test suite (Issue #32)

## Database Migration Checklist
- [ ] Alembic properly initialized (`alembic init alembic`)
- [ ] `alembic/env.py` configured with correct database URL
- [ ] Model metadata properly imported in env.py
- [ ] Migration runs without errors (`alembic upgrade head`)
- [ ] Database schema matches models