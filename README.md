# InquisitorNet

## Functional module layout (scaffolded)
- Ingestion pipeline lives under `inquisitor/ingestion/` with CLI entry point `python -m inquisitor.ingestion.cli`.
- Policy gate lives under `inquisitor/policy/` with CLI wrapper `python -m inquisitor.policy.gate_cli`.
- Labeling utilities live under `inquisitor/labeling/` (`python -m inquisitor.labeling.label_cli`).
- Metrics job lives under `inquisitor/metrics/` and reports to `reports/metrics/` (scheduler at `tools/schedule_metrics.py`).
- Action planning stubs live under `inquisitor/operations/` (`inquisitor/operations/inquisitor_cli.py`, `inquisitor/operations/bots/base.py`).
