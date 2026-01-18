# Vibeify API

A modern FastAPI application with async SQLAlchemy and PostgreSQL database support.

## Features

- 🚀 **FastAPI** - High-performance async web framework
- 🗄️ **SQLAlchemy 2.0** - Modern async ORM with PostgreSQL
- 📦 **Alembic** - Database migration management
- ⚙️ **Pydantic Settings** - Environment-based configuration
- 🔄 **Async/Await** - Full async support throughout the stack
- 📝 **OpenAPI/Swagger** - Automatic API documentation

## Requirements

- Python >= 3.12
- PostgreSQL >= 12
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
│       │   └── database.py # Database connection
│       ├── models/         # SQLAlchemy models
│       ├── schemas/        # Pydantic schemas
│       ├── services/       # Business logic
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

## API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /api/v1/` - API v1 root

Interactive API documentation is available at `/docs` when the server is running.

## License

[Add your license here]

## Contributing

[Add contributing guidelines here]
