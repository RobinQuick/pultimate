from typing import List, Type
from .base import BaseRule

class RuleRegistry:
    _rules: List[Type[BaseRule]] = []

    @classmethod
    def register(cls, rule_cls: Type[BaseRule]):
        cls._rules.append(rule_cls)
        return rule_cls

    @classmethod
    def get_all_rules(cls) -> List[BaseRule]:
        return [rule_cls() for rule_cls in cls._rules]

registry = RuleRegistry
