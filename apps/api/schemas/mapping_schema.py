"""Strict Pydantic schemas for LLM mapping output.

NO-GEN POLICY ENFORCED:
- LLM outputs only JSON mapping
- No text generation
- No content modification
- Schema validation = hard failure if invalid
"""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ElementType(str, Enum):
    """Types of deck elements."""

    TITLE = "TITLE"
    BODY = "BODY"
    IMAGE = "IMAGE"
    TABLE = "TABLE"
    CHART = "CHART"
    SHAPE = "SHAPE"
    OTHER = "OTHER"


class PlaceholderType(str, Enum):
    """Types of template placeholders."""

    TITLE = "TITLE"
    BODY = "BODY"
    CONTENT = "CONTENT"
    PICTURE = "PICTURE"
    CHART = "CHART"
    TABLE = "TABLE"
    SUBTITLE = "SUBTITLE"
    FOOTER = "FOOTER"
    SLIDE_NUMBER = "SLIDE_NUMBER"
    DATE = "DATE"
    OTHER = "OTHER"


class MappingAction(str, Enum):
    """Actions for element mapping."""

    MAP = "MAP"  # Map element to placeholder
    SKIP = "SKIP"  # Skip this element (won't be in output)
    OVERFLOW = "OVERFLOW"  # Element overflows, needs new slide


# =============================================================================
# Deck Element Schema (Input to LLM)
# =============================================================================


class BoundingBox(BaseModel):
    """Bounding box coordinates."""

    x: float
    y: float
    width: float
    height: float


class DeckElement(BaseModel):
    """An element extracted from the source deck."""

    element_id: str = Field(..., description="Stable unique ID for this element")
    slide_index: int = Field(..., ge=0, description="0-based slide index")
    element_type: ElementType
    name: str | None = None
    bbox: BoundingBox
    text_preview: str | None = Field(None, max_length=200, description="First 200 chars of text if any")
    has_image: bool = False
    has_table: bool = False
    has_chart: bool = False


class DeckElementList(BaseModel):
    """List of all deck elements."""

    elements: list[DeckElement]
    slide_count: int


# =============================================================================
# Template Placeholder Schema (Input to LLM)
# =============================================================================


class TemplatePlaceholder(BaseModel):
    """A placeholder from the template."""

    placeholder_id: str = Field(..., description="Stable unique ID for this placeholder")
    layout_name: str
    layout_index: int = Field(..., ge=0)
    placeholder_type: PlaceholderType
    bbox: BoundingBox
    idx: int | None = Field(None, description="python-pptx placeholder idx")


class TemplatePlaceholderList(BaseModel):
    """List of all template placeholders."""

    placeholders: list[TemplatePlaceholder]
    layout_count: int


# =============================================================================
# LLM Mapping Output Schema (STRICT)
# =============================================================================


class ElementMapping(BaseModel):
    """Single element mapping decision from LLM.

    NO-GEN POLICY: This schema only allows mapping decisions.
    Any attempt to include generated content will fail validation.
    """

    source_element_id: str = Field(..., description="ID from DeckElement")
    target_placeholder_id: str | None = Field(None, description="ID from TemplatePlaceholder, null if SKIP")
    action: MappingAction
    target_layout_index: int | None = Field(None, ge=0, description="Layout index in template")
    target_slide_index: int | None = Field(None, ge=0, description="Target slide in output")
    reason: str | None = Field(None, max_length=100, description="Brief reason for decision")

    @field_validator("target_placeholder_id")
    @classmethod
    def validate_placeholder_for_action(cls, v, info):
        """Ensure placeholder is set for MAP action."""
        action = info.data.get("action")
        if action == MappingAction.MAP and v is None:
            raise ValueError("target_placeholder_id required when action is MAP")
        return v


class SlideMapping(BaseModel):
    """Mapping decisions for a single output slide."""

    output_slide_index: int = Field(..., ge=0)
    layout_index: int = Field(..., ge=0)
    layout_name: str
    element_mappings: list[ElementMapping]


class MappingResult(BaseModel):
    """Complete mapping result from LLM.

    NO-GEN POLICY ENFORCED:
    - Only contains mapping decisions
    - No generated text
    - No modified content
    - Strict schema validation
    """

    slide_mappings: list[SlideMapping]
    skipped_elements: list[str] = Field(default_factory=list, description="Element IDs that were skipped")
    warnings: list[str] = Field(default_factory=list, max_length=10)

    @field_validator("slide_mappings")
    @classmethod
    def validate_non_empty(cls, v):
        """Ensure at least one mapping."""
        if not v:
            raise ValueError("slide_mappings cannot be empty")
        return v


# =============================================================================
# LLM Request Schema
# =============================================================================


class MappingRequest(BaseModel):
    """Request sent to LLM for mapping.

    Minimal information to prevent content leakage.
    """

    elements: list[DeckElement]
    placeholders: list[TemplatePlaceholder]
    source_slide_count: int
    instructions: str = Field(
        default="Map each source element to the most appropriate template placeholder. "
        "Output ONLY valid JSON matching the schema. No explanations.",
        max_length=500,
    )


# =============================================================================
# LLM Provider Abstraction
# =============================================================================


class LLMConfig(BaseModel):
    """Configuration for LLM provider."""

    provider: Literal["openai", "anthropic", "mock"] = "openai"
    model: str = "gpt-4o-mini"
    timeout: int = Field(default=60, ge=10, le=300)
    max_tokens: int = Field(default=4000, ge=100, le=16000)
    temperature: float = Field(default=0.0, ge=0.0, le=1.0)  # 0 for deterministic


# =============================================================================
# Validation Helpers
# =============================================================================


def validate_mapping_against_inputs(
    mapping: MappingResult,
    elements: list[DeckElement],
    placeholders: list[TemplatePlaceholder],
) -> list[str]:
    """Validate that mapping references valid element and placeholder IDs.

    Returns list of validation errors (empty if valid).
    """
    errors = []

    element_ids = {e.element_id for e in elements}
    placeholder_ids = {p.placeholder_id for p in placeholders}

    for slide in mapping.slide_mappings:
        for em in slide.element_mappings:
            if em.source_element_id not in element_ids:
                errors.append(f"Unknown source element: {em.source_element_id}")
            if em.action == MappingAction.MAP and em.target_placeholder_id not in placeholder_ids:
                errors.append(f"Unknown target placeholder: {em.target_placeholder_id}")

    for skipped_id in mapping.skipped_elements:
        if skipped_id not in element_ids:
            errors.append(f"Unknown skipped element: {skipped_id}")

    return errors
