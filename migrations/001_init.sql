CREATE TABLE IF NOT EXISTS scrape_hits (
  item_id TEXT PRIMARY KEY,
  subreddit TEXT,
  author_token TEXT,
  body TEXT,
  created_utc TEXT,
  parent_id TEXT, link_id TEXT, permalink TEXT,
  keywords_hit TEXT,
  post_meta_json TEXT,
  inserted_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS detector_marks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  item_id TEXT REFERENCES scrape_hits(item_id),
  subreddit TEXT,
  comment_text TEXT,
  post_meta_json TEXT,
  reasoning_for_mark TEXT,
  rules_triggered TEXT,
  degree_of_confidence REAL,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS detector_acquittals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  item_id TEXT REFERENCES scrape_hits(item_id),
  subreddit TEXT,
  comment_text TEXT,
  post_meta_json TEXT,
  reasoning_for_acquittal TEXT,
  rules_triggered TEXT,
  degree_of_confidence REAL,
  created_at TEXT DEFAULT (datetime('now'))
);

-- Future placeholders (no use in Phase 1)
CREATE TABLE IF NOT EXISTS inquisitor_thoughts (id INTEGER PRIMARY KEY AUTOINCREMENT, item_id TEXT, text TEXT, meta TEXT, created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS inquisitor_discussions (id INTEGER PRIMARY KEY AUTOINCREMENT, thread_id TEXT, text TEXT, meta TEXT, created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS inquisitor_actions (id INTEGER PRIMARY KEY AUTOINCREMENT, item_id TEXT, action_type TEXT, payload TEXT, status TEXT, created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS summaries (id INTEGER PRIMARY KEY AUTOINCREMENT, scope TEXT, text TEXT, meta TEXT, created_at TEXT DEFAULT (datetime('now')));
