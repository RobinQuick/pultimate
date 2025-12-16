"""LLM service for mapping generation.

NO-GEN POLICY ENFORCED:
- LLM outputs only JSON mapping
- Strict schema validation
- No text generation
- Any non-JSON = hard failure
"""

import json
import logging

from pydantic import ValidationError

from core.config import settings
from schemas.mapping_schema import (
    DeckElement,
    LLMConfig,
    MappingResult,
    TemplatePlaceholder,
    validate_mapping_against_inputs,
)

logger = logging.getLogger(__name__)


class LLMServiceError(Exception):
    """Base exception for LLM service errors."""

    pass


class LLMValidationError(LLMServiceError):
    """Raised when LLM output fails validation."""

    def __init__(self, message: str, raw_output: str | None = None):
        super().__init__(message)
        self.raw_output = raw_output


class LLMProviderError(LLMServiceError):
    """Raised when LLM provider fails."""

    pass


# =============================================================================
# SYSTEM PROMPT (NO-GEN POLICY)
# =============================================================================

MAPPING_SYSTEM_PROMPT = """You are a PowerPoint mapping assistant. Your ONLY job is to output JSON.

RULES:
1. Output ONLY valid JSON - no explanations, no prose, no markdown
2. Map source elements to template placeholders by type compatibility
3. TITLE elements should map to TITLE placeholders
4. BODY/text elements should map to BODY/CONTENT placeholders
5. IMAGE elements should map to PICTURE placeholders
6. If no compatible placeholder exists, set action to "SKIP"
7. Each element can only be mapped once
8. Each placeholder can only be used once per slide

OUTPUT SCHEMA:
{
  "slide_mappings": [
    {
      "output_slide_index": 0,
      "layout_index": 0,
      "layout_name": "Title Slide",
      "element_mappings": [
        {
          "source_element_id": "slide_0_shape_2",
          "target_placeholder_id": "layout_0_ph_0",
          "action": "MAP",
          "target_layout_index": 0,
          "target_slide_index": 0,
          "reason": "Title to title placeholder"
        }
      ]
    }
  ],
  "skipped_elements": ["slide_0_shape_5"],
  "warnings": []
}

REMEMBER: Output ONLY the JSON object. No other text."""


def _build_mapping_prompt(
    elements: list[DeckElement],
    placeholders: list[TemplatePlaceholder],
) -> str:
    """Build user prompt for mapping request."""
    elements_json = [
        {
            "element_id": e.element_id,
            "slide_index": e.slide_index,
            "type": e.element_type.value,
            "text_preview": e.text_preview[:50] if e.text_preview else None,
        }
        for e in elements
    ]

    placeholders_json = [
        {
            "placeholder_id": p.placeholder_id,
            "layout_index": p.layout_index,
            "layout_name": p.layout_name,
            "type": p.placeholder_type.value,
        }
        for p in placeholders
    ]

    return f"""Map these source elements to template placeholders:

SOURCE ELEMENTS:
{json.dumps(elements_json, indent=2)}

TEMPLATE PLACEHOLDERS:
{json.dumps(placeholders_json, indent=2)}

Output the mapping JSON:"""


# =============================================================================
# PROVIDERS
# =============================================================================


def _call_openai(prompt: str, system_prompt: str, config: LLMConfig) -> str:
    """Call OpenAI API."""
    try:
        import openai

        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

        response = client.chat.completions.create(
            model=config.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            response_format={"type": "json_object"},
        )

        return response.choices[0].message.content or ""

    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        raise LLMProviderError(f"OpenAI API failed: {e}") from e


def _call_mock(prompt: str, system_prompt: str, config: LLMConfig) -> str:
    """Mock LLM for testing - returns minimal valid mapping."""
    logger.info("Using mock LLM provider")

    # Parse elements from prompt to generate mock mapping
    mock_mapping = {
        "slide_mappings": [
            {
                "output_slide_index": 0,
                "layout_index": 0,
                "layout_name": "Title Slide",
                "element_mappings": [],
            }
        ],
        "skipped_elements": [],
        "warnings": ["Mock LLM - no real mapping performed"],
    }

    return json.dumps(mock_mapping)


# =============================================================================
# MAIN SERVICE
# =============================================================================


def call_llm_for_mapping(
    elements: list[DeckElement],
    placeholders: list[TemplatePlaceholder],
    config: LLMConfig | None = None,
) -> MappingResult:
    """Call LLM to generate element-to-placeholder mapping.

    NO-GEN POLICY:
    - LLM only outputs JSON mapping
    - No content generation
    - Strict schema validation
    - Any failure = hard error

    Args:
        elements: Source deck elements
        placeholders: Template placeholders
        config: LLM configuration (uses settings defaults if None)

    Returns:
        Validated MappingResult

    Raises:
        LLMValidationError: If output fails validation
        LLMProviderError: If LLM call fails
    """
    if config is None:
        config = LLMConfig(
            provider=settings.LLM_PROVIDER,
            model=settings.LLM_MODEL,
            timeout=settings.LLM_TIMEOUT,
        )

    # Build prompts
    user_prompt = _build_mapping_prompt(elements, placeholders)
    system_prompt = MAPPING_SYSTEM_PROMPT

    logger.info(f"Calling LLM ({config.provider}/{config.model}) for mapping")
    logger.debug(f"Elements: {len(elements)}, Placeholders: {len(placeholders)}")

    # Call provider
    if config.provider == "mock":
        raw_output = _call_mock(user_prompt, system_prompt, config)
    elif config.provider == "openai":
        if not settings.OPENAI_API_KEY:
            raise LLMProviderError("OPENAI_API_KEY not configured")
        raw_output = _call_openai(user_prompt, system_prompt, config)
    elif config.provider == "google":
        if not settings.GOOGLE_API_KEY:
            raise LLMProviderError("GOOGLE_API_KEY not configured")
        raw_output = _call_google(user_prompt, system_prompt, config)
    else:
        raise LLMProviderError(f"Unknown provider: {config.provider}")

    # Parse JSON
    try:
        raw_json = json.loads(raw_output)
    except json.JSONDecodeError as e:
        logger.error(f"LLM output is not valid JSON: {raw_output[:500]}")
        raise LLMValidationError(f"Invalid JSON: {e}", raw_output=raw_output) from e

    # Validate against schema
    try:
        mapping = MappingResult.model_validate(raw_json)
    except ValidationError as e:
        logger.error(f"LLM output failed schema validation: {e}")
        raise LLMValidationError(f"Schema validation failed: {e}", raw_output=raw_output) from e

    # Validate references
    ref_errors = validate_mapping_against_inputs(mapping, elements, placeholders)
    if ref_errors:
        logger.error(f"Mapping references invalid: {ref_errors}")
        raise LLMValidationError(f"Invalid references: {ref_errors}", raw_output=raw_output)

    logger.info(f"LLM mapping complete: {len(mapping.slide_mappings)} slides, {len(mapping.skipped_elements)} skipped")

    return mapping
