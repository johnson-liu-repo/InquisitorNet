from pathlib import Path

from inquisitor.ingestion.scraper import run_scraper_to_db


def test_scraper_filters_allow_block_policy(settings, db_conn):
    settings.subreddits["mode"] = "fixtures"
    fixtures_path = Path(__file__).parent / "fixtures" / "sample_reddit.jsonl"
    settings.subreddits["fixtures_path"] = str(fixtures_path)
    settings.subreddits["allow"] = ["AllowedSub"]
    settings.subreddits["avoid"] = ["BlockedSub"]
    settings.scraper["keywords"] = {"include": ["(?i)heresy"], "exclude": []}
    settings.scraper["discard_if"] = []
    settings.scraper["discard_rules"] = {"min_length": 3}

    kept = run_scraper_to_db(settings, db_conn)
    assert kept == 1

    cur = db_conn.cursor()
    cur.execute("SELECT item_id, keywords_hit FROM scrape_hits")
    rows = cur.fetchall()
    assert len(rows) == 1
    assert rows[0][0] == "t1_allowed_hit"
    assert "heresy" in rows[0][1].lower()
