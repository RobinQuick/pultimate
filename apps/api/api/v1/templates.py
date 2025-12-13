import os
import shutil
import tempfile

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.config import settings
from ...database import get_db
from ...deps import get_current_user
from ...models.sql_models import Template, TemplateVersion, User
from ...schemas.template_spec import TemplateSpec
from ...services.ingestion import ingestor
from ...services.storage import storage

router = APIRouter(prefix="/templates", tags=["templates"])

@router.post("/", response_model=TemplateSpec) # Returning spec for verifying immediate result
async def create_template(
    name: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Validate
    if not file.filename.lower().endswith(('.potx', '.pptx')):
         raise HTTPException(status_code=400, detail="Only .potx/.pptx allowed")

    # Mock Workspace
    workspace_id = "default-ws"
    # Ensure workspace exists (pseudo-check)
    # result = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    # if not result.scalars().first(): ...
    
    # 1. Create Template Container
    new_template = Template(
        workspace_id=workspace_id,
        name=name
    )
    db.add(new_template)
    await db.flush()
    
    # 2. Save File key
    s3_key = await storage.upload_file(file, settings.S3_BUCKET_TEMPLATES)
    
    # 3. Ingest Process (Sync for V1 simplicity, should be async job for large files)
    try:
        # Need local file for python-pptx
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pptx") as tmp:
            file.file.seek(0)
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
        
        spec = ingestor.ingest(tmp_path)
        os.unlink(tmp_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}") from e

    # 4. Create Version 1
    version = TemplateVersion(
        template_id=new_template.id,
        version_num=1,
        s3_key_potx=s3_key,
        config_json=spec.model_dump(mode='json'),
        status="PUBLISHED", # Auto-publish V1
        published_at=datetime.utcnow()
    )
    db.add(version)
    await db.commit()
    
    return spec
