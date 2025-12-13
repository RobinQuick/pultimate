
from pydantic import BaseModel


class BoundingBox(BaseModel):
    x: float
    y: float
    width: float
    height: float

class TextStyle(BaseModel):
    font_family: str | None = None
    font_size: float | None = None
    is_bold: bool = False
    is_italic: bool = False
    color_hex: str | None = None
    alignment: str | None = None # LEFT, CENTER, RIGHT, JUSTIFY

class ElementSpec(BaseModel):
    id: str
    type: str # TEXT, SHAPE, IMAGE, TABLE, GROUP, CHART
    name: str
    bbox: BoundingBox
    rotation: float = 0.0
    z_order: int
    
    # Text Specific
    text_content: str | None = None
    text_style: TextStyle | None = None
    
    # Image Specific
    is_stretched: bool = False
    original_size: dict[str, float] | None = None
    
    # Shape Specific
    fill_color: str | None = None

class SlideStats(BaseModel):
    used_fonts: list[str] = []
    used_colors: list[str] = []
    text_coverage_pct: float = 0.0

class SlideSpec(BaseModel):
    index: int
    layout_name: str
    elements: list[ElementSpec] = []
    stats: SlideStats
    suspect_issues: list[str] = [] # "Low Res Image", "Non-Embed Font"

class DeckSpec(BaseModel):
    filename: str
    slide_count: int
    slides: list[SlideSpec] = []
