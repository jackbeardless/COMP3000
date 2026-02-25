# src/normalize_run.py
from __future__ import annotations

import json
import os
import re
from glob import glob
from typing import Any, Dict, List, Optional, Tuple

from normalize import normalize_events


def _latest_file(pattern: str) -> Optional[str]:
    files = glob(pattern)
    if not files:
        return None
    files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return files[0]


def _infer_target_from_filename(path: str) -> Optional[str]:
    # spiderfoot_<target>_<timestamp>.json
    base = os.path.basename(path)
    m = re.match(r"spiderfoot_(.+?)_\d+\.json$", base)
    if m:
        return m.group(1)
    return None


def _infer_target_from_events(events: List[Dict[str, Any]]) -> Optional[str]:
    # Prefer an explicit Username event's data
    for ev in events:
        if str(ev.get("type", "")).lower() == "username":
            v = ev.get("data")
            if isinstance(v, str) and v.strip():
                return v.strip()

    # Fallback: first event source or data
    if events:
        for key in ("source", "data"):
            v = events[0].get(key)
            if isinstance(v, str) and v.strip():
                return v.strip()

    return None


def _load_raw(path: str) -> Tuple[Optional[str], List[Dict[str, Any]]]:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # Case A: SpiderFoot output (top-level list)
    if isinstance(raw, list):
        events = [e for e in raw if isinstance(e, dict)]
        return None, events

    # Case B: wrapped dict format
    if isinstance(raw, dict):
        # try common keys
        target = raw.get("target") or raw.get("scan_target") or raw.get("scanTarget")
        # try common events keys
        events = raw.get("events") or raw.get("data") or raw.get("results") or []
        if not isinstance(events, list):
            events = []
        events = [e for e in events if isinstance(e, dict)]
        return target, events

    # Unknown format
    return None, []


def main() -> None:
    results_dir = os.path.join(os.path.dirname(__file__), "..", "results")
    results_dir = os.path.abspath(results_dir)

    latest = _latest_file(os.path.join(results_dir, "spiderfoot_*.json"))
    if not latest:
        raise SystemExit(f"No input files found in {results_dir} matching spiderfoot_*.json")

    raw_target, events = _load_raw(latest)
    if not events:
        raise SystemExit(f"Loaded 0 events from {latest} (unexpected).")

    # Infer target
    target = raw_target or _infer_target_from_filename(latest) or _infer_target_from_events(events) or "unknown"

    normalized = normalize_events(events, target=target)

    out_name = f"normalized_{os.path.basename(latest)}"
    out_path = os.path.join(results_dir, out_name)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(normalized, f, indent=2, ensure_ascii=False)

    print(f"\nInput:  {os.path.basename(latest)}")
    print(f"Output: {os.path.basename(out_path)}")
    print(f"Counts: {normalized.get('counts')}")


if __name__ == "__main__":
    main()