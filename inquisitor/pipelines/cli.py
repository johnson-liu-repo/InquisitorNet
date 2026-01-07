import argparse
from pathlib import Path

from inquisitor.ingestion.config import Settings
from inquisitor.ingestion.db import get_conn
from inquisitor.pipelines.policy_pipeline import run_policy_pipeline


def main() -> None:
    ap = argparse.ArgumentParser(description="Policy gate pipeline")
    ap.add_argument("--db", default=None, help="Path to SQLite DB")
    ap.add_argument("--drafts", default="fixtures/drafts.jsonl", help="Path to draft JSONL")
    ap.add_argument("--policy-config", default="config/policy_gate.yml", help="Policy gate YAML")
    ap.add_argument("--draft-scope", default="fixtures", help="Label for draft source")
    ap.add_argument("--skip-metrics", action="store_true", help="Skip metrics aggregation")
    args = ap.parse_args()

    base = Path(__file__).resolve().parents[2]
    settings = Settings(base)
    if args.db:
        settings.database_path = args.db

    conn = get_conn(settings.database_path)
    stored = run_policy_pipeline(
        settings,
        conn,
        drafts_path=Path(args.drafts),
        policy_config_path=Path(args.policy_config),
        draft_scope=args.draft_scope,
        write_metrics=not args.skip_metrics,
    )
    print(f"Stored {stored} policy decisions in {settings.database_path}")


if __name__ == "__main__":
    main()
