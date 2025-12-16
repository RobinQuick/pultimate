import sys

from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text, create_engine
from core.config import settings

def update_schema():
    print("Updating schema...")
    # Fix URL for sync engine
    db_url = settings.DATABASE_URL
    if "+asyncpg" in db_url:
        db_url = db_url.replace("+asyncpg", "")
    if "postgresql+asyncpg://" in db_url:
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

    engine = create_engine(db_url)
    with engine.connect() as conn:
        with conn.begin():
            conn.execute(text("ALTER TABLE rebuild_jobs ADD COLUMN IF NOT EXISTS share_token_hash VARCHAR"))
            conn.execute(text("ALTER TABLE rebuild_jobs ADD COLUMN IF NOT EXISTS share_expires_at TIMESTAMP"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_rebuild_jobs_share_token_hash ON rebuild_jobs (share_token_hash)"))
    print("Schema updated successfully.")

if __name__ == "__main__":
    update_schema()
