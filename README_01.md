##  InquisitorNet - overview & deployment (added by ChatGPT)

*Warhammer 40,000*-flavoured Reddit bot network.  Each “Inquisitor” account can post, reply, and audit subreddits for *heresy*.

### Tech stack
* **Python 3.11** - single file `inquisitor_net.py` (needs modularisation).
* **PRAW 7.7**, **OpenAI API**, **APScheduler** for scheduling posts.
* SQLite via `DatabaseManager` (simple ORM wrapper).

<!-- ### Quick start
```bash
export REDDIT_CLIENT_ID=...
export REDDIT_CLIENT_SECRET=...
export REDDIT_USERNAME_VERAX=...
export OPENAI_API_KEY=...
pip install -r requirements.txt
python inquisitor_net.py  # starts scheduler
``` -->

### Problems spotted
1. Credentials are read from *plain* env vars - supply an `.env.example`.  
2. Bot personalities / templates hard‑coded - move to `json/yaml`.  
3. No tests: skeleton shown in `directory_structure.txt` but not committed.  
4. Heresy keyword lists are simplistic; consider embedding similarity instead.  
5. Long file (800+ LOC) - split into modules (`bots.py`, `database.py`, `scheduler.py`).

### Suggested enhancements
* Add rate‑limit + exception back‑off for Reddit API.  
* Replace polling with Reddit stream listeners.  
* Expose CLI (`python -m inquisitornet …`).  
* Dockerfile for containerised deployment.

---



---

# Ingestion pipeline (scraper + detector)

This repository now contains a **Phase 1 pipeline** that matches your latest scope:  
- **Set‑1 Scraper** with allow/avoid controls and a **fixtures** mode (default).  
- **Set‑2 Detector** using configurable regex **rules + weights** with an optional LLM explainer stub (noop by default).  
- **SQLite DB** schema for: `scrape_hits`, `detector_marks`, and `detector_acquittals` (plus placeholders for future phases).

## Quick start (fixtures mode)

```bash
python -m pip install -r requirements.txt
python -m inquisitor.ingestion.cli
# -> Scraper kept X items. Detector → marked Y, acquitted Z. DB: inquisitor_net_phase1.db
```

Config files (all editable at runtime):  
- `config/subreddits.yml` - allow/avoid lists and `mode: fixtures|api`.  
- `config/scraper_rules.yml` - include/exclude regex, discard rules, context fetch hints.  
- `config/detector_rules.yml` - rule patterns, weights, thresholds.

DB migrations: `migrations/001_init.sql`.

**Note:** Reddit API mode is scaffolded but not enabled in this Phase‑1 adaptation; use fixtures until your private sub is ready.


# Policy Gate, Labeling, and Metrics (dry-run)

## New commands
- Policy Gate (dry-run):
```
python -m inquisitor.policy.gate_cli --config config/policy_gate.yaml --input fixtures/drafts.jsonl --output tmp_gate.jsonl
```
- Label a small sample (auto-skip placeholder labels):
```
python -m inquisitor.labeling.label_cli --db inquisitor_net_phase1.db --mode auto-skip --sample 10
```
- Compute and store daily metrics:
```
python -m inquisitor.metrics.metrics_job --db inquisitor_net_phase1.db --since 7
```

## Notes
- The policy gate reads regex checks from `config/policy_gate.yml` (or `.yaml`).
- All Phase 2 writes are internal only (no public posting).
