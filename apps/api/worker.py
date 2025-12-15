"""Celery worker for async rebuild processing.

NO-GEN POLICY: This worker copies content, never generates.
"""

import json
import logging
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

from celery import Celery

from core.config import settings
from models.sql_models import DeckFile, RebuildJob, TemplateVersion
from services.job_events import emit_event
from services.llm_service import LLMValidationError, call_llm_for_mapping
from services.rebuild_service import (
    apply_mapping,
    parse_deck_elements,
    parse_template_placeholders,
)
from services.storage import storage

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


def _get_sync_session():
    """Create sync SQLAlchemy session for worker."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    # Convert async URL to sync
    db_url = settings.DATABASE_URL
    if "+asyncpg" in db_url:
        db_url = db_url.replace("+asyncpg", "")
    if "postgresql+asyncpg://" in db_url:
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    return Session()


def _add_artifact(
    session, job_id: str, artifact_type: str, s3_key: str, filename: str, size_bytes: int | None = None
):
    """Add a job artifact."""
    from models.sql_models import JobArtifact

    artifact = JobArtifact(
        job_id=job_id,
        artifact_type=artifact_type,
        s3_key=s3_key,
        filename=filename,
        size_bytes=size_bytes,
    )
    session.add(artifact)
    session.commit()
    return artifact


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def rebuild_deck_task(self, job_id: str):
    """
    Rebuild a deck using a template.

    NO-GEN POLICY: Content is ONLY copied, never generated.
    LLM only outputs mapping (ElementID -> PlaceholderID).

    Pipeline:
    1. Download deck + template from S3
    2. Parse deck elements
    3. Parse template placeholders
    4. Call LLM for mapping (strict JSON only)
    5. Apply mapping (copy content, no generation)
    6. Save output to S3
    7. Update job status + create artifacts
    """
    logger.info(f"[Job {job_id}] Starting rebuild task")

    session = _get_sync_session()
    work_dir = None

    try:
        # =====================================================================
        # STEP 1: Load job and validate
        # =====================================================================
        job = session.query(RebuildJob).filter(RebuildJob.id == job_id).first()
        if not job:
            logger.error(f"[Job {job_id}] Job not found")
            return {"status": "FAILED", "error": "Job not found"}

        # IDEMPOTENCE CHECK: If output exists and success, skip
        output_s3_key = f"jobs/{job_id}/output.pptx"
        if job.status == "SUCCEEDED" or storage.file_exists_sync(output_s3_key):
             logger.info(f"[Job {job_id}] Output already exists. Skipping rebuild.")
             # Ensure artifacts exist in DB if missing (repair state)
             # But for now, just return success
             return {"status": "SUCCEEDED", "message": "Idempotent skip"}

        # PROD CHECK: Ensure secrets exist
        if settings.LLM_PROVIDER == "openai" and not os.environ.get("OPENAI_API_KEY"):
            error_msg = "OPENAI_API_KEY missing in environment"
            emit_event(session, job_id, "FAILED", error_msg)
            job.status = "FAILED"
            job.error_message = error_msg
            session.commit()
            return {"status": "FAILED", "error": error_msg}

        # Update status to RUNNING
        job.status = "RUNNING"
        job.started_at = datetime.utcnow()
        job.progress = 5
        session.commit()
        emit_event(session, job_id, "STARTED", "Rebuild job started")

        # Check for dry_run mode
        dry_run = job.options.get("dry_run", False) if job.options else False
        logger.info(f"[Job {job_id}] Mode: {'DRY_RUN' if dry_run else 'FULL'}")

        # Get deck source file
        deck_file = (
            session.query(DeckFile).filter(DeckFile.deck_id == job.deck_id, DeckFile.type == "SOURCE").first()
        )
        if not deck_file:
            raise ValueError("Deck has no source file")

        # Get template version
        template_version = (
            session.query(TemplateVersion)
            .filter(
                TemplateVersion.template_id == job.template_id,
                TemplateVersion.status == "PUBLISHED",
            )
            .order_by(TemplateVersion.version_num.desc())
            .first()
        )
        if not template_version:
            raise ValueError("Template has no published version")

        job.progress = 10
        session.commit()

        # =====================================================================
        # STEP 2: Download inputs from S3
        # =====================================================================
        emit_event(session, job_id, "PROGRESS", "Downloading inputs from storage")

        work_dir = Path(tempfile.mkdtemp(prefix=f"rebuild_{job_id}_"))
        deck_path = work_dir / "input.pptx"
        template_path = work_dir / "template.pptx"

        # Download using new sync methods
        storage.download_file_sync(deck_file.s3_key, str(deck_path))
        storage.download_file_sync(template_version.s3_key_potx, str(template_path))

        if not deck_path.exists() or not template_path.exists():
            raise ValueError("Failed to download input files")

        job.progress = 25
        session.commit()
        emit_event(session, job_id, "DOWNLOADED", "Downloaded inputs from storage")

        # =====================================================================
        # STEP 3: Parse deck elements
        # =====================================================================
        emit_event(session, job_id, "PROGRESS", "Parsing deck elements")

        elements_result = parse_deck_elements(deck_path)
        logger.info(f"[Job {job_id}] Parsed {len(elements_result.elements)} elements")

        job.progress = 35
        session.commit()
        emit_event(session, job_id, "PARSED_DECK", f"Parsed {len(elements_result.elements)} elements")

        # =====================================================================
        # STEP 4: Parse template placeholders
        # =====================================================================
        emit_event(session, job_id, "PROGRESS", "Parsing template placeholders")

        placeholders_result = parse_template_placeholders(template_path)
        logger.info(f"[Job {job_id}] Parsed {len(placeholders_result.placeholders)} placeholders")

        job.progress = 45
        session.commit()
        emit_event(session, job_id, "PARSED_TEMPLATE", f"Parsed {len(placeholders_result.placeholders)} placeholders")

        # =====================================================================
        # STEP 5: Call LLM for mapping (NO-GEN - JSON only)
        # =====================================================================
        
        # IDEMPOTENCE: Check if mapping exists
        s3_mapping_key = f"jobs/{job_id}/mapping.json"
        mapping = None
        
        if storage.file_exists_sync(s3_mapping_key):
             logger.info(f"[Job {job_id}] Found existing mapping.json, skipping LLM.")
             emit_event(session, job_id, "PROGRESS", "Using existing mapping from storage")
             local_mapping_path = work_dir / "mapping.json"
             storage.download_file_sync(s3_mapping_key, str(local_mapping_path))
             try:
                 # Load and validate existing mapping
                 from models.sql_models import MappingResult  # Re-import just to be safe if moved
                 # Actually MappingResult is in schemas
                 from schemas.mapping_schema import MappingResult
                 mapping = MappingResult.model_validate_json(local_mapping_path.read_text())
             except Exception as e:
                 logger.warning(f"Failed to load existing mapping: {e}. Re-generating.")
                 mapping = None

        if not mapping:
            emit_event(session, job_id, "PROGRESS", "Generating element mapping via LLM")
            try:
                mapping = call_llm_for_mapping(
                    elements_result.elements, 
                    placeholders_result.placeholders
                )
                logger.info(f"[Job {job_id}] LLM mapping complete: {len(mapping.slide_mappings)} slides")

            except LLMValidationError as e:
                # Save failed mapping for debugging
                if e.raw_output:
                    raw_output = e.raw_output  # Capture before closure
                    mapping_path = work_dir / "failed_mapping.json"
                    mapping_path.write_text(raw_output)
                    # Upload as artifact
                    failed_key = f"jobs/{job_id}/failed_mapping.json"
                    storage.upload_bytes_sync(raw_output.encode(), failed_key)
                    _add_artifact(session, job_id, "MAPPING_JSON", failed_key, "failed_mapping.json")

                raise ValueError(f"LLM mapping failed: {e}")
            
            # Save mapping as artifact
            mapping_json = mapping.model_dump_json(indent=2)
            mapping_path = work_dir / "mapping.json"
            mapping_path.write_text(mapping_json)

            storage.upload_bytes_sync(mapping_json.encode(), s3_mapping_key)
            # Upsert logic skipped for simplicity, but acceptable for idempotence inside same job
            _add_artifact(session, job_id, "MAPPING_JSON", s3_mapping_key, "mapping.json", len(mapping_json))

        job.progress = 60
        session.commit()
        emit_event(
            session,
            job_id,
            "LLM_MAPPING",
            f"LLM mapping complete: {len(mapping.slide_mappings)} output slides",
            {"skipped": len(mapping.skipped_elements), "warnings": len(mapping.warnings)},
        )

        # =====================================================================
        # STEP 6: Apply mapping (DRY RUN stops here)
        # =====================================================================
        if dry_run:
            job.status = "SUCCEEDED"
            job.progress = 100
            job.completed_at = datetime.utcnow()
            session.commit()
            emit_event(session, job_id, "COMPLETED", "Dry run complete - mapping only")
            logger.info(f"[Job {job_id}] Dry run complete")
            return {"status": "SUCCEEDED", "mode": "dry_run", "job_id": job_id}

        # Apply mapping (NO-GEN - content copy only)
        emit_event(session, job_id, "PROGRESS", "Applying mapping to rebuild deck")

        output_dir = work_dir / "output"
        output_dir.mkdir()

        result = apply_mapping(deck_path, template_path, mapping, output_dir)

        if result.errors:
            raise ValueError(f"Apply mapping errors: {result.errors}")

        if not result.output_path or not result.output_path.exists():
            raise ValueError("No output file generated")

        job.progress = 85
        session.commit()
        emit_event(
            session,
            job_id,
            "MAPPING_APPLIED",
            f"Deck rebuilt: {result.slides_created} slides, {result.elements_mapped} elements",
            {"warnings": result.warnings},
        )

        # =====================================================================
        # STEP 7: Upload output to S3
        # =====================================================================
        emit_event(session, job_id, "PROGRESS", "Uploading output to storage")

        output_size = result.output_path.stat().st_size

        with open(result.output_path, "rb") as f:
            storage.upload_bytes_sync(f.read(), output_s3_key)

        _add_artifact(session, job_id, "OUTPUT_DECK", output_s3_key, "output.pptx", output_size)
        emit_event(session, job_id, "UPLOADED", "Output deck uploaded to storage")

        # =====================================================================
        # COMPLETE
        # =====================================================================
        job.status = "SUCCEEDED"
        job.progress = 100
        job.completed_at = datetime.utcnow()
        session.commit()
        emit_event(session, job_id, "COMPLETED", "Rebuild completed successfully")

        logger.info(f"[Job {job_id}] Completed successfully")
        return {
            "status": "SUCCEEDED",
            "job_id": job_id,
            "slides_created": result.slides_created,
            "elements_mapped": result.elements_mapped,
            "elements_skipped": result.elements_skipped,
        }

    except Exception as e:
        logger.error(f"[Job {job_id}] Failed: {e}", exc_info=True)

        try:
            job = session.query(RebuildJob).filter(RebuildJob.id == job_id).first()
            if job:
                job.status = "FAILED"
                job.error_message = str(e)[:500]
                job.completed_at = datetime.utcnow()
                session.commit()
                emit_event(session, job_id, "FAILED", str(e)[:500])
        except Exception:
            logger.exception("Failed to update job status")

        # Retry if appropriate
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)

        return {"status": "FAILED", "error": str(e)}

    finally:
        session.close()
        # Cleanup work directory
        if work_dir and work_dir.exists():
            try:
                shutil.rmtree(work_dir)
            except Exception:
                pass


# Legacy task for backwards compatibility
@celery_app.task
def process_deck(deck_id: str, file_key: str, template_id: str | None = None):
    """Legacy task - use rebuild_deck_task instead."""
    logger.warning("process_deck is deprecated, use rebuild_deck_task")
    return {"status": "DEPRECATED", "message": "Use rebuild_deck_task"}
