import json
from pathlib import Path
from typing import Any, Dict

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"

def latest_clustered_json() -> Path:
    files = sorted(RESULTS_DIR.glob("clustered_normalized_spiderfoot_*.json"),
                   key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        raise FileNotFoundError("No clustered_normalized_spiderfoot_*.json files found in results/")
    return files[0]

def classify_status(cluster: Dict[str, Any]) -> str:
    """
    Simple deterministic labels to help the LLM / UI:
    - candidate_profile: looks like a profile page
    - invite_or_redirect: discord invite etc
    - search_or_tooling: archive/search/api etc
    - unknown_pattern: fallback
    """
    plat = (cluster.get("platform") or "unknown").lower()

    if plat in {"archive", "wikimedia"}:
        return "search_or_tooling"
    if plat == "discord":
        return "invite_or_redirect"

    # Use structured score_features from the updated cluster.py
    feature_names = {f.get("feature") for f in (cluster.get("score_features") or [])}
    if "profile_url" in feature_names:
        return "candidate_profile"
    if "non_profile_url" in feature_names:
        return "search_or_tooling"

    # weak fallback: if we at least have a handle, treat as candidate
    if cluster.get("handle"):
        return "candidate_profile"

    return "unknown_pattern"

def reduce_cluster_for_llm(target: str, cluster: Dict[str, Any]) -> Dict[str, Any]:
    plat = cluster.get("platform")
    key = cluster.get("key")
    handle = cluster.get("handle")
    cluster_id = f"{plat}:{key}"

    # Build a compact evidence summary
    # accounts[*].signals is list of dicts with module/source/from_event
    accounts = cluster.get("accounts") or []
    modules = set()
    event_types = set()
    sources = set()
    for a in accounts:
        for s in (a.get("signals") or []):
            if s.get("module"):
                modules.add(s["module"])
            if s.get("from_event"):
                event_types.add(s["from_event"])
            if s.get("source"):
                sources.add(s["source"])

    reduced = {
        "target": target,
        "cluster_id": cluster_id,
        "platform": plat,
        "handle": handle,
        "key": key,
        "urls": cluster.get("urls") or [],
        "display_names": cluster.get("display_names") or [],
        "metadata": cluster.get("metadata") or {},
        "signals": sorted(list(modules)),
        "event_types": sorted(list(event_types)),
        "sources": sorted(list(sources)),
        "heuristic_score": cluster.get("confidence", 0.0),
        "score_features": cluster.get("score_features") or [],
        "source_reliability": cluster.get("source_reliability", "unknown"),
        "status": classify_status(cluster),
        "account_count": len(accounts),
    }
    return reduced

def main() -> None:
    fp = latest_clustered_json()
    data = json.loads(fp.read_text(encoding="utf-8"))

    target = data.get("target") or ""
    clusters = data.get("clusters") or []
    breaches = data.get("breaches") or []

    reduced = [reduce_cluster_for_llm(target, c) for c in clusters]

    out = {
        "target": target,
        "input_file": fp.name,
        "counts": {
            "clusters": len(clusters),
            "breaches": len(breaches),
        },
        "clusters": reduced,
        "breaches": breaches,
    }

    out_path = RESULTS_DIR / f"llm_ready_{fp.stem}.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    print("Input:", fp.name)
    print("Output:", out_path.name)
    print("Clusters:", len(reduced))
    print("Top 5 (platform, handle, score, status):")
    for c in sorted(reduced, key=lambda x: x["heuristic_score"], reverse=True)[:5]:
        print("-", c["platform"], c.get("handle"), round(c["heuristic_score"], 3), c["status"])

if __name__ == "__main__":
    main()