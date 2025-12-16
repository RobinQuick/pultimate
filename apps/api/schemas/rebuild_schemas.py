"""Pydantic schemas for rebuild jobs API."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class JobStatus(str, Enum):
    """Rebuild job status lifecycle."""

    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class ArtifactType(str, Enum):
    """Types of artifacts produced by a rebuild job."""

    INPUT_DECK = "INPUT_DECK"
    INPUT_TEMPLATE = "INPUT_TEMPLATE"
    OUTPUT_DECK = "OUTPUT_DECK"
    MAPPING_JSON = "MAPPING_JSON"
    LOG = "LOG"


# =============================================================================
# Request Schemas
# =============================================================================


class RebuildJobCreate(BaseModel):
    """Request to create a new rebuild job."""

    deck_id: str
    template_id: str
    options: dict | None = None  # dry_run: bool, mode: str, etc.


class RebuildJobOptions(BaseModel):
    """Options for a rebuild job."""

    dry_run: bool = False  # If true, return mapping without generating output
    mode: str = "SAFE"  # SAFE, AGGRESSIVE


# =============================================================================
# Response Schemas
# =============================================================================


class RebuildJobResponse(BaseModel):
    """Response for a single rebuild job."""

    id: str
    deck_id: str
    template_id: str
    status: JobStatus
    progress: int
    options: dict | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None

    model_config = ConfigDict(from_attributes=True)


class RebuildJobDetail(RebuildJobResponse):
    """Detailed response including error details."""

    error_details: dict | None = None


class JobEventResponse(BaseModel):
    """Response for a job event."""

    id: str
    event_type: str
    message: str | None
    data: dict | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobArtifactResponse(BaseModel):
    """Response for a job artifact."""

    id: str
    artifact_type: ArtifactType
    filename: str
    size_bytes: int | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ArtifactWithUrl(JobArtifactResponse):
    """Artifact with presigned download URL."""

    download_url: str
    expires_in: int  # seconds


class JobArtifactsResponse(BaseModel):
    """Response containing all artifacts for a job."""

    job_id: str
    artifacts: list[ArtifactWithUrl]


class RebuildJobList(BaseModel):
    """Paginated list of rebuild jobs."""

    items: list[RebuildJobResponse]
    total: int


class ShareJobResponse(BaseModel):
    """Response when creating a share link."""
    share_url: str
    token: str
    expires_at: datetime


class SharedJobDetail(BaseModel):
    """Public details of a shared job."""

    id: str
    status: JobStatus
    progress: int
    created_at: datetime
    completed_at: datetime | None = None
    # evidence: dict | None = None  # Computed on frontend or backend?
    events: list[JobEventResponse]
    artifacts: list[ArtifactWithUrl]

