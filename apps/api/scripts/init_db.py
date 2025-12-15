"""
Database initialization script for Pultimate API.

Usage (Fly.io SSH):
    fly ssh console -a pultimate-api
    cd /app/apps/api
    python scripts/init_db.py

This script creates all SQLAlchemy tables defined in models/sql_models.py.
Idempotent: safe to run multiple times (CREATE TABLE IF NOT EXISTS).
"""
import asyncio
import os
import sys

# Ensure the app directory is in the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def mask_database_url(url: str) -> str:
    """Mask password in database URL for safe logging."""
    if "@" in url and "://" in url:
        # postgresql+asyncpg://user:password@host:port/db
        prefix = url.split("://")[0]
        rest = url.split("://")[1]
        if "@" in rest:
            user_pass = rest.split("@")[0]
            host_db = rest.split("@")[1]
            if ":" in user_pass:
                user = user_pass.split(":")[0]
                return f"{prefix}://{user}:****@{host_db}"
    return url


async def main() -> None:
    """Initialize database schema."""
    # Import after path setup
    # Force import all models to register them with Base.metadata
    import models.sql_models  # noqa: F401
    from core.config import settings
    from database import Base, engine
    
    print(f"Database URL: {mask_database_url(str(settings.SQLALCHEMY_DATABASE_URI))}")
    print(f"Tables to create: {list(Base.metadata.tables.keys())}")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("✓ Database schema created successfully.")
    print(f"  Created {len(Base.metadata.tables)} tables.")


if __name__ == "__main__":
    asyncio.run(main())
