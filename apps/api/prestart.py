import logging
import sys
import time
import json
import subprocess
from sqlalchemy import text, create_engine
from sqlalchemy.exc import OperationalError, ProgrammingError
from core.config import settings

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
    # Force sync driver if async is configured, or assume settings.SQLALCHEMY_DATABASE_URI works with create_engine
    # If URL is async (postgresql+asyncpg), we need to replace it for this script or use async engine.
    # For simplicity/reliability in scripts, replacing with sync driver 'postgresql+psycopg' or 'postgresql' is common.
    url = str(settings.SQLALCHEMY_DATABASE_URI)
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
            logger.warning(f"Database not ready yet (Attempt {i+1}/{MAX_RETRIES}): {e}")
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
    logger.info("Running pending migrations (alembic upgrade head)...")
    try:
        # Run alembic as subprocess to ensure clean state and separate logging
        subprocess.run(["alembic", "upgrade", "head"], check=True)
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

    if not wait_for_db(engine):
        sys.exit(1)

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
    main()
