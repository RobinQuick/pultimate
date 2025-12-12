from pydantic import BaseModel,  Field
from typing import List, Optional, Dict

class RgbColor(BaseModel):
    r: int
    g: int
    b: int

class ThemeColors(BaseModel):
    # Simplified theme model
    dark1: Optional[RgbColor] = None
    light1: Optional[RgbColor] = None
    dark2: Optional[RgbColor] = None
    light2: Optional[RgbColor] = None
    accent1: Optional[RgbColor] = None
    accent2: Optional[RgbColor] = None
    accent3: Optional[RgbColor] = None
    accent4: Optional[RgbColor] = None
    accent5: Optional[RgbColor] = None
    accent6: Optional[RgbColor] = None

class ThemeFonts(BaseModel):
    major: str # Heading font
    minor: str # Body font

class PlaceholderSpec(BaseModel):
    idx: int
    type: str # TITLE, BODY, CTR_TITLE, SUBTITLE, DT, FTR, SLDNUM, OBJ, CHART, TBL, CLIPART, DGM, MEDIA, PIC
    name: str
    left: int
    top: int
    width: int
    height: int

class LayoutSpec(BaseModel):
    index: int # Internal index in the master
    name: str
    placeholders: List[PlaceholderSpec] = []

class MasterSpec(BaseModel):
    id: int # Internal ID/Index
    name: str # e.g. "Office Theme"
    layouts: List[LayoutSpec] = []

class TemplateSpec(BaseModel):
    version: str = "1.0"
    name: str
    theme_colors: ThemeColors
    theme_fonts: ThemeFonts
    masters: List[MasterSpec] = []
