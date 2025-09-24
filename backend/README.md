# BRS Backend

Backend service for the Business Registration System prototype.

## Architecture

The backend follows a modular structure organized under the `brs_backend/` directory:

```
backend/
├── brs_backend/              # Main application module
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── core/                # Core configuration and utilities
│   │   ├── config.py        # Environment configuration
│   │   └── logging.py       # Logging configuration
│   ├── database/            # Database connection and utilities
│   │   └── connection.py    # SQLAlchemy engine and session
│   ├── models/              # Data models
│   │   └── database.py      # SQLAlchemy models (User, Course, Request, etc.)
│   ├── agents/              # AI agents for student/advisor interactions
│   │   ├── __init__.py      # Agent initialization and validation
│   │   ├── student_tools.py # Student-specific tool functions
│   │   └── advisor_tools.py # Advisor-specific tool functions
│   ├── api/                 # REST API endpoints
│   │   ├── users.py         # User management endpoints
│   │   ├── requests.py      # Request management endpoints
│   │   ├── courses.py       # Course information endpoints
│   │   └── chat.py          # AI chat endpoints
│   └── seed_personas.py     # Database seeding script
├── entrypoint.sh            # Docker container entrypoint
├── Dockerfile              # Container definition
├── pyproject.toml          # Python project configuration (uv)
├── requirements.txt        # Python dependencies (Docker)
├── run_tests.sh           # Test execution script
└── tests/                 # Test files
```

## Development Setup

### Prerequisites

- Python 3.11+
- uv (for dependency management)
- Docker and Docker Compose (for running the full application)

### Configuration Requirements

The application requires the following environment variables (no defaults provided):

- `OPENAI_API_KEY`: OpenAI API key for AI agents (required)
- `OPENAI_API_BASE`: OpenAI API base URL (required - e.g., https://api.openai.com/v1 or http://localhost:11434/v1 for Ollama)
- `OPENAI_MODEL`: OpenAI model to use (required - e.g., gpt-4o-mini or llama3.2:latest for Ollama)
- `DATABASE_URL`: PostgreSQL connection string (required)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `ENABLE_DETAILED_LOGGING`: Enable detailed logging (true/false)

The application validates API configuration at startup and will log errors if any required configuration is missing or invalid.

## Database Reset

To reset the database to a clean state with fresh persona data:

### Method 1: Complete System Reset (Recommended)

```bash
# Stop all containers and clean up
docker-compose down
docker system prune -f

# Remove any existing log files
rm -f backend/app.log backend/*.log

# Start only the database first
docker-compose up -d db
sleep 5

# Start all services (database seeding happens automatically via entrypoint.sh)
docker-compose up -d
```

### Method 2: Manual Database Reset

If you need to reset the database manually:

```bash
# Run the seed script directly
docker-compose exec backend python -m brs_backend.seed_personas

# Or run with Sarah's enrollments for testing
docker-compose exec backend python -m brs_backend.seed_personas --enroll_sarah
```

### Verify Database Reset

Check that the database has been properly seeded:

```bash
docker-compose exec db psql -U postgres -d brs_prototype_db -c "
SELECT 'users' as table_name, COUNT(*) as count FROM users
UNION SELECT 'courses', COUNT(*) FROM courses
UNION SELECT 'sections', COUNT(*) FROM sections
UNION SELECT 'requests', COUNT(*) FROM requests
ORDER BY table_name;"
```

Expected output after reset:
- courses: 8
- requests: 0
- sections: 6
- users: 7

## Development Commands

### Local Development (without Docker)

```bash
# Install dependencies
uv sync

# Set up environment variables in .env file (copy from .env.example)
cp ../.env.example ../.env
# Edit .env with your configuration

# Run the seed script
uv run -m brs_backend.seed_personas

# Start the development server
uv run uvicorn brs_backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Testing

```bash
# Run tests
./run_tests.sh
```

## Entry Points

- **Main Application**: `brs_backend.main:app` - FastAPI application
- **Database Seeding**: `python -m brs_backend.seed_personas` - Populates database with test personas and courses
- **Container Entry**: `entrypoint.sh` - Docker container startup script

## Configuration

The backend requires environment variables for configuration:

- `OPENAI_API_KEY`: OpenAI API key for AI agents (required)
- `OPENAI_API_BASE`: OpenAI API base URL (required - e.g., https://api.openai.com/v1 for OpenAI or http://host.docker.internal:11434/v1 for Ollama)
- `OPENAI_MODEL`: OpenAI model to use (required - e.g., gpt-4o-mini for OpenAI or qwen3:latest for Ollama)
- `DATABASE_URL`: PostgreSQL connection string (required)
- `DEBUG`: Enable debug mode (optional, default: false)
- `LOG_LEVEL`: Logging level (optional, default: info)
