from pathlib import Path
import sqlite3
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from inquisitor.ingestion.config import Settings
from inquisitor.ingestion.db import migrate, column_exists


@pytest.fixture
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture
def settings(repo_root: Path) -> Settings:
    return Settings(repo_root)


@pytest.fixture
def db_conn(tmp_path: Path, repo_root: Path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    migrate(conn, repo_root / "migrations" / "001_init.sql")
    if not column_exists(conn, "detector_marks", "rules_triggered"):
        migrate(conn, repo_root / "migrations" / "005_rules_triggered.sql")
    return conn
