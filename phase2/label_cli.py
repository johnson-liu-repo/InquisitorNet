# phase2/label_cli.py
import argparse, sqlite3, sys
from pathlib import Path

DB_DEFAULT = "inquisitor_net_phase1.db"

SCHEMA = {
    "labels": "CREATE TABLE IF NOT EXISTS labels(item_id TEXT PRIMARY KEY, label TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)"
}

def ensure_schema(conn):
    for ddl in SCHEMA.values():
        conn.execute(ddl)

def sample_items(conn, near_threshold_only=False, limit=20):
    # Heuristic: sample from detector_marks plus near-threshold in a 'scores' view if available
    cur = conn.cursor()
    items = []
    try:
        if near_threshold_only:
            # Attempt to read detector_scores if exists; else fallback
            cur.execute("""
                SELECT item_id FROM detector_marks ORDER BY RANDOM() LIMIT ?
            """, (limit,))
        else:
            cur.execute("""
                SELECT item_id FROM detector_marks
                UNION
                SELECT item_id FROM detector_acquittals
                ORDER BY RANDOM() LIMIT ?
            """, (limit,))
        items = [r[0] for r in cur.fetchall()]
    except sqlite3.OperationalError:
        cur.execute("SELECT item_id FROM detector_marks ORDER BY RANDOM() LIMIT ?", (limit,))
        items = [r[0] for r in cur.fetchall()]
    return items

def label_loop(conn, items):
    print("Label items as TP/FP/TN/FN. Enter to skip. Ctrl+C to exit.")
    ensure_schema(conn)
    for it in items:
        print(f"Item: {it}")
        label = input("Label [TP/FP/TN/FN/skip]: ").strip().upper()
        if not label or label == "SKIP":
            continue
        if label not in {"TP","FP","TN","FN"}:
            print("Invalid label; skipping.")
            continue
        conn.execute("INSERT OR REPLACE INTO labels(item_id, label) VALUES (?,?)", (it, label))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DB_DEFAULT)
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--near-threshold", action="store_true")
    args = ap.parse_args()
    with sqlite3.connect(args.db) as conn:
        items = sample_items(conn, near_threshold_only=args.near_threshold, limit=args.limit)
        if not sys.stdin.isatty():
            print("Non-interactive session; listing items only:")
            for it in items:
                print(it)
            return
        label_loop(conn, items)

if __name__ == "__main__":
    main()
