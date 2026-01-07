# InquisitorNet - overview & deployment

*Warhammer 40,000*-flavoured Reddit bot network. Each "Inquisitor" account can post, reply, and audit subreddits for heresy.


### Ingestion pipeline (scraper + detector)

This repository now contains a pipeline that matches the **Phase 1** scope:  
- **Set 1 Scraper** "bots" with allow/avoid controls and a **fixtures** mode (default).  
- **Set 2 Detector** "bots" using configurable regex **rules + weights** with an optional LLM explainer stub (noop by default).  
- **SQLite DB** schema for: `scrape_hits`, `detector_marks`, and `detector_acquittals` (plus placeholders for future phases).

---

## Testing

### Phase 1

#### Test Run

1. Create/activate a venv:<br>
`python -m venv .venv`
1. Install deps:<br>
`pip install -r requirements.txt`
1. (Optional) Copy `.env.example` to `.env` and fill Reddit/OpenAI keys only if you plan to use api mode; fixtures mode needs none.
1. Run the Phase 1 pipeline in fixtures mode (uses `reddit_sample.jsonl`):<br>
`python -m inquisitor.ingestion.cli --mode fixtures --db inquisitor_net_phase1.db`<br>
Expect a summary like "Scraper kept X items. Detector marked Y, acquitted Z."
1. Verify the Definition of Done checks:<br>
`python verifications/phase1_acceptance_checklist.py --db inquisitor_net_phase1.db --config-dir config --fixtures-dir fixtures --verbose`
1. Alternate consolidated verifier (relaxes/controls acquittal requirements):<br>
`python verifications/verify_inquisitornet.py --db inquisitor_net_phase1.db --config-dir config --require-acquittals true`
1. Test offline-table mode instead of fixtures (load data into `fixtures_submissions` per `004_offline_fixtures.sql`):<br>
`python -m inquisitor.ingestion.cli --mode offline --db inquisitor_net_phase1.db`
1. Test live Reddit API mode (requires credentials in `.env`; keep `config/subreddits.yml` allowlist to private test subs):<br>
`python -m inquisitor.ingestion.cli --mode api --db inquisitor_net_phase1.db`

<br>

#### Check Output

**Kept (scrape_hits)**:<br>
`python -m sqlite3 inquisitor_net_phase1.db "SELECT item_id, subreddit, keywords_hit, body FROM scrape_hits ORDER BY item_id;"`

**Marked**:<br>
`python -m sqlite3 inquisitor_net_phase1.db "SELECT item_id, subreddit, rules_triggered, reasoning_for_mark FROM detector_marks ORDER BY item_id;"`

**Acquitted**:<br>
`python -m sqlite3 inquisitor_net_phase1.db "SELECT item_id, subreddit, rules_triggered, reasoning_for_acquittal FROM detector_acquittals ORDER BY item_id;"`

---

### Phase 2

#### Test Run

1. Run the policy gate pipeline against fixture drafts (persists to `policy_checks`):<br>
`python -m inquisitor.pipelines.cli --db inquisitor_net_phase1.db --drafts fixtures/drafts.jsonl --policy-config config/policy_gate.yml`
1. (Optional) Generate JSONL gate output and persist to DB via the policy CLI:<br>
`python -m inquisitor.policy.gate_cli --input fixtures/drafts.jsonl --config config/policy_gate.yml --db inquisitor_net_phase1.db --draft-scope fixtures`
1. Verify the Phase 2 checks (policy gate, labels, metrics are optional by default):<br>
`python verifications/verify_inquisitornet.py --db inquisitor_net_phase1.db --config-dir config --require-acquittals false --require-labels false --require-metrics false`

#### Check Output

**Policy checks**:<br>
`python -m sqlite3 inquisitor_net_phase1.db "SELECT id, draft_scope, allow, flags, raw_match, created_at FROM policy_checks ORDER BY id;"`
