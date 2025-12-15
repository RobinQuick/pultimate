from abc import ABC, abstractmethod

from schemas.ai_rebuild import RebuildPlan, SlideIntent
from schemas.slide_spec import SlideSpec
from schemas.template_spec import TemplateSpec


class BaseAIProvider(ABC):
    @abstractmethod
    async def classify_intent(self, slide_spec: SlideSpec, image_bytes: bytes | None = None) -> SlideIntent:
        """
        Determines the semantic intent of a slide based on its content and visual appearance.
        """
        pass

    @abstractmethod
    async def generate_rebuild_plan(
        self, slide_spec: SlideSpec, slide_intent: SlideIntent, template: TemplateSpec
    ) -> RebuildPlan:
        """
        Generates a mapping strategy to move content from Source to Target Layout.
        MUST NOT hallucinate content. Output is purely structural mapping.
        """
        pass


class MockAIProvider(BaseAIProvider):
    async def classify_intent(self, slide_spec: SlideSpec, image_bytes: bytes | None = None) -> SlideIntent:
        # Simple heuristic rule-based mock
        # If > 5 text boxes -> Content 2 Col?
        return SlideIntent(slide_type="CONTENT_1_COL", description="Mock Classification", confidence=0.5)

    async def generate_rebuild_plan(
        self, slide_spec: SlideSpec, slide_intent: SlideIntent, template: TemplateSpec
    ) -> RebuildPlan:
        return RebuildPlan(
            source_slide_index=slide_spec.index,
            target_layout_index=1,  # Title and Content
            reasoning="Mock Plan: Moving everything to body placeholder",
            mappings=[],
        )
