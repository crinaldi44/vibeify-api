# Vibeify API

A modern FastAPI application with async SQLAlchemy and PostgreSQL database support.

## Features

- 🚀 **FastAPI** - High-performance async web framework
- 🗄️ **SQLAlchemy 2.0** - Modern async ORM with PostgreSQL
- 📦 **Alembic** - Database migration management
- ⚙️ **Pydantic Settings** - Environment-based configuration
- 🔄 **Async/Await** - Full async support throughout the stack
- 📝 **OpenAPI/Swagger** - Automatic API documentation
- 🔄 **Celery** - Distributed task queue for background jobs
- 📊 **Redis** - Message broker and result backend for Celery

## Requirements

- Python >= 3.12
- PostgreSQL >= 12
- Redis >= 7 (for Celery)
- Poetry (for dependency management)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd vibeify-api
   ```

2. **Install dependencies using Poetry**
   ```bash
   poetry install
   ```

   Or if you prefer pip:
   ```bash
   pip install -e .
   ```

3. **Set up environment variables**
   
   Create a `.env` file in the project root:
   ```env
   # Application Settings
   API_V1_PREFIX=/api/v1
   PROJECT_NAME=Vibeify API
   VERSION=0.1.0
   DEBUG=false

   # Database Configuration
   DB_HOST=localhost
   DB_PORT=5432
   DB_USER=postgres
   DB_PASSWORD=postgres
   DB_NAME=vibeify

   # Or use a complete DATABASE_URL (takes precedence over individual components)
   # DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/vibeify

   # CORS Settings (comma-separated)
   # CORS_ORIGINS=http://localhost:3000,http://localhost:8000
   
   # Redis/Celery Settings
   REDIS_URL=redis://localhost:6379/0
   # Optional: Override broker and backend separately
   # CELERY_BROKER_URL=redis://localhost:6379/0
   # CELERY_RESULT_BACKEND=redis://localhost:6379/0

   # Provider APIs (Serper)
   # SERPER_API_KEY=your-serper-api-key
   # SERPER_BASE_URL=https://google.serper.dev
   # SERPER_TIMEOUT_SECONDS=15
   # SERPER_MAX_CONCURRENCY=5
   # SERPER_MIN_INTERVAL_SECONDS=0.0
   # SERPER_MAX_RETRIES=2
   ```

4. **Set up the database**
   
   Make sure PostgreSQL is running and create the database:
   ```sql
   CREATE DATABASE vibeify;
   ```

## Running the Application

### Development Server

Run the development server with auto-reload:
```bash
poetry run uvicorn vibeify_api.main:app --reload
```

Or activate the virtual environment first:
```bash
poetry shell
uvicorn vibeify_api.main:app --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive API Docs (Swagger)**: http://localhost:8000/docs
- **Alternative API Docs (ReDoc)**: http://localhost:8000/redoc

### Running with Docker Compose

Start all services (database, Redis, API, Celery workers):
```bash
docker-compose up -d
```

Start specific services:
```bash
# Start only database and Redis
docker-compose up -d db redis

# Start Celery worker
docker-compose up -d celery

# Start Celery beat (for scheduled tasks)
docker-compose up -d celery-beat
```

View logs:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f celery
```

## Celery Background Tasks

This project includes Celery for running background tasks and scheduled jobs.

### Running Celery Worker

In development:
```bash
poetry run celery -A vibeify_api.core.celery_app worker --loglevel=info
```

With Docker:
```bash
docker-compose up celery
```

### Running Celery Beat (Scheduled Tasks)

For periodic/scheduled tasks:
```bash
poetry run celery -A vibeify_api.core.celery_app beat --loglevel=info
```

With Docker:
```bash
docker-compose up celery-beat
```

### Example: Creating a Scheduled Task

Here's an example of how to create a nightly report task:

**1. Create a task file** (`src/vibeify_api/tasks/reports.py`):
```python
from datetime import datetime
from typing import List

from vibeify_api.core.celery_app import celery_app
from vibeify_api.core.logging import get_logger
from vibeify_api.services.user import UserService

logger = get_logger(__name__)


@celery_app.task(name="tasks.reports.generate_daily_report")
def generate_daily_report() -> dict:
    """Generate a daily report of user activity.
    
    This task runs nightly to create reports.
    
    Returns:
        Dictionary with report data
    """
    logger.info("Starting daily report generation")
    
    try:
        # Example: Get user statistics
        user_service = UserService()
        # Note: You'll need to implement a method to get stats
        # users = await user_service.get_active_users_count()
        
        report = {
            "date": datetime.utcnow().isoformat(),
            "type": "daily_report",
            "status": "completed",
            # Add your report data here
        }
        
        logger.info(f"Daily report generated: {report}")
        return report
        
    except Exception as e:
        logger.error(f"Error generating daily report: {e}", exc_info=True)
        raise
