"""Celery worker for async rebuild processing."""

import logging

from celery import Celery

from core.config import settings

logger = logging.getLogger(__name__)

celery_app = Celery("worker", broker=settings.REDIS_URL, backend=settings.REDIS_URL)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def rebuild_deck_task(self, job_id: str):
    """
    Rebuild a deck using a template.

    Pipeline:
    1. Download deck + template from R2
    2. Parse deck elements (TEXT/IMAGE/SHAPE with IDs)
    3. Parse template placeholders
    4. Call LLM for mapping (strict JSON, NO content generation)
    5. Apply mapping (copy content only)
    6. Save output to R2
    7. Update job status + create artifacts

    This task is designed to be retryable and idempotent.
    """
    from datetime import datetime

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from models.sql_models import JobEvent, RebuildJob

    logger.info(f"[Job {job_id}] Starting rebuild task")

    # Create sync engine for worker (Celery is sync)
    sync_url = settings.DATABASE_URL.replace("+asyncpg", "").replace("postgresql://", "postgresql://")
    engine = create_engine(sync_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Get job
        job = session.query(RebuildJob).filter(RebuildJob.id == job_id).first()
        if not job:
            logger.error(f"[Job {job_id}] Job not found")
            return {"status": "FAILED", "error": "Job not found"}

        # Update status to RUNNING
        job.status = "RUNNING"
        job.started_at = datetime.utcnow()
        job.progress = 5
        session.add(JobEvent(job_id=job_id, event_type="STARTED", message="Rebuild job started"))
        session.commit()
        logger.info(f"[Job {job_id}] Status: RUNNING")

        # TODO: Phase B implementation
        # 1. Download deck from R2
        # 2. Download template from R2
        # 3. Parse deck elements
        # 4. Parse template placeholders
        # 5. Call LLM for mapping
        # 6. Apply mapping
        # 7. Save output

        # For now, simulate work
        import time

        for i in range(10, 100, 10):
            time.sleep(0.5)  # Simulate processing
            job.progress = i
            session.commit()

        # Mark as succeeded (stub)
        job.status = "SUCCEEDED"
        job.progress = 100
        job.completed_at = datetime.utcnow()
        session.add(
            JobEvent(
                job_id=job_id,
                event_type="COMPLETED",
                message="Rebuild completed (stub)",
                data={"output": "pending_implementation"},
            )
        )
        session.commit()

        logger.info(f"[Job {job_id}] Completed successfully (stub)")
        return {"status": "SUCCEEDED", "job_id": job_id}

    except Exception as e:
        logger.error(f"[Job {job_id}] Failed: {e}")
        try:
            job = session.query(RebuildJob).filter(RebuildJob.id == job_id).first()
            if job:
                job.status = "FAILED"
                job.error_message = str(e)
                job.completed_at = datetime.utcnow()
                session.add(
                    JobEvent(
                        job_id=job_id,
                        event_type="FAILED",
                        message=str(e),
                    )
                )
                session.commit()
        except Exception:
            pass

        # Retry if appropriate
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        return {"status": "FAILED", "error": str(e)}

    finally:
        session.close()


# Legacy task for backwards compatibility
@celery_app.task
def process_deck(deck_id: str, file_key: str, template_id: str | None = None):
    """Legacy task - use rebuild_deck_task instead."""
    logger.warning("process_deck is deprecated, use rebuild_deck_task")
    return {"status": "DEPRECATED", "message": "Use rebuild_deck_task"}
