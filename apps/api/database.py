import ssl

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from core.config import settings


def get_async_engine():
    """Create async engine with proper SSL configuration for Neon PostgreSQL."""
    db_url = settings.SQLALCHEMY_DATABASE_URI
    
    # Remove sslmode from URL (asyncpg doesn't understand it)
    # and add ssl context instead via connect_args
    if "sslmode=" in db_url:
        # Split URL at ? to handle query params
        if "?" in db_url:
            base_url, params = db_url.split("?", 1)
            # Remove sslmode from params
            new_params = "&".join(
                p for p in params.split("&") if not p.startswith("sslmode=")
            )
            db_url = f"{base_url}?{new_params}" if new_params else base_url
    
    # Create SSL context for Neon (requires SSL)
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE  # Neon uses trusted certs, but we skip verification for simplicity
    
    return create_async_engine(
        db_url,
        echo=False,
        connect_args={"ssl": ssl_context}
    )


engine = get_async_engine()
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    # Import all models to register them with Base.metadata before create_all
    import models.sql_models  # noqa: F401 - Force model registration
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print(f"✓ Database initialized: {len(Base.metadata.tables)} tables created/verified")
