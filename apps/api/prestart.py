import json
import logging
import os
import subprocess
import sys
import time

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from core.config import settings

# Handle case where DATABASE_URL is not set (skip migrations)
DATABASE_URL = getattr(settings, "SQLALCHEMY_DATABASE_URI", None) or os.getenv("DATABASE_URL", "")


# --- JSON Logging Setup ---
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


logger = logging.getLogger("prestart")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())
logger.addHandler(handler)

# --- Config ---
# Stable key for Advisory Lock (Arbitrary large int)
MIGRATION_LOCK_ID = 4242424242
MAX_RETRIES = 30
SLEEP_INTERVAL = 2


def init_db_connection():
    """Create a sync engine for pre-start checks"""
    if not DATABASE_URL:
        logger.info("DATABASE_URL not set, skipping DB checks")
        return None

    url = DATABASE_URL
    if "asyncpg" in url:
        url = url.replace("+asyncpg", "")

    return create_engine(url)


def wait_for_db(engine):
    """Wait until DB is ready accepting connections"""
    logger.info("Waiting for database connection...")
    for i in range(MAX_RETRIES):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection established.")
            return True
        except OperationalError as e:
            logger.warning(f"Database not ready yet (Attempt {i + 1}/{MAX_RETRIES}): {e}")
            time.sleep(SLEEP_INTERVAL)

    logger.error("Could not connect to database after max retries.")
    return False


def acquire_advisory_lock(conn):
    """
    Try to acquire transaction-level advisory lock.
    Blocks until available (or we could use try_lock).
    Blocking is better here: we WANT to wait if another replica is migrating.
    """
    logger.info(f"Acquiring advisory lock {MIGRATION_LOCK_ID}...")
    try:
        conn.execute(text(f"SELECT pg_advisory_xact_lock({MIGRATION_LOCK_ID})"))
        return True
    except Exception as e:
        logger.error(f"Failed to acquire lock: {e}")
        raise


def run_migrations():
    """Run Alembic upgrades"""
    if os.getenv("SKIP_MIGRATIONS", "false").lower() == "true":
         logger.info("SKIP_MIGRATIONS is true, skipping alembic upgrade.")
         return

    logger.info(f"Current working directory: {os.getcwd()}")
    alembic_cfg = Path("alembic.ini")
    if not alembic_cfg.exists():
         logger.error(f"alembic.ini not found at {alembic_cfg.absolute()}")
         # Try to find it nearby for debugging context
         logger.info(f"Directory listing: {os.listdir('.')}")
         raise FileNotFoundError("alembic.ini not found")

    logger.info(f"Found alembic.ini at: {alembic_cfg.absolute()}")
    logger.info("Running pending migrations (alembic upgrade head)...")
    try:
        # Run alembic as subprocess to ensure clean state and separate logging
        # We use current python executable to ensure we use the same env
        subprocess.run([sys.executable, "-m", "alembic", "-c", "alembic.ini", "upgrade", "head"], check=True)
        logger.info("Migrations completed successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Migration failed with exit code {e.returncode}")
        raise


def main():
    logger.info("Starting Service Initialization (Prestart)")

    try:
        engine = init_db_connection()
    except Exception as e:
        logger.error(f"Failed to initialize DB engine config: {e}")
        sys.exit(1)

    if engine is None:
        logger.info("No database configured, skipping migrations.")
    elif not wait_for_db(engine):
        sys.exit(1)
    else:
        # Wrap migration in a transaction to hold the lock
        # pg_advisory_xact_lock automatically releases at end of transaction
        try:
            with engine.begin() as conn:
                acquire_advisory_lock(conn)
                # Run migrations (Safe because we hold the exclusive lock for this ID)
                run_migrations()
                # Lock released when 'with engine.begin()' exits (commits)
                logger.info("Advisory lock released.")
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            sys.exit(1)

    logger.info("Prestart complete. App is ready to launch.")


if __name__ == "__main__":
    from pathlib import Path  # Ensure Path is available
    main()
