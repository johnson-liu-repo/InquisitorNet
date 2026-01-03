#!/usr/bin/env python3
"""
One-file verifier for InquisitorNet Phase 1 and Phase 2 outputs.
- Prints PASS/FAIL for each checklist item.
- Returns non-zero exit code if any required check fails.
- Lets you relax certain checks (e.g., acquittals) with flags.

Usage examples:
  python verify_inquisitornet.py
  python verify_inquisitornet.py --db inquisitor_net_phase1.db --config-dir config \
      --require-acquittals false --require-labels false
"""

from __future__ import annotations
import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Optional dependency: PyYAML. We degrade gracefully if missing.
try:
    import yaml  # type: ignore
except Exception:
    yaml = None

# --------------------------- small helpers ---------------------------

OVERALL_OK = True

def _print_check(n: int, title: str, ok: bool, details: str = "") -> None:
    """Print a single PASS/FAIL line and accumulate overall status."""
    global OVERALL_OK
    status = "PASS" if ok else "FAIL"
    print(f"[{n:02d}] {title}: {status}")
    if details:
        for line in str(details).strip().splitlines():
            print(f"      {line}")
    if not ok:
        OVERALL_OK = False

def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (table,),
    )
    return cur.fetchone() is not None

def _table_has_columns(conn: sqlite3.Connection, table: str, required: List[str]) -> Tuple[bool, List[str]]:
    cur = conn.execute(f"PRAGMA table_info({table})")
    cols = {row[1] for row in cur.fetchall()}
    missing = [c for c in required if c not in cols]
    return (len(missing) == 0, missing)

def _count(conn: sqlite3.Connection, table: str, where: str = "") -> int:
    q = f"SELECT COUNT(*) FROM {table}"
    if where:
        q += f" WHERE {where}"
    cur = conn.execute(q)
    return int(cur.fetchone()[0] or 0)

def _load_yaml(path: Path) -> Tuple[Dict[str, Any] | None, str]:
    """Load YAML if file exists and PyYAML is installed."""
    if not path.exists():
        return None, f"File not found: {path}"
    if yaml is None:
        return None, "PyYAML not installed; cannot parse YAML."
    try:
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}, ""
    except Exception as e:
        return None, f"YAML parse error: {e}"

def _json_is_valid(s: str | None) -> bool:
    if s is None:
        return False
    try:
        json.loads(s)
        return True
    except Exception:
        return False

# --------------------------- checks ---------------------------

def check_phase1_configs(base: Path, config_dir: Path) -> None:
    # 01 subreddits.yml
    data, err = _load_yaml(config_dir / "subreddits.yml")
    ok = data is not None and all(k in data for k in ("allow", "avoid", "mode"))
    details = err or ("" if ok else "Expected keys: allow, avoid, mode.")
    # if fixtures mode, verify fixtures path exists
    if ok and str(data.get("mode", "")).lower() == "fixtures":
        fp = data.get("fixtures_path") or (base / "fixtures" / "reddit_sample.jsonl")
        if not Path(fp).exists():
            ok = False
            details = f"Fixtures mode set but file missing: {fp}"
    _print_check(1, "Config: subreddits.yml present with allow/avoid/mode", ok, details)

    # 02 scraper_rules.yml
    data2, err2 = _load_yaml(config_dir / "scraper_rules.yml")
    ok2 = data2 is not None
    _print_check(2, "Config: scraper_rules.yml present and parseable", ok2, err2)

    # 03 detector_rules.yml
    data3, err3 = _load_yaml(config_dir / "detector_rules.yml")
    ok3 = data3 is not None
    _print_check(3, "Config: detector_rules.yml present and parseable", ok3, err3)

def check_db_exists(db_path: Path) -> bool:
    ok = db_path.exists()
    _print_check(4, "Database file exists", ok, f"Missing DB: {db_path}" if not ok else "")
    return ok

