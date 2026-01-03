"""Thin Reddit client wrapper with basic pacing and JSON-friendly outputs."""
from __future__ import annotations

import time
from typing import Dict, Iterable, List, Optional

import praw


class RedditClient:
    def __init__(self, cfg: Dict[str, str], pause_seconds: float = 0.5):
        required = ["client_id", "client_secret", "username", "password"]
        missing = [k for k in required if not cfg.get(k)]
        if missing:
            raise ValueError(f"Missing Reddit credentials: {', '.join(missing)}")
        self.pause = pause_seconds
        self.reddit = praw.Reddit(
            client_id=cfg["client_id"],
            client_secret=cfg["client_secret"],
            password=cfg["password"],
            user_agent=cfg.get("user_agent", "InquisitorNetBot/0.1"),
            username=cfg["username"],
            ratelimit_seconds=60,
        )

    def stream_submissions(self, subs: List[str], limit: Optional[int] = None) -> Iterable[Dict]:
        for name in subs:
            sr = self.reddit.subreddit(name)
            for post in sr.new(limit=limit):
                yield {
                    "id": post.id,
                    "subreddit": str(post.subreddit),
                    "author": str(post.author) if post.author else "[DELETED]",
                    "body": post.selftext or post.title or "",
                    "created_utc": post.created_utc,
                    "permalink": post.permalink,
                    "link_id": post.id,
                    "parent_id": None,
                    "post_meta": {"score": post.score, "num_comments": post.num_comments},
                }
                time.sleep(self.pause)

    def stream_comments(self, subs: List[str], limit: Optional[int] = None) -> Iterable[Dict]:
        for name in subs:
            sr = self.reddit.subreddit(name)
            for c in sr.comments(limit=limit):
                yield {
                    "id": c.id,
                    "subreddit": str(c.subreddit),
                    "author": str(c.author) if c.author else "[DELETED]",
                    "body": c.body or "",
                    "created_utc": c.created_utc,
                    "permalink": c.permalink,
                    "link_id": c.link_id,
                    "parent_id": c.parent_id,
                    "post_meta": {"score": c.score},
                }
                time.sleep(self.pause)
