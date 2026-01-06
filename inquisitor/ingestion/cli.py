import argparse
from pathlib import Path

from inquisitor.ingestion.config import Settings
from inquisitor.ingestion.db import get_conn, migrate, column_exists
from inquisitor.ingestion.scraper import run_scraper_to_db
from inquisitor.ingestion.detector import run_detector_to_db


# print(Path(__file__).resolve().parents[:])
BASE = Path(__file__).resolve().parents[2]
# print(BASE)


def main():
    ap = argparse.ArgumentParser(description="Phase 1 pipeline (scraper + detector)")
    ap.add_argument("--mode", choices=["fixtures", "api", "offline"], help="Override mode from config/subreddits.yml")
    ap.add_argument("--db", help="Override database path")
    args = ap.parse_args()

    settings = Settings(BASE)
    if args.mode:
        settings.subreddits["mode"] = args.mode
    if args.db:
        settings.database_path = args.db

    conn = get_conn(settings.database_path)
    migrate(conn, BASE / "migrations" / "001_init.sql")
    migrate(conn, BASE / "migrations" / "004_offline_fixtures.sql")
    if not column_exists(conn, "detector_marks", "rules_triggered"):
        migrate(conn, BASE / "migrations" / "005_rules_triggered.sql")

    kept = run_scraper_to_db(settings, conn)
    marked, acquitted = run_detector_to_db(settings, conn)
    print(f"Scraper kept {kept} items. Detector marked {marked}, acquitted {acquitted}. DB: {settings.database_path}")

if __name__ == "__main__":
    main()
