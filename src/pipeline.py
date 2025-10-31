from __future__ import annotations

from dataclasses import dataclass
import logging
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RuleDefinition:
    """Representeert een enkele guardrail-regel."""

    id: str
    pattern: str
    explanation: str
    category: str
    severity: str

    def compile(self) -> re.Pattern[str]:
        return re.compile(self.pattern, re.MULTILINE)


@dataclass(frozen=True)
class RuleMatch:
    """Information about a matched rule."""

    rule_id: str
    category: str
    severity: str
    explanation: str
    match_text: str
    start: int
    end: int


@dataclass
class PipelineResult:
    """Result of the pipeline evaluation."""

    prompt: str
    matches: List[RuleMatch]

    @property
    def is_blocked(self) -> bool:
        return bool(self.matches)

    @property
    def status(self) -> str:
        return "blocked" if self.is_blocked else "ok"

    def highest_severity(self) -> Optional[str]:
        if not self.matches:
            return None
        severities = [match.severity.lower() for match in self.matches]
        order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        return max(severities, key=lambda sev: order.get(sev, -1))

    def by_category(self) -> Dict[str, List[RuleMatch]]:
        grouped: Dict[str, List[RuleMatch]] = {}
        for match in self.matches:
            grouped.setdefault(match.category, []).append(match)
        return grouped


class GuardrailPipeline:
    """Pipeline that evaluates prompts against configured regex rules."""

    def __init__(self, rules: Iterable[RuleDefinition]):
        # Convert rules iterator to list and store compiled patterns
        self._rules = list(rules)
        self._compiled_rules = [(rule, rule.compile()) for rule in self._rules]

    @classmethod
    def from_yaml(cls, rules_path: Path) -> "GuardrailPipeline":
        # Log debug message for rules loading
        logger.debug("Loading guardrail rules from %s", rules_path)
        # Open and parse YAML file
        with rules_path.open("r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}

        # Extract categories from YAML
        categories = payload.get("categories", {})
        rules: List[RuleDefinition] = []

        # Iterate through categories to create rule definitions
        for category, metadata in categories.items():
            severity = metadata.get("severity", "medium")  # Default severity is medium
            for rule in metadata.get("rules", []):
                # Extract rule properties
                rule_id = rule.get("id")
                pattern = rule.get("pattern")
                explanation = rule.get("explanation", "")
                
                # Skip invalid rules
                if not rule_id or not pattern:
                    logger.warning("Skipping malformed rule in category '%s'", category)
                    continue
                
                # Create and append rule definition
                rules.append(
                    RuleDefinition(
                        id=rule_id,
                        pattern=pattern,
                        explanation=explanation,
                        category=category,
                        severity=severity,
                    )
                )

        return cls(rules)

    def evaluate(self, prompt: str) -> PipelineResult:
        # Log debug message for prompt evaluation
        logger.debug("Evaluating prompt of length %d", len(prompt))
        matches: List[RuleMatch] = []

        # Check each rule against the prompt
        for definition, compiled in self._compiled_rules:
            for match in compiled.finditer(prompt):
                matched_text = match.group(0)
                # Create match object for each pattern match
                matches.append(
                    RuleMatch(
                        rule_id=definition.id,
                        category=definition.category,
                        severity=definition.severity,
                        explanation=definition.explanation,
                        match_text=matched_text,
                        start=match.start(),
                        end=match.end(),
                    )
                )

        return PipelineResult(prompt=prompt, matches=matches)


__all__ = [
    "GuardrailPipeline",
    "PipelineResult",
    "RuleMatch",
    "RuleDefinition",
]