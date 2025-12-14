import os
import shutil
import tempfile

from fastapi import APIRouter, Depends, File, UploadFile

from deps import get_current_user
from models.sql_models import User
from schemas.common import AnalysisResponse, AnalysisStart
from schemas.slide_spec import DeckSpec
from services.parser import deck_parser
from worker import process_deck

router = APIRouter(prefix="/analysis", tags=["analysis"])

@router.post("/{deck_id}", response_model=AnalysisResponse)
async def run_analysis(
    deck_id: str,
    payload: AnalysisStart,
    current_user: User = Depends(get_current_user)
):
    # Trigger Celery
    task = process_deck.delay(deck_id)
    
    return AnalysisResponse(
        id=task.id, # Returning task ID as analysis ID for now, usually separate DB record
        status="PENDING",
        score=0
    )

@router.post("/debug/parse", response_model=DeckSpec)
async def debug_parse_deck(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pptx") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
        
    try:
        spec = deck_parser.parse(tmp_path, file.filename)
        return spec
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
