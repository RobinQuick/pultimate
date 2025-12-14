
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
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # S3-Compatible Storage (Cloudflare R2 / MinIO / AWS S3)
    S3_ENDPOINT_URL: str = Field(
        default="http://localhost:9000",
        description="S3-compatible endpoint URL (Cloudflare R2, MinIO, etc.)"
    )
    S3_ACCESS_KEY_ID: str = Field(
        default="minioadmin",
        description="S3 access key ID"
    )
    S3_SECRET_ACCESS_KEY: str = Field(
        default="minioadmin",
        description="S3 secret access key"
    )
    S3_BUCKET: str = Field(
        default="pultimate",
        description="Single bucket name - files organized by prefix (decks/, templates/)"
    )
    S3_REGION: str = Field(
        default="auto",
        description="S3 region (use 'auto' for Cloudflare R2)"
    )
    
    # Upload limits
    MAX_UPLOAD_SIZE_MB: int = Field(
        default=50,
        description="Maximum file upload size in megabytes"
    )
    
    # Legacy S3 settings (kept for backwards compatibility)
    S3_ENDPOINT: str = ""  # Will be set from S3_ENDPOINT_URL
    S3_ACCESS_KEY: str = ""  # Will be set from S3_ACCESS_KEY_ID
    S3_SECRET_KEY: str = ""  # Will be set from S3_SECRET_ACCESS_KEY
    S3_BUCKET_TEMPLATES: str = ""  # Deprecated - use S3_BUCKET with prefix
    S3_BUCKET_DECKS: str = ""  # Deprecated - use S3_BUCKET with prefix
    
    # Features
    RENDERING_ENABLED: bool = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set legacy vars from new standardized vars for backwards compatibility
        if not self.S3_ENDPOINT:
            object.__setattr__(self, 'S3_ENDPOINT', self.S3_ENDPOINT_URL)
        if not self.S3_ACCESS_KEY:
            object.__setattr__(self, 'S3_ACCESS_KEY', self.S3_ACCESS_KEY_ID)
        if not self.S3_SECRET_KEY:
            object.__setattr__(self, 'S3_SECRET_KEY', self.S3_SECRET_ACCESS_KEY)
        if not self.S3_BUCKET_TEMPLATES:
            object.__setattr__(self, 'S3_BUCKET_TEMPLATES', self.S3_BUCKET)
        if not self.S3_BUCKET_DECKS:
            object.__setattr__(self, 'S3_BUCKET_DECKS', self.S3_BUCKET)

    class Config:
        case_sensitive = True
        populate_by_name = True


settings = Settings()
