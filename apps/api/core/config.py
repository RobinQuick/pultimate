
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Pultimate API"
    API_V1_STR: str = "/api/v1"
    
    # DB
    SQLALCHEMY_DATABASE_URI: str = "postgresql+asyncpg://pultimate:pultimate@localhost:5432/pultimate"
    
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

settings = Settings()
