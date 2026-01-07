# inquisitor/policy/gate.py
from __future__ import annotations
import re
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import yaml  # type: ignore
except Exception as e:  # pragma: no cover
    yaml = None

@dataclass
class GateRule:
    id: str
    pattern: str
    flags: int = re.IGNORECASE | re.MULTILINE
    weight: float = 1.0
    action: str = "flag"  # one of: note|flag|block
    category: str = "general"

    def compiled(self):
        return re.compile(self.pattern, self.flags)

@dataclass
class GateDecision:
    decision: str  # allow|flag|block
    reasons: List[Dict[str, Any]] = field(default_factory=list)
    llm_reason: Optional[str] = None

def load_rules(config_path: str | Path) -> List[GateRule]:
    path = Path(config_path)
    if yaml is None:
        raise RuntimeError("PyYAML is required to load gate rules")
    data = yaml.safe_load(path.read_text())
    rules = []
    for item in data.get("rules", []):
        rules.append(GateRule(
            id=item["id"],
            pattern=item["pattern"],
            weight=float(item.get("weight", 1.0)),
            action=item.get("action", "flag"),
            category=item.get("category", "general"),
        ))
    return rules

def evaluate_text(text: str, rules: List[GateRule]) -> GateDecision:
    hits = []
    block_score = 0.0
    flag_score = 0.0
    for rule in rules:
        m = rule.compiled().search(text or "")
        if not m:
            continue
        snippet = m.group(0)
        hit = {"id": rule.id, "category": rule.category, "action": rule.action, "weight": rule.weight, "snippet": snippet}
        hits.append(hit)
        if rule.action == "block":
            block_score += rule.weight
        elif rule.action == "flag":
            flag_score += rule.weight

    # Decision policy: any block hit -> block; else if flag_score >= 1 -> flag; else allow
    if any(h["action"] == "block" for h in hits):
        decision = "block"
    elif flag_score >= 1.0:
        decision = "flag"
    else:
        decision = "allow"
    return GateDecision(decision=decision, reasons=hits)


def evaluate_text_with_raw_matches(
    text: str,
    rules: List[GateRule],
) -> tuple[GateDecision, Dict[str, List[str]]]:
    hits = []
    raw_match: Dict[str, List[str]] = {}
    block_score = 0.0
    flag_score = 0.0
    for rule in rules:
        m = rule.compiled().search(text or "")
        if not m:
            continue
        snippet = m.group(0)
        raw_match.setdefault(rule.id, []).append(snippet)
        hit = {
            "id": rule.id,
            "category": rule.category,
            "action": rule.action,
            "weight": rule.weight,
            "snippet": snippet,
        }
        hits.append(hit)
        if rule.action == "block":
            block_score += rule.weight
        elif rule.action == "flag":
            flag_score += rule.weight

    if any(h["action"] == "block" for h in hits):
        decision = "block"
    elif flag_score >= 1.0:
        decision = "flag"
    else:
        decision = "allow"

    return GateDecision(decision=decision, reasons=hits), raw_match

# Optional LLM reasoning hook — pluggable provider, defaults to stub
class LLMProvider:
    def summarize(self, text: str, hits: List[Dict[str, Any]]) -> str:
        # basic heuristic explanation to avoid external calls by default
        cats = {}
        for h in hits:
            cats.setdefault(h["category"], 0)
            cats[h["category"]] += 1
        if not hits:
            return "No policy checks triggered; content appears compliant per current regex rules."
        parts = [f"{len(hits)} check(s) triggered."]
        if cats:
            parts.append("Categories: " + ", ".join(f"{k}×{v}" for k,v in cats.items()))
        return " ".join(parts)

def check_draft(text: str, config_path: str | Path, llm: Optional[LLMProvider] = None) -> GateDecision:
    rules = load_rules(config_path)
    decision = evaluate_text(text, rules)
    if llm is None:
        llm = LLMProvider()
    decision.llm_reason = llm.summarize(text, decision.reasons)
    return decision
