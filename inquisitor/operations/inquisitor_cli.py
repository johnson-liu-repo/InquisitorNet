# inquisitor/operations/inquisitor_cli.py
import argparse, json, sqlite3
from pathlib import Path

from inquisitor.operations.bots.base import BaseBot, InquisitorPersonality
from inquisitor.policy.gate import check_draft

def ensure_operations_tables(conn):
    conn.execute("CREATE TABLE IF NOT EXISTS planned_actions (id INTEGER PRIMARY KEY AUTOINCREMENT, item_id TEXT, type TEXT, payload_json TEXT, status TEXT DEFAULT 'queued', created_at DATETIME DEFAULT CURRENT_TIMESTAMP)")
    conn.execute("CREATE TABLE IF NOT EXISTS dossiers (id INTEGER PRIMARY KEY AUTOINCREMENT, subject_token TEXT, markdown TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, visibility TEXT DEFAULT 'private')")

def create_dossier(mark: dict) -> str:
    # Minimal dossier format
    md = [f"# Dossier for item {mark.get('item_id','?')}",
          "## Summary", mark.get("rationale","(no rationale)"),
          "## Entities", "- Unknown",
          "## Claims", "- TBD",
          "## Contradictions", "- TBD",
          "## Recommendation", "- Review required"]
    return "\n".join(md)

def main():
    ap = argparse.ArgumentParser(description="Phase 3 inquisitor stub")
    ap.add_argument("--db", default="inquisitor_net.db")
    ap.add_argument("--marks-jsonl", required=True, help="Input marks (JSONL with item_id, score, rationale)")
    ap.add_argument("--policy-config", default="config/policy_gate.yml")
    args = ap.parse_args()

    bot = BaseBot(InquisitorPersonality(name="Verax"))
    with sqlite3.connect(args.db) as conn, open(args.marks_jsonl) as f:
        ensure_operations_tables(conn)
        for line in f:
            mark = json.loads(line)
            decision = bot.decide(mark)
            act = decision["planned_action"]
            # Gate any 'post' actions
            if act["type"] == "post":
                text = act["payload"].get("body","")
                d = check_draft(text, args.policy_config)
                if d.decision != "allow":
                    # downgrade to dossier if failed gate
                    act = {"type":"dossier", "payload":{"subject_token":"SUBJ-001"}}
            if act["type"] == "dossier":
                md = create_dossier(mark)
                conn.execute("INSERT INTO dossiers(subject_token, markdown) VALUES (?,?)", ("SUBJ-001", md))
            conn.execute("INSERT INTO planned_actions(item_id, type, payload_json, status) VALUES (?,?,?,?)", (mark.get("item_id","?"), act["type"], json.dumps(act["payload"]), "queued"))

if __name__ == "__main__":
    main()
