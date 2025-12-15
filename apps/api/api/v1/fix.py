"""Fix/Restyle endpoints for applying corrections to presentations."""
from fastapi import APIRouter

router = APIRouter(prefix="/fix", tags=["fix"])


@router.post("/preview_fix")
async def preview_fix_endpoint():
    """Preview a fix before applying it.
    
    TODO: Implement when fix preview feature is needed.
    """
    return {"msg": "Fix preview not yet implemented"}


@router.post("/debug/run_fix_flow")  
async def debug_run_fix_flow():
    """Debug endpoint for testing the full fix flow.
    
    TODO: Implement full audit -> fix -> download flow.
    """
    return {"msg": "Use unit tests or separate components for now"}
