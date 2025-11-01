# Code Style and Conventions

## Python (Backend)

### Code Style
- **Formatter**: Black (line length: 88 characters)
- **Linter**: Flake8
- **Type Checker**: MyPy
- **Import Order**: Follow PEP 8 guidelines

### Naming Conventions
- **Variables/Functions**: snake_case
- **Classes**: PascalCase
- **Constants**: UPPER_SNAKE_CASE
- **Private attributes**: _leading_underscore

### Documentation
- **Docstrings**: Use triple quotes `"""` for module, class, and function docstrings
- **Comments**: Japanese comments are acceptable (seen in main.py)
- **Type Hints**: Required for all function parameters and return values

### FastAPI Conventions
- **App Configuration**: Centralized in main.py with descriptive title and docs URLs
- **API Endpoints**: Use routers in `api/routers/` directory
- **Response Models**: Use Pydantic models for API responses
- **Error Handling**: Use JSONResponse for consistent error responses

## TypeScript (Frontend)

### Code Style
- **Formatter**: Prettier
- **Linter**: ESLint with TypeScript rules
- **Import Order**: Automatic sorting via ESLint

### Naming Conventions
- **Variables/Functions**: camelCase
- **Components**: PascalCase
- **Constants**: UPPER_SNAKE_CASE
- **Types/Interfaces**: PascalCase

### React Conventions
- **Components**: Functional components with TypeScript
- **State Management**: Zustand for global state
- **Data Fetching**: React Query (@tanstack/react-query)
- **Forms**: react-hook-form with Zod validation
- **Styling**: Tailwind CSS with class-variance-authority for variants

### Project Structure
- **Pages**: App Router structure in `src/app/`
- **Components**: Reusable components in `src/components/`
- **Utilities**: Helper functions in `src/lib/`

## General Conventions

### File Organization
- **Imports**: Standard library → Third party → Local imports
- **File Names**: Use kebab-case for files, PascalCase for components
- **Directory Structure**: Feature-based organization

### Environment Variables
- **Backend**: Use python-dotenv, never commit .env files
- **Frontend**: Use Next.js environment variable conventions
- **Template**: Always maintain .env.example

### Error Handling
- **Backend**: Use FastAPI exception handling with proper HTTP status codes
- **Frontend**: Use error boundaries and proper error states
- **Logging**: Use structured logging with proper levels

### Testing
- **Backend**: pytest with async support
- **Frontend**: Setup available but not yet implemented
- **Coverage**: Aim for comprehensive test coverage