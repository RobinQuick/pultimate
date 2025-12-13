from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.config import settings
from ...database import get_db
from ...deps import get_current_user
from ...models.sql_models import Deck, DeckFile, User
from ...schemas.common import DeckResponse
from ...services.storage import storage

router = APIRouter(prefix="/decks", tags=["decks"])

@router.post("/upload", response_model=DeckResponse)
async def upload_deck(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Validate extension
    if not file.filename.lower().endswith(('.pptx', '.ppt')):
         raise HTTPException(status_code=400, detail="Only .pptx allowed")
         
    # Create Deck Record
    # Assuming workspace_id comes from user context or header in full impl
    # For now, pick first workspace or fail if logic depends on real multi-tenancy init
    # We'll mock workspace fetch for this demo
    workspace_id = "default-ws" # In real app, fetch from user.tenant.workspaces[0]
    
    # 1. Upload to S3
    s3_key = await storage.upload_file(file, settings.S3_BUCKET_UPLOADS)
    
    # 2. Save DB
    new_deck = Deck(
        workspace_id=workspace_id,
        owner_id=current_user.id
    )
    db.add(new_deck)
    await db.flush()
    
    new_file = DeckFile(
        deck_id=new_deck.id,
        type="SOURCE",
        s3_key=s3_key,
        filename=file.filename
    )
    db.add(new_file)
    await db.commit()
    await db.refresh(new_deck)
    
    return new_deck

@router.get("/", response_model=list[DeckResponse])
async def list_decks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Filtering query would go here
    return [] # Stub
