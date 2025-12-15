"""API endpoints for rebuild jobs."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from deps import get_current_user
from models.sql_models import (
    Deck,
    DeckFile,
    JobArtifact,
    RebuildJob,
    Template,
    TemplateVersion,
    User,
)
from schemas.rebuild_schemas import (
    ArtifactWithUrl,
    JobArtifactsResponse,
    RebuildJobCreate,
    RebuildJobDetail,
    RebuildJobList,
    RebuildJobResponse,
)
from services.storage import storage
from worker import rebuild_deck_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rebuild-jobs", tags=["rebuild-jobs"])

# Presigned URL expiration (1 hour)
DOWNLOAD_URL_EXPIRES_IN = 3600


@router.post("/", response_model=RebuildJobResponse, status_code=status.HTTP_201_CREATED)
async def create_rebuild_job(
    job_data: RebuildJobCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new rebuild job.

    This will:
    1. Validate deck and template exist
    2. Create job record with QUEUED status
    3. Enqueue worker task
    4. Return job ID for polling
    """
    # Validate deck exists and user has access
    deck_result = await db.execute(select(Deck).where(Deck.id == job_data.deck_id))
    deck = deck_result.scalars().first()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")

    # Get source file for the deck
    files_result = await db.execute(select(DeckFile).where(DeckFile.deck_id == deck.id, DeckFile.type == "SOURCE"))
    source_file = files_result.scalars().first()
    if not source_file:
        raise HTTPException(status_code=404, detail="Deck has no source file")

    # Validate template exists
    template_result = await db.execute(select(Template).where(Template.id == job_data.template_id))
    template = template_result.scalars().first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Get latest published template version
    version_result = await db.execute(
        select(TemplateVersion)
        .where(TemplateVersion.template_id == template.id, TemplateVersion.status == "PUBLISHED")
        .order_by(TemplateVersion.version_num.desc())
    )
    template_version = version_result.scalars().first()
    if not template_version:
        raise HTTPException(status_code=400, detail="Template has no published version")

    # Create job record
    job = RebuildJob(
        workspace_id=deck.workspace_id,
        user_id=current_user.id,
        deck_id=deck.id,
        template_id=template.id,
        status="QUEUED",
        progress=0,
        options=job_data.options,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    logger.info(f"Created rebuild job {job.id} for deck {deck.id} with template {template.id}")

    # Enqueue worker task
    try:
        rebuild_deck_task.delay(job.id)
        logger.info(f"Enqueued rebuild task for job {job.id}")
    except Exception as e:
        logger.error(f"Failed to enqueue task for job {job.id}: {e}")
        job.status = "FAILED"
        job.error_message = "Failed to enqueue worker task"
        await db.commit()
        raise HTTPException(status_code=500, detail="Failed to start rebuild job")

    return job


@router.get("/", response_model=RebuildJobList)
async def list_rebuild_jobs(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List rebuild jobs for the current user."""
    # Count total
    count_result = await db.execute(select(RebuildJob).where(RebuildJob.user_id == current_user.id))
    total = len(count_result.scalars().all())

    # Get paginated results
    result = await db.execute(
        select(RebuildJob)
        .where(RebuildJob.user_id == current_user.id)
        .order_by(RebuildJob.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    jobs = result.scalars().all()

    return RebuildJobList(items=jobs, total=total)


@router.get("/{job_id}", response_model=RebuildJobDetail)
async def get_rebuild_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get details of a specific rebuild job."""
    result = await db.execute(
        select(RebuildJob)
        .where(RebuildJob.id == job_id, RebuildJob.user_id == current_user.id)
        .options(selectinload(RebuildJob.events))
    )
    job = result.scalars().first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job


@router.get("/{job_id}/artifacts", response_model=JobArtifactsResponse)
async def get_job_artifacts(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all artifacts for a job with presigned download URLs."""
    # Verify job exists and belongs to user
    job_result = await db.execute(
        select(RebuildJob).where(RebuildJob.id == job_id, RebuildJob.user_id == current_user.id)
    )
    job = job_result.scalars().first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Get artifacts
    artifacts_result = await db.execute(select(JobArtifact).where(JobArtifact.job_id == job_id))
    artifacts = artifacts_result.scalars().all()

    # Generate presigned URLs
    artifacts_with_urls = []
    for artifact in artifacts:
        try:
            download_url = await storage.generate_presigned_url(
                artifact.s3_key,
                expires_in=DOWNLOAD_URL_EXPIRES_IN,
                filename=artifact.filename,
            )
            artifacts_with_urls.append(
                ArtifactWithUrl(
                    id=artifact.id,
                    artifact_type=artifact.artifact_type,
                    filename=artifact.filename,
                    size_bytes=artifact.size_bytes,
                    created_at=artifact.created_at,
                    download_url=download_url,
                    expires_in=DOWNLOAD_URL_EXPIRES_IN,
                )
            )
        except Exception as e:
            logger.error(f"Failed to generate presigned URL for artifact {artifact.id}: {e}")

    return JobArtifactsResponse(job_id=job_id, artifacts=artifacts_with_urls)
