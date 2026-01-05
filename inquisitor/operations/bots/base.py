# inquisitor/operations/bots/base.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class InquisitorPersonality:
    name: str
    style: str = "formal"
    traits: Dict[str, Any] = None

class BaseBot:
    def __init__(self, persona: InquisitorPersonality):
        self.persona = persona

    def decide(self, mark: Dict[str, Any]) -> Dict[str, Any]:
        # Minimal rule: high score => post draft; medium => dossier; low => log
        score = float(mark.get("score", 0.0))
        if score >= 0.8:
            action = {"type":"post", "payload":{"title":"Draft: Heresy Found", "body": mark.get("rationale","")[:800]}}
            label = "heretical"
            priority = "high"
        elif score >= 0.5:
            action = {"type":"dossier", "payload":{"subject_token": "SUBJ-001"}}
            label = "uncertain"
            priority = "medium"
        else:
            action = {"type":"log", "payload":{}}
            label = "not_heretical"
            priority = "low"
        return {"label":label, "priority":priority, "rationale": mark.get("rationale",""), "planned_action": action}
