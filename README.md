##  InquisitorNet - overview & deployment

*Warhammer 40,000*-flavoured Reddit bot network.  Each “Inquisitor” account can post, reply, and audit subreddits for *heresy*.


# Ingestion pipeline (scraper + detector)

This repository now contains a pipeline that matches the **Phase 1** scope:  
- **Set‑1 Scraper** "bots" with allow/avoid controls and a **fixtures** mode (default).  
- **Set‑2 Detector** "bots" using configurable regex **rules + weights** with an optional LLM explainer stub (noop by default).  
- **SQLite DB** schema for: `scrape_hits`, `detector_marks`, and `detector_acquittals` (plus placeholders for future phases).