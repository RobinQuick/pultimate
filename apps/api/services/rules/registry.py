from services.rules.base import BaseRule


class RuleRegistry:
    _rules: list[type[BaseRule]] = []

    @classmethod
    def register(cls, rule_cls: type[BaseRule]):
        cls._rules.append(rule_cls)
        return rule_cls

    @classmethod
    def get_all_rules(cls) -> list[BaseRule]:
        return [rule_cls() for rule_cls in cls._rules]


registry = RuleRegistry
