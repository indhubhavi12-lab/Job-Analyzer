import json
from pathlib import Path

DB_FILE = Path(__file__).resolve().parent / "seen_jobs.json"

def is_new_job(link):
    seen_jobs = _load_seen()
    if link in seen_jobs:
        return False
    seen_jobs.add(link)
    _save_seen(seen_jobs)
    return True

def _load_seen():
    if not DB_FILE.exists():
        return set()
    try:
        return set(json.loads(DB_FILE.read_text()))
    except:
        return set()

def _save_seen(seen_set):
    DB_FILE.write_text(json.dumps(list(seen_set)))