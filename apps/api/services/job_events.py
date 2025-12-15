"""Job events service helpers."""

import logging
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from models.sql_models import JobEvent

logger = logging.getLogger(__name__)


def emit_event(
    session: Session,
    job_id: str,
    event_type: str,
    message: str,
    data: Optional[dict[str, Any]] = None,
) -> JobEvent:
    """Emit a job event.

    Args:
        session: DB session
        job_id: Rebuild job ID
        event_type: Event type string (e.g. STARTED, COMPLETED)
        message: Human readable message
        data: Optional metadata dict

    Returns:
        Created JobEvent
    """
    try:
        event = JobEvent(
            job_id=job_id,
            event_type=event_type,
            message=message,
            data=data,
            created_at=datetime.utcnow(),
        )
        session.add(event)
        session.commit()
        return event
    except Exception as e:
        logger.error(f"Failed to emit event {event_type} for job {job_id}: {e}")
        session.rollback()
        raise
