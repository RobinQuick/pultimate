"""Deck upload and management endpoints."""

import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from deps import get_current_user
from models.sql_models import Deck, DeckFile, User
from schemas.common import DeckResponse
from services.storage import storage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/decks", tags=["decks"])


@router.post("/upload", response_model=DeckResponse)
async def upload_deck(
    file: UploadFile = File(...), current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Upload a PowerPoint deck for analysis.

    - Accepts .pptx, .ppt files only
    - Maximum file size: 50MB (configurable)
    - Files stored in S3-compatible storage with 'decks/' prefix
    """
    # Use default workspace for POC
    workspace_id = "default-ws"

    try:
        # 1. Create Deck record first to get ID
        new_deck = Deck(workspace_id=workspace_id, owner_id=current_user.id)
        db.add(new_deck)
        await db.flush()  # Get the ID without committing

        logger.info(f"Created deck record: {new_deck.id} for user {current_user.email}")

        # 2. Upload to S3 with deck ID as filename
        s3_key = await storage.upload_deck(file, deck_id=new_deck.id)

        # 3. Create DeckFile record
        new_file = DeckFile(deck_id=new_deck.id, type="SOURCE", s3_key=s3_key, filename=file.filename)
        db.add(new_file)
        await db.commit()
        await db.refresh(new_deck)

        logger.info(f"Deck upload complete: {new_deck.id} -> {s3_key}")
        return new_deck

    except IntegrityError as e:
        await db.rollback()
        logger.exception(f"Database integrity error on deck upload for user {current_user.id}")
        raise HTTPException(status_code=400, detail="Database constraint violation. Ensure workspace exists.") from e
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.exception(f"Unexpected error on deck upload: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}") from e


@router.get("/", response_model=list[DeckResponse])
async def list_decks(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """List decks for the current user."""
    from sqlalchemy import select

    result = await db.execute(select(Deck).where(Deck.owner_id == current_user.id))
    decks = result.scalars().all()
    return decks


@router.get("/{deck_id}", response_model=DeckResponse)
async def get_deck(deck_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get a specific deck by ID."""
    from sqlalchemy import select

    result = await db.execute(select(Deck).where(Deck.id == deck_id, Deck.owner_id == current_user.id))
    deck = result.scalars().first()

    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")

    return deck


@router.get("/{deck_id}/download-url")
async def get_deck_download_url(
    deck_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Get a presigned URL to download the deck file."""
    from sqlalchemy import select

    result = await db.execute(select(DeckFile).where(DeckFile.deck_id == deck_id, DeckFile.type == "SOURCE"))
    deck_file = result.scalars().first()

    if not deck_file:
        raise HTTPException(status_code=404, detail="Deck file not found")

    url = await storage.generate_presigned_url(deck_file.s3_key, filename=deck_file.filename)
    return {"download_url": url, "filename": deck_file.filename, "expires_in": 900}
