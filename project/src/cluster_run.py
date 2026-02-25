import json
from pathlib import Path
from cluster import cluster_accounts

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"

def latest_normalized_json() -> Path:
    files = sorted(RESULTS_DIR.glob("normalized_spiderfoot_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        raise FileNotFoundError("No normalized_spiderfoot_*.json files found in results/")
    return files[0]

if __name__ == "__main__":
    fp = latest_normalized_json()
    data = json.loads(fp.read_text(encoding="utf-8"))

    target = data["target"]
    accounts = data.get("accounts", [])

    clusters = cluster_accounts(target, accounts)

    out = {
        "target": target,
        "input_file": fp.name,
        "counts": {
            "accounts": len(accounts),
            "clusters": len(clusters),
        },
        "clusters": clusters,
    }

    out_path = RESULTS_DIR / f"clustered_{fp.stem}.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    print("Input:", fp.name)
    print("Output:", out_path.name)
    print("Counts:", out["counts"])
    print("Top 5 clusters (platform, handle, confidence):")
    for c in clusters[:5]:
        print("-", c["platform"], c.get("handle"), round(c["confidence"], 3))