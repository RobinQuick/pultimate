import logging
import os
import shutil
import tempfile
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from database import get_db
from deps import get_current_user
from models.sql_models import Template, TemplateVersion, User
from schemas.template_spec import TemplateSpec
from services.ingestion import ingestor
from services.storage import storage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/templates", tags=["templates"])


@router.post("/", response_model=TemplateSpec)
async def create_template(
    name: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload and process a PowerPoint template."""
    # Validate file type
    if not file.filename.lower().endswith(('.potx', '.pptx')):
        raise HTTPException(status_code=400, detail="Only .potx/.pptx files allowed")

    # Use default workspace for POC
    workspace_id = "default-ws"
    
    try:
        # 1. Create Template container
        new_template = Template(
            workspace_id=workspace_id,
            name=name
        )
        db.add(new_template)
        await db.flush()
        
        # 2. Upload to S3
        s3_key = await storage.upload_file(file, settings.S3_BUCKET_TEMPLATES)
        
        # 3. Ingest and process template
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pptx") as tmp:
            file.file.seek(0)
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
        
        try:
            spec = ingestor.ingest(tmp_path)
        finally:
            os.unlink(tmp_path)
        
        # 4. Create TemplateVersion
        version = TemplateVersion(
            template_id=new_template.id,
            version_num=1,
            s3_key_potx=s3_key,
            config_json=spec.model_dump(mode='json'),
            status="PUBLISHED",
            published_at=datetime.utcnow()
        )
        db.add(version)
        await db.commit()
        
        return spec
    
    except IntegrityError as e:
        await db.rollback()
        logger.exception("Database integrity error on template creation")
        raise HTTPException(
            status_code=400,
            detail="Database constraint violation. Ensure workspace exists."
        ) from e
    except AttributeError as e:
        logger.exception("Configuration error")
        raise HTTPException(
            status_code=500,
            detail=f"Server configuration error: {e}"
        ) from e
    except Exception as e:
        await db.rollback()
        logger.exception("Unexpected error on template creation")
        raise HTTPException(
            status_code=500,
            detail=f"Template creation failed: {str(e)}"
        ) from e
