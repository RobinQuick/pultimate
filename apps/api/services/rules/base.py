from pydantic import BaseModel, Field
from typing import List, Optional, Any
from abc import ABC, abstractmethod
from ...schemas.slide_spec import SlideSpec, ElementSpec
from ...schemas.template_spec import TemplateSpec

class FindingSpec(BaseModel):
    rule_id: str
    slide_index: int
    element_id: Optional[str] = None
    severity: str # LOW, MEDIUM, HIGH, CRITICAL
    message: str
    expected: Optional[str] = None
    actual: Optional[str] = None
    suggestion: Optional[str] = None

class BaseRule(ABC):
    id: str = "base_rule"
    description: str = "Base Rule"
    severity: str = "MEDIUM"

    @abstractmethod
    def check(self, slide: SlideSpec, template: TemplateSpec) -> List[FindingSpec]:
        """
        Run the rule logic on a single slide against the template.
        """
        pass
