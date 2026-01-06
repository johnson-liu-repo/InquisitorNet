from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional


@dataclass
class ReasoningResult:
    reasoning: str
    confidence: float


class LLMReasoningStub:
    def explain_mark(self, matched_rules: Iterable[str], score: float, threshold: float) -> ReasoningResult:
        rules = ", ".join(sorted(matched_rules)) if matched_rules else "unlisted omens"
        reasoning = (
            "By decree of the Inquisition, this utterance bears the stain of heresy. "
            f"Signs detected: {rules}. The matter warrants scrutiny under the Emperor's light."
        )
        confidence = min(1.0, max(0.0, score))
        return ReasoningResult(reasoning=reasoning, confidence=confidence)

    def explain_acquittal(
        self,
        matched_rules: Iterable[str],
        exculpatory_rules: Optional[Iterable[str]],
        score: float,
        threshold: float,
    ) -> ReasoningResult:
        if matched_rules:
            rules = ", ".join(sorted(matched_rules))
            reasoning = (
                "The utterance was examined for heresy and found wanting. "
                f"Minor signs were noted ({rules}), yet they fall below the threshold of censure."
            )
        else:
            reasoning = (
                "No heretical taint was discerned within the utterance. The subject is cleared."
            )
        if exculpatory_rules:
            exculp = ", ".join(sorted(exculpatory_rules))
            reasoning = f"{reasoning} Benign context observed: {exculp}."
        confidence = min(1.0, max(0.0, 1.0 - score))
        return ReasoningResult(reasoning=reasoning, confidence=confidence)