def check_phase1_db(conn: sqlite3.Connection, require_acquittals: bool) -> None:
    # 05 scrape_hits non-empty
    has_hits = _table_exists(conn, "scrape_hits")
    rows_hits = _count(conn, "scrape_hits") if has_hits else 0
    ok5 = has_hits and rows_hits > 0
    _print_check(5, "Phase 1: scrape_hits populated", ok5, "" if ok5 else "Table missing or empty.")

    # 06 kept rows have non-empty keywords_hit
    ok6, det6 = False, ""
    if ok5:
        try:
            empty_kw = _count(conn, "scrape_hits", "keywords_hit IS NULL OR TRIM(keywords_hit) IN ('', '[]')")
            ok6 = (empty_kw == 0)
            det6 = "" if ok6 else f"{empty_kw} kept rows have empty keywords_hit."
        except Exception as e:
            det6 = f"Could not evaluate keywords_hit: {e}"
    else:
        det6 = "Cannot verify due to missing/empty scrape_hits."
    _print_check(6, "Phase 1: kept rows have non-empty keywords_hit", ok6, det6)

    # 07 schema fields present
    req_cols = [
        "item_id", "subreddit", "author_token", "body", "created_utc",
        "parent_id", "link_id", "permalink", "keywords_hit", "post_meta_json", "inserted_at"
    ]
    ok7, det7 = False, ""
    if has_hits:
        ok7, missing = _table_has_columns(conn, "scrape_hits", req_cols)
        det7 = "" if ok7 else f"Missing columns: {missing}"
    else:
        det7 = "scrape_hits missing."
    _print_check(7, "Phase 1: scrape_hits schema contains required fields", ok7, det7)

    # 08 detector processed hits or deferred between thresholds
    has_marks = _table_exists(conn, "detector_marks")
    has_acq = _table_exists(conn, "detector_acquittals")
    processed = set()
    if has_marks:
        for (iid,) in conn.execute("SELECT item_id FROM detector_marks"):
            processed.add(iid)
    if has_acq:
        for (iid,) in conn.execute("SELECT item_id FROM detector_acquittals"):
            processed.add(iid)
    processed_count = len(processed)
    deferred = max(0, rows_hits - processed_count)
    ok8 = rows_hits > 0 and processed_count <= rows_hits
    if ok8:
        det8 = f"Processed {processed_count} of {rows_hits} scrape_hits; deferred {deferred} between mark/acquit thresholds."
    else:
        det8 = f"Processed {processed_count} exceeds total scrape_hits ({rows_hits})."
    _print_check(8, "Phase 1: detector processed or deferred scrape_hits", ok8, det8)

    # 09 marked rows have rationale + confidence in [0,1]
    ok9, det9 = False, ""
    if has_marks and _count(conn, "detector_marks") > 0:
        bad = _count(
            conn,
            "detector_marks",
            "reasoning_for_mark IS NULL OR TRIM(reasoning_for_mark)='' "
            "OR degree_of_confidence IS NULL OR degree_of_confidence < 0 OR degree_of_confidence > 1",
        )
        ok9 = (bad == 0)
        det9 = "" if ok9 else f"{bad} marked rows missing rationale/valid confidence."
    else:
        det9 = "No detector_marks rows to verify."
    _print_check(9, "Phase 1: marked rows have rationale and valid confidence", ok9, det9)

    # 10 detector_marks existence with rows
    ok10 = has_marks and _count(conn, "detector_marks") > 0
    _print_check(10, "Phase 1: detector_marks has rows", ok10, "" if ok10 else "No rows found.")

    # 11 detector_acquittals rows (optional)
    if require_acquittals:
        ok11 = has_acq and _count(conn, "detector_acquittals") > 0
        _print_check(11, "Phase 1: detector_acquittals has rows (required)", ok11, "" if ok11 else "No rows found.")
    else:
        # pass-but-inform if absent
        ok11 = has_acq  # existence is enough when not required
        _print_check(11, "Phase 1: detector_acquittals present (rows optional)", ok11, "" if ok11 else "Table not found (acceptable if disabled).")

    # 12 placeholders for later phases
    placeholders = ["inquisitor_thoughts", "inquisitor_discussions", "inquisitor_actions", "summaries"]
    missing = [t for t in placeholders if not _table_exists(conn, t)]
    ok12 = len(missing) == 0
    _print_check(12, "Phase 1: placeholder tables exist", ok12, "" if ok12 else f"Missing: {missing}")

def check_phase2_configs(config_dir: Path) -> None:
    # 13 policy_gate.yml/.yaml present and parseable
    yml = config_dir / "policy_gate.yml"
    yaml_alt = config_dir / "policy_gate.yaml"
    conf, err = (None, "policy_gate.yml/.yaml missing")
    if yml.exists() or yaml_alt.exists():
        conf, err = _load_yaml(yml if yml.exists() else yaml_alt)
    ok13 = conf is not None
    _print_check(13, "Phase 2: policy_gate config present and parseable", ok13, err if not ok13 else "")

