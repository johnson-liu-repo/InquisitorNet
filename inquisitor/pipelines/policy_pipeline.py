from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

from inquisitor.ingestion.config import Settings
from inquisitor.ingestion.db import migrate
from inquisitor.metrics.metrics_job import compute_metrics, write_metrics_to_db
from inquisitor.policy.gate import evaluate_text_with_raw_matches, load_rules
from inquisitor.policy.store import insert_policy_check


def _iter_drafts(path: Path) -> Iterable[dict]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            yield json.loads(line)


def run_policy_pipeline(
    settings: Settings,
    conn: sqlite3.Connection,
    *,
    drafts_path: Path,
    policy_config_path: Path,
    draft_scope: str = "fixtures",
    write_metrics: bool = True,
) -> int:
    migrate(conn, settings.base_path / "migrations" / "002_phase2.sql")
    rules = load_rules(policy_config_path)
    stored = 0
    for item in _iter_drafts(drafts_path):
        text = item.get("text") or item.get("body") or ""
        decision, raw_match = evaluate_text_with_raw_matches(text, rules)
        insert_policy_check(
            conn,
            draft_scope=draft_scope,
            draft_text=text,
            decision=decision,
            raw_match=raw_match,
        )
        stored += 1

    if write_metrics:
        metrics = compute_metrics(conn, days=7)
        write_metrics_to_db(conn, metrics)

    conn.commit()
    return stored
