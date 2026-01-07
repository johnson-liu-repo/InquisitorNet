import yaml
from pathlib import Path

def load_yaml(path: str|Path):
    p = Path(path)
    with p.open('r', encoding='utf-8') as f:
        return yaml.safe_load(f)

class Settings:
    def __init__(self, base_dir: str|Path):
        base = Path(base_dir)
        self.base_path = base
        self.subreddits = load_yaml(base/'config'/'subreddits.yml')
        self.scraper = load_yaml(base/'config'/'scraper_rules.yml')
        self.detector = load_yaml(base/'config'/'detector_rules.yml')
        self.policy_gate_path = base/'config'/'policy_gate.yml'
        self.database_path = str(base/'inquisitor_net_phase1.db')