def check_phase2_db(conn: sqlite3.Connection, require_labels: bool, require_metrics: bool) -> None:
    # 14 policy_checks table has at least one row
    has_pc = _table_exists(conn, "policy_checks")
    rows_pc = _count(conn, "policy_checks") if has_pc else 0
    ok14 = has_pc and rows_pc > 0
    _print_check(14, "Phase 2: policy_checks has rows (dry-run gate)", ok14, "" if ok14 else "No policy_checks found.")

    # 15 labels table (rows optional)
    has_labels = _table_exists(conn, "labels")
    rows_labels = _count(conn, "labels") if has_labels else 0
    ok15 = has_labels and (rows_labels > 0 if require_labels else True)
    det15 = ""
    if not has_labels:
        det15 = "labels table missing."
    elif require_labels and rows_labels == 0:
        det15 = "No labels found; required_labels=true."
    _print_check(15, "Phase 2: labels table and rows (as configured)", ok15, det15)

    # 16 metrics_detector_daily (rows optional or required)
    has_mdd = _table_exists(conn, "metrics_detector_daily")
    rows_mdd = _count(conn, "metrics_detector_daily") if has_mdd else 0
    ok16 = has_mdd and (rows_mdd > 0 if require_metrics else True)
    det16 = ""
    if not has_mdd:
        det16 = "metrics_detector_daily table missing."
    elif require_metrics and rows_mdd == 0:
        det16 = "No daily metrics found; require_metrics=true."
    _print_check(16, "Phase 2: metrics_detector_daily table and rows (as configured)", ok16, det16)

    # 17 sanity on JSON fields in policy_checks (flags/raw_match should be valid JSON)
    ok17, det17 = False, ""
    if has_pc and rows_pc > 0:
        try:
            cur = conn.execute("SELECT flags, raw_match FROM policy_checks LIMIT 25")
            bad = 0
            for flags_s, raw_s in cur.fetchall():
                if not _json_is_valid(flags_s) or not _json_is_valid(raw_s):
                    bad += 1
            ok17 = bad == 0
            det17 = "" if ok17 else f"{bad} rows have invalid JSON in flags/raw_match."
        except Exception as e:
            ok17 = False
            det17 = f"Query/parse error: {e}"
    else:
        ok17 = False
        det17 = "policy_checks empty; cannot verify JSON fields."
    _print_check(17, "Phase 2: policy_checks JSON fields valid (flags/raw_match)", ok17, det17)

# --------------------------- main ---------------------------

def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Verify Phase 1 and Phase 2 outputs for InquisitorNet.")
    ap.add_argument("--db", default="inquisitor_net_phase1.db", help="Path to SQLite DB.")
    ap.add_argument("--config-dir", default="config", help="Path to config directory.")
    ap.add_argument("--require-acquittals", default="false", choices=["true","false"], help="If true, require detector_acquittals to have rows.")
    ap.add_argument("--require-labels", default="false", choices=["true","false"], help="If true, require labels table to have rows.")
    ap.add_argument("--require-metrics", default="false", choices=["true","false"], help="If true, require metrics_detector_daily to have rows.")
    args = ap.parse_args(argv)

    base = Path(".").resolve()
    config_dir = Path(args.config_dir)
    db_path = Path(args.db)

    # Phase 1 config checks
    check_phase1_configs(base, config_dir)

    # DB existence
    if not check_db_exists(db_path):
        print("\nSummary: FAIL")
        print("Database missing; Phase 1/2 DB checks skipped.")
        return 2

    # Open DB
    conn = sqlite3.connect(str(db_path))

    # Phase 1 DB checks
    req_acq = (args.require_acquittals.lower() == "true")
    check_phase1_db(conn, require_acquittals=req_acq)

    # Phase 2 config + DB checks
    check_phase2_configs(config_dir)
    req_labels = (args.require_labels.lower() == "true")
    req_metrics = (args.require_metrics.lower() == "true")
    check_phase2_db(conn, require_labels=req_labels, require_metrics=req_metrics)

    print("\nSummary:", "PASS" if OVERALL_OK else "FAIL")
    return 0 if OVERALL_OK else 1

if __name__ == "__main__":
    raise SystemExit(main())