```

**2. Register the task** in `src/vibeify_api/tasks/__init__.py`:
```python
from vibeify_api.core.celery_app import celery_app

# Import tasks to register them
from vibeify_api.tasks.reports import generate_daily_report  # noqa: F401

__all__ = ["celery_app"]
```

**3. Schedule the task** in `src/vibeify_api/core/celery_app.py`:
```python
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    "generate-daily-report": {
        "task": "tasks.reports.generate_daily_report",
        "schedule": crontab(hour=2, minute=0),  # Run at 2 AM daily
    },
}
```

**4. Call the task from your API** (optional):
```python
from vibeify_api.tasks.reports import generate_daily_report

# Trigger task immediately
result = generate_daily_report.delay()

# Or schedule it for later
from datetime import timedelta
result = generate_daily_report.apply_async(eta=datetime.utcnow() + timedelta(hours=1))
```

### Monitoring Celery Tasks

Check task status:
```bash
# Using Celery CLI
poetry run celery -A vibeify_api.core.celery_app inspect active
poetry run celery -A vibeify_api.core.celery_app inspect scheduled
poetry run celery -A vibeify_api.core.celery_app inspect stats
```

Or use Flower (optional, add to dependencies):
```bash
poetry add flower
poetry run celery -A vibeify_api.core.celery_app flower
```

## Database Migrations

This project uses Alembic for database migrations.

### Creating Migrations

After creating or modifying models, generate a migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

**Important**: Make sure to import your models in `alembic/env.py` so autogenerate can detect changes:
```python
from vibeify_api.models.your_model import YourModel
```

### Applying Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply migrations one step at a time
alembic upgrade +1

# Rollback one migration
alembic downgrade -1

# Rollback to a specific revision
alembic downgrade <revision>
```

### Migration Commands

```bash
# Show current database revision
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic heads
```

## Project Structure

```
vibeify-api/
├── alembic/                 # Database migrations
│   ├── versions/            # Migration files
│   ├── env.py              # Alembic environment config
│   └── script.py.mako      # Migration template
├── src/
│   └── vibeify_api/
│       ├── api/            # API routes
│       │   └── v1/         # API version 1
│       ├── core/           # Core functionality
│       │   ├── config.py   # Application settings
│       │   ├── database.py # Database connection
│       │   ├── celery_app.py # Celery configuration
│       │   └── logging.py  # Logging configuration
│       ├── models/         # SQLAlchemy models
│       ├── schemas/        # Pydantic schemas
│       ├── services/       # Business logic
│       ├── tasks/          # Celery background tasks
│       ├── tests/          # Test files
│       └── main.py         # FastAPI application entry point
├── alembic.ini             # Alembic configuration
├── pyproject.toml          # Project dependencies and config
└── .env                    # Environment variables (create this)
```

## Development

### Code Formatting

This project uses `ruff` for linting and formatting:
```bash
poetry run ruff check .
poetry run ruff format .
```

### Testing

Run tests with pytest:
```bash
poetry run pytest
```

### Adding New Models

1. Create your model in `src/vibeify_api/models/`:
   ```python
   from vibeify_api.models.base import BaseModel
   
   class YourModel(BaseModel):
       __tablename__ = "your_table"
       # Your fields here
   ```

2. Import it in `alembic/env.py` for migration autogenerate

3. Create a migration:
   ```bash
   alembic revision --autogenerate -m "Add YourModel"
   ```

4. Apply the migration:
   ```bash
   alembic upgrade head
   ```

## Configuration

Configuration is managed through environment variables and the `.env` file. All settings are defined in `vibeify_api/core/config.py`.

Key settings:
- `DATABASE_URL` or individual `DB_*` components
- `DEBUG` - Enable/disable debug mode
- `CORS_ORIGINS` - Allowed CORS origins (comma-separated)
- `REDIS_URL` - Redis connection URL for Celery
- `CELERY_BROKER_URL` - Optional override for Celery broker
- `CELERY_RESULT_BACKEND` - Optional override for Celery result backend

## API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /api/v1/` - API v1 root
- `POST /api/v1/search` - Provider-based search (eg Serper) returning normalized results
- `POST /api/v1/discovery` - CommonCrawl-based URL discovery + ingestion (async via Celery)

Interactive API documentation is available at `/docs` when the server is running.

### Provider-based search (`/api/v1/search`)

This endpoint is synchronous and will call the configured provider (default: Serper).
For large-scale ingestion, prefer a **batch/async workflow** (eg enqueue Celery jobs with per-task rate limits)
to avoid tying up HTTP workers and to better control throughput.

## License

[Add your license here]

## Contributing

[Add contributing guidelines here]
