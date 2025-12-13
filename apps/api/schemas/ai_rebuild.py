from typing import Literal

from pydantic import BaseModel

# --- Slide Intent ---

class LogicalBlock(BaseModel):
    id: str # internal ID
    role: str # HEADER, BODY_COL_1, BODY_COL_2, FOOTER, CHART_LEGEND
    element_ids: list[str] # List of element IDs from SlideSpec belonging to this block

class SlideIntent(BaseModel):
    slide_type: Literal[
        "UNKNOWN", "TITLE", "AGENDA", "SECTION_HEADER", 
        "CONTENT_1_COL", "CONTENT_2_COL", "CONTENT_3_COL", 
        "BIG_NUMBER", "QUOTE", "TEAM", "CHART"
    ] = "UNKNOWN"
    description: str # "Two columns of text with a header"
    logical_blocks: list[LogicalBlock] = []
    content_density: Literal["LOW", "MEDIUM", "HIGH"] = "MEDIUM"
    confidence: float = 0.0

# --- Rebuild Plan ---

class ElementMapping(BaseModel):
    source_element_id: str
    target_placeholder_idx: int
    transform_action: Literal["MOVE", "COPY", "MERGE"] = "MOVE" # MERGE if multiple sources go to one placeholder

class StyleTransform(BaseModel):
    element_id: str
    action: Literal["PROMOTE_HEADING", "DEMOTE_BULLET", "RESET_STYLE", "APPLY_COLOR"]
    params: dict[str, str] = {} # e.g. {"level": "1"}

class RebuildPlan(BaseModel):
    source_slide_index: int
    target_layout_index: int # Index in the Template Master
    target_master_index: int = 0
    mappings: list[ElementMapping] = []
    transforms: list[StyleTransform] = []
    reasoning: str # Explainability trace
    safety_flags: list[str] = [] # "Potential Text Truncation", "Overlap Risk"
