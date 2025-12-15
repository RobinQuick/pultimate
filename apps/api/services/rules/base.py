from abc import ABC, abstractmethod

from pydantic import BaseModel

from schemas.slide_spec import SlideSpec
from schemas.template_spec import TemplateSpec


class FindingSpec(BaseModel):
    rule_id: str
    slide_index: int
    element_id: str | None = None
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    message: str
    expected: str | None = None
    actual: str | None = None
    suggestion: str | None = None


class BaseRule(ABC):
    id: str = "base_rule"
    description: str = "Base Rule"
    severity: str = "MEDIUM"

    @abstractmethod
    def check(self, slide: SlideSpec, template: TemplateSpec) -> list[FindingSpec]:
        """
        Run the rule logic on a single slide against the template.
        """
        pass
