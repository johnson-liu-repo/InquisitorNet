# inquisitor/policy/gate_cli.py
import argparse, json, sys
from pathlib import Path
from .gate import check_draft

def main():
    ap = argparse.ArgumentParser(description="Policy gate CLI")
    ap.add_argument("--config", default="config/policy_gate.yml", help="Path to policy gate YAML")
    ap.add_argument("--input", required=True, help="Path to JSONL file with {'text': ...} drafts")
    ap.add_argument("--output", default="policy_gate_results.jsonl", help="Where to write decisions")
    args = ap.parse_args()

    config_path = Path(args.config)
    input_path = Path(args.input)
    out_path = Path(args.output)

    n = 0
    with input_path.open() as f_in, out_path.open("w") as f_out:
        for line in f_in:
            if not line.strip():
                continue
            item = json.loads(line)
            text = item.get("text") or item.get("body") or ""
            decision = check_draft(text, config_path)
            record = {
                "input_id": item.get("id"),
                "decision": decision.decision,
                "reasons": decision.reasons,
                "llm_reason": decision.llm_reason
            }
            f_out.write(json.dumps(record) + "\n")
            n += 1

    print(f"Wrote {n} decisions to {out_path}")

if __name__ == "__main__":
    main()
