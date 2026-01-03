-- Offline pseudo-subreddit storage for local testing (no Reddit API)
CREATE TABLE IF NOT EXISTS fixtures_submissions (
  id TEXT PRIMARY KEY,
  subreddit TEXT,
  author TEXT,
  body TEXT,
  created_utc TEXT,
  parent_id TEXT,
  link_id TEXT,
  permalink TEXT,
  post_meta_json TEXT,
  inserted_at TEXT DEFAULT (datetime('now'))
);
