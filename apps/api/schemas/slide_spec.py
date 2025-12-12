from pydantic import BaseModel
from typing import List, Optional, Any, Dict

class BoundingBox(BaseModel):
    x: float
    y: float
    width: float
    height: float

class TextStyle(BaseModel):
    font_family: Optional[str] = None
    font_size: Optional[float] = None
    is_bold: bool = False
    is_italic: bool = False
    color_hex: Optional[str] = None
    alignment: Optional[str] = None # LEFT, CENTER, RIGHT, JUSTIFY

class ElementSpec(BaseModel):
    id: str
    type: str # TEXT, SHAPE, IMAGE, TABLE, GROUP, CHART
    name: str
    bbox: BoundingBox
    rotation: float = 0.0
    z_order: int
    
    # Text Specific
    text_content: Optional[str] = None
    text_style: Optional[TextStyle] = None
    
    # Image Specific
    is_stretched: bool = False
    original_size: Optional[Dict[str, float]] = None
    
    # Shape Specific
    fill_color: Optional[str] = None

class SlideStats(BaseModel):
    used_fonts: List[str] = []
    used_colors: List[str] = []
    text_coverage_pct: float = 0.0

class SlideSpec(BaseModel):
    index: int
    layout_name: str
    elements: List[ElementSpec] = []
    stats: SlideStats
    suspect_issues: List[str] = [] # "Low Res Image", "Non-Embed Font"

class DeckSpec(BaseModel):
    filename: str
    slide_count: int
    slides: List[SlideSpec] = []
