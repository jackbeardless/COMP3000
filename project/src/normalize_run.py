import json
from pathlib import Path
from normalize import normalize_events

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"

def latest_spiderfoot_json() -> Path:
    files = sorted(RESULTS_DIR.glob("spiderfoot_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        raise FileNotFoundError("No spiderfoot_*.json files found in results/")
    return files[0]

def best_effort_target_from_filename(fp: Path) -> str:
    parts = fp.stem.split("_")
    if len(parts) >= 3:
        return parts[1]
    return "unknown"

if __name__ == "__main__":
    fp = latest_spiderfoot_json()
    target = best_effort_target_from_filename(fp)

    events = json.loads(fp.read_text(encoding="utf-8"))
    norm = normalize_events(target, events)

    out_path = RESULTS_DIR / f"normalized_{fp.stem}.json"
    out_path.write_text(json.dumps(norm, indent=2), encoding="utf-8")

    print("Input:", fp.name)
    print("Output:", out_path.name)
    print("Counts:", norm["counts"])
