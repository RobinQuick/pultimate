import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from database import get_db
from deps import get_current_user
from models.sql_models import Deck, DeckFile, User
from schemas.common import DeckResponse
from services.storage import storage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/decks", tags=["decks"])


@router.post("/upload", response_model=DeckResponse)
async def upload_deck(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload a PowerPoint deck for analysis."""
    # Validate extension
    if not file.filename.lower().endswith(('.pptx', '.ppt')):
        raise HTTPException(status_code=400, detail="Only .pptx/.ppt files allowed")
    
    # Use default workspace for POC
    workspace_id = "default-ws"
    
    try:
        # 1. Upload to S3
        s3_key = await storage.upload_file(file, settings.S3_BUCKET_DECKS)
        
        # 2. Create Deck record
        new_deck = Deck(
            workspace_id=workspace_id,
            owner_id=current_user.id
        )
        db.add(new_deck)
        await db.flush()
        
        # 3. Create DeckFile record
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
    
    except IntegrityError as e:
        await db.rollback()
        logger.exception("Database integrity error on deck upload")
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
        logger.exception("Unexpected error on deck upload")
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        ) from e


@router.get("/", response_model=list[DeckResponse])
async def list_decks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List decks for the current user."""
    # TODO: Implement proper query with workspace filtering
    return []
