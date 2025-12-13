from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class JobStatus(str, Enum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class SlideStatus(str, Enum):
    CLEAN = "CLEAN"
    REVIEW = "REVIEW"
    REBUILD = "REBUILD"

class IssueSeverity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"

class AuditIssue(BaseModel):
    rule_id: str
    severity: IssueSeverity
    message: str
    slide_index: int

class SlideSummary(BaseModel):
    index: int
    status: SlideStatus
    issues: list[AuditIssue] = []

class JobState(BaseModel):
    id: str
    created_at: datetime
    status: JobStatus
    original_filename: str
    template_filename: str
    summary: list[SlideSummary] | None = []
    error: str | None = None
