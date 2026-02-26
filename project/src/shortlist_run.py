import json
from pathlib import Path

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"

def latest_clustered_json() -> Path:
    files = sorted(RESULTS_DIR.glob("clustered_normalized_spiderfoot_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        raise FileNotFoundError("No clustered_normalized_spiderfoot_*.json files found in results/")
    return files[0]

if __name__ == "__main__":
    fp = latest_clustered_json()
    data = json.loads(fp.read_text(encoding="utf-8"))

    clusters = data.get("clusters", [])
    likely = [c for c in clusters if c.get("confidence", 0) >= 0.80]
    maybe  = [c for c in clusters if 0.50 <= c.get("confidence", 0) < 0.80]
    low    = [c for c in clusters if c.get("confidence", 0) < 0.50]

    out = {
        "target": data.get("target"),
        "input_file": fp.name,
        "counts": {
            "clusters": len(clusters),
            "likely": len(likely),
            "maybe": len(maybe),
            "low": len(low),
        },
        "likely": likely,
        "maybe": maybe,
        "low": low,
    }

    out_path = RESULTS_DIR / f"shortlist_{fp.stem}.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    print("Input:", fp.name)
    print("Output:", out_path.name)
    print("Counts:", out["counts"])