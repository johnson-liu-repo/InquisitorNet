from pathlib import Path

from inquisitor.ingestion.detector import run_detector_to_db
from inquisitor.ingestion.scraper import run_scraper_to_db


def test_pipeline_scraper_to_detector(settings, db_conn):
    settings.subreddits["mode"] = "fixtures"
    fixtures_path = Path(__file__).parent / "fixtures" / "sample_reddit.jsonl"
    settings.subreddits["fixtures_path"] = str(fixtures_path)
    settings.subreddits["allow"] = ["AllowedSub"]
    settings.subreddits["avoid"] = []
    settings.scraper["keywords"] = {"include": ["(?i)heresy"], "exclude": []}
    settings.scraper["discard_if"] = []
    settings.scraper["discard_rules"] = {"min_length": 3}
    settings.detector = {
        "rules": [
            {"id": "H1", "name": "Heresy mention", "pattern": "(?i)heresy", "weight": 0.8, "exculpatory": []}
        ],
        "thresholds": {"mark": 0.7, "acquit": 0.2},
    }

    kept = run_scraper_to_db(settings, db_conn)
    marked, acquitted = run_detector_to_db(settings, db_conn)

    assert kept == 1
    assert marked == 1
    assert acquitted == 0
