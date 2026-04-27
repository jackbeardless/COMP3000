"""
pipeline_runner.py

Runs the OSINT pipeline steps in a background thread, sends progress
updates via an in-memory store, and writes results to Supabase.

Progress is stored in _progress[scan_id] as a list of dicts so that
the WebSocket endpoint can stream them to the client.
"""
import json
import os
import sys
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from config import settings
from database import get_admin_client

# Add project/src to path so pipeline modules are importable
_src = str(settings.pipeline_src_dir)
if _src not in sys.path:
    sys.path.insert(0, _src)

from contradiction_detector import detect_contradictions  # noqa: E402 (after sys.path patch)

# In-memory progress store: scan_id -> list of progress message dicts
_progress: dict[str, list[dict]] = {}


def _push(scan_id: str, step: str, status: str, message: str, done: bool = False):
    if scan_id not in _progress:
        _progress[scan_id] = []
    _progress[scan_id].append({
        "step": step,
        "status": status,
        "message": message,
        "done": done,
        "ts": datetime.now(timezone.utc).isoformat(),
    })


def get_progress(scan_id: str) -> list[dict]:
    return _progress.get(scan_id, [])


def clear_progress(scan_id: str):
    _progress.pop(scan_id, None)


def _update_scan_status(scan_id: str, status: str, error: Optional[str] = None):
    admin = get_admin_client()
    payload: dict = {"status": status}
    if status == "running":
        payload["started_at"] = datetime.now(timezone.utc).isoformat()
    if status in ("complete", "failed"):
        payload["completed_at"] = datetime.now(timezone.utc).isoformat()
    if error:
        payload["error"] = error
    admin.table("scans").update(payload).eq("id", scan_id).execute()


def _save_clusters_to_db(scan_id: str, final_json_path: Path):
    """Read the final LLM-judged JSON and insert each cluster into Supabase."""
    admin = get_admin_client()
    data = json.loads(final_json_path.read_text(encoding="utf-8"))

    all_clusters = data.get("shown", []) + data.get("hidden", [])
    breaches = data.get("breaches") or []

    # Annotate with contradiction flags before saving
    all_clusters = detect_contradictions(all_clusters)

    rows = []
    for c in all_clusters:
        rows.append({
            "scan_id": scan_id,
            "cluster_key": c.get("cluster_id") or f"{c.get('platform')}:{c.get('key')}",
            "platform": c.get("platform"),
            "handle": c.get("handle"),
            "urls": c.get("urls") or [],
            "heuristic_score": float(c.get("heuristic_score") or 0),
            "final_confidence": float(c.get("final_confidence") or 0),
            "verdict": c.get("verdict"),
            "llm_status": c.get("status"),
            "rationale": c.get("rationale"),
            "flags": c.get("flags") or [],
            "signals": c.get("signals") or [],
            "score_features": c.get("score_features") or [],
            "source_reliability": c.get("source_reliability") or "unknown",
            "contradiction_flags": c.get("contradiction_flags") or [],
            "raw_data": c,
        })

    if rows:
        admin.table("clusters").insert(rows).execute()

    return len(rows), breaches


