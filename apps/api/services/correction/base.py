from abc import ABC, abstractmethod

from pptx.slide import Slide
from pydantic import BaseModel

from ...schemas.template_spec import TemplateSpec
from ...services.rules.base import FindingSpec


class FixResult(BaseModel):
    finding_id: str | None = "custom"
    element_id: str
    action_taken: str
    status: str = "SUCCESS" # SUCCESS, SKIPPED, FAILED
    confidence: float = 1.0

class BaseFixer(ABC):
    rule_id: str # Matches the Rule ID this fixer addresses (e.g. FONT_MISMATCH)
    
    @abstractmethod
    def apply(self, slide: Slide, finding: FindingSpec, template: TemplateSpec) -> FixResult:
        """
        Apply the fix to the python-pptx Slide object in-place.
        """
        pass
