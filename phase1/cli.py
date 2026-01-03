import argparse
from pathlib import Path
from phase1.config import Settings
from phase1.db import get_conn, migrate
from phase1.scraper import run_scraper_to_db
from phase1.detector import run_detector_to_db

BASE = Path(__file__).resolve().parents[1]

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

    kept = run_scraper_to_db(settings, conn)
    marked, acquitted = run_detector_to_db(settings, conn)
    print(f"Scraper kept {kept} items. Detector marked {marked}, acquitted {acquitted}. DB: {settings.database_path}")

if __name__ == "__main__":
    main()
