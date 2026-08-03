"""Built-in rules."""

from specforge_gate.rules.base import Rule
from specforge_gate.rules.structure import structural_rules
from specforge_gate.rules.wording import (
    CompoundRequirementRule,
    UntestableAcceptanceRule,
    VagueWordingRule,
)


def builtin_rules() -> tuple[Rule, ...]:
    return (
        *structural_rules(),
        VagueWordingRule(),
        UntestableAcceptanceRule(),
        CompoundRequirementRule(),
    )


__all__ = ["Rule", "builtin_rules"]