def run_pipeline(scan_id: str, target: str, config: dict, target_type: str = "username"):  # target_type kept for signature compat
    """
    Synchronous pipeline runner — call this in a thread pool executor.

    Steps:
        1. (optional) SpiderFoot scan
        2. Normalise
        3. Cluster
        4. Reduce for LLM
        5. LLM judge (optional)
        6. Save clusters to Supabase
    """
    try:
        _update_scan_status(scan_id, "running")

        # ── Step 1: Data Collection (SpiderFoot + Sherlock + Maigret) ────
        if config.get("run_spiderfoot", True):
            _push(scan_id, "collect", "running", f"Running SpiderFoot for '{target}'…")
            import run_spiderfoot as sf
            sf_result = sf.run_spiderfoot_username_scan(target)
            all_events = list(sf_result["events"]) if isinstance(sf_result["events"], list) else []
            _push(scan_id, "collect", "running",
                  f"SpiderFoot: {sf_result['event_count']} events. Running Sherlock…")

            try:
                import run_sherlock
                sherlock_events = run_sherlock.run_sherlock_scan(target)
                all_events.extend(sherlock_events)
                _push(scan_id, "collect", "running",
                      f"Sherlock: {len(sherlock_events)} accounts found. Running Maigret…")
            except Exception as e:
                _push(scan_id, "collect", "running", f"Sherlock skipped: {e}")

            try:
                import run_maigret
                maigret_events = run_maigret.run_maigret_scan(target)
                all_events.extend(maigret_events)
                _push(scan_id, "collect", "running",
                      f"Maigret: {len(maigret_events)} accounts found.")
            except Exception as e:
                _push(scan_id, "collect", "running", f"Maigret skipped: {e}")

            # Overwrite SpiderFoot file with merged events so normalize_run picks it up
            Path(sf_result["output_file"]).write_text(
                json.dumps(all_events, ensure_ascii=False), encoding="utf-8"
            )
            _push(scan_id, "collect", "complete",
                  f"Data collection complete — {len(all_events)} total events.")
        else:
            _push(scan_id, "collect", "complete", "Skipped — using existing results file.")

        # ── Step 2: Normalise ─────────────────────────────────
        _push(scan_id, "normalize", "running", "Normalising events…")
        import normalize_run
        normalize_run.main()
        _push(scan_id, "normalize", "complete", "Normalisation complete.")

        # ── Step 3: Cluster + metadata enrichment ─────────────
        _push(scan_id, "cluster", "running", "Clustering accounts and fetching profile metadata…")
        import cluster_run
        cluster_run.main()
        _push(scan_id, "cluster", "complete", "Clustering and metadata enrichment complete.")

        # ── Step 4: Reduce for LLM ────────────────────────────
        _push(scan_id, "reduce", "running", "Preparing LLM-ready summaries…")
        import reduce_for_llm
        reduce_for_llm.main()
        _push(scan_id, "reduce", "complete", "Reduction complete.")

        # ── Step 5: LLM judge ─────────────────────────────────
        if config.get("skip_llm", False):
            _push(scan_id, "llm", "complete", "LLM step skipped.")
            # Use the clustered file as the final output
            from cluster_run import latest_normalized_json  # reuse path logic
            results_dir = settings.pipeline_src_dir.parent / "results"
            llm_files = sorted(
                results_dir.glob("llm_ready_clustered_normalized_spiderfoot_*.json"),
                key=lambda p: p.stat().st_mtime, reverse=True
            )
            final_path = llm_files[0] if llm_files else None
        else:
            _push(scan_id, "llm", "running", "Sending clusters to Gemini for judgement…")

            # Apply config to env vars for this run
            os.environ["OSINT_THRESHOLD"] = str(config.get("threshold", settings.osint_threshold))
            os.environ["OSINT_MODEL"] = config.get("model", settings.osint_model)
            os.environ["OSINT_BATCH_SIZE"] = str(config.get("batch_size", settings.osint_batch_size))
            os.environ["OSINT_SKIP_NOISE"] = "1" if config.get("skip_noise", True) else "0"
            os.environ["OSINT_DRY_RUN"] = "1" if config.get("dry_run", False) else "0"
            if settings.gemini_api_key:
                os.environ["GEMINI_API_KEY"] = settings.gemini_api_key

            known_info = config.get("known_info") or {}
            import llm_judge_gemini
            final_path = llm_judge_gemini.main(known_info=known_info or None)
            _push(scan_id, "llm", "complete", "LLM judgement complete.")

        # ── Step 6: Save to Supabase ──────────────────────────
        _push(scan_id, "saving", "running", "Saving results to database…")
        if final_path and Path(final_path).exists():
            count, breaches = _save_clusters_to_db(scan_id, Path(final_path))
            _push(scan_id, "saving", "complete", f"Saved {count} clusters to database.")
            if breaches:
                updated_config = dict(config)
                updated_config["breaches"] = breaches
                get_admin_client().table("scans").update({"config": updated_config}).eq("id", scan_id).execute()
        else:
            _push(scan_id, "saving", "complete", "No final output file found — nothing saved.")

        _update_scan_status(scan_id, "complete")
        _push(scan_id, "done", "complete", "Pipeline finished successfully.", done=True)

    except Exception as exc:
        error_msg = str(exc)
        _push(scan_id, "error", "failed", f"Pipeline failed: {error_msg}", done=True)
        _update_scan_status(scan_id, "failed", error=error_msg)


async def run_pipeline_async(scan_id: str, target: str, config: dict, target_type: str = "username"):
    """Async wrapper — runs the sync pipeline in a thread pool so it doesn't block FastAPI."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, run_pipeline, scan_id, target, config, target_type)
