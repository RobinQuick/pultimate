import ssl
from urllib.parse import urlparse, parse_qs, urlencode

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from core.config import settings


def get_async_engine():
    """Create async engine with proper SSL configuration for Neon PostgreSQL."""
    db_url = settings.SQLALCHEMY_DATABASE_URI
    
    # Parse URL to handle query parameters
    parsed = urlparse(db_url)
    
    # Remove non-asyncpg-compatible parameters from Neon URLs
    # (sslmode, channel_binding, options, etc.)
    if parsed.query:
        params = parse_qs(parsed.query)
        # Keep only standard asyncpg parameters
        # Remove: sslmode, channel_binding, options, gssencmode, etc.
        filtered_params = {}
        for key, values in params.items():
            if key not in ("sslmode", "channel_binding", "options", "gssencmode"):
                filtered_params[key] = values[0]  # parse_qs returns lists
        
        # Reconstruct URL without problematic params
        new_query = urlencode(filtered_params) if filtered_params else ""
        db_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if new_query:
            db_url = f"{db_url}?{new_query}"
    
    # Create SSL context for Neon (requires SSL)
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE  # Neon uses trusted certs
    
    print(f"Database URL (masked): {parsed.scheme}://{parsed.username}:****@{parsed.hostname}{parsed.path}")
    
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
