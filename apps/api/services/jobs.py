import json
import logging
import os
import shutil
import uuid
from datetime import datetime

from fastapi import UploadFile

from audit import audit_engine
from models import JobState, JobStatus

# Configuration
DATA_DIR = "/data/workspaces"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)

logger = logging.getLogger(__name__)

class JobManager:
    def create_job(self, original: UploadFile, template: UploadFile) -> JobState:
        job_id = str(uuid.uuid4())
        job_dir = os.path.join(DATA_DIR, job_id)
        os.makedirs(job_dir, exist_ok=True)

        # Save files
        org_path = os.path.join(job_dir, "original.pptx")
        tpl_path = os.path.join(job_dir, "template.pptx")
        
        with open(org_path, "wb") as f:
            shutil.copyfileobj(original.file, f)
        with open(tpl_path, "wb") as f:
            shutil.copyfileobj(template.file, f)

        # Initialize State
        state = JobState(
            id=job_id,
            created_at=datetime.utcnow(),
            status=JobStatus.CREATED,
            original_filename=original.filename,
            template_filename=template.filename
        )
        self.save_state(job_id, state)
        return state

    def get_job(self, job_id: str) -> JobState:
        state_path = os.path.join(DATA_DIR, job_id, "state.json")
        if not os.path.exists(state_path):
            return None
        with open(state_path) as f:
            data = json.load(f)
            # Handle datetime parsing if needed, but pydantic usually handles isoformat
            return JobState(**data)

    def save_state(self, job_id: str, state: JobState):
        state_path = os.path.join(DATA_DIR, job_id, "state.json")
        with open(state_path, "w") as f:
            f.write(state.model_dump_json())

    def run_audit(self, job_id: str):
        # Placeholder for V1 audit logic
        # In real implementation, this would invoke the audit engine
        try:
            state = self.get_job(job_id)
            if not state:
                return
            
            state.status = JobStatus.RUNNING
            self.save_state(job_id, state)

            # Run Audit
            org_path = os.path.join(DATA_DIR, job_id, "original.pptx")
            summary = audit_engine.audit_deck(org_path)
            
            state.summary = summary
            state.status = JobStatus.COMPLETED
            self.save_state(job_id, state)
            
        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}")
            if state:
                state.status = JobStatus.FAILED
                state.error = str(e)
                self.save_state(job_id, state)

job_manager = JobManager()
