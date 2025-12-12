from typing import List, Dict
from ..schemas.slide_spec import DeckSpec
from ..schemas.template_spec import TemplateSpec
from .rules.registry import registry
from .rules.base import FindingSpec
# Import definitions to trigger registration
from .rules.definitions import basics 

class DeckLintEngine:
    def __init__(self):
        self.rules = registry.get_all_rules()

    def audit(self, deck: DeckSpec, template: TemplateSpec) -> List[FindingSpec]:
        all_findings = []
        
        for slide in deck.slides:
            for rule in self.rules:
                findings = rule.check(slide, template)
                all_findings.extend(findings)
                
        return all_findings

audit_engine = DeckLintEngine()
