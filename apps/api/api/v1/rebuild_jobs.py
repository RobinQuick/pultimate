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
from pathlib import Path
from schemas.rebuild_schemas import (
    ArtifactWithUrl,
    JobArtifactsResponse,
    JobEventResponse,
    RebuildJobCreate,
    RebuildJobDetail,
    RebuildJobList,
    RebuildJobResponse,
    ShareJobResponse,
    SharedJobDetail,
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


@router.get("/{job_id}/events", response_model=list[JobEventResponse])
async def get_job_events(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get timeline events for a job."""
    from models.sql_models import JobEvent

    # Verify job ownership
    job_result = await db.execute(
        select(RebuildJob).where(RebuildJob.id == job_id, RebuildJob.user_id == current_user.id)
    )
    if not job_result.scalars().first():
        raise HTTPException(status_code=404, detail="Job not found")

    # Fetch events ordered by time
    events_result = await db.execute(
        select(JobEvent).where(JobEvent.job_id == job_id).order_by(JobEvent.created_at.desc())
    )
    return events_result.scalars().all()


@router.post("/demo", response_model=RebuildJobResponse)
async def create_demo_job(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Start a 'One-Click' demo job using the Golden Set case 001.
    If 'Demo Deck' or 'Demo Template' don't exist for user, they are created.
    """
    # Define demo asset paths
    BASE_DIR = Path(__file__).resolve().parents[3]  # apps/api
    CASE_DIR = BASE_DIR / "golden_set" / "cases" / "case_001"

    DEMO_DECK_NAME = "Demo Deck (Golden Sample)"
    DEMO_TEMPLATE_NAME = "Demo Template (Golden Sample)"

    if not CASE_DIR.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Demo assets missing on server: {CASE_DIR}"
        )

    # 1. Ensure Demo Deck
    deck_result = await db.execute(
        select(Deck).where(Deck.user_id == current_user.id, Deck.name == DEMO_DECK_NAME)
    )
    deck = deck_result.scalars().first()

    if not deck:
        # Create deck
        deck = Deck(
            name=DEMO_DECK_NAME,
            workspace_id=current_user.active_workspace_id or "default", # Fallback if needed
            owner_id=current_user.id,
        )
        # Handle workspace if null (shouldn't be ifauth is correct but safe)
        if not deck.workspace_id:
             # Find a workspace
             from models.sql_models import Workspace
             ws = (await db.execute(select(Workspace).where(Workspace.owner_id == current_user.id))).scalars().first()
             if ws:
                 deck.workspace_id = ws.id
             else:
                 # Should fail or create default?
                 # For demo let's assume valid user state or fail hard
                 pass

        db.add(deck)
        await db.commit()
        await db.refresh(deck)

        # Upload file
        input_file = CASE_DIR / "input.pptx"
        s3_key = await storage.upload_bytes(input_file.read_bytes(), f"decks/{deck.id}.pptx")

        # Create DeckFile record
        deck_file = DeckFile(
            deck_id=deck.id,
            type="SOURCE",
            filename="demo_input.pptx",
            s3_key=s3_key,
            size_bytes=input_file.stat().st_size
        )
        db.add(deck_file)
        await db.commit()
        logger.info(f"Created demo deck: {deck.id}")

    # 2. Ensure Demo Template
    tpl_result = await db.execute(
        select(Template).where(Template.user_id == current_user.id, Template.name == DEMO_TEMPLATE_NAME)
    )
    template = tpl_result.scalars().first()

    if not template:
        template = Template(
            name=DEMO_TEMPLATE_NAME,
            workspace_id=deck.workspace_id,
            user_id=current_user.id,
        )
        db.add(template)
        await db.commit()
        await db.refresh(template)

        # Upload files
        potx_file = CASE_DIR / "template.pptx" # Uses pptx as potx source for demo
        if not potx_file.exists():
             potx_file = CASE_DIR / "template.potx"

        s3_key = await storage.upload_bytes(potx_file.read_bytes(), f"templates/{template.id}/v1.potx")

        # Create Version
        version = TemplateVersion(
            template_id=template.id,
            version_num=1,
            s3_key_potx=s3_key,
            filename=potx_file.name,
            status="PUBLISHED",
        )
        db.add(version)
        await db.commit()
        logger.info(f"Created demo template: {template.id}")

    # 3. Create Job
    job = RebuildJob(
        workspace_id=deck.workspace_id,
        user_id=current_user.id,
        deck_id=deck.id,
        template_id=template.id,
        status="QUEUED",
        progress=0,
        options={"demo_mode": True},
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Enqueue
    rebuild_deck_task.delay(job.id)

    return job


@router.post("/{job_id}/share", response_model=ShareJobResponse)
async def share_rebuild_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate a shareable link for a rebuild job.
    Token is valid for 7 days.
    """
    import secrets
    import hashlib
    from datetime import datetime, timedelta
    from core.config import settings

    # Verify job ownership
    job_result = await db.execute(
        select(RebuildJob).where(RebuildJob.id == job_id, RebuildJob.user_id == current_user.id)
    )
    job = job_result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Generate token
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    expires_at = datetime.utcnow() + timedelta(days=7)

    job.share_token_hash = token_hash
    job.share_expires_at = expires_at
    await db.commit()

    # Construct URL (Frontend URL)
    base_url = settings.API_BASE or "http://localhost:3000"
    share_url = f"{base_url}/share/{token}"

    return ShareJobResponse(share_url=share_url, token=token, expires_at=expires_at)


@router.get("/shared/{token}", response_model=SharedJobDetail)
async def get_shared_job(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get public details of a shared job.
    """
    import hashlib
    from datetime import datetime

    token_hash = hashlib.sha256(token.encode()).hexdigest()

    # Find job
    result = await db.execute(
        select(RebuildJob)
        .where(RebuildJob.share_token_hash == token_hash)
        .options(selectinload(RebuildJob.events))
    )
    job = result.scalars().first()

    if not job:
        raise HTTPException(status_code=404, detail="Shared job not found")

    # Check expiry
    if job.share_expires_at and job.share_expires_at < datetime.utcnow():
         raise HTTPException(status_code=410, detail="Share link expired")

    # Get Whitelisted Artifacts (Output Deck + Mapping)
    artifacts_result = await db.execute(
        select(JobArtifact).where(
            JobArtifact.job_id == job.id,
            JobArtifact.artifact_type.in_(["OUTPUT_DECK", "MAPPING_JSON"])
        )
    )
    artifacts = artifacts_result.scalars().all()

    # Generate presigned URLs
    artifacts_with_urls = []
    for artifact in artifacts:
        try:
            download_url = await storage.generate_presigned_url(
                artifact.s3_key,
                expires_in=3600,
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
                    expires_in=3600,
                )
            )
        except Exception as e:
            logger.error(f"Failed to generate presigned URL for shared artifact {artifact.id}: {e}")

    return SharedJobDetail(
        id=job.id,
        status=job.status,
        progress=job.progress,
        created_at=job.created_at,
        completed_at=job.completed_at,
        events=job.events,
        artifacts=artifacts_with_urls,
    )
