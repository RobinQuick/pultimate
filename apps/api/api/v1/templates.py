"""Template upload and management endpoints."""
import logging
import os
import shutil
import tempfile
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

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
    """Upload and process a PowerPoint template.
    
    - Accepts .potx, .pptx files only
    - Maximum file size: 50MB (configurable)
    - Files stored in S3-compatible storage with 'templates/' prefix
    - Template is automatically ingested and published as version 1
    """
    # Use default workspace for POC
    workspace_id = "default-ws"
    tmp_path = None
    
    try:
        # 1. Create Template container first to get ID
        new_template = Template(
            workspace_id=workspace_id,
            name=name
        )
        db.add(new_template)
        await db.flush()  # Get the ID without committing
        
        logger.info(f"Created template record: {new_template.id} for user {current_user.email}")
        
        # 2. Upload to S3 with template ID as filename
        s3_key = await storage.upload_template(file, template_id=new_template.id)
        
        # 3. Ingest and process template (requires local file for python-pptx)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pptx") as tmp:
            file.file.seek(0)
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
        
        try:
            spec = ingestor.ingest(tmp_path)
            logger.info(f"Template ingested successfully: {new_template.id}")
        except Exception as e:
            logger.exception(f"Template ingestion failed: {e}")
            raise HTTPException(
                status_code=422,
                detail=f"Template processing failed: {str(e)}"
            ) from e
        
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
        
        logger.info(f"Template created and published: {new_template.id} -> {s3_key}")
        return spec
    
    except IntegrityError as e:
        await db.rollback()
        logger.exception(f"Database integrity error on template creation")
        raise HTTPException(
            status_code=400,
            detail="Database constraint violation. Ensure workspace exists."
        ) from e
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.exception(f"Unexpected error on template creation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Template creation failed: {str(e)}"
        ) from e
    finally:
        # Clean up temp file
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.get("/")
async def list_templates(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all templates in the default workspace."""
    from sqlalchemy import select
    
    result = await db.execute(
        select(Template).where(Template.workspace_id == "default-ws")
    )
    templates = result.scalars().all()
    
    return [
        {
            "id": t.id,
            "name": t.name,
            "is_archived": t.is_archived
        }
        for t in templates
    ]


@router.get("/{template_id}")
async def get_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific template with its latest version."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    
    result = await db.execute(
        select(Template)
        .where(Template.id == template_id)
        .options(selectinload(Template.versions))
    )
    template = result.scalars().first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Get latest version
    latest_version = max(template.versions, key=lambda v: v.version_num) if template.versions else None
    
    return {
        "id": template.id,
        "name": template.name,
        "is_archived": template.is_archived,
        "latest_version": {
            "version_num": latest_version.version_num,
            "status": latest_version.status,
            "config": latest_version.config_json
        } if latest_version else None
    }


@router.get("/{template_id}/download-url")
async def get_template_download_url(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a presigned URL to download the template file."""
    from sqlalchemy import select
    
    result = await db.execute(
        select(TemplateVersion)
        .where(TemplateVersion.template_id == template_id)
        .order_by(TemplateVersion.version_num.desc())
    )
    version = result.scalars().first()
    
    if not version:
        raise HTTPException(status_code=404, detail="Template version not found")
    
    # Construct filename from template name
    filename = f"template_{template_id}.pptx"
    url = await storage.generate_presigned_url(version.s3_key_potx, filename=filename)
    return {"download_url": url, "filename": filename, "expires_in": 900}
