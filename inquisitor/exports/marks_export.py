from __future__ import annotations

import json
import sqlite3
from pathlib import Path


def export_marks(conn: sqlite3.Connection, out_path: Path) -> int:
    cur = conn.execute(
        """
        SELECT item_id, degree_of_confidence, reasoning_for_mark
        FROM detector_marks
        ORDER BY inserted_at
        """
    )
    rows = cur.fetchall()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        for item_id, score, rationale in rows:
            payload = {
                "item_id": item_id,
                "score": float(score) if score is not None else 0.0,
                "rationale": rationale or "",
            }
            handle.write(json.dumps(payload) + "\n")
    return len(rows)
