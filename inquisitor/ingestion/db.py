from pathlib import Path
import sqlite3

def get_conn(db_path: str|Path):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    return conn

def migrate(conn: sqlite3.Connection, sql_path: str|Path):
    with open(sql_path, 'r', encoding='utf-8') as f:
        sql = f.read()
    conn.executescript(sql)
    conn.commit()
