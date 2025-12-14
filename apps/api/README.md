# Pultimate API

FastAPI backend for DeckLint+Fix - PowerPoint audit and correction platform.

## Quick Start (Local)

```bash
# Install dependencies
pip install -r requirements.txt

# Run API
uvicorn main:app --reload --port 8000
```

## Database Initialization

The API requires PostgreSQL with the schema created before first use.

### Fly.io Production

```bash
# SSH into Fly.io container
fly ssh console -a pultimate-api

# Initialize database schema
python scripts/init_db.py
```

### Local Development

```bash
# Ensure PostgreSQL is running
# Set DATABASE_URL environment variable or update core/config.py

# Initialize database
python scripts/init_db.py
```

## API Endpoints

- `GET /health` - Health check
- `POST /api/v1/auth/register` - Register user
- `POST /api/v1/auth/token` - Get JWT token
- `GET /api/v1/decks/` - List decks (auth required)
- `POST /api/v1/templates/` - Upload template (auth required)

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection URL | `postgresql+asyncpg://...` |
| `SECRET_KEY` | JWT signing key | `secret` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `RENDERING_ENABLED` | Enable LibreOffice rendering | `true` |

## Project Structure

```
apps/api/
├── main.py              # FastAPI app
├── database.py          # SQLAlchemy engine & Base
├── core/
│   └── config.py        # Settings (pydantic-settings)
├── models/
│   └── sql_models.py    # SQLAlchemy ORM models
├── api/v1/              # API routes
├── services/            # Business logic
└── scripts/
    └── init_db.py       # Database initialization
```
