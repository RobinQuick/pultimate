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

# Initialize database schema and seed default workspace
python -c "import asyncio; from database import init_db; asyncio.run(init_db())"
```

### Local Development

```bash
# Ensure PostgreSQL is running
# Set DATABASE_URL environment variable or update core/config.py

# Initialize database
python scripts/init_db.py
```

## S3-Compatible Storage Setup

The API uses S3-compatible storage (Cloudflare R2, MinIO, AWS S3) for file uploads.

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `S3_ENDPOINT_URL` | S3-compatible endpoint | `https://<account>.r2.cloudflarestorage.com` |
| `S3_ACCESS_KEY_ID` | Access key ID | `<your-access-key>` |
| `S3_SECRET_ACCESS_KEY` | Secret access key | `<your-secret-key>` |
| `S3_BUCKET` | Single bucket name | `pultimate` |
| `S3_REGION` | Region (use 'auto' for R2) | `auto` |
| `MAX_UPLOAD_SIZE_MB` | Max file upload size | `50` |

### Fly.io Secrets Setup

```bash
# Set S3 secrets for production
flyctl secrets set -a pultimate-api \
  S3_ENDPOINT_URL="https://<account-id>.r2.cloudflarestorage.com" \
  S3_ACCESS_KEY_ID="<your-access-key>" \
  S3_SECRET_ACCESS_KEY="<your-secret-key>" \
  S3_BUCKET="pultimate" \
  S3_REGION="auto"
```

### Cloudflare R2 Setup

1. Create R2 bucket named `pultimate` in Cloudflare dashboard
2. Create R2 API token with Object Read & Write permissions
3. Get Account ID from Cloudflare dashboard
4. Endpoint URL format: `https://<account-id>.r2.cloudflarestorage.com`
5. Set secrets as shown above

### File Organization

Files are organized in a single bucket with prefixes:
- `decks/{deck_id}.pptx` - Uploaded presentations
- `templates/{template_id}.pptx` - Corporate templates

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register user
- `POST /api/v1/auth/token` - Get JWT token

### Decks
- `POST /api/v1/decks/upload` - Upload deck (auth required)
- `GET /api/v1/decks/` - List user's decks
- `GET /api/v1/decks/{id}` - Get deck details
- `GET /api/v1/decks/{id}/download-url` - Get presigned download URL

### Templates
- `POST /api/v1/templates/` - Upload template (auth required)
- `GET /api/v1/templates/` - List templates
- `GET /api/v1/templates/{id}` - Get template details
- `GET /api/v1/templates/{id}/download-url` - Get presigned download URL

### Health
- `GET /health` - Health check

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection URL | `postgresql+asyncpg://...` |
| `SECRET_KEY` | JWT signing key | `secret` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `RENDERING_ENABLED` | Enable LibreOffice rendering | `true` |
| `S3_ENDPOINT_URL` | S3-compatible endpoint | `http://localhost:9000` |
| `S3_ACCESS_KEY_ID` | S3 access key | `minioadmin` |
| `S3_SECRET_ACCESS_KEY` | S3 secret key | `minioadmin` |
| `S3_BUCKET` | Storage bucket name | `pultimate` |
| `S3_REGION` | S3 region | `auto` |
| `MAX_UPLOAD_SIZE_MB` | Max upload size | `50` |

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
│   ├── auth.py          # Authentication
│   ├── decks.py         # Deck upload/management
│   └── templates.py     # Template management
├── services/
│   ├── storage.py       # S3-compatible storage
│   └── ingestion.py     # Template ingestion
└── scripts/
    └── init_db.py       # Database initialization
```

## File Upload Validation

- **Allowed extensions:** `.pptx`, `.potx`, `.ppt`
- **Maximum size:** 50MB (configurable via `MAX_UPLOAD_SIZE_MB`)
- **MIME types validated:** PowerPoint presentation/template types
