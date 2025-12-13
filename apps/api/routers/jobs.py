from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile

from ..models import JobState
from ..services.jobs import job_manager

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])

@router.post("", response_model=JobState)
async def create_job(
    original_file: UploadFile = File(...),
    template_file: UploadFile = File(...)
):
    return job_manager.create_job(original_file, template_file)

@router.post("/{job_id}/run")
async def run_job(job_id: str, background_tasks: BackgroundTasks):
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    background_tasks.add_task(job_manager.run_audit, job_id)
    return {"message": "Job execution started", "job_id": job_id}

@router.get("/{job_id}", response_model=JobState)
async def get_job(job_id: str):
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
