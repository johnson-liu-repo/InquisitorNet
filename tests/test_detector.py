import json

from inquisitor.ingestion.detector import run_detector_to_db


def test_detector_marks_and_acquits(settings, db_conn):
    cur = db_conn.cursor()
    cur.execute(
        """
        INSERT INTO scrape_hits (item_id, subreddit, author_token, body, created_utc, parent_id, link_id, permalink, keywords_hit, post_meta_json)
        VALUES (?,?,?,?,?,?,?,?,?,?)
        """,
        (
            "t1_mark",
            "AllowedSub",
            "[USER]",
            "This is blatant heresy.",
            "2025-08-14T12:00:00Z",
            "t1_parent",
            "t3_link",
            "/r/AllowedSub/comments/xyz/t1_mark/",
            json.dumps(["heresy"]),
            json.dumps({}),
        ),
    )
    cur.execute(
        """
        INSERT INTO scrape_hits (item_id, subreddit, author_token, body, created_utc, parent_id, link_id, permalink, keywords_hit, post_meta_json)
        VALUES (?,?,?,?,?,?,?,?,?,?)
        """,
        (
            "t1_acquit",
            "AllowedSub",
            "[USER]",
            "A calm discussion about supplies.",
            "2025-08-14T12:10:00Z",
            "t1_parent",
            "t3_link",
            "/r/AllowedSub/comments/xyz/t1_acquit/",
            json.dumps([]),
            json.dumps({}),
        ),
    )
    db_conn.commit()

    settings.detector = {
        "rules": [
            {"id": "H1", "name": "Heresy mention", "pattern": "(?i)heresy", "weight": 0.8, "exculpatory": []}
        ],
        "thresholds": {"mark": 0.7, "acquit": 0.2},
    }

    marked, acquitted = run_detector_to_db(settings, db_conn)
    assert marked == 1
    assert acquitted == 1

    cur.execute("SELECT reasoning_for_mark, rules_triggered, degree_of_confidence FROM detector_marks")
    mark_row = cur.fetchone()
    assert "Inquisition" in mark_row[0]
    assert json.loads(mark_row[1]) == ["H1"]
    assert mark_row[2] == 0.8

    cur.execute("SELECT reasoning_for_acquittal, rules_triggered FROM detector_acquittals")
    acquit_row = cur.fetchone()
    assert "cleared" in acquit_row[0].lower()
    assert json.loads(acquit_row[1]) == []
