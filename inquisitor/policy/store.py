from __future__ import annotations

import json
import sqlite3
from typing import Any, Dict

from inquisitor.policy.gate import GateDecision


def insert_policy_check(
    conn: sqlite3.Connection,
    *,
    draft_scope: str,
    draft_text: str,
    decision: GateDecision,
    raw_match: Dict[str, Any],
) -> None:
    flags = [reason["id"] for reason in decision.reasons]
    conn.execute(
        """
        INSERT INTO policy_checks (draft_scope, draft_text, allow, flags, reasons, raw_match)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            draft_scope,
            draft_text,
            decision.decision == "allow",
            json.dumps(flags),
            json.dumps(decision.reasons),
            json.dumps(raw_match),
        ),
    )
