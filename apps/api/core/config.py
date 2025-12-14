
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Pultimate API"
    API_V1_STR: str = "/api/v1"
    
    # DB - Uses DATABASE_URL env var (Fly.io standard), transforms to async driver
    SQLALCHEMY_DATABASE_URI: str = Field(
        default="postgresql+asyncpg://pultimate:pultimate@localhost:5432/pultimate",
        alias="DATABASE_URL"
    )
    
    @field_validator("SQLALCHEMY_DATABASE_URI", mode="after")
    @classmethod
    def ensure_async_driver(cls, v: str) -> str:
        """Transform postgresql:// to postgresql+asyncpg:// for async SQLAlchemy."""
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgresql://") and "+asyncpg" not in v:
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v
    
    # Security
    SECRET_KEY: str = "secret"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # S3
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET_TEMPLATES: str = "templates"
    S3_BUCKET_DECKS: str = "decks"
    
    # Features
    RENDERING_ENABLED: bool = True

    class Config:
        case_sensitive = True
        populate_by_name = True

settings = Settings()
