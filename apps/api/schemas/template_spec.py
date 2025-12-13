
from pydantic import BaseModel


class RgbColor(BaseModel):
    r: int
    g: int
    b: int

class ThemeColors(BaseModel):
    # Simplified theme model
    dark1: RgbColor | None = None
    light1: RgbColor | None = None
    dark2: RgbColor | None = None
    light2: RgbColor | None = None
    accent1: RgbColor | None = None
    accent2: RgbColor | None = None
    accent3: RgbColor | None = None
    accent4: RgbColor | None = None
    accent5: RgbColor | None = None
    accent6: RgbColor | None = None

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
    placeholders: list[PlaceholderSpec] = []

class MasterSpec(BaseModel):
    id: int # Internal ID/Index
    name: str # e.g. "Office Theme"
    layouts: list[LayoutSpec] = []

class TemplateSpec(BaseModel):
    version: str = "1.0"
    name: str
    theme_colors: ThemeColors
    theme_fonts: ThemeFonts
    masters: list[MasterSpec] = []
